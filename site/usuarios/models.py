"""
Models do app usuarios (seção 2.6.2).

Usuario é a única tabela de usuário (herda de AbstractUser), com login por
e-mail e um discriminador tipo_usuario (familiar/cuidador). Não há mais
especialização: o vínculo de cada usuário com um paciente (e seu papel) vive
na tabela ``pacientes.Participacao``.
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

    class Genero(models.TextChoices):
        FEMININO = "feminino", "Feminino"
        MASCULINO = "masculino", "Masculino"
        OUTRO = "outro", "Outro"
        NAO_INFORMAR = "nao_informar", "Prefiro não informar"

    class EstadoCivil(models.TextChoices):
        SOLTEIRO = "solteiro", "Solteiro(a)"
        CASADO = "casado", "Casado(a)"
        DIVORCIADO = "divorciado", "Divorciado(a)"
        VIUVO = "viuvo", "Viúvo(a)"
        UNIAO_ESTAVEL = "uniao_estavel", "União estável"

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
    rg = models.CharField("RG", max_length=20, blank=True)
    data_nascimento = models.DateField("data de nascimento", null=True, blank=True)
    genero = models.CharField(
        "gênero", max_length=15, choices=Genero.choices, blank=True
    )
    estado_civil = models.CharField(
        "estado civil", max_length=15, choices=EstadoCivil.choices, blank=True
    )
    telefone = models.CharField("telefone", max_length=11, blank=True)
    whatsapp = models.CharField("WhatsApp", max_length=11, blank=True)
    # Endereço detalhado
    endereco = models.CharField("rua", max_length=255, blank=True)
    complemento = models.CharField("complemento", max_length=100, blank=True)
    cidade = models.CharField("cidade", max_length=100, blank=True)
    estado = models.CharField("estado (UF)", max_length=2, blank=True)
    cep = models.CharField("CEP", max_length=8, blank=True)
    pais = models.CharField("país", max_length=60, blank=True, default="Brasil")
    foto = models.FileField(
        "foto de perfil", upload_to="avatares/", null=True, blank=True
    )
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
