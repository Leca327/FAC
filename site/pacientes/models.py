"""
Models do app pacientes (seções 2.6.3 e DER).

- Paciente: pessoa que recebe os cuidados, com um familiar responsável.
- Participacao: entidade associativa que vincula usuários (familiares ou
  cuidadores) a pacientes, com sistema de convites e permissões.
"""

from datetime import date

from django.conf import settings
from django.db import models
from django.utils.crypto import get_random_string


def _novo_token():
    return get_random_string(40)


class Paciente(models.Model):
    """Pessoa que recebe os cuidados domiciliares."""

    nome = models.CharField("nome", max_length=255)
    cpf = models.CharField("CPF", max_length=11, unique=True, null=True, blank=True)
    data_nascimento = models.DateField("data de nascimento")
    # Endereço em partes (a "rua" fica em `endereco`).
    endereco = models.CharField("rua", max_length=255, blank=True)
    complemento = models.CharField("complemento", max_length=100, blank=True)
    cidade = models.CharField("cidade", max_length=100, blank=True)
    estado = models.CharField("estado (UF)", max_length=2, blank=True)
    cep = models.CharField("CEP", max_length=8, blank=True)
    pais = models.CharField("país", max_length=60, blank=True, default="Brasil")
    telefone = models.CharField("telefone", max_length=11, blank=True)

    familiar_responsavel = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="pacientes_responsavel",
        verbose_name="familiar responsável",
    )

    condicoes_saude = models.TextField("condições de saúde", blank=True)
    alergias = models.TextField("alergias", blank=True)
    foto = models.FileField("foto", upload_to="pacientes/", null=True, blank=True)

    # Localização para validação de check-in via GPS (RN01)
    latitude_gps = models.DecimalField(max_digits=10, decimal_places=8, null=True, blank=True)
    longitude_gps = models.DecimalField(max_digits=11, decimal_places=8, null=True, blank=True)
    raio_validacao_gps = models.FloatField("raio de validação (m)", default=100)

    data_criacao = models.DateTimeField("data de criação", auto_now_add=True)
    ativo = models.BooleanField("ativo", default=True)

    class Meta:
        db_table = "paciente"
        verbose_name = "paciente"
        verbose_name_plural = "pacientes"
        ordering = ["nome"]

    def __str__(self):
        return self.nome

    @property
    def idade(self):
        """Idade do paciente em anos completos."""
        if not self.data_nascimento:
            return None
        hoje = date.today()
        return (
            hoje.year - self.data_nascimento.year
            - ((hoje.month, hoje.day) < (self.data_nascimento.month, self.data_nascimento.day))
        )


class Participacao(models.Model):
    """
    Vínculo (convite) entre um usuário e um paciente — tabela única que
    intermedeia ``usuario`` e ``paciente`` para toda a Equipe do paciente
    (familiares e cuidadores). É também o que governa o controle de acesso.
    """

    class Tipo(models.TextChoices):
        FAMILIAR = "familiar", "Familiar"
        CUIDADOR = "cuidador", "Cuidador"

    class Status(models.TextChoices):
        PENDENTE = "pendente", "Pendente"
        ACEITO = "aceito", "Aceito"
        REJEITADO = "rejeitado", "Rejeitado"

    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="participacoes",
    )
    paciente = models.ForeignKey(
        Paciente,
        on_delete=models.CASCADE,
        related_name="participacoes",
    )
    tipo_participacao = models.CharField(max_length=10, choices=Tipo.choices)
    # Relação com o paciente (Filha, Marido, ...) — só faz sentido no tipo familiar.
    vinculo = models.CharField("vínculo", max_length=100, blank=True)
    status_convite = models.CharField(
        max_length=10, choices=Status.choices, default=Status.PENDENTE
    )
    # Token do link de aceite enviado por e-mail.
    token = models.CharField(
        "token do convite", max_length=40, unique=True, default=_novo_token
    )
    data_convite = models.DateTimeField(auto_now_add=True)
    data_resposta = models.DateTimeField(null=True, blank=True)
    permissao_leitura = models.BooleanField(default=True)
    permissao_escrita = models.BooleanField(default=False)

    class Meta:
        db_table = "participacao"
        verbose_name = "participação"
        verbose_name_plural = "participações"
        constraints = [
            models.UniqueConstraint(
                fields=["usuario", "paciente"], name="unique_participacao"
            )
        ]

    def __str__(self):
        return f"{self.usuario} → {self.paciente} ({self.get_status_convite_display()})"

    @property
    def is_aceito(self):
        return self.status_convite == self.Status.ACEITO

    @property
    def nome(self):
        """Nome de exibição do membro (vem da conta vinculada)."""
        return self.usuario.get_full_name() or self.usuario.email

    @property
    def email(self):
        return self.usuario.email

    @property
    def telefone(self):
        return self.usuario.telefone

    @property
    def iniciais(self):
        """Inicial do nome para o avatar."""
        return (self.nome.strip()[:1] or "?").upper()
