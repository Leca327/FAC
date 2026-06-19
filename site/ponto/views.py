"""
Views do app ponto (tela "Meu Ponto").

O cuidador inicia (check-in) e finaliza (check-out) seu plantão do dia, e vê
o histórico dos últimos plantões finalizados (com filtro por intervalo de
data). Familiares não registram ponto (apenas cuidadores).
"""

from datetime import datetime

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views import View

from pacientes.services import PacienteService

from .services import (
    ForaDoLocalError,
    PlantaoAbertoError,
    PontoService,
    SemPlantaoAbertoError,
)

__all__ = ["PontoView", "CheckInView", "CheckOutView", "EditarPontoView"]


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

        de = _parse_data(request.GET.get("de"))
        ate = _parse_data(request.GET.get("ate"))

        context = {
            "paciente": paciente,
            "hoje": timezone.localdate(),
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
