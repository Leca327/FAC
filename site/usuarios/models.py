"""
Models do app usuarios (seções 2.6.2 e 2.6.3).

Usuario é a superclasse de autenticação (herda de AbstractUser), com login
por e-mail e um discriminador tipo_usuario que diferencia Familiar e Cuidador.
Familiar e Cuidador são especializações (herança por tabela), implementadas
como OneToOne com chave primária compartilhada — espelhando o DER.
"""

from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator
from django.db import models

from .managers import UsuarioManager


class Usuario(AbstractUser):
    """Superclasse de usuário com autenticação por e-mail."""

    class Tipo(models.TextChoices):
        FAMILIAR = "familiar", "Familiar"
        CUIDADOR = "cuidador", "Cuidador"

    # Login por e-mail — removemos o username padrão do AbstractUser
    username = None
    email = models.EmailField("e-mail", unique=True)

    tipo_usuario = models.CharField(
        "tipo de usuário", max_length=10, choices=Tipo.choices
    )
    cpf = models.CharField(
        "CPF",
        max_length=11,
        unique=True,
        null=True,
        blank=True,
        validators=[RegexValidator(r"^\d{11}$", "O CPF deve conter 11 dígitos.")],
    )
    telefone = models.CharField("telefone", max_length=11, blank=True)
    endereco = models.CharField("endereço", max_length=255, blank=True)
    cep = models.CharField("CEP", max_length=8, blank=True)
    data_criacao = models.DateTimeField("data de criação", auto_now_add=True)
    # True quando a senha atual é uma temporária gerada pela recuperação,
    # forçando o usuário a redefini-la no próximo acesso.
    senha_temporaria = models.BooleanField("senha temporária", default=False)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []  # email + password já são exigidos

    objects = UsuarioManager()

    class Meta:
        db_table = "usuario"
        verbose_name = "usuário"
        verbose_name_plural = "usuários"

    def __str__(self):
        return f"{self.get_full_name() or self.email} ({self.get_tipo_usuario_display()})"

    @property
    def is_familiar(self):
        return self.tipo_usuario == self.Tipo.FAMILIAR

    @property
    def is_cuidador(self):
        return self.tipo_usuario == self.Tipo.CUIDADOR


class Familiar(models.Model):
    """Especialização de Usuario (responsável pelo gerenciamento do cuidado)."""

    usuario = models.OneToOneField(
        Usuario,
        on_delete=models.CASCADE,
        primary_key=True,
        related_name="familiar",
    )
    vinculo = models.CharField(
        "vínculo", max_length=100, blank=True,
        help_text="Relação com o paciente: pai, filho, cônjuge, etc.",
    )

    class Meta:
        db_table = "familiar"
        verbose_name = "familiar"
        verbose_name_plural = "familiares"

    def __str__(self):
        return f"Familiar: {self.usuario.email}"


class Cuidador(models.Model):
    """Especialização de Usuario (profissional de cuidado domiciliar)."""

    usuario = models.OneToOneField(
        Usuario,
        on_delete=models.CASCADE,
        primary_key=True,
        related_name="cuidador",
    )
    numero_registro = models.CharField(
        "número de registro", max_length=50, blank=True, null=True, unique=True
    )
    especialidade = models.CharField("especialidade", max_length=150, blank=True)
    data_ultima_atividade = models.DateTimeField(
        "última atividade", null=True, blank=True
    )

    class Meta:
        db_table = "cuidador"
        verbose_name = "cuidador"
        verbose_name_plural = "cuidadores"

    def __str__(self):
        return f"Cuidador: {self.usuario.email}"
