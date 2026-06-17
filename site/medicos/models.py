"""
Model do app medicos.

Tela "Médicos" do paciente: cadastro dos médicos, clínicas e laboratórios
ligados ao paciente, com todos os dados de contato (baseado na tabela
`medico_clinica` do DER). Diferente da tela de Medicamentos, aqui todos
os campos do médico aparecem.
"""

from django.db import models

from pacientes.models import Paciente


class Medico(models.Model):
    """Médico, clínica ou laboratório vinculado a um paciente."""

    class Tipo(models.TextChoices):
        MEDICO = "medico", "Médico"
        CLINICA = "clinica", "Clínica"
        LABORATORIO = "laboratorio", "Laboratório"

    paciente = models.ForeignKey(
        Paciente,
        on_delete=models.CASCADE,
        related_name="medicos",
        verbose_name="paciente",
    )

    nome = models.CharField("nome", max_length=255)
    tipo = models.CharField(
        "tipo", max_length=15, choices=Tipo.choices, default=Tipo.MEDICO
    )
    especialidade = models.CharField("especialidade", max_length=150, blank=True)
    crm_cnpj = models.CharField("CRM/CNPJ", max_length=50, blank=True)
    telefone = models.CharField("telefone", max_length=11, blank=True)
    email = models.EmailField("e-mail", max_length=255, blank=True)
    endereco = models.CharField("endereço", max_length=255, blank=True)
    cidade = models.CharField("cidade", max_length=100, blank=True)
    uf = models.CharField("UF", max_length=2, blank=True)

    data_criacao = models.DateTimeField("data de criação", auto_now_add=True)

    class Meta:
        db_table = "medico"
        verbose_name = "médico"
        verbose_name_plural = "médicos"
        ordering = ["nome"]

    def __str__(self):
        return self.nome

    @property
    def localizacao(self):
        """Endereço resumido para exibição (ex.: 'Av. Paulista, 1000 - São Paulo/SP')."""
        cidade_uf = ""
        if self.cidade and self.uf:
            cidade_uf = f"{self.cidade}/{self.uf}"
        else:
            cidade_uf = self.cidade or self.uf
        partes = [p for p in [self.endereco, cidade_uf] if p]
        return " - ".join(partes)
