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


class RotinaPosologiaForm(forms.ModelForm):
    """
    Formulário da posologia da rotina (popup "Adicionar remédio à rotina" e
    edição na tela Medicação Diária).

    Não cadastra o remédio em si — ele é escolhido à parte, num <select> com
    os remédios já cadastrados. Aqui definimos só a posologia: horários,
    quantidade por dose, período de uso e dias da semana. Ao remover da
    rotina esses campos são limpos, mantendo o cadastro do remédio.
    """

    class Meta:
        model = Medicamento
        fields = [
            "quantidade_dose", "horarios", "data_inicio", "data_fim",
            "seg", "ter", "qua", "qui", "sex", "sab", "dom",
            "observacoes",
        ]
        widgets = {
            "quantidade_dose": forms.TextInput(attrs={"placeholder": "Ex.: 1 comprimido"}),
            "horarios": forms.TextInput(attrs={
                "placeholder": "Digite um horário e tecle espaço (ex.: 08:00)",
                "class": "js-taginput",
            }),
            "data_inicio": forms.DateInput(attrs={"type": "date"}),
            "data_fim": forms.DateInput(attrs={"type": "date"}),
            "observacoes": forms.Textarea(attrs={"rows": 2, "placeholder": "Ex.: Tomar com água, de manhã"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        obrigatorios = {"horarios", "quantidade_dose", "data_inicio"}
        for nome, campo in self.fields.items():
            campo.required = nome in obrigatorios

    def clean_horarios(self):
        """Valida e normaliza os horários (lista HH:MM separada por vírgula)."""
        bruto = self.cleaned_data.get("horarios", "")
        horarios = []
        for parte in bruto.split(","):
            parte = parte.strip()
            if not parte:
                continue
            try:
                hh, mm = parte.split(":")
                hh, mm = int(hh), int(mm)
                if not (0 <= hh <= 23 and 0 <= mm <= 59):
                    raise ValueError
            except (ValueError, TypeError):
                raise forms.ValidationError(
                    f'Horário inválido: "{parte}". Use o formato HH:MM (ex.: 08:00).'
                )
            horarios.append(f"{hh:02d}:{mm:02d}")
        if not horarios:
            raise forms.ValidationError("Informe ao menos um horário.")
        return ", ".join(horarios)

    def clean(self):
        cleaned = super().clean()
        inicio = cleaned.get("data_inicio")
        fim = cleaned.get("data_fim")
        if inicio and fim and fim < inicio:
            self.add_error("data_fim", "A data de fim deve ser igual ou posterior ao início.")
        return cleaned
