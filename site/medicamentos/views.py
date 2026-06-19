"""
Views do app medicamentos (seção 2.6.4).

Tela "Medicamentos" do paciente: cadastro dos remédios utilizados, em
visão de cards ou tabela, com busca e ordenação. Cadastro e edição são
feitos por popups (apenas familiares — RF).
"""

from datetime import datetime, timedelta

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils import timezone
from django.utils.http import url_has_allowed_host_and_scheme
from django.views import View

from pacientes.services import PacienteService

from .forms import MedicamentoForm, RotinaPosologiaForm
from .services import DoseFuturaError, MedicamentoService

__all__ = [
    "MedicamentosPacienteView",
    "NovoMedicamentoView",
    "EditarMedicamentoView",
    "DeletarMedicamentoView",
    "MedicacaoDiariaView",
    "MarcarDoseView",
    "AdicionarRotinaView",
    "EditarRotinaView",
    "RemoverRotinaView",
]


def _parse_data(valor, padrao):
    """Converte 'YYYY-MM-DD' (input type=date) em date, ou usa o padrão."""
    if valor:
        try:
            return datetime.strptime(valor, "%Y-%m-%d").date()
        except ValueError:
            pass
    return padrao


def _url_diaria(paciente, de, ate):
    """URL da Medicação Diária preservando o período selecionado."""
    base = reverse("medicamentos:diaria", args=[paciente.pk])
    return f"{base}?de={de:%Y-%m-%d}&ate={ate:%Y-%m-%d}"


def _diaria_context(paciente, de, ate, **extra):
    """Contexto da tela de Medicação Diária, com extras opcionais."""
    context = {
        "paciente": paciente,
        "dias": MedicamentoService.rotina_periodo(paciente, de, ate),
        "de": de,
        "ate": ate,
        "rotina_form": RotinaPosologiaForm(),
        "medicamentos_disponiveis": MedicamentoService.medicamentos_fora_da_rotina(
            paciente
        ),
        "modal_aberto": False,
    }
    context.update(extra)
    return context


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


# =====================================================
# Tela "Medicação Diária" (rotina por período)
# =====================================================

class MedicacaoDiariaView(LoginRequiredMixin, View):
    """Rotina completa de medicamentos do paciente, agrupada por dia."""

    template_name = "medicamentos/diaria.html"

    def get(self, request, pk):
        paciente = PacienteService.paciente_acessivel(request.user, pk)
        if not paciente:
            messages.error(request, "Paciente não encontrado ou sem acesso.")
            return redirect("pacientes:dashboard")

        hoje = timezone.localdate()
        de = _parse_data(request.GET.get("de"), hoje)
        ate = _parse_data(request.GET.get("ate"), hoje + timedelta(days=6))

        context = _diaria_context(paciente, de, ate)
        return render(request, self.template_name, context)


class MarcarDoseView(LoginRequiredMixin, View):
    """Marca/desmarca uma dose como tomada (familiares e cuidadores)."""

    def post(self, request, pk):
        paciente = PacienteService.paciente_acessivel(request.user, pk)
        if not paciente:
            messages.error(request, "Paciente não encontrado ou sem acesso.")
            return redirect("pacientes:dashboard")

        hoje = timezone.localdate()
        de = _parse_data(request.POST.get("de"), hoje)
        ate = _parse_data(request.POST.get("ate"), hoje + timedelta(days=6))
        data_dose = _parse_data(request.POST.get("data"), hoje)
        horario = request.POST.get("horario", "").strip()
        medicamento_id = request.POST.get("medicamento_id")

        try:
            resultado = MedicamentoService.alternar_dose(
                paciente=paciente,
                medicamento_id=medicamento_id,
                data=data_dose,
                horario=horario,
                usuario=request.user,
            )
        except DoseFuturaError as erro:
            messages.error(request, str(erro))
            resultado = False
        else:
            if resultado is None:
                messages.error(request, "Medicamento não encontrado.")

        # Volta para a página de origem (ex.: Visão Geral) quando informada.
        destino = request.POST.get("next")
        if destino and url_has_allowed_host_and_scheme(
            destino, allowed_hosts={request.get_host()}
        ):
            return redirect(destino)
        return redirect(_url_diaria(paciente, de, ate))


