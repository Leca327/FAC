"""
Model do app prontuario (tela "Prontuário").

O Prontuário é a linha do tempo do dia do paciente. Ele agrega tres fontes:
- ANOTACOES manuais que o familiar/cuidador registra (este model);
- medicamentos tomados (derivados de medicamentos.MedicamentoTomado);
- consultas realizadas (derivadas de consultas.Consulta).

Apenas a anotacao manual e persistida aqui; os demais eventos sao montados
em tempo de exibicao pela camada de Services, sem duplicar dados.
"""

from django.conf import settings
from django.db import models

from pacientes.models import Paciente


class Anotacao(models.Model):
    """Anotacao manual do prontuario (um 'ponto' do que aconteceu no dia)."""

    paciente = models.ForeignKey(
        Paciente,
        on_delete=models.CASCADE,
        related_name="anotacoes",
        verbose_name="paciente",
    )
    data_hora = models.DateTimeField("data e hora")
    titulo = models.CharField("título", max_length=255)
    descricao = models.TextField("descrição", blank=True)
    # Quem registrou (familiar ou cuidador).
    autor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="anotacoes",
        verbose_name="autor",
    )
    data_criacao = models.DateTimeField("data de criação", auto_now_add=True)

    class Meta:
        db_table = "anotacao"
        verbose_name = "anotação"
        verbose_name_plural = "anotações"
        ordering = ["-data_hora"]
        indexes = [
            models.Index(fields=["paciente", "data_hora"], name="idx_anotacao_pac_data"),
        ]

    def __str__(self):
        return f"{self.titulo} ({self.data_hora:%d/%m/%Y %H:%M})"
