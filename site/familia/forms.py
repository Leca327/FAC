"""Formulários da Equipe (convite por e-mail e edição de vínculo)."""

from django import forms

from pacientes.models import Participacao

# Vínculos comuns oferecidos no menu suspenso (apenas para familiares).
VINCULO_CHOICES = [
    ("Cônjuge", "Cônjuge"),
    ("Marido", "Marido"),
    ("Esposa", "Esposa"),
    ("Filho", "Filho"),
    ("Filha", "Filha"),
    ("Pai", "Pai"),
    ("Mãe", "Mãe"),
    ("Irmão", "Irmão"),
    ("Irmã", "Irmã"),
    ("Neto", "Neto"),
    ("Neta", "Neta"),
    ("Genro", "Genro"),
    ("Nora", "Nora"),
    ("Outro", "Outro"),
]

TIPO_CHOICES = [
    (Participacao.Tipo.FAMILIAR, "Família"),
    (Participacao.Tipo.CUIDADOR, "Cuidador"),
]


class ConvidarMembroForm(forms.Form):
    """Convite de um membro da equipe — exige uma conta existente (e-mail)."""

    tipo = forms.ChoiceField(choices=TIPO_CHOICES, label="Tipo")
    email = forms.EmailField(
        label="E-mail",
        widget=forms.EmailInput(attrs={"placeholder": "e-mail da conta no CuidaCare"}),
    )
    vinculo = forms.ChoiceField(
        choices=VINCULO_CHOICES, label="Vínculo", required=False
    )

    def clean(self):
        dados = super().clean()
        if dados.get("tipo") == Participacao.Tipo.FAMILIAR and not dados.get("vinculo"):
            self.add_error("vinculo", "Informe o vínculo do familiar.")
        return dados


class EditarMembroForm(forms.Form):
    """Edita apenas o vínculo de um familiar da equipe."""

    vinculo = forms.ChoiceField(choices=VINCULO_CHOICES, label="Vínculo")