class AdicionarRotinaView(LoginRequiredMixin, View):
    """
    Adiciona um remédio (já cadastrado) à rotina via popup. O remédio é
    escolhido num <select>; aqui só preenchemos a posologia. Exclusivo de
    familiares.
    """

    def post(self, request, pk):
        paciente = PacienteService.paciente_acessivel(request.user, pk)
        if not paciente:
            messages.error(request, "Paciente não encontrado ou sem acesso.")
            return redirect("pacientes:dashboard")
        if not request.user.is_familiar:
            messages.error(request, "Apenas familiares podem alterar a rotina.")
            return redirect("medicamentos:diaria", pk=paciente.pk)

        hoje = timezone.localdate()
        de = _parse_data(request.POST.get("de"), hoje)
        ate = _parse_data(request.POST.get("ate"), hoje + timedelta(days=6))

        medicamento = MedicamentoService.medicamento_acessivel(
            paciente, request.POST.get("medicamento")
        )
        form = RotinaPosologiaForm(request.POST, instance=medicamento)

        if medicamento and form.is_valid():
            form.save()
            messages.success(request, f"{medicamento.nome} adicionado à rotina.")
            return redirect(_url_diaria(paciente, de, ate))

        if not medicamento:
            messages.error(request, "Selecione um remédio cadastrado.")

        # Erros → reabre a tela com o popup aberto e os erros preenchidos.
        context = _diaria_context(
            paciente, de, ate,
            rotina_form=form,
            medicamento_selecionado=request.POST.get("medicamento") or "",
            modal_aberto=True,
        )
        return render(request, "medicamentos/diaria.html", context)


class EditarRotinaView(LoginRequiredMixin, View):
    """Edita um remédio da rotina via popup (exclusivo de familiares)."""

    def post(self, request, pk, medicamento_id):
        paciente = PacienteService.paciente_acessivel(request.user, pk)
        if not paciente:
            messages.error(request, "Paciente não encontrado ou sem acesso.")
            return redirect("pacientes:dashboard")
        if not request.user.is_familiar:
            messages.error(request, "Apenas familiares podem alterar a rotina.")
            return redirect("medicamentos:diaria", pk=paciente.pk)

        hoje = timezone.localdate()
        de = _parse_data(request.POST.get("de"), hoje)
        ate = _parse_data(request.POST.get("ate"), hoje + timedelta(days=6))

        medicamento = MedicamentoService.medicamento_acessivel(paciente, medicamento_id)
        if not medicamento:
            messages.error(request, "Medicamento não encontrado.")
            return redirect(_url_diaria(paciente, de, ate))

        form = RotinaPosologiaForm(request.POST, instance=medicamento)
        if form.is_valid():
            form.save()
            messages.success(request, f"Rotina de {medicamento.nome} atualizada.")
        else:
            primeiro = next(iter(form.errors.values()))[0]
            messages.error(request, f"Não foi possível salvar: {primeiro}")
        return redirect(_url_diaria(paciente, de, ate))


class RemoverRotinaView(LoginRequiredMixin, View):
    """
    Remove o remédio da rotina limpando apenas a posologia (quantidade,
    horários, período, dias, observação). O cadastro do remédio é mantido.
    Exclusivo de familiares.
    """

    def post(self, request, pk, medicamento_id):
        paciente = PacienteService.paciente_acessivel(request.user, pk)
        if not paciente:
            messages.error(request, "Paciente não encontrado ou sem acesso.")
            return redirect("pacientes:dashboard")
        if not request.user.is_familiar:
            messages.error(request, "Apenas familiares podem alterar a rotina.")
            return redirect("medicamentos:diaria", pk=paciente.pk)

        hoje = timezone.localdate()
        de = _parse_data(request.POST.get("de"), hoje)
        ate = _parse_data(request.POST.get("ate"), hoje + timedelta(days=6))

        if MedicamentoService.remover_da_rotina(paciente=paciente, pk=medicamento_id):
            messages.success(
                request, "Remédio removido da rotina (cadastro mantido em Medicamentos)."
            )
        else:
            messages.error(request, "Medicamento não encontrado.")
        return redirect(_url_diaria(paciente, de, ate))
