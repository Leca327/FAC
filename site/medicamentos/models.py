"""
Model do app medicamentos (seção 2.6 — app `medicamentos`).

Tela "Medicamentos" do paciente: lista (em cards ou tabela) os
medicamentos agendados, com dosagem, forma, horários, dias da semana,
médico responsável e período de uso.

Decisão de modelagem (RN — enxugar o BD): o script SQL original separava
`medicamento` (catálogo) e `prescricao_medicamento` (uso pelo paciente).
Para esta tela isso adicionava campos que não são exibidos (princípio
ativo, laboratório, FK para médico_clinica/consulta). Consolidamos tudo
em um único modelo `Medicamento` com apenas os campos usados na página,
e o médico vira um simples campo de texto.
"""

from django.conf import settings
from django.db import models
from django.utils import timezone

from pacientes.models import Paciente


class Medicamento(models.Model):
    """Medicamento agendado para um paciente."""

    # Janela (em minutos) antes da dose em que ela é considerada "Pendente"
    # (perto da hora de tomar).
    JANELA_PENDENTE_MIN = 60

    class Status(models.TextChoices):
        ATIVO = "ativo", "Ativo"
        DESCONTINUADO = "descontinuado", "Descontinuado"

    paciente = models.ForeignKey(
        Paciente,
        on_delete=models.CASCADE,
        related_name="medicamentos",
        verbose_name="paciente",
    )

    # Identificação e apresentação
    nome = models.CharField("remédio", max_length=255)
    dosagem = models.CharField("dosagem", max_length=50)  # ex.: 50mg
    forma_farmaceutica = models.CharField(  # ex.: Comprimido, Líquido
        "forma farmacêutica", max_length=100, blank=True
    )

    # Posologia
    frequencia = models.CharField(  # ex.: "2x ao dia", "A cada 6h"
        "frequência", max_length=100, blank=True
    )
    horarios = models.CharField(  # ex.: "08:00,20:00"
        "horários", max_length=255, blank=True,
        help_text="Horários separados por vírgula (ex.: 08:00, 20:00).",
    )
    quantidade_dose = models.CharField(  # ex.: "1 comprimido"
        "quantidade por dose", max_length=50, blank=True
    )
    medico = models.CharField("médico", max_length=255, blank=True)

    # Período de uso (definido na tela de Medicação Diária)
    data_inicio = models.DateField("data de início", null=True, blank=True)
    data_fim = models.DateField(  # nulo = uso contínuo
        "data de fim", null=True, blank=True,
        help_text="Deixe em branco para uso contínuo.",
    )

    # Controle por dia da semana (segunda a domingo)
    seg = models.BooleanField("segunda", default=True)
    ter = models.BooleanField("terça", default=True)
    qua = models.BooleanField("quarta", default=True)
    qui = models.BooleanField("quinta", default=True)
    sex = models.BooleanField("sexta", default=True)
    sab = models.BooleanField("sábado", default=True)
    dom = models.BooleanField("domingo", default=True)

    observacoes = models.TextField("observação", blank=True)
    status = models.CharField(
        "status", max_length=15, choices=Status.choices, default=Status.ATIVO
    )
    data_criacao = models.DateTimeField("data de criação", auto_now_add=True)

    class Meta:
        db_table = "medicamento"
        verbose_name = "medicamento"
        verbose_name_plural = "medicamentos"
        ordering = ["data_inicio", "nome"]

    def __str__(self):
        return f"{self.nome} ({self.dosagem})"

    # ---------- Helpers para a tela ----------
    @property
    def na_rotina(self):
        """
        True quando o remédio está na "Medicação Diária": tem posologia
        definida (horários + data de início). Ao remover da rotina, esses
        campos são limpos, mas o cadastro do remédio (nome, dosagem, forma,
        médico) permanece.
        """
        return bool(self.horarios.strip() and self.data_inicio)

    @property
    def is_continuo(self):
        """True quando não há data de fim (uso contínuo)."""
        return self.data_fim is None

    @property
    def horarios_lista(self):
        """Lista de horários a partir do campo `horarios`."""
        return [h.strip() for h in self.horarios.split(",") if h.strip()]

    def _horarios_em_minutos(self):
        """Horários do dia convertidos em minutos desde a meia-noite."""
        minutos = []
        for h in self.horarios_lista:
            try:
                hh, mm = h.split(":")
                minutos.append(int(hh) * 60 + int(mm))
            except (ValueError, TypeError):
                continue
        return sorted(minutos)

    @property
    def dias_semana(self):
        """
        Controle por dia para os círculos S T Q Q S S D (Seg→Dom),
        na ordem exibida na tela.
        """
        return [
            {"label": "S", "ativo": self.seg},
            {"label": "T", "ativo": self.ter},
            {"label": "Q", "ativo": self.qua},
            {"label": "Q", "ativo": self.qui},
            {"label": "S", "ativo": self.sex},
            {"label": "S", "ativo": self.sab},
            {"label": "D", "ativo": self.dom},
        ]

    @property
    def situacao(self):
        """
        Situação exibida no badge do card, conforme a hora atual em relação
        aos horários de hoje:

        - 'pendente': perto da hora de tomar (próxima dose dentro da janela);
        - 'proximo': ainda há dose a tomar hoje, mas falta mais tempo;
        - 'passou': todas as doses de hoje já passaram da hora.

        Retorna None quando não há horários definidos (sem badge).
        """
        minutos = self._horarios_em_minutos()
        if not minutos:
            return None

        agora = timezone.localtime()
        agora_min = agora.hour * 60 + agora.minute

        futuros = [m for m in minutos if m >= agora_min]
        if not futuros:
            return "passou"
        if min(futuros) - agora_min <= self.JANELA_PENDENTE_MIN:
            return "pendente"
        return "proximo"

    @property
    def situacao_label(self):
        return {
            "pendente": "Pendente",
            "proximo": "Próximo",
            "passou": "Passou",
        }.get(self.situacao)


