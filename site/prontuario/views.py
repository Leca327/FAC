"""
Views do app prontuario (tela "Prontuário").

Linha do tempo do dia do paciente, com botao "Adicionar Anotação" (popup).
Familiares e cuidadores com acesso ao paciente podem registrar anotacoes.
"""

from datetime import datetime, timedelta

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views import View

from pacientes.services import PacienteService

from .forms import AnotacaoForm
from .services import ProntuarioService

__all__ = ["ProntuarioView", "AdicionarAnotacaoView"]


def _parse_data(valor, padrao):
    if valor:
        try:
            return datetime.strptime(valor, "%Y-%m-%d").date()
        except ValueError:
            pass
    return padrao


def _url_diario(paciente, dia):
    base = reverse("prontuario:diario", args=[paciente.pk])
    return f"{base}?data={dia:%Y-%m-%d}"


def _form_inicial():
    agora = timezone.localtime().strftime("%Y-%m-%dT%H:%M")
    return AnotacaoForm(initial={"data_hora": agora})


def _contexto(paciente, dia, busca, **extra):
    context = {
        "paciente": paciente,
        "dia": dia,
        "dia_anterior": dia - timedelta(days=1),
        "dia_proximo": dia + timedelta(days=1),
        "is_hoje": dia == timezone.localdate(),
        "busca": busca,
        "eventos": ProntuarioService.eventos_do_dia(paciente, dia, busca),
        "contagens": ProntuarioService.contagens(paciente, dia),
        "anotacao_form": _form_inicial(),
        "modal_aberto": False,
    }
    context.update(extra)
    return context


class ProntuarioView(LoginRequiredMixin, View):
    """Linha do tempo do dia do paciente."""

    template_name = "prontuario/diario.html"

    def get(self, request, pk):
        paciente = PacienteService.paciente_acessivel(request.user, pk)
        if not paciente:
            messages.error(request, "Paciente não encontrado ou sem acesso.")
            return redirect("pacientes:dashboard")

        dia = _parse_data(request.GET.get("data"), timezone.localdate())
        busca = request.GET.get("q", "").strip()
        return render(request, self.template_name, _contexto(paciente, dia, busca))


class AdicionarAnotacaoView(LoginRequiredMixin, View):
    """Cria uma anotação manual no prontuário (popup)."""

    def post(self, request, pk):
        paciente = PacienteService.paciente_acessivel(request.user, pk)
        if not paciente:
            messages.error(request, "Paciente não encontrado ou sem acesso.")
            return redirect("pacientes:dashboard")

        form = AnotacaoForm(request.POST)
        if form.is_valid():
            anotacao = ProntuarioService.criar_anotacao(
                paciente=paciente, form=form, usuario=request.user
            )
            messages.success(request, "Anotação adicionada ao prontuário.")
            return redirect(_url_diario(paciente, timezone.localtime(anotacao.data_hora).date()))

        dia = timezone.localdate()
        context = _contexto(paciente, dia, "", anotacao_form=form, modal_aberto=True)
        return render(request, ProntuarioView.template_name, context)
