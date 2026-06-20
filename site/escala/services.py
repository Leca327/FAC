"""
Camada de Services do app escala.

Concentra o cálculo da escala (qual cuidador trabalha em cada turno/dia) a
partir do padrão base de cada turno, aplicando as exceções pontuais.
"""

from datetime import date, datetime, time, timedelta

from django.db import transaction
from django.utils import timezone

from pacientes.services import PacienteService
from ponto.models import Plantao

from .models import ExcecaoDia, PadraoTurno, RodizioItem, SemanalItem, Turno, TURNO_HORARIOS

# Nomes dos dias (segunda → domingo) para o cabeçalho da grade.
DIAS_NOMES = ["Segunda", "Terça", "Quarta", "Quinta", "Sexta", "Sábado", "Domingo"]

# Janela (hora início, hora fim) de cada turno. A noite cruza a meia-noite.
TURNO_JANELA = {
    Turno.MANHA.value: (time(6, 0), time(12, 0)),
    Turno.TARDE.value: (time(12, 0), time(18, 0)),
    Turno.NOITE.value: (time(18, 0), time(6, 0)),
}


def segunda_da_semana(dia):
    """Segunda-feira da semana que contém ``dia``."""
    return dia - timedelta(days=dia.weekday())


def janela_turno(data, turno):
    """Início e fim (datetime) da janela do turno em ``data``.

    A noite vai das 18:00 desse dia às 06:00 do dia seguinte.
    """
    h_ini, h_fim = TURNO_JANELA[turno]
    ini = datetime.combine(data, h_ini)
    fim = datetime.combine(data, h_fim)
    if turno == Turno.NOITE.value:
        fim = datetime.combine(data + timedelta(days=1), h_fim)
    return ini, fim


def _intervalo_plantao(p, agora):
    """Intervalo [início, fim] (datetime) de presença de um plantão.

    Fechado: entrada → entrada + duração (ou hora de saída, virando o dia se
    preciso). Aberto: entrada → agora. Devolve None se não der para calcular.
    """
    if not p.hora_entrada:
        return None
    ini = datetime.combine(p.data_plantao, p.hora_entrada)
    if p.status == Plantao.Status.ABERTO:
        fim = agora
    elif p.status == Plantao.Status.FECHADO:
        if p.duracao_horas is not None:
            fim = ini + timedelta(minutes=int(round(float(p.duracao_horas) * 60)))
        elif p.hora_saida:
            fim = datetime.combine(p.data_plantao, p.hora_saida)
            if fim <= ini:
                fim += timedelta(days=1)
        else:
            return None
    else:  # cancelado
        return None
    return (ini, fim) if fim > ini else None


def _nome(usuario):
    if not usuario:
        return ""
    return usuario.get_full_name() or usuario.email


def _label_dt(d, t):
    """Rótulo 'dd/mm • HH:MM' para a tabela da agenda."""
    return f"{d:%d/%m} • {t:%H:%M}"


