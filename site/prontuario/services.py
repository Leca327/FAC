"""
Camada de Services do app prontuario.

Monta a linha do tempo do dia (eventos horizontais) agregando, sem duplicar
dados, tres fontes: anotacoes manuais, medicamentos tomados e consultas
realizadas. Tambem cria anotacoes e calcula os numeros do topo.
"""

from datetime import datetime, time, timedelta

from django.utils import timezone

from consultas.models import Consulta
from medicamentos.models import MedicamentoTomado

from .models import Anotacao


def _nome(usuario):
    if not usuario:
        return ""
    return usuario.get_full_name() or usuario.email


def _intervalo_dia(dia):
    """
    Intervalo [início, fim) do dia em datetimes aware no fuso local.

    Usado em vez do lookup ``__date`` porque no MySQL ele depende de
    CONVERT_TZ (tabelas de fuso), que pode não estar carregado.
    """
    tz = timezone.get_current_timezone()
    inicio = timezone.make_aware(datetime.combine(dia, time.min), tz)
    return inicio, inicio + timedelta(days=1)


class ProntuarioService:
    """Regras da tela de Prontuário de um paciente."""

    @staticmethod
    def contagens(paciente, dia):
        """Numeros rapidos do dia (cabecalho)."""
        inicio, fim = _intervalo_dia(dia)
        return {
            "medicamentos": MedicamentoTomado.objects.filter(
                medicamento__paciente=paciente, data=dia, tomado=True
            ).count(),
            "consultas": Consulta.objects.filter(
                paciente=paciente,
                status=Consulta.Status.REALIZADA,
                data_hora__gte=inicio,
                data_hora__lt=fim,
            ).count(),
            "anotacoes": Anotacao.objects.filter(
                paciente=paciente, data_hora__gte=inicio, data_hora__lt=fim
            ).count(),
        }

    @staticmethod
    def eventos_do_dia(paciente, dia, busca=""):
        """
        Linha do tempo do dia: lista de eventos ordenados por horario.

        Cada evento e um dict com tipo, tipo_label, hora, titulo, detalhe,
        subtitulo e rodape — formato neutro consumido direto pela template.
        """
        eventos = []
        inicio, fim = _intervalo_dia(dia)

        # 1) Medicamentos tomados (entram no horario indicado da dose).
        registros = (
            MedicamentoTomado.objects.filter(
                medicamento__paciente=paciente, data=dia, tomado=True
            )
            .select_related("medicamento", "marcado_por")
        )
        for r in registros:
            med = r.medicamento
            detalhe = " • ".join(p for p in [med.dosagem, med.quantidade_dose] if p)
            hora = r.horario_previsto
            if not hora and r.tomado_em:
                hora = timezone.localtime(r.tomado_em).strftime("%H:%M")
            eventos.append({
                "tipo": "medicamento",
                "tipo_label": "Medicamento Tomado",
                "hora": hora or "",
                "titulo": med.nome,
                "detalhe": detalhe,
                "subtitulo": med.observacoes,
                "rodape": f"Marcado por {_nome(r.marcado_por)}" if r.marcado_por else "",
            })

        # 2) Consultas realizadas (entram no horario marcado da consulta).
        consultas = (
            Consulta.objects.filter(
                paciente=paciente,
                status=Consulta.Status.REALIZADA,
                data_hora__gte=inicio,
                data_hora__lt=fim,
            )
            .select_related("medico")
        )
        for c in consultas:
            local = timezone.localtime(c.data_hora)
            medico = c.medico
            sub = []
            if medico and medico.localizacao:
                sub.append(f"Local: {medico.localizacao}")
            if medico and medico.crm_cnpj:
                sub.append(f"CRM/ID: {medico.crm_cnpj}")
            if not sub and c.resultado:
                sub.append(c.resultado)
            eventos.append({
                "tipo": "consulta",
                "tipo_label": "Consulta Realizada",
                "hora": local.strftime("%H:%M"),
                "titulo": c.titulo,
                "detalhe": f"com {medico.nome}" if medico else "",
                "subtitulo": " • ".join(sub),
                "rodape": "",
            })

        # 3) Anotacoes manuais.
        anotacoes = (
            Anotacao.objects.filter(
                paciente=paciente, data_hora__gte=inicio, data_hora__lt=fim
            )
            .select_related("autor")
        )
        for a in anotacoes:
            local = timezone.localtime(a.data_hora)
            eventos.append({
                "tipo": "anotacao",
                "tipo_label": "Anotação",
                "hora": local.strftime("%H:%M"),
                "titulo": a.titulo,
                "detalhe": "",
                "subtitulo": a.descricao,
                "rodape": f"Registrado por {_nome(a.autor)}" if a.autor else "",
            })

        # 4) Ponto: entrada (check-in) e saída (check-out) dos plantões do dia.
        # Derivado da tabela plantao — se o ponto for editado/excluído, o
        # prontuário reflete automaticamente.
        from ponto.models import Plantao
        from ponto.services import formatar_minutos, turno_label, _minutos

        plantoes = (
            Plantao.objects.filter(paciente=paciente, data_plantao=dia)
            .select_related("cuidador")
        )
        for p in plantoes:
            cuidador = _nome(p.cuidador)
            turno = turno_label(p.hora_entrada)
            if p.hora_entrada:
                eventos.append({
                    "tipo": "ponto",
                    "tipo_label": "Entrada de Plantão",
                    "hora": p.hora_entrada.strftime("%H:%M"),
                    "titulo": cuidador,
                    "detalhe": f"— {turno}" if turno else "",
                    "subtitulo": "Check-in do plantão",
                    "rodape": "",
                })
            if p.hora_saida:
                mins = _minutos(p.hora_entrada, p.hora_saida) if p.hora_entrada else None
                sub = "Check-out do plantão"
                if mins is not None:
                    sub += f" • {formatar_minutos(mins)} trabalhadas"
                eventos.append({
                    "tipo": "ponto",
                    "tipo_label": "Saída de Plantão",
                    "hora": p.hora_saida.strftime("%H:%M"),
                    "titulo": cuidador,
                    "detalhe": f"— {turno}" if turno else "",
                    "subtitulo": sub,
                    "rodape": "",
                })

        # Filtro de busca por tipo de evento (ou titulo).
        if busca:
            b = busca.lower()
            eventos = [
                e for e in eventos
                if b in e["tipo_label"].lower() or b in e["titulo"].lower()
            ]

        # Mais recentes primeiro (horário decrescente).
        eventos.sort(key=lambda e: e["hora"], reverse=True)
        return eventos

    @staticmethod
    def ultimas_anotacoes(paciente, limite=3):
        """
        As anotacoes mais recentes do paciente (painel "Atividades Recentes"
        da Visao Geral). O ordering padrao do model ja e -data_hora.
        """
        return list(
            Anotacao.objects.filter(paciente=paciente).select_related("autor")[:limite]
        )

    @staticmethod
    def criar_anotacao(*, paciente, form, usuario):
        anotacao = form.save(commit=False)
        anotacao.paciente = paciente
        anotacao.autor = usuario
        anotacao.save()
        return anotacao
