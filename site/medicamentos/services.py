"""
Camada de Services do app medicamentos (seção 2.6.5).
"""

from datetime import date, datetime, time, timedelta

from django.db.models import Q
from django.utils import timezone

from .models import Medicamento, MedicamentoTomado

# Campo booleano do model correspondente a cada dia da semana (0 = segunda).
CAMPO_DIA = ["seg", "ter", "qua", "qui", "sex", "sab", "dom"]

# Nomes em português para montar o rótulo de cada dia da rotina.
MESES_PT = [
    "janeiro", "fevereiro", "março", "abril", "maio", "junho",
    "julho", "agosto", "setembro", "outubro", "novembro", "dezembro",
]

# Limite de dias exibidos de uma vez na tela de Medicação Diária.
MAX_DIAS_ROTINA = 31

# Rótulos dos status de cada dose na rotina.
STATUS_LABEL = {
    "tomado": "Tomado",
    "pendente": "Pendente",
    "atrasado": "Atrasado",
}


def _rotulo_dia(dia, hoje):
    """Ex.: 'Hoje - 16 de junho de 2026' ou '17 de junho de 2026'."""
    data_fmt = f"{dia.day} de {MESES_PT[dia.month - 1]} de {dia.year}"
    return f"Hoje - {data_fmt}" if dia == hoje else data_fmt


def _hora_prevista_dt(dia, horario):
    """Datetime aware do horário previsto (HH:MM) num dia, ou None se inválido."""
    try:
        hh, mm = (int(p) for p in horario.split(":"))
    except (ValueError, TypeError):
        return None
    return timezone.make_aware(
        datetime.combine(dia, time(hh, mm)), timezone.get_current_timezone()
    )


def _status_dose(dia, horario, tomado, agora):
    """
    Status de uma dose, conforme o registro e a hora atual:
    - 'tomado'   → já existe registro de que foi tomada;
    - 'atrasado' → não foi tomada e o horário agendado já passou;
    - 'pendente' → não foi tomada e o horário ainda não chegou.
    """
    if tomado:
        return "tomado"
    prevista = _hora_prevista_dt(dia, horario)
    if prevista is None:
        return "pendente"
    return "atrasado" if prevista < agora else "pendente"


