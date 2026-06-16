"""
Formulário de cadastro de medicamento (popup "Novo Medicamento").

Esta tela cadastra apenas o remédio em si (identificação e apresentação).
Os dados de agendamento (horários, quantidade, período e dias da semana)
são definidos na tela de Medicação Diária.

As validações de frontend (seção 2.7.7) são duplicadas no backend
(seção 2.6.6).
"""

from django import forms

from .models import Medicamento


class MedicamentoForm(forms.ModelForm):
    class Meta:
        model = Medicamento
        fields = ["nome", "dosagem", "forma_farmaceutica", "medico"]
        widgets = {
            "nome": forms.TextInput(attrs={"placeholder": "Ex.: Losartana"}),
            "dosagem": forms.TextInput(attrs={"placeholder": "Ex.: 50mg"}),
            "forma_farmaceutica": forms.TextInput(attrs={"placeholder": "Ex.: Comprimido"}),
            "medico": forms.TextInput(attrs={"placeholder": "Ex.: Dr. Carlos"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Campos essenciais obrigatórios; o restante é opcional.
        obrigatorios = {"nome", "dosagem"}
        for nome, campo in self.fields.items():
            campo.required = nome in obrigatorios
