"""
Camada de Services do app escala.

Concentra o cálculo da escala (qual cuidador trabalha em cada turno/dia) a
partir do padrão base de cada turno, aplicando as exceções pontuais.
"""

from datetime import date, timedelta

from django.db import transaction

from pacientes.services import PacienteService

from .models import ExcecaoDia, PadraoTurno, RodizioItem, SemanalItem, Turno, TURNO_HORARIOS

# Nomes dos dias (segunda → domingo) para o cabeçalho da grade.
DIAS_NOMES = ["Segunda", "Terça", "Quarta", "Quinta", "Sexta", "Sábado", "Domingo"]


def segunda_da_semana(dia):
    """Segunda-feira da semana que contém ``dia``."""
    return dia - timedelta(days=dia.weekday())


def _nome(usuario):
    if not usuario:
        return ""
    return usuario.get_full_name() or usuario.email


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

        hoje = date.today()
        linhas = []
        for turno in Turno:
            celulas = []
            padrao = padroes.get(turno)
            for d in dias:
                exc = excecoes.get((d, turno.value))
                if exc is not None:
                    cuidador, alterado = exc.cuidador, True
                else:
                    cuidador, alterado = EscalaService.cuidador_do_padrao(padrao, d), False
                celulas.append(
                    {
                        "data": d,
                        "cuidador": cuidador,
                        "nome": _nome(cuidador),
                        "alterado": alterado,
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