class MedicamentoTomado(models.Model):
    """
    Registro de que uma dose de medicamento foi tomada (tela "Medicação
    Diária"). Cada linha representa uma única dose, identificada pelo
    medicamento, pela data e pelo horário previsto (ex.: Losartana,
    16/06/2026, previsto "08:00").

    Guarda os três dados pedidos:
    - `tomado`           → se a pessoa tomou (booleano);
    - `horario_previsto` → a hora em que a dose DEVERIA ser tomada;
    - `tomado_em`        → a data/hora em que foi MARCADA como tomada.

    É o que permite derivar o status da rotina:
    - existe registro tomado            → "tomado";
    - não tomado e o horário já passou   → "atrasado";
    - não tomado e o horário não chegou  → "pendente".
    """

    medicamento = models.ForeignKey(
        Medicamento,
        on_delete=models.CASCADE,
        related_name="registros_tomado",
        verbose_name="medicamento",
    )
    data = models.DateField("data da dose")
    horario_previsto = models.CharField(  # "HH:MM" — hora que deveria ser tomada
        "horário previsto", max_length=5
    )
    tomado = models.BooleanField("tomado", default=True)
    tomado_em = models.DateTimeField(  # quando foi marcada como tomada
        "marcado como tomado em", null=True, blank=True
    )
    marcado_por = models.ForeignKey(  # quem marcou (familiar ou cuidador)
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="doses_marcadas",
        verbose_name="marcado por",
    )

    class Meta:
        db_table = "medicamento_tomado"
        verbose_name = "medicamento tomado"
        verbose_name_plural = "medicamentos tomados"
        ordering = ["data", "horario_previsto"]
        constraints = [
            models.UniqueConstraint(
                fields=["medicamento", "data", "horario_previsto"],
                name="uq_tomado_med_data_horario",
            ),
        ]
        indexes = [
            models.Index(fields=["medicamento", "data"], name="idx_tomado_med_data"),
        ]

    def __str__(self):
        situacao = "tomado" if self.tomado else "não tomado"
        return f"{self.medicamento.nome} {self.data} {self.horario_previsto} ({situacao})"
