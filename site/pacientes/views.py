"""
Views do app pacientes (seção 2.6.4).

A tela gerencial lista os pacientes vinculados ao usuário logado e
escolhe automaticamente a versão correta (Familiar ou Cuidador) conforme
o tipo do usuário — sem necessidade de alternância manual.
"""

import calendar
from datetime import date

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect, render
from django.utils import timezone
from django.views import View
from django.views.generic import TemplateView

from .forms import PacienteForm
from .services import PacienteService

__all__ = [
    "PacientesDashboardView",
    "NovoPacienteView",
    "VisaoGeralPacienteView",
    "AgendaPacienteView",
]

MESES_PT = [
    "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
    "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro",
]
DIAS_SEMANA_PT = ["Seg", "Ter", "Qua", "Qui", "Sex", "Sáb", "Dom"]


def modo_atual(request):
    """
    Modo de uso escolhido na tela de pacientes (familiar/cuidador), guardado
    na sessão. Pode ser alterado via ?modo=. Padrão: familiar (tema rosa).
    """
    novo = request.GET.get("modo")
    if novo in ("familiar", "cuidador"):
        request.session["modo"] = novo
    return request.session.get("modo", "familiar")


class PacientesDashboardView(LoginRequiredMixin, TemplateView):
    """
    Lista os pacientes do usuário conforme o MODO escolhido (Familiar/Cuidador).
    O toggle define quais pacientes aparecem e o layout/tema da tela.
    """

    def get_template_names(self):
        if self.request.session.get("modo") == "cuidador":
            return ["pacientes/dashboard_cuidador.html"]
        return ["pacientes/dashboard_familiar.html"]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        modo = modo_atual(self.request)
        busca = self.request.GET.get("busca", "").strip()
        context["modo"] = modo
        context["busca"] = busca
        context["pacientes"] = PacienteService.pacientes_do_usuario(
            self.request.user, busca, modo
        )
        # Formulário do popup "Novo Paciente" (cadastro no modo familiar)
        context.setdefault("paciente_form", PacienteForm())
        context.setdefault("modal_aberto", False)
        return context


class VisaoGeralPacienteView(LoginRequiredMixin, View):
    """
    Tela inicial do paciente (seção 2.6.4 — VisaoGeralPacienteView).

    Agrega informações do paciente, equipe, medicamentos do dia, próxima
    consulta e atividades recentes. Os blocos que dependem de apps ainda
    não implementados (agenda, medicamentos, ponto, diário) ficam com
    estado vazio até que esses apps sejam criados.
    """

    def get(self, request, pk):
        paciente = PacienteService.paciente_acessivel(request.user, pk)
        if not paciente:
            messages.error(request, "Paciente não encontrado ou sem acesso.")
            return redirect("pacientes:dashboard")

        from consultas.services import ConsultaService
        from medicamentos.services import MedicamentoService
        from prontuario.services import ProntuarioService
        from ponto.models import Plantao

        plantao_aberto = (
            Plantao.objects.filter(paciente=paciente, status=Plantao.Status.ABERTO)
            .select_related("cuidador")
            .order_by("hora_entrada")
            .first()
        )
        equipe = PacienteService.equipe_do_paciente(paciente)
        context = {
            "paciente": paciente,
            "cuidadores": equipe["cuidadores"],
            "familiares": equipe["familiares"],
            "medicamentos_hoje": MedicamentoService.medicamentos_do_dia(paciente),
            "doses_pendentes": MedicamentoService.contar_doses_pendentes(paciente),
            "proximas_doses": MedicamentoService.proximas_doses(paciente),
            "consultas_hoje": ConsultaService.contar_agendadas_hoje(paciente),
            "hoje": timezone.localdate(),
            # "Atividades Recentes": as 3 anotações mais recentes do prontuário.
            "atividades": ProntuarioService.ultimas_anotacoes(paciente, 3),
            # Cuidador do plantão aberto agora (se houver).
            "cuidador_plantao": plantao_aberto.cuidador if plantao_aberto else None,
        }
        return render(request, "pacientes/visao_geral.html", context)