class MedicamentoService:
    """Regras de negócio relacionadas aos medicamentos de um paciente."""

    ORDENS = {
        "nome": ("nome",),
        "recentes": ("-data_criacao",),
    }

    @staticmethod
    def medicamentos_do_dia(paciente, dia=None):
        """
        Medicamentos ativos a serem tomados no dia informado (padrão: hoje):
        status ativo, período vigente e marcado para o dia da semana.
        """
        dia = dia or date.today()
        campo_hoje = CAMPO_DIA[dia.weekday()]
        return list(
            Medicamento.objects.filter(
                Q(data_fim__isnull=True) | Q(data_fim__gte=dia),
                paciente=paciente,
                status=Medicamento.Status.ATIVO,
                data_inicio__lte=dia,
                **{campo_hoje: True},
            ).order_by("horarios", "nome")
        )

    @staticmethod
    def medicamentos_do_paciente(paciente, busca="", ordenar="nome"):
        """
        Retorna os medicamentos do paciente, aplicando busca por nome e
        ordenação escolhidas na barra de ferramentas.
        """
        qs = Medicamento.objects.filter(paciente=paciente)

        if busca:
            qs = qs.filter(nome__icontains=busca)

        ordem = MedicamentoService.ORDENS.get(ordenar, MedicamentoService.ORDENS["nome"])
        return list(qs.order_by(*ordem))

    @staticmethod
    def medicamento_acessivel(paciente, pk):
        """Retorna o medicamento do paciente, ou None se não existir."""
        return Medicamento.objects.filter(paciente=paciente, pk=pk).first()

    @staticmethod
    def criar_medicamento(*, paciente, form):
        """Cria um medicamento vinculado ao paciente a partir de um form válido."""
        medicamento = form.save(commit=False)
        medicamento.paciente = paciente
        medicamento.save()
        return medicamento

    @staticmethod
    def deletar_medicamento(*, paciente, pk):
        """Remove um medicamento do paciente. Retorna True se removeu."""
        deletados, _ = Medicamento.objects.filter(
            paciente=paciente, pk=pk
        ).delete()
        return deletados > 0

    # ---------- Medicação Diária (rotina) ----------
    @staticmethod
    def rotina_periodo(paciente, inicio, fim):
        """
        Monta a rotina de doses do paciente entre `inicio` e `fim` (inclusive),
        agrupada por dia. Cada dose já vem com o status calculado
        (tomado/pendente/atrasado).

        Retorna uma lista de dicts:
            {"data", "label", "is_hoje", "doses": [
                {"medicamento", "horario", "status", "status_label"}
            ]}
        """
        if fim < inicio:
            inicio, fim = fim, inicio
        # Limita a janela para não montar listas gigantes.
        if (fim - inicio).days > MAX_DIAS_ROTINA - 1:
            fim = inicio + timedelta(days=MAX_DIAS_ROTINA - 1)

        ativos = list(
            Medicamento.objects.filter(
                Q(data_fim__isnull=True) | Q(data_fim__gte=inicio),
                paciente=paciente,
                status=Medicamento.Status.ATIVO,
                data_inicio__lte=fim,
            ).exclude(horarios="")
        )

        # Registros de doses tomadas no período: (medicamento_id, data, horario)
        # -> registro (para saber quem marcou e quando).
        registros = {
            (r.medicamento_id, r.data, r.horario_previsto): r
            for r in MedicamentoTomado.objects.filter(
                medicamento__paciente=paciente, data__range=(inicio, fim), tomado=True
            ).select_related("marcado_por")
        }

        hoje = timezone.localdate()
        agora = timezone.now()

        dias = []
        atual = inicio
        while atual <= fim:
            campo = CAMPO_DIA[atual.weekday()]
            doses = []
            for med in ativos:
                if not getattr(med, campo):
                    continue
                if med.data_inicio and med.data_inicio > atual:
                    continue
                if med.data_fim and med.data_fim < atual:
                    continue
                for horario in med.horarios_lista:
                    registro = registros.get((med.id, atual, horario))
                    status = _status_dose(atual, horario, registro is not None, agora)
                    doses.append(
                        {
                            "medicamento": med,
                            "horario": horario,
                            "status": status,
                            "status_label": STATUS_LABEL[status],
                            "marcado_por": registro.marcado_por if registro else None,
                            "tomado_em": registro.tomado_em if registro else None,
                        }
                    )
            doses.sort(key=lambda d: (d["horario"], d["medicamento"].nome))
            dias.append(
                {
                    "data": atual,
                    "label": _rotulo_dia(atual, hoje),
                    "is_hoje": atual == hoje,
                    "doses": doses,
                }
            )
            atual += timedelta(days=1)
        return dias

    # Por quanto tempo, após o HORÁRIO PREVISTO, uma dose tomada continua
    # visível no card da Visão Geral antes de sair e dar lugar à próxima.
    JANELA_TOMADO_VISIVEL = timedelta(hours=1)

    @staticmethod
    def proximas_doses(paciente, limite=3):
        """
        Próximas doses de HOJE para o card "Medicamentos do Dia" da Visão
        Geral — uma dose por horário, com status (tomado/pendente/atrasado).

        Regra de exibição:
        - doses ainda não tomadas (pendentes/atrasadas) sempre entram;
        - uma dose tomada continua visível só até 1 hora APÓS o horário
          previsto; passado isso, sai e a próxima pendente toma o lugar;
        - se foi marcada já atrasada (depois do horário previsto), sai na
          hora (não fica como confirmação).

        Tudo ordenado por horário e limitado a `limite` itens. Cada item
        inclui a data (hoje), usada ao marcar a dose.
        """
        hoje = timezone.localdate()
        agora = timezone.now()

        dias = MedicamentoService.rotina_periodo(paciente, hoje, hoje)
        doses = dias[0]["doses"] if dias else []

        # Quando cada dose tomada de hoje foi marcada: (med_id, horario) -> tomado_em
        marcadas_em = {
            (r.medicamento_id, r.horario_previsto): r.tomado_em
            for r in MedicamentoTomado.objects.filter(
                medicamento__paciente=paciente, data=hoje, tomado=True
            )
        }

        visiveis = []
        for d in doses:
            if d["status"] != "tomado":
                visiveis.append(d)
                continue

            prevista = _hora_prevista_dt(hoje, d["horario"])
            tomado_em = marcadas_em.get((d["medicamento"].id, d["horario"]))
            # Mantém visível só se foi tomada NO horário (não atrasada) e
            # ainda não passou 1h do horário previsto.
            if (
                prevista
                and tomado_em
                and tomado_em <= prevista
                and agora < prevista + MedicamentoService.JANELA_TOMADO_VISIVEL
            ):
                visiveis.append(d)

        visiveis.sort(key=lambda d: d["horario"])
        return [dict(d, data=hoje) for d in visiveis[:limite]]

    @staticmethod
    def contar_doses_pendentes(paciente):
        """
        Quantas doses de HOJE ainda não foram tomadas (pendentes + atrasadas)
        — usado no card "Medicamentos pendentes para Hoje" da Visão Geral.
        """
        hoje = timezone.localdate()
        dias = MedicamentoService.rotina_periodo(paciente, hoje, hoje)
        doses = dias[0]["doses"] if dias else []
        return sum(1 for d in doses if d["status"] != "tomado")

    @staticmethod
    def medicamentos_fora_da_rotina(paciente):
        """
        Remédios cadastrados do paciente que ainda NÃO estão na rotina
        (sem posologia) — usados no <select> do popup "Adicionar à rotina".
        """
        candidatos = Medicamento.objects.filter(
            paciente=paciente, status=Medicamento.Status.ATIVO
        ).order_by("nome")
        return [m for m in candidatos if not m.na_rotina]

    @staticmethod
    def remover_da_rotina(*, paciente, pk):
        """
        Remove o remédio da rotina limpando apenas a posologia (quantidade,
        horários, período, dias e observação). O cadastro do remédio (nome,
        dosagem, forma, médico) é mantido. Retorna True se encontrou o item.
        """
        medicamento = Medicamento.objects.filter(paciente=paciente, pk=pk).first()
        if not medicamento:
            return False
        medicamento.quantidade_dose = ""
        medicamento.horarios = ""
        medicamento.frequencia = ""
        medicamento.data_inicio = None
        medicamento.data_fim = None
        medicamento.observacoes = ""
        medicamento.seg = medicamento.ter = medicamento.qua = medicamento.qui = True
        medicamento.sex = medicamento.sab = medicamento.dom = True
        medicamento.save()
        # Os registros de doses tomadas ficam órfãos de horário — limpa também.
        MedicamentoTomado.objects.filter(medicamento=medicamento).delete()
        return True

    @staticmethod
    def alternar_dose(*, paciente, medicamento_id, data, horario, usuario=None):
        """
        Marca/desmarca uma dose como tomada. Retorna True se passou a estar
        tomada, False se foi desmarcada, ou None se o medicamento não existe.

        Ao marcar, guarda o horário previsto, a hora atual em que foi
        marcada (tomado_em) e QUEM marcou (marcado_por — familiar ou
        cuidador). Ao desmarcar, apaga o registro.
        """
        medicamento = Medicamento.objects.filter(
            paciente=paciente, pk=medicamento_id
        ).first()
        if not medicamento:
            return None

        registro = MedicamentoTomado.objects.filter(
            medicamento=medicamento, data=data, horario_previsto=horario
        ).first()
        if registro:
            registro.delete()
            return False
        MedicamentoTomado.objects.create(
            medicamento=medicamento,
            data=data,
            horario_previsto=horario,
            tomado=True,
            tomado_em=timezone.now(),
            marcado_por=usuario,
        )
        return True
