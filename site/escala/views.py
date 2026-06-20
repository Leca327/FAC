"""
Views do app escala (tela "Escala de Cuidadores").

Mostra a escala semanal (turnos × dias) gerada do padrão base, com navegação
entre semanas e exceções pontuais. Ver a escala vale nos dois modos; editar
(Editar Padrão / Alterar Dia) só no modo familiar.
"""

from datetime import date, datetime, timedelta

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views import View

from pacientes.services import PacienteService

from .models import DIAS_SEMANA, PadraoTurno, Turno, TURNO_HORARIOS
from .services import EscalaService, segunda_da_semana

MESES_PT = [
    "janeiro", "fevereiro", "março", "abril", "maio", "junho",
    "julho", "agosto", "setembro", "outubro", "novembro", "dezembro",
]


def _modo_familiar(request):
    return request.session.get("modo", "familiar") != "cuidador"


def _parse_data(valor, padrao=None):
    try:
        return date.fromisoformat(valor)
    except (TypeError, ValueError):
        return padrao


def _data_extenso(d):
    return f"{d.day} de {MESES_PT[d.month - 1]} de {d.year}"


def _url_semanal(paciente, inicio, aba="semanal"):
    url = reverse("escala:semanal", args=[paciente.pk])
    return f"{url}?aba={aba}&inicio={inicio.isoformat()}"


class EscalaView(LoginRequiredMixin, View):
    """Escala semanal (tabela) + aba Padrão Base, com navegação de semanas."""

    def get(self, request, pk):
        paciente = PacienteService.paciente_acessivel(request.user, pk)
        if not paciente:
            messages.error(request, "Paciente não encontrado ou sem acesso.")
            return redirect("pacientes:dashboard")

        inicio = segunda_da_semana(
            _parse_data(request.GET.get("inicio"), date.today())
        )
        aba = "padrao" if request.GET.get("aba") == "padrao" else "semanal"

        semana = EscalaService.semana(paciente, inicio)
        cuidadores = EscalaService.cuidadores_disponiveis(paciente)

        # Resumo do padrão por turno (para a aba "Padrão Base").
        padroes = EscalaService.padroes(paciente)
        resumo = []
        for turno in Turno:
            p = padroes.get(turno)
            resumo.append({
                "turno": turno.value,
                "label": turno.label,
                "horario": TURNO_HORARIOS[turno],
                "padrao": p,
                "itens_rodizio": list(p.itens_rodizio.all()) if p and p.is_rodizio else [],
                "itens_semanal": list(p.itens_semanal.all()) if p and not p.is_rodizio else [],
            })

        context = {
            "paciente": paciente,
            "aba": aba,
            "pode_editar": _modo_familiar(request),
            "semana": semana,
            "periodo": f"Semana de {semana['inicio'].day} a {_data_extenso(semana['fim'])}",
            "cuidadores": cuidadores,
            "turnos": [{"valor": t.value, "label": t.label} for t in Turno],
            "resumo_padrao": resumo,
            "nav_anterior": (inicio - timedelta(days=7)).isoformat(),
            "nav_proxima": (inicio + timedelta(days=7)).isoformat(),
            "nav_hoje": segunda_da_semana(date.today()).isoformat(),
            "inicio": inicio.isoformat(),
        }
        return render(request, "escala/semanal.html", context)


