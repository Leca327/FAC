"""
Views do app medicamentos (seção 2.6.4).

Tela "Medicamentos" do paciente: cadastro dos remédios utilizados, em
visão de cards ou tabela, com busca e ordenação. Cadastro e edição são
feitos por popups (apenas familiares — RF).
"""

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views import View

from pacientes.services import PacienteService

from .forms import MedicamentoForm
from .services import MedicamentoService

__all__ = [
    "MedicamentosPacienteView",
    "NovoMedicamentoView",
    "EditarMedicamentoView",
    "DeletarMedicamentoView",
]


# Opções da barra de ferramentas (rótulo exibido no <select>)
ORDEM_OPCOES = [
    ("nome", "Nome"),
    ("recentes", "Mais recentes"),
]


def _lista_context(paciente, *, busca="", ordenar="nome", **extra):
    """Monta o contexto da tela de listagem, com extras opcionais."""
    context = {
        "paciente": paciente,
        "medicamentos": MedicamentoService.medicamentos_do_paciente(
            paciente, busca=busca, ordenar=ordenar
        ),
        "busca": busca,
        "ordenar": ordenar or "nome",
        "ordem_opcoes": ORDEM_OPCOES,
        "medicamento_form": MedicamentoForm(),
        "modal_aberto": False,
    }
    context.update(extra)
    return context


class MedicamentosPacienteView(LoginRequiredMixin, View):
    """Lista os medicamentos de um paciente (cards + tabela)."""

    template_name = "medicamentos/lista.html"

    def get(self, request, pk):
        paciente = PacienteService.paciente_acessivel(request.user, pk)
        if not paciente:
            messages.error(request, "Paciente não encontrado ou sem acesso.")
            return redirect("pacientes:dashboard")

        busca = request.GET.get("busca", "").strip()
        ordenar = request.GET.get("ordenar", "nome").strip()

        context = _lista_context(paciente, busca=busca, ordenar=ordenar)
        return render(request, self.template_name, context)


class NovoMedicamentoView(LoginRequiredMixin, View):
    """Cadastra um novo medicamento via popup (exclusivo de familiares)."""

    def post(self, request, pk):
        paciente = PacienteService.paciente_acessivel(request.user, pk)
        if not paciente:
            messages.error(request, "Paciente não encontrado ou sem acesso.")
            return redirect("pacientes:dashboard")
        if not request.user.is_familiar:
            messages.error(request, "Apenas familiares podem cadastrar medicamentos.")
            return redirect("medicamentos:lista", pk=paciente.pk)

        form = MedicamentoForm(request.POST)
        if form.is_valid():
            medicamento = MedicamentoService.criar_medicamento(
                paciente=paciente, form=form
            )
            messages.success(
                request, f"Medicamento {medicamento.nome} cadastrado com sucesso!"
            )
            return redirect("medicamentos:lista", pk=paciente.pk)

        # Erros de validação → reabre a lista com o popup de cadastro aberto
        context = _lista_context(paciente, medicamento_form=form, modal_aberto=True)
        return render(request, "medicamentos/lista.html", context)


class EditarMedicamentoView(LoginRequiredMixin, View):
    """Edita um medicamento via popup (exclusivo de familiares)."""

    def post(self, request, pk, medicamento_id):
        paciente = PacienteService.paciente_acessivel(request.user, pk)
        if not paciente:
            messages.error(request, "Paciente não encontrado ou sem acesso.")
            return redirect("pacientes:dashboard")
        if not request.user.is_familiar:
            messages.error(request, "Apenas familiares podem editar medicamentos.")
            return redirect("medicamentos:lista", pk=paciente.pk)

        medicamento = MedicamentoService.medicamento_acessivel(paciente, medicamento_id)
        if not medicamento:
            messages.error(request, "Medicamento não encontrado.")
            return redirect("medicamentos:lista", pk=paciente.pk)

        form = MedicamentoForm(request.POST, instance=medicamento)
        if form.is_valid():
            form.save()
            messages.success(request, f"Medicamento {medicamento.nome} atualizado.")
            return redirect("medicamentos:lista", pk=paciente.pk)

        # Erros de validação → reabre a lista com o popup de edição preenchido
        context = _lista_context(
            paciente,
            edit_modal_aberto=True,
            edit_action=reverse(
                "medicamentos:editar", args=[paciente.pk, medicamento.pk]
            ),
            edit_values=form.data,
            edit_errors=form.errors,
        )
        return render(request, "medicamentos/lista.html", context)


class DeletarMedicamentoView(LoginRequiredMixin, View):
    """Remove um medicamento do paciente (exclusivo de familiares)."""

    def post(self, request, pk, medicamento_id):
        paciente = PacienteService.paciente_acessivel(request.user, pk)
        if not paciente:
            messages.error(request, "Paciente não encontrado ou sem acesso.")
            return redirect("pacientes:dashboard")
        if not request.user.is_familiar:
            messages.error(request, "Apenas familiares podem remover medicamentos.")
            return redirect("medicamentos:lista", pk=paciente.pk)

        if MedicamentoService.deletar_medicamento(paciente=paciente, pk=medicamento_id):
            messages.success(request, "Medicamento removido.")
        else:
            messages.error(request, "Medicamento não encontrado.")
        return redirect("medicamentos:lista", pk=paciente.pk)
