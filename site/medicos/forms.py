"""
Formulário de cadastro/edição de médico (popups da tela "Médicos").

As validações de frontend (seção 2.7.7) são duplicadas no backend
(seção 2.6.6).
"""

from django import forms

from .models import Medico


class MedicoForm(forms.ModelForm):
    class Meta:
        model = Medico
        fields = [
            "nome", "tipo", "especialidade", "crm_cnpj",
            "telefone", "email", "endereco", "cidade", "uf",
        ]
        widgets = {
            "nome": forms.TextInput(attrs={"placeholder": "Ex.: Dr. Carlos"}),
            "especialidade": forms.TextInput(attrs={"placeholder": "Ex.: Cardiologia"}),
            "crm_cnpj": forms.TextInput(attrs={"placeholder": "Ex.: 123456/SP"}),
            "telefone": forms.TextInput(attrs={
                "inputmode": "numeric", "maxlength": "11",
                "pattern": r"\d*", "class": "js-digits",
                "placeholder": "DDD + número",
            }),
            "email": forms.EmailInput(attrs={"placeholder": "Ex.: contato@clinica.com"}),
            "endereco": forms.TextInput(attrs={"placeholder": "Rua, número, bairro"}),
            "cidade": forms.TextInput(attrs={"placeholder": "Ex.: Rio de Janeiro"}),
            "uf": forms.TextInput(attrs={
                "maxlength": "2", "placeholder": "UF", "style": "text-transform:uppercase",
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Apenas o nome é obrigatório; tipo tem padrão; o restante é opcional.
        for nome, campo in self.fields.items():
            campo.required = nome == "nome"

    def clean_telefone(self):
        telefone = (self.cleaned_data.get("telefone") or "").strip()
        if telefone and (not telefone.isdigit() or len(telefone) not in (10, 11)):
            raise forms.ValidationError(
                "O telefone deve conter 10 ou 11 dígitos numéricos (com DDD)."
            )
        return telefone

    def clean_uf(self):
        return (self.cleaned_data.get("uf") or "").strip().upper()
