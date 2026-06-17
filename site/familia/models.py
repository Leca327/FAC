"""
Model do app familia (tela "Família").

Sistema de convites: um membro da família é convidado por e-mail e fica
"Pendente" até aceitar (via link do convite), quando passa a "Aceito" e,
se tiver conta, é vinculado ao usuário.
"""

from django.conf import settings
from django.db import models
from django.utils.crypto import get_random_string

from pacientes.models import Paciente


def _novo_token():
    return get_random_string(40)


class MembroFamilia(models.Model):
    """Membro/convite da família de um paciente."""

    class Status(models.TextChoices):
        PENDENTE = "pendente", "Pendente"
        ACEITO = "aceito", "Aceito"

    paciente = models.ForeignKey(
        Paciente,
        on_delete=models.CASCADE,
        related_name="membros_familia",
        verbose_name="paciente",
    )

    nome = models.CharField("nome", max_length=255)
    email = models.EmailField("e-mail", max_length=255)
    telefone = models.CharField("telefone", max_length=20, blank=True)
    vinculo = models.CharField("vínculo", max_length=100)  # Filha, Marido, Filho...

    status = models.CharField(
        "status", max_length=10, choices=Status.choices, default=Status.PENDENTE
    )
    # Token do link de convite (para aceitar sem estar logado).
    token = models.CharField(
        "token do convite", max_length=40, unique=True, default=_novo_token
    )

    # Vinculado quando o convite é aceito (se a pessoa tiver conta).
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="membros_familia",
        verbose_name="usuário",
    )
    convidado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="convites_familia_enviados",
        verbose_name="convidado por",
    )

    data_convite = models.DateTimeField("convite enviado em", auto_now_add=True)
    data_resposta = models.DateTimeField("aceito em", null=True, blank=True)

    class Meta:
        db_table = "membro_familia"
        verbose_name = "membro da família"
        verbose_name_plural = "membros da família"
        ordering = ["status", "nome"]
        indexes = [
            models.Index(fields=["paciente", "status"], name="idx_membro_pac_status"),
        ]

    def __str__(self):
        return f"{self.nome} ({self.vinculo}) — {self.get_status_display()}"

    @property
    def is_aceito(self):
        return self.status == self.Status.ACEITO

    @property
    def iniciais(self):
        """Inicial do nome para o avatar."""
        return (self.nome.strip()[:1] or "?").upper()
