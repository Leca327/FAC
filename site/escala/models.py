"""
Models do app escala (tela "Escala de Cuidadores").

A escala de um paciente é gerada por turno (Manhã/Tarde/Noite) a partir de um
PADRÃO que se repete. O padrão de cada turno pode ser:

- ``rodizio``: uma sequência ordenada de cuidadores que gira a cada
  ``dias_por_pessoa`` dias, a partir de ``data_inicio`` (ex.: 2 dias um, 2 dias
  outro; ou dia sim dia não).
- ``semanal``: cada dia da semana tem um cuidador fixo (ex.: Seg/Qua = fulano).

Exceções pontuais (trocas de um dia específico) ficam em ``ExcecaoDia`` e têm
prioridade sobre o padrão (é o "Alterado no Dia / ALT" da tela).
"""

from django.conf import settings
from django.db import models

from pacientes.models import Paciente


class Turno(models.TextChoices):
    MANHA = "manha", "Manhã"
    TARDE = "tarde", "Tarde"
    NOITE = "noite", "Noite"


# Horário fixo de cada turno (apenas exibição).
TURNO_HORARIOS = {
    Turno.MANHA: "06:00-12:00",
    Turno.TARDE: "12:00-18:00",
    Turno.NOITE: "18:00-06:00",
}

# Dias da semana (0 = segunda ... 6 = domingo), para o padrão semanal.
DIAS_SEMANA = [
    (0, "Segunda"),
    (1, "Terça"),
    (2, "Quarta"),
    (3, "Quinta"),
    (4, "Sexta"),
    (5, "Sábado"),
    (6, "Domingo"),
]


class PadraoTurno(models.Model):
    """Padrão base de um turno de um paciente."""

    class Tipo(models.TextChoices):
        RODIZIO = "rodizio", "Rodízio"
        SEMANAL = "semanal", "Por dia da semana"

    paciente = models.ForeignKey(
        Paciente, on_delete=models.CASCADE, related_name="padroes_escala"
    )
    turno = models.CharField("turno", max_length=10, choices=Turno.choices)
    tipo_padrao = models.CharField(
        "tipo de padrão", max_length=10, choices=Tipo.choices, default=Tipo.RODIZIO
    )
    # Apenas para o rodízio:
    dias_por_pessoa = models.PositiveSmallIntegerField("dias por pessoa", default=1)
    data_inicio = models.DateField("início do rodízio", null=True, blank=True)

    class Meta:
        db_table = "padrao_turno"
        verbose_name = "padrão de turno"
        verbose_name_plural = "padrões de turno"
        constraints = [
            models.UniqueConstraint(
                fields=["paciente", "turno"], name="unique_padrao_turno"
            )
        ]

    def __str__(self):
        return f"{self.paciente} — {self.get_turno_display()} ({self.get_tipo_padrao_display()})"

    @property
    def is_rodizio(self):
        return self.tipo_padrao == self.Tipo.RODIZIO


class RodizioItem(models.Model):
    """Posição de um cuidador na sequência do rodízio."""

    padrao = models.ForeignKey(
        PadraoTurno, on_delete=models.CASCADE, related_name="itens_rodizio"
    )
    ordem = models.PositiveSmallIntegerField("ordem", default=0)
    cuidador = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="+"
    )

    class Meta:
        db_table = "rodizio_item"
        ordering = ["ordem"]

    def __str__(self):
        return f"{self.padrao} #{self.ordem}: {self.cuidador}"


class SemanalItem(models.Model):
    """Cuidador fixo de um dia da semana (padrão semanal)."""

    padrao = models.ForeignKey(
        PadraoTurno, on_delete=models.CASCADE, related_name="itens_semanal"
    )
    dia_semana = models.PositiveSmallIntegerField("dia da semana", choices=DIAS_SEMANA)
    cuidador = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="+",
    )

    class Meta:
        db_table = "semanal_item"
        ordering = ["dia_semana"]
        constraints = [
            models.UniqueConstraint(
                fields=["padrao", "dia_semana"], name="unique_semanal_dia"
            )
        ]

    def __str__(self):
        return f"{self.padrao} — {self.get_dia_semana_display()}: {self.cuidador}"


class ExcecaoDia(models.Model):
    """Troca pontual de um (dia, turno) — sobrepõe o padrão (ALT)."""

    paciente = models.ForeignKey(
        Paciente, on_delete=models.CASCADE, related_name="excecoes_escala"
    )
    data = models.DateField("data")
    turno = models.CharField("turno", max_length=10, choices=Turno.choices)
    cuidador = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="+",
        help_text="Vazio = folga (ninguém).",
    )

    class Meta:
        db_table = "excecao_dia"
        verbose_name = "exceção de dia"
        verbose_name_plural = "exceções de dia"
        constraints = [
            models.UniqueConstraint(
                fields=["paciente", "data", "turno"], name="unique_excecao_dia"
            )
        ]

    def __str__(self):
        return f"{self.paciente} — {self.data} {self.get_turno_display()}: {self.cuidador or 'folga'}"