class AgendaPacienteView(LoginRequiredMixin, View):
    """
    Agenda do paciente (RF05/RF08): calendário mensal, plantões da semana
    e compromissos do dia. Consultas e plantões dependem dos apps agenda/
    ponto (ainda não implementados) — por ora ficam com estado vazio.
    """

    template_name = "pacientes/agenda.html"

    def get(self, request, pk):
        paciente = PacienteService.paciente_acessivel(request.user, pk)
        if not paciente:
            messages.error(request, "Paciente não encontrado ou sem acesso.")
            return redirect("pacientes:dashboard")

        hoje = date.today()
        try:
            ano = int(request.GET.get("ano", hoje.year))
            mes = int(request.GET.get("mes", hoje.month))
            if not 1 <= mes <= 12:
                raise ValueError
        except (TypeError, ValueError):
            ano, mes = hoje.year, hoje.month

        # Dia selecionado (clicado). Padrão: hoje, se estiver no mês exibido.
        dias_no_mes = calendar.monthrange(ano, mes)[1]
        try:
            dia_sel = int(request.GET["dia"])
            if not 1 <= dia_sel <= dias_no_mes:
                raise ValueError
        except (KeyError, TypeError, ValueError):
            dia_sel = hoje.day if (ano == hoje.year and mes == hoje.month) else 1
        data_sel = date(ano, mes, dia_sel)

        # Consultas do mês (para mostrar os títulos no calendário).
        from consultas.services import ConsultaService

        consultas_mes = ConsultaService.consultas_do_mes(paciente, ano, mes)

        # Monta as semanas do mês (segunda a domingo)
        cal = calendar.Calendar(firstweekday=0)
        semanas = []
        for semana in cal.monthdatescalendar(ano, mes):
            semanas.append([
                {
                    "dia": d.day,
                    "hoje": d == hoje,
                    "mes_atual": d.month == mes,
                    "selecionado": d == data_sel,
                    "eventos": (
                        [c.titulo for c in consultas_mes.get(d.day, [])]
                        if d.month == mes else []
                    ),
                }
                for d in semana
            ])

        mes_anterior = (mes - 2) % 12 + 1
        ano_anterior = ano - 1 if mes == 1 else ano
        mes_seguinte = mes % 12 + 1
        ano_seguinte = ano + 1 if mes == 12 else ano

        if data_sel == hoje:
            painel_label = f"Hoje, {dia_sel} de {MESES_PT[mes - 1]} de {ano}"
        else:
            painel_label = f"{dia_sel} de {MESES_PT[mes - 1]} de {ano}"

        context = {
            "paciente": paciente,
            "ano": ano,
            "mes": mes,
            "semanas": semanas,
            "dias_semana": DIAS_SEMANA_PT,
            "mes_nome": f"{MESES_PT[mes - 1]} de {ano}",
            "nav_anterior": {"ano": ano_anterior, "mes": mes_anterior},
            "nav_seguinte": {"ano": ano_seguinte, "mes": mes_seguinte},
            "painel_label": painel_label,
            "eventos_dia": [
                {
                    "titulo": c.titulo,
                    "hora": timezone.localtime(c.data_hora).strftime("%H:%M"),
                    "tipo": c.get_tipo_display(),
                    "realizada": c.is_realizada,
                }
                for c in ConsultaService.consultas_do_dia(paciente, data_sel)
            ],
            # Placeholder até o app ponto existir:
            "plantoes_semana": [],
        }
        return render(request, self.template_name, context)


class NovoPacienteView(LoginRequiredMixin, View):
    """Cria um novo paciente via popup (RF03 — no modo familiar)."""

    def post(self, request):
        if modo_atual(request) != "familiar":
            messages.error(request, "Só é possível cadastrar pacientes no modo Familiar.")
            return redirect("pacientes:dashboard")

        form = PacienteForm(request.POST)
        if form.is_valid():
            paciente = PacienteService.criar_paciente(
                familiar=request.user, form=form
            )
            messages.success(request, f"Paciente {paciente.nome} cadastrado com sucesso!")
            return redirect("pacientes:dashboard")

        # Erros de validação → reabre o dashboard com o popup aberto
        context = {
            "modo": "familiar",
            "busca": "",
            "pacientes": PacienteService.pacientes_do_usuario(request.user, modo="familiar"),
            "paciente_form": form,
            "modal_aberto": True,
        }
        return render(request, "pacientes/dashboard_familiar.html", context)