class EditarPadraoView(LoginRequiredMixin, View):
    """Editor do padrão base dos 3 turnos (só modo familiar)."""

    def _cuidadores_por_id(self, paciente):
        return {str(c.id): c for c in EscalaService.cuidadores_disponiveis(paciente)}

    def get(self, request, pk):
        paciente = PacienteService.paciente_acessivel(request.user, pk)
        if not paciente:
            messages.error(request, "Paciente não encontrado ou sem acesso.")
            return redirect("pacientes:dashboard")
        if not _modo_familiar(request):
            messages.error(request, "Apenas no modo Familiar é possível editar o padrão.")
            return redirect("escala:semanal", pk=paciente.pk)

        padroes = EscalaService.padroes(paciente)
        turnos = []
        for turno in Turno:
            p = padroes.get(turno)
            sel_por_dia = (
                {i.dia_semana: str(i.cuidador_id) for i in p.itens_semanal.all() if i.cuidador_id}
                if (p and not p.is_rodizio) else {}
            )
            turnos.append({
                "valor": turno.value,
                "label": turno.label,
                "horario": TURNO_HORARIOS[turno],
                "tipo": p.tipo_padrao if p else PadraoTurno.Tipo.RODIZIO,
                "dias_por_pessoa": p.dias_por_pessoa if p else 1,
                "data_inicio": p.data_inicio.isoformat() if (p and p.data_inicio) else "",
                "rodizio_ids": [str(i.cuidador_id) for i in p.itens_rodizio.all()] if (p and p.is_rodizio) else [],
                "semanal": [
                    {"dia": dia, "label": label, "sel": sel_por_dia.get(dia, "")}
                    for dia, label in DIAS_SEMANA
                ],
            })

        context = {
            "paciente": paciente,
            "cuidadores": EscalaService.cuidadores_disponiveis(paciente),
            "turnos": turnos,
        }
        return render(request, "escala/editar_padrao.html", context)

    def post(self, request, pk):
        paciente = PacienteService.paciente_acessivel(request.user, pk)
        if not paciente:
            messages.error(request, "Paciente não encontrado ou sem acesso.")
            return redirect("pacientes:dashboard")
        if not _modo_familiar(request):
            messages.error(request, "Apenas no modo Familiar é possível editar o padrão.")
            return redirect("escala:semanal", pk=paciente.pk)

        por_id = self._cuidadores_por_id(paciente)
        for turno in Turno:
            t = turno.value
            tipo = request.POST.get(f"tipo_{t}", PadraoTurno.Tipo.RODIZIO)
            if tipo == PadraoTurno.Tipo.RODIZIO:
                ordenados = [
                    por_id[i] for i in request.POST.getlist(f"rodizio_{t}") if i in por_id
                ]
                EscalaService.salvar_padrao(
                    paciente=paciente, turno=t, tipo=tipo,
                    dias_por_pessoa=int(request.POST.get(f"dias_{t}") or 1),
                    data_inicio=_parse_data(request.POST.get(f"inicio_{t}"), date.today()),
                    cuidadores_rodizio=ordenados,
                )
            else:
                semanal = {}
                for dia, _label in DIAS_SEMANA:
                    valor = request.POST.get(f"semanal_{t}_{dia}", "")
                    semanal[dia] = por_id.get(valor)  # vazio → None (folga)
                EscalaService.salvar_padrao(
                    paciente=paciente, turno=t, tipo=tipo, semanal=semanal,
                )

        messages.success(request, "Padrão da escala atualizado.")
        return redirect(f"{reverse('escala:semanal', args=[paciente.pk])}?aba=padrao")


class AlterarDiaView(LoginRequiredMixin, View):
    """Cria/atualiza ou remove uma exceção de um dia (só modo familiar)."""

    def post(self, request, pk):
        paciente = PacienteService.paciente_acessivel(request.user, pk)
        if not paciente:
            messages.error(request, "Paciente não encontrado ou sem acesso.")
            return redirect("pacientes:dashboard")

        inicio = segunda_da_semana(
            _parse_data(request.POST.get("inicio"), date.today())
        )
        if not _modo_familiar(request):
            messages.error(request, "Apenas no modo Familiar é possível alterar dias.")
            return redirect(_url_semanal(paciente, inicio))

        data = _parse_data(request.POST.get("data"))
        turno = request.POST.get("turno")
        if not data or turno not in Turno.values:
            messages.error(request, "Informe um dia e turno válidos.")
            return redirect(_url_semanal(paciente, inicio))

        # RN12: dia já passado e com plantão registrado não pode ser alterado —
        # a escala reflete o que realmente aconteceu.
        if data < date.today() and EscalaService.tem_plantao(paciente, data, turno):
            messages.error(
                request,
                "Este dia já passou e teve plantão registrado; a escala mostra "
                "o que realmente aconteceu e não pode ser alterada.",
            )
            return redirect(_url_semanal(paciente, segunda_da_semana(data)))

        if request.POST.get("acao") == "restaurar":
            EscalaService.limpar_excecao(paciente=paciente, data=data, turno=turno)
            messages.info(request, "Dia restaurado ao padrão base.")
        else:
            cuidador = None
            cid = request.POST.get("cuidador", "")
            if cid:
                cuidador = next(
                    (c for c in EscalaService.cuidadores_disponiveis(paciente) if str(c.id) == cid),
                    None,
                )
            EscalaService.definir_excecao(
                paciente=paciente, data=data, turno=turno, cuidador=cuidador
            )
            messages.success(request, "Dia alterado com sucesso.")

        return redirect(_url_semanal(paciente, segunda_da_semana(data)))
