"""
Views da tela "Equipe" do paciente.

Tela exclusiva do MODO familiar (quem gerencia o cuidado). Mostra uma lista
única de quem faz parte do paciente — familiares e cuidadores — com um filtro
suspenso por tipo (Todos / Família / Cuidador) e por status. Tudo lê a tabela
única ``pacientes.Participacao``. O convite só é permitido para quem já possui
conta no CuidaCare (senão, mensagem de erro).
"""

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme
from django.views import View

from pacientes.models import Participacao
from pacientes.services import PacienteService

from .forms import ConvidarMembroForm, EditarMembroForm
from .services import ContaInexistenteError, EquipeService, JaNaEquipeError

__all__ = [
    "EquipeView",
    "ConvidarMembroView",
    "EditarMembroView",
    "RemoverMembroView",
    "ReenviarConviteView",
    "AceitarConviteView",
    "ResponderConviteView",
]

TEMPLATE_LISTA = "familia/lista.html"


def _modo_familiar(request):
    """A Equipe só existe no modo familiar."""
    return request.session.get("modo", "familiar") != "cuidador"


def _tipo_filtro(valor):
    if valor in (Participacao.Tipo.FAMILIAR, Participacao.Tipo.CUIDADOR):
        return valor
    return "todos"


def _url_lista(paciente, tipo="todos", status="todos"):
    url = reverse("equipe:lista", args=[paciente.pk])
    return f"{url}?tipo={tipo}&status={status}"


def _contexto(paciente, *, tipo="todos", status="todos", **extra):
    tipo_f = tipo if tipo in (Participacao.Tipo.FAMILIAR, Participacao.Tipo.CUIDADOR) else None
    status_f = status if status in ("aceito", "pendente") else None
    context = {
        "paciente": paciente,
        "tipo": tipo or "todos",
        "status": status or "todos",
        "membros": EquipeService.membros(paciente, tipo_f, status_f),
        "contagens": EquipeService.contagens(paciente),
        "convidar_form": ConvidarMembroForm(),
        "modal_aberto": False,
    }
    context.update(extra)
    return context


class EquipeView(LoginRequiredMixin, View):
    """Lista única da equipe (cards + tabela), com filtro por tipo e status."""

    def get(self, request, pk):
        paciente = PacienteService.paciente_acessivel(request.user, pk)
        if not paciente:
            messages.error(request, "Paciente não encontrado ou sem acesso.")
            return redirect("pacientes:dashboard")
        if not _modo_familiar(request):
            messages.error(request, "A Equipe está disponível apenas no modo Familiar.")
            return redirect("pacientes:visao_geral", pk=paciente.pk)

        tipo = _tipo_filtro(request.GET.get("tipo", "todos").strip())
        status = request.GET.get("status", "todos").strip()
        return render(request, TEMPLATE_LISTA, _contexto(paciente, tipo=tipo, status=status))


class ConvidarMembroView(LoginRequiredMixin, View):
    """Convida um membro da equipe (família ou cuidador)."""

    def post(self, request, pk):
        paciente = PacienteService.paciente_acessivel(request.user, pk)
        if not paciente:
            messages.error(request, "Paciente não encontrado ou sem acesso.")
            return redirect("pacientes:dashboard")
        if not _modo_familiar(request):
            messages.error(request, "Apenas no modo Familiar é possível convidar membros.")
            return redirect("pacientes:visao_geral", pk=paciente.pk)

        form = ConvidarMembroForm(request.POST)
        if form.is_valid():
            tipo = form.cleaned_data["tipo"]
            try:
                membro = EquipeService.convidar(
                    paciente=paciente,
                    tipo=tipo,
                    email=form.cleaned_data["email"],
                    vinculo=form.cleaned_data.get("vinculo", ""),
                    convidado_por=request.user,
                    request=request,
                )
            except ContaInexistenteError:
                messages.error(
                    request,
                    "Essa pessoa não possui conta no CuidaCare. "
                    "Peça que ela se cadastre antes de ser convidada.",
                )
                return redirect(_url_lista(paciente))
            except JaNaEquipeError:
                messages.error(request, "Essa pessoa já faz parte da equipe.")
                return redirect(_url_lista(paciente))

            messages.success(request, f"Convite enviado para {membro.nome}.")
            return redirect(_url_lista(paciente, tipo=tipo))

        context = _contexto(paciente, convidar_form=form, modal_aberto=True)
        return render(request, TEMPLATE_LISTA, context)


