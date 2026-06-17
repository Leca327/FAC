"""
Model do app consultas (tela "Consultas e Exames").

Espelha a tela de Medicação Diária: agenda de consultas, exames e
procedimentos do paciente, agrupados por dia. Cada item pode ser marcado
como "Realizada" — e aí guarda o resultado e QUEM marcou (mesma lógica do
medicamento_tomado).

Mudanças em relação à tabela `consulta` original do DER:
- `motivo` virou `observacao`;
- removido `proximo_agendamento`;
- `familiar_marcou_id` virou `agendada_por` (pode ser familiar OU cuidador);
- adicionados `realizada_por` e `realizada_em` (quem marcou como realizada);
- médico/clínica viraram campos de texto (como em medicamentos), em vez de
  uma FK — a tela é autossuficiente.
"""

from django.conf import settings
from django.db import models

from medicos.models import Medico
from pacientes.models import Paciente


class Consulta(models.Model):
    """Consulta ou exame agendado para um paciente."""

    class Tipo(models.TextChoices):
        CONSULTA = "consulta", "Consulta"
        EXAME = "exame", "Exame"

    class Status(models.TextChoices):
        AGENDADA = "agendada", "Agendada"
        REALIZADA = "realizada", "Realizada"
        CANCELADA = "cancelada", "Cancelada"

    paciente = models.ForeignKey(
        Paciente,
        on_delete=models.CASCADE,
        related_name="consultas",
        verbose_name="paciente",
    )

    tipo = models.CharField(
        "tipo", max_length=10, choices=Tipo.choices, default=Tipo.CONSULTA
    )
    titulo = models.CharField(  # Cardiologia / Eletrocardiograma / Clínica Geral
        "título", max_length=255
    )
    # Médico/clínica/laboratório escolhido entre os cadastrados do paciente.
    # Nome e CRM/CNPJ exibidos vêm daqui.
    medico = models.ForeignKey(
        Medico,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="consultas",
        verbose_name="médico/clínica",
    )

    data_hora = models.DateTimeField("data e hora")
    observacao = models.TextField("observação", blank=True)

    status = models.CharField(
        "status", max_length=10, choices=Status.choices, default=Status.AGENDADA
    )
    resultado = models.TextField(  # preenchido no popup ao marcar como realizada
        "resultado", blank=True
    )

    # Quem agendou (familiar ou cuidador) — exibido como "Agendado por ...".
    agendada_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="consultas_agendadas",
        verbose_name="agendada por",
    )
    # Quem marcou como realizada e quando (mesma lógica do medicamento_tomado).
    realizada_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="consultas_realizadas",
        verbose_name="realizada por",
    )
    realizada_em = models.DateTimeField("realizada em", null=True, blank=True)

    data_criacao = models.DateTimeField("data de criação", auto_now_add=True)

    class Meta:
        db_table = "consulta"
        verbose_name = "consulta"
        verbose_name_plural = "consultas"
        ordering = ["data_hora"]
        indexes = [
            models.Index(fields=["paciente", "data_hora"], name="idx_consulta_pac_data"),
            models.Index(fields=["status"], name="idx_consulta_status"),
        ]

    def __str__(self):
        return f"{self.titulo} ({self.data_hora:%d/%m/%Y %H:%M})"

    @property
    def is_realizada(self):
        return self.status == self.Status.REALIZADA
