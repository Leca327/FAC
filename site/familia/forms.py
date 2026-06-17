"""Formulários do app familia (convite e edição de membros)."""

from django import forms

from .models import MembroFamilia

# Vínculos comuns oferecidos no menu suspenso.
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


class ConvidarMembroForm(forms.ModelForm):
    """Convite de um novo membro da família (popup "Convidar Membro")."""

    vinculo = forms.ChoiceField(choices=VINCULO_CHOICES, label="Vínculo")

    class Meta:
        model = MembroFamilia
        fields = ["nome", "email", "telefone", "vinculo"]
        widgets = {
            "nome": forms.TextInput(attrs={"placeholder": "Ex.: Joana Silva"}),
            "email": forms.EmailInput(attrs={"placeholder": "Ex.: joana@example.com"}),
            "telefone": forms.TextInput(attrs={"placeholder": "Ex.: (21) 98765-4321"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        obrigatorios = {"nome", "email", "vinculo"}
        for nome, campo in self.fields.items():
            campo.required = nome in obrigatorios


class EditarMembroForm(forms.ModelForm):
    """Edita os dados de um membro (nome, telefone, vínculo)."""

    vinculo = forms.ChoiceField(choices=VINCULO_CHOICES, label="Vínculo")

    class Meta:
        model = MembroFamilia
        fields = ["nome", "telefone", "vinculo"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["nome"].required = True
        self.fields["vinculo"].required = True
        self.fields["telefone"].required = False
