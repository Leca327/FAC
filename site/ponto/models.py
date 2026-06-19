"""
Model do app ponto (tela "Meu Ponto").

Mapeia a tabela `plantao` (já existente no dump): cada plantão é um turno de
trabalho de um cuidador com um paciente, com check-in (hora_entrada),
check-out (hora_saida) e a duração trabalhada. A regra de um plantão aberto
por vez (RN05) fica na camada de Services.
"""

from django.conf import settings
from django.db import models

from pacientes.models import Paciente


class Plantao(models.Model):
    """Turno de trabalho (ponto) de um cuidador em um paciente."""

    class Status(models.TextChoices):
        ABERTO = "aberto", "Aberto"
        FECHADO = "fechado", "Fechado"
        CANCELADO = "cancelado", "Cancelado"

    paciente = models.ForeignKey(
        Paciente,
        on_delete=models.CASCADE,
        related_name="plantoes",
        verbose_name="paciente",
    )
    cuidador = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="plantoes",
        verbose_name="cuidador",
    )
    data_plantao = models.DateField("data do plantão")
    hora_entrada = models.TimeField("hora de entrada", null=True, blank=True)
    hora_saida = models.TimeField("hora de saída", null=True, blank=True)
    localizacao_gps_entrada = models.CharField(
        "GPS de entrada", max_length=100, blank=True
    )
    status = models.CharField(
        "status", max_length=10, choices=Status.choices, default=Status.ABERTO
    )
    duracao_horas = models.DecimalField(
        "duração (horas)", max_digits=5, decimal_places=2, null=True, blank=True
    )
    observacoes = models.TextField("observações", blank=True)
    data_criacao = models.DateTimeField("data de criação", auto_now_add=True)

    class Meta:
        db_table = "plantao"
        verbose_name = "plantão"
        verbose_name_plural = "plantões"
        ordering = ["-data_plantao", "-hora_entrada"]
        constraints = [
            models.UniqueConstraint(
                fields=["paciente", "cuidador", "data_plantao"],
                name="unique_plantao_aberto",
            )
        ]

    def __str__(self):
        return f"{self.cuidador} — {self.data_plantao} ({self.get_status_display()})"

    @property
    def is_aberto(self):
        return self.status == self.Status.ABERTO

    @property
    def is_fechado(self):
        return self.status == self.Status.FECHADO