class EscalaService:
    """Regras de negócio da escala de cuidadores de um paciente."""

    @staticmethod
    def cuidadores_disponiveis(paciente):
        """Cuidadores aceitos na equipe do paciente (para escolher na escala)."""
        return list(PacienteService.equipe_do_paciente(paciente)["cuidadores"])

    @staticmethod
    def padroes(paciente):
        """Dict turno→PadraoTurno (com itens pré-carregados) do paciente."""
        qs = (
            PadraoTurno.objects.filter(paciente=paciente)
            .prefetch_related("itens_rodizio__cuidador", "itens_semanal__cuidador")
        )
        return {p.turno: p for p in qs}

    @staticmethod
    def cuidador_do_padrao(padrao, dia):
        """Cuidador previsto pelo padrão (sem exceções) para um dia. Pode ser None."""
        if padrao is None:
            return None
        if padrao.is_rodizio:
            itens = list(padrao.itens_rodizio.all())
            if not itens or not padrao.data_inicio:
                return None
            por = max(padrao.dias_por_pessoa or 1, 1)
            bloco = (dia - padrao.data_inicio).days // por
            return itens[bloco % len(itens)].cuidador
        # semanal
        for item in padrao.itens_semanal.all():
            if item.dia_semana == dia.weekday():
                return item.cuidador
        return None

    @staticmethod
    def semana(paciente, inicio):
        """
        Monta a grade da semana (turnos × 7 dias) a partir de ``inicio`` (segunda).

        Retorna {"dias": [...], "linhas": [{turno, label, horario, celulas: [...]}]}
        onde cada célula = {data, cuidador, nome, alterado}.
        """
        inicio = segunda_da_semana(inicio)
        dias = [inicio + timedelta(days=i) for i in range(7)]
        padroes = EscalaService.padroes(paciente)

        # Exceções da semana, indexadas por (data, turno).
        excecoes = {
            (e.data, e.turno): e
            for e in ExcecaoDia.objects.filter(
                paciente=paciente, data__range=(dias[0], dias[-1])
            ).select_related("cuidador")
        }

        # Quem REALMENTE cobriu cada (dia, turno) — por quem ficou mais tempo.
        # A realidade tem prioridade sobre exceção manual e padrão.
        realizados = EscalaService.realizados_semana(paciente, dias)

        hoje = date.today()
        linhas = []
        for turno in Turno:
            celulas = []
            padrao = padroes.get(turno)
            for d in dias:
                previsto = EscalaService.cuidador_do_padrao(padrao, d)
                real = realizados.get((d, turno.value))
                if real is not None:
                    # Quem trabalhou de fato. É ALT quando difere do previsto.
                    cuidador = real
                    alterado = not (previsto and previsto.id == real.id)
                    realizado = True
                else:
                    exc = excecoes.get((d, turno.value))
                    if exc is not None:
                        cuidador, alterado = exc.cuidador, True
                    else:
                        cuidador, alterado = previsto, False
                    realizado = False
                celulas.append(
                    {
                        "data": d,
                        "cuidador": cuidador,
                        "nome": _nome(cuidador),
                        "alterado": alterado,
                        # Teve plantão; e, se o dia já passou, não pode mais ser
                        # alterado (a escala reflete o que aconteceu).
                        "realizado": realizado,
                        "bloqueado": realizado and d < hoje,
                    }
                )
            linhas.append(
                {
                    "turno": turno.value,
                    "label": turno.label,
                    "horario": TURNO_HORARIOS[turno],
                    "celulas": celulas,
                }
            )

        return {
            "inicio": inicio,
            "fim": dias[-1],
            "dias": [
                {"data": d, "nome": DIAS_NOMES[i], "hoje": d == hoje}
                for i, d in enumerate(dias)
            ],
            "linhas": linhas,
        }

    @staticmethod
    @transaction.atomic
    def salvar_padrao(*, paciente, turno, tipo, dias_por_pessoa=1,
                      data_inicio=None, cuidadores_rodizio=None, semanal=None):
        """
        Cria/atualiza o padrão de um turno e regrava seus itens.

        - cuidadores_rodizio: lista ordenada de objetos Usuario (rodízio).
        - semanal: dict {dia_semana(int): Usuario|None} (semanal).
        """
        padrao, _ = PadraoTurno.objects.update_or_create(
            paciente=paciente,
            turno=turno,
            defaults={
                "tipo_padrao": tipo,
                "dias_por_pessoa": max(dias_por_pessoa or 1, 1),
                "data_inicio": data_inicio,
            },
        )
        # Regrava os itens conforme o tipo (limpa ambos para evitar resíduos).
        padrao.itens_rodizio.all().delete()
        padrao.itens_semanal.all().delete()

        if tipo == PadraoTurno.Tipo.RODIZIO:
            for ordem, cuidador in enumerate(cuidadores_rodizio or []):
                RodizioItem.objects.create(padrao=padrao, ordem=ordem, cuidador=cuidador)
        else:
            for dia, cuidador in (semanal or {}).items():
                SemanalItem.objects.create(padrao=padrao, dia_semana=dia, cuidador=cuidador)
        return padrao

    @staticmethod
    def definir_excecao(*, paciente, data, turno, cuidador):
        """Cria/atualiza uma exceção (troca pontual). cuidador None = folga."""
        excecao, _ = ExcecaoDia.objects.update_or_create(
            paciente=paciente, data=data, turno=turno,
            defaults={"cuidador": cuidador},
        )
        return excecao

    @staticmethod
    def limpar_excecao(*, paciente, data, turno):
        """Remove a exceção, voltando o dia ao padrão base."""
        ExcecaoDia.objects.filter(paciente=paciente, data=data, turno=turno).delete()

    # ------------------------------------------------------------------
    # Integração com o ponto (plantões realmente realizados)
    # ------------------------------------------------------------------
    @staticmethod
    def realizados_semana(paciente, dias):
        """
        Para cada (dia, turno) da semana, qual cuidador REALMENTE cobriu mais
        tempo aquele turno — calculado pela sobreposição dos plantões com a
        janela do turno.

        Ex.: se Ana ficou das 07:00 às 19:00 e Joana das 19:00 ao dia seguinte,
        a manhã e a tarde ficam com a Ana, e a noite com a Joana (quem somou
        mais minutos dentro de cada janela). Devolve {(dia, turno): cuidador}
        apenas para os turnos que tiveram presença.
        """
        agora = timezone.localtime().replace(tzinfo=None, microsecond=0)
        # Busca um dia a mais de cada lado: plantões de véspera/madrugada podem
        # cair dentro de uma janela da semana.
        qs = (
            Plantao.objects.filter(
                paciente=paciente,
                data_plantao__range=(dias[0] - timedelta(days=1), dias[-1] + timedelta(days=1)),
            )
            .exclude(status=Plantao.Status.CANCELADO)
            .select_related("cuidador")
        )
        intervalos = []
        for p in qs:
            iv = _intervalo_plantao(p, agora)
            if iv:
                intervalos.append((p.cuidador, iv[0], iv[1]))

        resultado = {}
        for d in dias:
            for turno in Turno:
                win_ini, win_fim = janela_turno(d, turno.value)
                segundos, objetos = {}, {}
                for cuidador, ini, fim in intervalos:
                    ov = (min(fim, win_fim) - max(ini, win_ini)).total_seconds()
                    if ov > 0:
                        segundos[cuidador.id] = segundos.get(cuidador.id, 0) + ov
                        objetos[cuidador.id] = cuidador
                if segundos:
                    melhor = max(segundos, key=segundos.get)
                    resultado[(d, turno.value)] = objetos[melhor]
        return resultado

    @staticmethod
    def tem_plantao(paciente, data, turno):
        """Houve plantão cobrindo esse (dia, turno)?"""
        return (data, turno) in EscalaService.realizados_semana(paciente, [data])

    @staticmethod
    def agenda_dia(paciente, dia):
        """
        Plantões do DIA selecionado para o painel "Plantão do dia" da agenda:

        - plantões REAIS que cobrem o dia (entram nele ou seguem de um plantão
          que cruzou a meia-noite), com os horários batidos e status
          (Fechado/Aberto);
        - se o dia for hoje: além dos já feitos, os turnos que ainda virão;
        - se for um dia futuro: o PLANEJADO (status "Planejado").
        - dia passado mostra só o que foi realizado.

        Cada item já vem formatado para a tabela e a lista vem ordenada no
        tempo.
        """
        hoje = date.today()
        agora = timezone.localtime().replace(tzinfo=None, microsecond=0)
        # A "janela do dia" cobre os 3 turnos: das 06:00 do dia às 06:00 do
        # dia seguinte (a noite cruza a meia-noite).
        dia_ini = datetime.combine(dia, time(6, 0))
        dia_fim = datetime.combine(dia + timedelta(days=1), time(6, 0))

        linhas = []

        # 1) Plantões reais que se sobrepõem ao dia (inclui os do dia anterior
        # que avançaram pela madrugada).
        qs = (
            Plantao.objects.filter(
                paciente=paciente,
                data_plantao__range=(dia - timedelta(days=1), dia),
            )
            .exclude(status=Plantao.Status.CANCELADO)
            .select_related("cuidador")
        )
        for p in qs:
            iv = _intervalo_plantao(p, agora)
            if not iv:
                continue
            ini, fim = iv
            if fim <= dia_ini or ini >= dia_fim:
                continue  # não toca o dia
            saida_label = (
                _label_dt(fim.date(), fim.time())
                if p.status == Plantao.Status.FECHADO else "—"
            )
            linhas.append({
                "ordem": ini,
                "cuidador_nome": _nome(p.cuidador),
                "entrada_label": _label_dt(p.data_plantao, p.hora_entrada),
                "saida_label": saida_label,
                "status_label": p.get_status_display(),
                "planejado": False,
            })

        # 2) Planejados do dia: só de hoje em diante, turnos sem plantão real.
        if dia >= hoje:
            realizados = EscalaService.realizados_semana(paciente, [dia])
            padroes = EscalaService.padroes(paciente)
            excecoes = {
                (e.data, e.turno): e
                for e in ExcecaoDia.objects.filter(
                    paciente=paciente, data=dia
                ).select_related("cuidador")
            }
            for turno in Turno:
                if (dia, turno.value) in realizados:
                    continue  # já tem plantão real cobrindo
                win_ini, win_fim = janela_turno(dia, turno.value)
                if dia == hoje and win_fim <= agora:
                    continue  # turno de hoje que já terminou sem plantão
                exc = excecoes.get((dia, turno.value))
                cuidador = (
                    exc.cuidador if exc is not None
                    else EscalaService.cuidador_do_padrao(padroes.get(turno), dia)
                )
                if cuidador is None:
                    continue  # folga / sem previsto
                linhas.append({
                    "ordem": win_ini,
                    "cuidador_nome": _nome(cuidador),
                    "entrada_label": _label_dt(win_ini.date(), win_ini.time()),
                    "saida_label": _label_dt(win_fim.date(), win_fim.time()),
                    "status_label": "Planejado",
                    "planejado": True,
                })

        linhas.sort(key=lambda x: x["ordem"])
        return linhas
