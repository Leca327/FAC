"""
Camada de Services do app consultas.
"""

import calendar
from collections import OrderedDict
from datetime import date, datetime, time, timedelta

from django.utils import timezone

from .models import Consulta

MESES_PT = [
    "janeiro", "fevereiro", "março", "abril", "maio", "junho",
    "julho", "agosto", "setembro", "outubro", "novembro", "dezembro",
]

# Limite de dias do filtro para não montar janelas absurdas.
MAX_DIAS_PERIODO = 366


def _rotulo_dia(dia, hoje):
    """Ex.: 'Hoje - 20 de junho de 2026' ou '20 de junho de 2026'."""
    data_fmt = f"{dia.day} de {MESES_PT[dia.month - 1]} de {dia.year}"
    return f"Hoje - {data_fmt}" if dia == hoje else data_fmt


class ConsultaService:
    """Regras de negócio das consultas/exames de um paciente."""

    @staticmethod
    def consulta_acessivel(paciente, pk):
        """Retorna a consulta do paciente, ou None se não existir."""
        return Consulta.objects.filter(paciente=paciente, pk=pk).first()

    @staticmethod
    def consultas_periodo(paciente, inicio, fim):
        """
        Consultas/exames do paciente entre `inicio` e `fim` (datas, inclusive),
        agrupados por dia. Só aparecem os dias que têm compromissos.

        Retorna lista de dicts:
            {"data", "label", "is_hoje", "consultas": [Consulta, ...]}
        """
        if fim < inicio:
            inicio, fim = fim, inicio
        if (fim - inicio).days > MAX_DIAS_PERIODO - 1:
            fim = inicio + timedelta(days=MAX_DIAS_PERIODO - 1)

        tz = timezone.get_current_timezone()
        ini_dt = timezone.make_aware(datetime.combine(inicio, time.min), tz)
        fim_dt = timezone.make_aware(datetime.combine(fim, time.max), tz)

        qs = (
            Consulta.objects.filter(
                paciente=paciente, data_hora__range=(ini_dt, fim_dt)
            )
            .select_related("agendada_por", "realizada_por")
            .order_by("data_hora")
        )

        hoje = timezone.localdate()
        grupos = OrderedDict()
        for c in qs:
            dia = timezone.localtime(c.data_hora).date()
            grupos.setdefault(dia, []).append(c)

        return [
            {
                "data": dia,
                "label": _rotulo_dia(dia, hoje),
                "is_hoje": dia == hoje,
                "consultas": consultas,
            }
            for dia, consultas in grupos.items()
        ]

    @staticmethod
    def _intervalo_dia(dia):
        """(início, fim) aware cobrindo o dia inteiro, no fuso local."""
        tz = timezone.get_current_timezone()
        return (
            timezone.make_aware(datetime.combine(dia, time.min), tz),
            timezone.make_aware(datetime.combine(dia, time.max), tz),
        )

    @staticmethod
    def consultas_do_dia(paciente, dia):
        """Consultas/exames do paciente num dia, ordenados por hora."""
        ini, fim = ConsultaService._intervalo_dia(dia)
        return list(
            Consulta.objects.filter(paciente=paciente, data_hora__range=(ini, fim))
            .select_related("medico")
            .order_by("data_hora")
        )

    @staticmethod
    def consultas_do_mes(paciente, ano, mes):
        """
        Mapa {dia_do_mes: [Consulta, ...]} para preencher o calendário da
        Agenda com os títulos dos compromissos.
        """
        ndias = calendar.monthrange(ano, mes)[1]
        ini, _ = ConsultaService._intervalo_dia(date(ano, mes, 1))
        _, fim = ConsultaService._intervalo_dia(date(ano, mes, ndias))
        por_dia = {}
        for c in (
            Consulta.objects.filter(paciente=paciente, data_hora__range=(ini, fim))
            .select_related("medico")
            .order_by("data_hora")
        ):
            por_dia.setdefault(timezone.localtime(c.data_hora).day, []).append(c)
        return por_dia

    @staticmethod
    def contar_agendadas_hoje(paciente):
        """Nº de consultas com status 'agendada' marcadas para hoje."""
        ini, fim = ConsultaService._intervalo_dia(timezone.localdate())
        return Consulta.objects.filter(
            paciente=paciente,
            status=Consulta.Status.AGENDADA,
            data_hora__range=(ini, fim),
        ).count()

    @staticmethod
    def criar(*, paciente, form, usuario):
        """Cria a consulta a partir de um form válido, registrando quem agendou."""
        consulta = form.save(commit=False)
        consulta.paciente = paciente
        consulta.agendada_por = usuario
        consulta.save()
        return consulta

    @staticmethod
    def marcar_realizada(*, paciente, pk, resultado, usuario):
        """
        Marca a consulta como realizada, guardando o resultado e QUEM marcou
        (mesma lógica do medicamento_tomado). Retorna a consulta ou None.
        """
        consulta = Consulta.objects.filter(paciente=paciente, pk=pk).first()
        if not consulta:
            return None
        consulta.status = Consulta.Status.REALIZADA
        consulta.resultado = (resultado or "").strip()
        consulta.realizada_por = usuario
        consulta.realizada_em = timezone.now()
        consulta.save()
        return consulta

    @staticmethod
    def desmarcar_realizada(*, paciente, pk):
        """Reverte a consulta para 'agendada' (limpa quem/quando realizou)."""
        consulta = Consulta.objects.filter(paciente=paciente, pk=pk).first()
        if not consulta:
            return None
        consulta.status = Consulta.Status.AGENDADA
        consulta.realizada_por = None
        consulta.realizada_em = None
        consulta.save()
        return consulta

    @staticmethod
    def deletar(*, paciente, pk):
        """Remove a consulta. Retorna True se removeu."""
        apagadas, _ = Consulta.objects.filter(paciente=paciente, pk=pk).delete()
        return apagadas > 0
