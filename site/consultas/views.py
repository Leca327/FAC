"""
Views do app consultas (tela "Consultas e Exames").

Espelha a Medicação Diária: lista por período (agrupada por dia), com
popups de Novo Agendamento, Editar e "Marcar como realizada" (que pede o
resultado). Familiares e cuidadores com acesso ao paciente podem operar.
"""

from datetime import datetime, timedelta

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views import View

from medicos.services import MedicoService
from pacientes.services import PacienteService

from .forms import ConsultaForm
from .services import ConsultaService

__all__ = [
    "ConsultasView",
    "NovaConsultaView",
    "EditarConsultaView",
    "DeletarConsultaView",
    "MarcarRealizadaView",
]


def _parse_data(valor, padrao):
    if valor:
        try:
            return datetime.strptime(valor, "%Y-%m-%d").date()
        except ValueError:
            pass
    return padrao


def _url_lista(paciente, de, ate):
    base = reverse("consultas:lista", args=[paciente.pk])
    return f"{base}?de={de:%Y-%m-%d}&ate={ate:%Y-%m-%d}"


def _periodo(request):
    """Lê de/ate (GET ou POST); padrão: hoje → hoje + 30 dias."""
    hoje = timezone.localdate()
    fonte = request.POST if request.method == "POST" else request.GET
    de = _parse_data(fonte.get("de"), hoje)
    ate = _parse_data(fonte.get("ate"), hoje + timedelta(days=30))
    return de, ate


def _contexto(paciente, de, ate, **extra):
    context = {
        "paciente": paciente,
        "dias": ConsultaService.consultas_periodo(paciente, de, ate),
        "de": de,
        "ate": ate,
        "consulta_form": ConsultaForm(paciente=paciente),
        "medicos": MedicoService.medicos_do_paciente(paciente),
        "modal_aberto": False,
    }
    context.update(extra)
    return context


class ConsultasView(LoginRequiredMixin, View):
    """Lista as consultas/exames de um paciente, agrupadas por dia."""

    template_name = "consultas/lista.html"

    def get(self, request, pk):
        paciente = PacienteService.paciente_acessivel(request.user, pk)
        if not paciente:
            messages.error(request, "Paciente não encontrado ou sem acesso.")
            return redirect("pacientes:dashboard")

        de, ate = _periodo(request)
        return render(request, self.template_name, _contexto(paciente, de, ate))


class NovaConsultaView(LoginRequiredMixin, View):
    """Agenda uma nova consulta/exame (popup)."""

    def post(self, request, pk):
        paciente = PacienteService.paciente_acessivel(request.user, pk)
        if not paciente:
            messages.error(request, "Paciente não encontrado ou sem acesso.")
            return redirect("pacientes:dashboard")

        de, ate = _periodo(request)
        form = ConsultaForm(request.POST, paciente=paciente)
        if form.is_valid():
            ConsultaService.criar(paciente=paciente, form=form, usuario=request.user)
            messages.success(request, "Agendamento criado com sucesso!")
            return redirect(_url_lista(paciente, de, ate))

        context = _contexto(paciente, de, ate, consulta_form=form, modal_aberto=True)
        return render(request, "consultas/lista.html", context)


class EditarConsultaView(LoginRequiredMixin, View):
    """Edita uma consulta/exame (popup)."""

    def post(self, request, pk, consulta_id):
        paciente = PacienteService.paciente_acessivel(request.user, pk)
        if not paciente:
            messages.error(request, "Paciente não encontrado ou sem acesso.")
            return redirect("pacientes:dashboard")

        de, ate = _periodo(request)
        consulta = ConsultaService.consulta_acessivel(paciente, consulta_id)
        if not consulta:
            messages.error(request, "Agendamento não encontrado.")
            return redirect(_url_lista(paciente, de, ate))

        form = ConsultaForm(request.POST, instance=consulta, paciente=paciente)
        if form.is_valid():
            form.save()
            messages.success(request, "Agendamento atualizado.")
        else:
            primeiro = next(iter(form.errors.values()))[0]
            messages.error(request, f"Não foi possível salvar: {primeiro}")
        return redirect(_url_lista(paciente, de, ate))


class DeletarConsultaView(LoginRequiredMixin, View):
    """Remove uma consulta/exame."""

    def post(self, request, pk, consulta_id):
        paciente = PacienteService.paciente_acessivel(request.user, pk)
        if not paciente:
            messages.error(request, "Paciente não encontrado ou sem acesso.")
            return redirect("pacientes:dashboard")

        de, ate = _periodo(request)
        if ConsultaService.deletar(paciente=paciente, pk=consulta_id):
            messages.success(request, "Agendamento removido.")
        else:
            messages.error(request, "Agendamento não encontrado.")
        return redirect(_url_lista(paciente, de, ate))


class MarcarRealizadaView(LoginRequiredMixin, View):
    """Marca/desmarca a consulta como realizada (popup pede o resultado)."""

    def post(self, request, pk, consulta_id):
        paciente = PacienteService.paciente_acessivel(request.user, pk)
        if not paciente:
            messages.error(request, "Paciente não encontrado ou sem acesso.")
            return redirect("pacientes:dashboard")

        de, ate = _periodo(request)
        consulta = ConsultaService.consulta_acessivel(paciente, consulta_id)
        if not consulta:
            messages.error(request, "Agendamento não encontrado.")
            return redirect(_url_lista(paciente, de, ate))

        # Botão "desmarcar" reverte para agendada; senão, marca como realizada.
        if request.POST.get("desmarcar"):
            ConsultaService.desmarcar_realizada(paciente=paciente, pk=consulta_id)
            messages.success(request, "Agendamento voltou para 'Agendada'.")
        else:
            ConsultaService.marcar_realizada(
                paciente=paciente,
                pk=consulta_id,
                resultado=request.POST.get("resultado", ""),
                usuario=request.user,
            )
            messages.success(request, "Agendamento marcado como realizado.")
        return redirect(_url_lista(paciente, de, ate))
