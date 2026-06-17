"""
Views do app familia (tela "Família").

Lista os membros da família em cards ou tabela (formato medicamentos/médicos),
com filtro de status em menu suspenso (Todos/Aceitos/Pendentes) e o sistema
de convites (convidar, reenviar, cancelar, aceitar).
"""

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect, render
from django.views import View

from pacientes.services import PacienteService

from .forms import ConvidarMembroForm, EditarMembroForm
from .services import MembroFamiliaService

__all__ = [
    "FamiliaView",
    "ConvidarMembroView",
    "EditarMembroView",
    "RemoverMembroView",
    "ReenviarConviteView",
    "AceitarConviteView",
]

TEMPLATE_LISTA = "familia/lista.html"


def _contexto(paciente, *, status="todos", **extra):
    filtro = status if status in ("aceito", "pendente") else None
    context = {
        "paciente": paciente,
        "status": status or "todos",
        "membros": MembroFamiliaService.membros(paciente, filtro),
        "contagens": MembroFamiliaService.contagens(paciente),
        "convidar_form": ConvidarMembroForm(),
        "modal_aberto": False,
    }
    context.update(extra)
    return context


class FamiliaView(LoginRequiredMixin, View):
    """Lista os membros da família (cards + tabela), com filtro de status."""

    def get(self, request, pk):
        paciente = PacienteService.paciente_acessivel(request.user, pk)
        if not paciente:
            messages.error(request, "Paciente não encontrado ou sem acesso.")
            return redirect("pacientes:dashboard")

        status = request.GET.get("status", "todos").strip()
        return render(request, TEMPLATE_LISTA, _contexto(paciente, status=status))


class ConvidarMembroView(LoginRequiredMixin, View):
    """Convida um novo membro da família (exclusivo de familiares)."""

    def post(self, request, pk):
        paciente = PacienteService.paciente_acessivel(request.user, pk)
        if not paciente:
            messages.error(request, "Paciente não encontrado ou sem acesso.")
            return redirect("pacientes:dashboard")
        if not request.user.is_familiar:
            messages.error(request, "Apenas familiares podem convidar membros.")
            return redirect("familia:lista", pk=paciente.pk)

        form = ConvidarMembroForm(request.POST)
        if form.is_valid():
            membro = MembroFamiliaService.convidar(
                paciente=paciente, form=form, convidado_por=request.user, request=request
            )
            messages.success(request, f"Convite enviado para {membro.nome}.")
            return redirect("familia:lista", pk=paciente.pk)

        context = _contexto(paciente, convidar_form=form, modal_aberto=True)
        return render(request, TEMPLATE_LISTA, context)


class EditarMembroView(LoginRequiredMixin, View):
    """Edita um membro da família (exclusivo de familiares)."""

    def post(self, request, pk, membro_id):
        paciente = PacienteService.paciente_acessivel(request.user, pk)
        if not paciente:
            messages.error(request, "Paciente não encontrado ou sem acesso.")
            return redirect("pacientes:dashboard")
        if not request.user.is_familiar:
            messages.error(request, "Apenas familiares podem editar membros.")
            return redirect("familia:lista", pk=paciente.pk)

        membro = MembroFamiliaService.membro_acessivel(paciente, membro_id)
        if not membro:
            messages.error(request, "Membro não encontrado.")
            return redirect("familia:lista", pk=paciente.pk)

        form = EditarMembroForm(request.POST, instance=membro)
        if form.is_valid():
            form.save()
            messages.success(request, f"Dados de {membro.nome} atualizados.")
        else:
            primeiro = next(iter(form.errors.values()))[0]
            messages.error(request, f"Não foi possível salvar: {primeiro}")
        return redirect("familia:lista", pk=paciente.pk)


class RemoverMembroView(LoginRequiredMixin, View):
    """Remove um membro / cancela um convite (exclusivo de familiares)."""

    def post(self, request, pk, membro_id):
        paciente = PacienteService.paciente_acessivel(request.user, pk)
        if not paciente:
            messages.error(request, "Paciente não encontrado ou sem acesso.")
            return redirect("pacientes:dashboard")
        if not request.user.is_familiar:
            messages.error(request, "Apenas familiares podem remover membros.")
            return redirect("familia:lista", pk=paciente.pk)

        if MembroFamiliaService.remover(paciente=paciente, pk=membro_id):
            messages.success(request, "Membro/convite removido.")
        else:
            messages.error(request, "Membro não encontrado.")
        return redirect("familia:lista", pk=paciente.pk)


class ReenviarConviteView(LoginRequiredMixin, View):
    """Reenvia o convite de um membro pendente (exclusivo de familiares)."""

    def post(self, request, pk, membro_id):
        paciente = PacienteService.paciente_acessivel(request.user, pk)
        if not paciente:
            messages.error(request, "Paciente não encontrado ou sem acesso.")
            return redirect("pacientes:dashboard")
        if not request.user.is_familiar:
            messages.error(request, "Apenas familiares podem reenviar convites.")
            return redirect("familia:lista", pk=paciente.pk)

        membro = MembroFamiliaService.membro_acessivel(paciente, membro_id)
        if membro and not membro.is_aceito:
            MembroFamiliaService.reenviar(membro=membro, request=request)
            messages.success(request, f"Convite reenviado para {membro.nome}.")
        else:
            messages.error(request, "Convite não encontrado ou já aceito.")
        return redirect("familia:lista", pk=paciente.pk)


class AceitarConviteView(View):
    """Página pública de aceite do convite (acessada pelo link do e-mail)."""

    def get(self, request, token):
        membro = MembroFamiliaService.aceitar(token)
        return render(request, "familia/convite.html", {"membro": membro})
