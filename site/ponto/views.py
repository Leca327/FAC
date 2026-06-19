"""
Views do app ponto (tela "Meu Ponto").

O cuidador inicia (check-in) e finaliza (check-out) seu plantão do dia, e vê
o histórico dos últimos plantões finalizados (com filtro por intervalo de
data). Familiares não registram ponto (apenas cuidadores).
"""

import csv
from datetime import datetime, timedelta

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views import View

from pacientes.services import PacienteService

from .services import (
    MESES_PT,
    ForaDoLocalError,
    MonitorService,
    PlantaoAbertoError,
    PontoService,
    SemPlantaoAbertoError,
)

__all__ = [
    "PontoView", "CheckInView", "CheckOutView", "EditarPontoView",
    "MonitoramentoView", "EditarPlantaoView", "ExcluirPlantaoView",
    "RelatorioCSVView",
]


def _parse_data(valor):
    if valor:
        try:
            return datetime.strptime(valor, "%Y-%m-%d").date()
        except ValueError:
            pass
    return None


def _parse_hora(valor):
    if valor:
        try:
            return datetime.strptime(valor, "%H:%M").time()
        except ValueError:
            pass
    return None


def _parse_coord(valor):
    try:
        return float(valor)
    except (TypeError, ValueError):
        return None


def _parse_mes(valor):
    """Lê 'YYYY-MM' (input type=month) → (ano, mes) ou None."""
    if valor:
        try:
            d = datetime.strptime(valor, "%Y-%m")
            return d.year, d.month
        except ValueError:
            pass
    return None


def _url_ponto(paciente):
    return reverse("ponto:meu", args=[paciente.pk])


class PontoView(LoginRequiredMixin, View):
    """Cartão de check-in/out de hoje + histórico de plantões finalizados."""

    template_name = "ponto/meu_ponto.html"

    def get(self, request, pk):
        paciente = PacienteService.paciente_acessivel(request.user, pk)
        if not paciente:
            messages.error(request, "Paciente não encontrado ou sem acesso.")
            return redirect("pacientes:dashboard")

        # Janela FIXA de 7 dias. Padrão: últimos 7 dias (hoje - 6 → hoje),
        # para o histórico já abrir mostrando os plantões finalizados recentes.
        # Qualquer intervalo informado é normalizado para 7 dias (a partir do
        # "de"); não se permite intervalo menor.
        de = _parse_data(request.GET.get("de"))
        ate = _parse_data(request.GET.get("ate"))
        hoje = timezone.localdate()
        if de is None:
            de = ate - timedelta(days=6) if ate else hoje - timedelta(days=6)
        ate = de + timedelta(days=6)

        context = {
            "paciente": paciente,
            "hoje": hoje,
            "estado": PontoService.estado_hoje(paciente, request.user),
            "historico": PontoService.historico_finalizados(
                paciente, request.user, de, ate
            ),
            "de": de,
            "ate": ate,
            "pode_registrar": request.user.is_cuidador,
        }
        return render(request, self.template_name, context)


class CheckInView(LoginRequiredMixin, View):
    """Inicia o plantão de hoje."""

    def post(self, request, pk):
        paciente = PacienteService.paciente_acessivel(request.user, pk)
        if not paciente:
            messages.error(request, "Paciente não encontrado ou sem acesso.")
            return redirect("pacientes:dashboard")
        if not request.user.is_cuidador:
            messages.error(request, "Apenas cuidadores podem registrar ponto.")
            return redirect(_url_ponto(paciente))

        try:
            PontoService.check_in(
                paciente=paciente,
                cuidador=request.user,
                latitude=_parse_coord(request.POST.get("lat")),
                longitude=_parse_coord(request.POST.get("lng")),
            )
            messages.success(request, "Check-in registrado. Bom trabalho!")
        except (PlantaoAbertoError, ForaDoLocalError) as erro:
            messages.error(request, str(erro))
        return redirect(_url_ponto(paciente))


class CheckOutView(LoginRequiredMixin, View):
    """Finaliza o plantão aberto de hoje."""

    def post(self, request, pk):
        paciente = PacienteService.paciente_acessivel(request.user, pk)
        if not paciente:
            messages.error(request, "Paciente não encontrado ou sem acesso.")
            return redirect("pacientes:dashboard")
        if not request.user.is_cuidador:
            messages.error(request, "Apenas cuidadores podem registrar ponto.")
            return redirect(_url_ponto(paciente))

        try:
            PontoService.check_out(paciente=paciente, cuidador=request.user)
            messages.success(request, "Check-out registrado. Até a próxima!")
        except SemPlantaoAbertoError as erro:
            messages.error(request, str(erro))
        return redirect(_url_ponto(paciente))


class EditarPontoView(LoginRequiredMixin, View):
    """Edita os horários do ponto de HOJE (somente o do dia atual)."""

    def post(self, request, pk):
        paciente = PacienteService.paciente_acessivel(request.user, pk)
        if not paciente:
            messages.error(request, "Paciente não encontrado ou sem acesso.")
            return redirect("pacientes:dashboard")
        if not request.user.is_cuidador:
            messages.error(request, "Apenas cuidadores podem editar o ponto.")
            return redirect(_url_ponto(paciente))

        entrada = _parse_hora(request.POST.get("entrada"))
        saida = _parse_hora(request.POST.get("saida"))
        if not entrada:
            messages.error(request, "Informe a hora de entrada.")
            return redirect(_url_ponto(paciente))

        try:
            PontoService.editar_hoje(
                paciente=paciente, cuidador=request.user,
                entrada=entrada, saida=saida,
            )
            messages.success(request, "Ponto de hoje atualizado.")
        except SemPlantaoAbertoError as erro:
            messages.error(request, str(erro))
        return redirect(_url_ponto(paciente))


