"""
Views do app medicos (seção 2.6.4).

Tela "Médicos" do paciente: cadastro dos médicos/clínicas/laboratórios,
em visão de cards ou tabela, com busca e ordenação. Cadastro e edição são
feitos por popups (apenas familiares — RF).
"""

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views import View

from pacientes.services import PacienteService

from .forms import MedicoForm
from .services import MedicoService

__all__ = [
    "MedicosPacienteView",
    "NovoMedicoView",
    "EditarMedicoView",
    "DeletarMedicoView",
]


ORDEM_OPCOES = [
    ("nome", "Nome"),
    ("recentes", "Mais recentes"),
]


def _lista_context(paciente, *, busca="", ordenar="nome", **extra):
    """Monta o contexto da tela de listagem, com extras opcionais."""
    context = {
        "paciente": paciente,
        "medicos": MedicoService.medicos_do_paciente(
            paciente, busca=busca, ordenar=ordenar
        ),
        "busca": busca,
        "ordenar": ordenar or "nome",
        "ordem_opcoes": ORDEM_OPCOES,
        "medico_form": MedicoForm(),
        "modal_aberto": False,
    }
    context.update(extra)
    return context


class MedicosPacienteView(LoginRequiredMixin, View):
    """Lista os médicos de um paciente (cards + tabela)."""

    template_name = "medicos/lista.html"

    def get(self, request, pk):
        paciente = PacienteService.paciente_acessivel(request.user, pk)
        if not paciente:
            messages.error(request, "Paciente não encontrado ou sem acesso.")
            return redirect("pacientes:dashboard")

        busca = request.GET.get("busca", "").strip()
        ordenar = request.GET.get("ordenar", "nome").strip()

        context = _lista_context(paciente, busca=busca, ordenar=ordenar)
        return render(request, self.template_name, context)


class NovoMedicoView(LoginRequiredMixin, View):
    """Cadastra um novo médico via popup (exclusivo de familiares)."""

    def post(self, request, pk):
        paciente = PacienteService.paciente_acessivel(request.user, pk)
        if not paciente:
            messages.error(request, "Paciente não encontrado ou sem acesso.")
            return redirect("pacientes:dashboard")
        if not request.user.is_familiar:
            messages.error(request, "Apenas familiares podem cadastrar médicos.")
            return redirect("medicos:lista", pk=paciente.pk)

        form = MedicoForm(request.POST)
        if form.is_valid():
            medico = MedicoService.criar_medico(paciente=paciente, form=form)
            messages.success(request, f"Médico {medico.nome} cadastrado com sucesso!")
            return redirect("medicos:lista", pk=paciente.pk)

        context = _lista_context(paciente, medico_form=form, modal_aberto=True)
        return render(request, "medicos/lista.html", context)


class EditarMedicoView(LoginRequiredMixin, View):
    """Edita um médico via popup (exclusivo de familiares)."""

    def post(self, request, pk, medico_id):
        paciente = PacienteService.paciente_acessivel(request.user, pk)
        if not paciente:
            messages.error(request, "Paciente não encontrado ou sem acesso.")
            return redirect("pacientes:dashboard")
        if not request.user.is_familiar:
            messages.error(request, "Apenas familiares podem editar médicos.")
            return redirect("medicos:lista", pk=paciente.pk)

        medico = MedicoService.medico_acessivel(paciente, medico_id)
        if not medico:
            messages.error(request, "Médico não encontrado.")
            return redirect("medicos:lista", pk=paciente.pk)

        form = MedicoForm(request.POST, instance=medico)
        if form.is_valid():
            form.save()
            messages.success(request, f"Médico {medico.nome} atualizado.")
            return redirect("medicos:lista", pk=paciente.pk)

        context = _lista_context(
            paciente,
            edit_modal_aberto=True,
            edit_action=reverse("medicos:editar", args=[paciente.pk, medico.pk]),
            edit_values=form.data,
            edit_errors=form.errors,
        )
        return render(request, "medicos/lista.html", context)


class DeletarMedicoView(LoginRequiredMixin, View):
    """Remove um médico do paciente (exclusivo de familiares)."""

    def post(self, request, pk, medico_id):
        paciente = PacienteService.paciente_acessivel(request.user, pk)
        if not paciente:
            messages.error(request, "Paciente não encontrado ou sem acesso.")
            return redirect("pacientes:dashboard")
        if not request.user.is_familiar:
            messages.error(request, "Apenas familiares podem remover médicos.")
            return redirect("medicos:lista", pk=paciente.pk)

        if MedicoService.deletar_medico(paciente=paciente, pk=medico_id):
            messages.success(request, "Médico removido.")
        else:
            messages.error(request, "Médico não encontrado.")
        return redirect("medicos:lista", pk=paciente.pk)
