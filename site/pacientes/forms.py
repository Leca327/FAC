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
            "endereco", "complemento", "cidade", "estado", "cep", "pais",
            "condicoes_saude", "alergias",
        ]
        labels = {
            "endereco": "Rua", "complemento": "Complemento", "cidade": "Cidade",
            "estado": "Estado", "cep": "CEP", "pais": "País",
        }
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
            "endereco": forms.TextInput(attrs={"placeholder": "Rua e número"}),
            "complemento": forms.TextInput(attrs={"placeholder": "Apto, bloco... (opcional)"}),
            "cidade": forms.TextInput(attrs={"placeholder": "Cidade"}),
            "estado": forms.TextInput(attrs={"maxlength": "2", "placeholder": "UF"}),
            "cep": forms.TextInput(attrs={
                "inputmode": "numeric", "maxlength": "8",
                "pattern": r"\d*", "class": "js-digits", "placeholder": "Somente números",
            }),
            "pais": forms.TextInput(attrs={"placeholder": "País"}),
            "condicoes_saude": forms.Textarea(attrs={
                "rows": 2, "placeholder": "Diagnósticos e condições de saúde",
            }),
            "alergias": forms.Textarea(attrs={
                "rows": 2, "placeholder": "Alergias conhecidas (ou 'Nenhuma')",
            }),
        }

    # Complemento e país não são obrigatórios (país tem padrão "Brasil").
    OPCIONAIS = {"complemento", "pais"}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for nome, campo in self.fields.items():
            campo.required = nome not in self.OPCIONAIS

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

    def clean_estado(self):
        return (self.cleaned_data.get("estado") or "").strip().upper()

    def clean_data_nascimento(self):
        nascimento = self.cleaned_data.get("data_nascimento")
        if nascimento and nascimento > date.today():
            raise forms.ValidationError("A data de nascimento não pode ser futura.")
        return nascimento


class PacientePerfilForm(forms.ModelForm):
    """Edição dos dados do paciente na tela 'Perfil do Paciente'."""

    class Meta:
        model = Paciente
        # latitude/longitude NÃO são editáveis: vêm do geocoding do endereço.
        fields = [
            "nome", "cpf", "data_nascimento", "telefone",
            "endereco", "complemento", "cidade", "estado", "cep", "pais",
            "condicoes_saude", "alergias", "raio_validacao_gps",
        ]
        labels = {
            "nome": "Nome completo", "cpf": "CPF",
            "data_nascimento": "Data de nascimento", "telefone": "Telefone",
            "endereco": "Rua", "complemento": "Complemento", "cidade": "Cidade",
            "estado": "Estado", "cep": "CEP", "pais": "País",
            "condicoes_saude": "Condições de saúde",
            "alergias": "Alergias", "raio_validacao_gps": "Raio (m)",
        }
        widgets = {
            "nome": forms.TextInput(attrs={"placeholder": "Nome completo"}),
            "cpf": forms.TextInput(attrs={
                "inputmode": "numeric", "maxlength": "11", "pattern": r"\d*",
                "class": "js-digits", "placeholder": "Somente números",
            }),
            "data_nascimento": forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"),
            "telefone": forms.TextInput(attrs={
                "inputmode": "numeric", "maxlength": "11", "pattern": r"\d*",
                "class": "js-digits", "placeholder": "DDD + número",
            }),
            "endereco": forms.TextInput(attrs={"placeholder": "Rua e número"}),
            "complemento": forms.TextInput(attrs={"placeholder": "Apto, bloco..."}),
            "cidade": forms.TextInput(),
            "estado": forms.TextInput(attrs={"maxlength": "2", "placeholder": "UF"}),
            "cep": forms.TextInput(attrs={
                "inputmode": "numeric", "maxlength": "8", "pattern": r"\d*",
                "class": "js-digits",
            }),
            "pais": forms.TextInput(),
            "condicoes_saude": forms.Textarea(attrs={"rows": 3}),
            "alergias": forms.Textarea(attrs={"rows": 3}),
            "raio_validacao_gps": forms.NumberInput(attrs={"step": "1", "min": "1"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["data_nascimento"].input_formats = ["%Y-%m-%d"]

    def clean_cpf(self):
        cpf = (self.cleaned_data.get("cpf") or "").strip()
        if not cpf:
            return None  # CPF é opcional no model (null permitido)
        if not cpf.isdigit() or len(cpf) != 11:
            raise forms.ValidationError("O CPF deve conter 11 dígitos numéricos.")
        if Paciente.objects.filter(cpf=cpf).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError("Este CPF já está cadastrado.")
        return cpf

    def clean_telefone(self):
        telefone = (self.cleaned_data.get("telefone") or "").strip()
        if telefone and (not telefone.isdigit() or len(telefone) not in (10, 11)):
            raise forms.ValidationError(
                "O telefone deve conter 10 ou 11 dígitos numéricos (com DDD)."
            )
        return telefone

    def clean_estado(self):
        return (self.cleaned_data.get("estado") or "").strip().upper()

    def clean_data_nascimento(self):
        nascimento = self.cleaned_data.get("data_nascimento")
        if nascimento and nascimento > date.today():
            raise forms.ValidationError("A data de nascimento não pode ser futura.")
        return nascimento