# =====================================================
# Monitoramento (visão do familiar)
# =====================================================
def _url_monitor(paciente, dia=None, cuidador=""):
    base = reverse("ponto:monitoramento", args=[paciente.pk])
    params = []
    if dia:
        params.append(f"dia={dia:%Y-%m-%d}")
    if cuidador:
        params.append(f"cuidador={cuidador}")
    return f"{base}?{'&'.join(params)}" if params else base


class MonitoramentoView(LoginRequiredMixin, View):
    """Painel de acompanhamento dos plantões dos cuidadores (familiar)."""

    template_name = "ponto/monitoramento.html"

    def get(self, request, pk):
        paciente = PacienteService.paciente_acessivel(request.user, pk)
        if not paciente:
            messages.error(request, "Paciente não encontrado ou sem acesso.")
            return redirect("pacientes:dashboard")

        hoje = timezone.localdate()
        dia = _parse_data(request.GET.get("dia")) or hoje
        cuidador_id = request.GET.get("cuidador") or ""
        # Mês de referência do relatório/resumo (padrão: mês atual).
        ano, mes = _parse_mes(request.GET.get("mes")) or (hoje.year, hoje.month)

        context = {
            "paciente": paciente,
            "hoje": hoje,
            "mes_label": f"{MESES_PT[mes - 1].capitalize()} {ano}",
            "mes_sel": f"{ano:04d}-{mes:02d}",
            "resumo": MonitorService.resumo_mes(paciente, ano, mes),
            "em_plantao": MonitorService.em_plantao_agora(paciente),
            "plantao_dia": MonitorService.plantoes_do_dia(paciente, hoje),
            "relatorio": MonitorService.relatorio_mes(paciente, ano, mes),
            "cuidadores": MonitorService.cuidadores_equipe(paciente),
            # Seção de lista por dia (com edição/exclusão)
            "dia": dia,
            "cuidador_sel": cuidador_id,
            "lista": MonitorService.plantoes_do_dia(paciente, dia, cuidador_id or None),
        }
        return render(request, self.template_name, context)


class EditarPlantaoView(LoginRequiredMixin, View):
    """Edita um plantão (familiar — qualquer dia)."""

    def post(self, request, pk, plantao_id):
        paciente = PacienteService.paciente_acessivel(request.user, pk)
        if not paciente:
            messages.error(request, "Paciente não encontrado ou sem acesso.")
            return redirect("pacientes:dashboard")

        entrada = _parse_hora(request.POST.get("entrada"))
        saida = _parse_hora(request.POST.get("saida"))
        dia = _parse_data(request.POST.get("dia"))
        cuidador = request.POST.get("cuidador", "")
        if not entrada:
            messages.error(request, "Informe a hora de entrada.")
            return redirect(_url_monitor(paciente, dia, cuidador))

        if MonitorService.editar_plantao(
            paciente=paciente, plantao_id=plantao_id, entrada=entrada, saida=saida
        ):
            messages.success(request, "Plantão atualizado.")
        else:
            messages.error(request, "Plantão não encontrado.")
        return redirect(_url_monitor(paciente, dia, cuidador))


class ExcluirPlantaoView(LoginRequiredMixin, View):
    """Exclui um plantão (familiar)."""

    def post(self, request, pk, plantao_id):
        paciente = PacienteService.paciente_acessivel(request.user, pk)
        if not paciente:
            messages.error(request, "Paciente não encontrado ou sem acesso.")
            return redirect("pacientes:dashboard")

        dia = _parse_data(request.POST.get("dia"))
        cuidador = request.POST.get("cuidador", "")
        if MonitorService.excluir_plantao(paciente=paciente, plantao_id=plantao_id):
            messages.success(request, "Plantão excluído.")
        else:
            messages.error(request, "Plantão não encontrado.")
        return redirect(_url_monitor(paciente, dia, cuidador))


class RelatorioCSVView(LoginRequiredMixin, View):
    """Baixa o relatório de horas do mês em CSV."""

    def get(self, request, pk):
        paciente = PacienteService.paciente_acessivel(request.user, pk)
        if not paciente:
            messages.error(request, "Paciente não encontrado ou sem acesso.")
            return redirect("pacientes:dashboard")

        hoje = timezone.localdate()
        ano, mes = _parse_mes(request.GET.get("mes")) or (hoje.year, hoje.month)
        rel = MonitorService.relatorio_mes(paciente, ano, mes)
        resp = HttpResponse(content_type="text/csv; charset=utf-8")
        resp["Content-Disposition"] = (
            f'attachment; filename="relatorio_ponto_{ano:04d}_{mes:02d}.csv"'
        )
        resp.write("﻿")  # BOM para acentos no Excel
        w = csv.writer(resp, delimiter=";")
        w.writerow(["Cuidador", "Plantões", "Horas trabalhadas"])
        for l in rel["linhas"]:
            w.writerow([l["cuidador"], l["plantoes"], l["horas"]])
        w.writerow(["TOTAL", rel["total_plantoes"], rel["total_horas"]])
        return resp
