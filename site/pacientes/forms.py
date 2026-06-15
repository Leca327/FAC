"""
Formulário de cadastro de paciente (RF03 — Manter Paciente).

Todos os campos são obrigatórios. As validações de frontend (seção 2.7.7)
são duplicadas aqui no backend (seção 2.6.6).
"""

from datetime import date

from django import forms

from .models import Paciente


class PacienteForm(forms.ModelForm):
    class Meta:
        model = Paciente
        fields = [
            "nome", "cpf", "data_nascimento", "telefone",
            "endereco", "condicoes_saude", "alergias",
        ]
        widgets = {
            "nome": forms.TextInput(attrs={"placeholder": "Nome completo"}),
            "cpf": forms.TextInput(attrs={
                "inputmode": "numeric", "maxlength": "11",
                "pattern": r"\d*", "class": "js-digits",
                "placeholder": "Somente números",
            }),
            "data_nascimento": forms.DateInput(
                attrs={"type": "date"}, format="%Y-%m-%d"
            ),
            "telefone": forms.TextInput(attrs={
                "inputmode": "numeric", "maxlength": "11",
                "pattern": r"\d*", "class": "js-digits",
                "placeholder": "DDD + número",
            }),
            "endereco": forms.TextInput(attrs={"placeholder": "Rua, número, bairro"}),
            "condicoes_saude": forms.Textarea(attrs={
                "rows": 2, "placeholder": "Diagnósticos e condições de saúde",
            }),
            "alergias": forms.Textarea(attrs={
                "rows": 2, "placeholder": "Alergias conhecidas (ou 'Nenhuma')",
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Todos os campos são obrigatórios
        for campo in self.fields.values():
            campo.required = True

    def clean_cpf(self):
        cpf = (self.cleaned_data.get("cpf") or "").strip()
        if not cpf.isdigit() or len(cpf) != 11:
            raise forms.ValidationError("O CPF deve conter 11 dígitos numéricos.")
        return cpf

    def clean_telefone(self):
        telefone = (self.cleaned_data.get("telefone") or "").strip()
        if not telefone.isdigit() or len(telefone) not in (10, 11):
            raise forms.ValidationError(
                "O telefone deve conter 10 ou 11 dígitos numéricos (com DDD)."
            )
        return telefone

    def clean_data_nascimento(self):
        nascimento = self.cleaned_data.get("data_nascimento")
        if nascimento and nascimento > date.today():
            raise forms.ValidationError("A data de nascimento não pode ser futura.")
        return nascimento