class EditarMembroView(LoginRequiredMixin, View):
    """Edita o vínculo de um familiar da equipe."""

    def post(self, request, pk, membro_id):
        paciente = PacienteService.paciente_acessivel(request.user, pk)
        if not paciente:
            messages.error(request, "Paciente não encontrado ou sem acesso.")
            return redirect("pacientes:dashboard")
        if not _modo_familiar(request):
            return redirect("pacientes:visao_geral", pk=paciente.pk)

        membro = EquipeService.membro_acessivel(paciente, membro_id)
        if not membro:
            messages.error(request, "Membro não encontrado.")
            return redirect(_url_lista(paciente))

        form = EditarMembroForm(request.POST)
        if form.is_valid():
            EquipeService.editar_vinculo(
                participacao=membro, vinculo=form.cleaned_data["vinculo"]
            )
            messages.success(request, f"Dados de {membro.nome} atualizados.")
        else:
            primeiro = next(iter(form.errors.values()))[0]
            messages.error(request, f"Não foi possível salvar: {primeiro}")
        return redirect(_url_lista(paciente))


class RemoverMembroView(LoginRequiredMixin, View):
    """Remove um membro / cancela um convite."""

    def post(self, request, pk, membro_id):
        paciente = PacienteService.paciente_acessivel(request.user, pk)
        if not paciente:
            messages.error(request, "Paciente não encontrado ou sem acesso.")
            return redirect("pacientes:dashboard")
        if not _modo_familiar(request):
            return redirect("pacientes:visao_geral", pk=paciente.pk)

        if EquipeService.remover(paciente=paciente, pk=membro_id):
            messages.success(request, "Membro/convite removido.")
        else:
            messages.error(request, "Membro não encontrado.")
        return redirect(_url_lista(paciente))


class ReenviarConviteView(LoginRequiredMixin, View):
    """Reenvia o convite de um membro pendente."""

    def post(self, request, pk, membro_id):
        paciente = PacienteService.paciente_acessivel(request.user, pk)
        if not paciente:
            messages.error(request, "Paciente não encontrado ou sem acesso.")
            return redirect("pacientes:dashboard")
        if not _modo_familiar(request):
            return redirect("pacientes:visao_geral", pk=paciente.pk)

        membro = EquipeService.membro_acessivel(paciente, membro_id)
        if membro and not membro.is_aceito:
            EquipeService.reenviar(participacao=membro, request=request)
            messages.success(request, f"Convite reenviado para {membro.nome}.")
        else:
            messages.error(request, "Convite não encontrado ou já aceito.")
        return redirect(_url_lista(paciente))


class AceitarConviteView(View):
    """Página pública de aceite do convite (acessada pelo link do e-mail)."""

    def get(self, request, token):
        membro = EquipeService.aceitar(token)
        return render(request, "familia/convite.html", {"membro": membro})


class ResponderConviteView(LoginRequiredMixin, View):
    """
    Aceita ou recusa um convite recebido pelo próprio usuário, direto pelo
    sininho de notificações do menu.
    """

    def post(self, request, pk):
        participacao = Participacao.objects.filter(pk=pk).select_related("paciente").first()
        aceitar = request.POST.get("acao") == "aceitar"
        if participacao and EquipeService.responder(
            participacao=participacao, usuario=request.user, aceitar=aceitar
        ):
            if aceitar:
                messages.success(
                    request, f"Convite de {participacao.paciente.nome} aceito!"
                )
            else:
                messages.info(request, "Convite recusado.")
        else:
            messages.error(request, "Convite não encontrado ou já respondido.")

        destino = request.POST.get("next", "")
        if destino and url_has_allowed_host_and_scheme(
            destino, allowed_hosts={request.get_host()}
        ):
            return redirect(destino)
        return redirect("pacientes:dashboard")
