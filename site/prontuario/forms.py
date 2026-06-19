"""Formulário de anotação do prontuário."""

from django import forms
from django.utils import timezone

from .models import Anotacao


class AnotacaoForm(forms.ModelForm):
    class Meta:
        model = Anotacao
        fields = ["titulo", "data_hora", "descricao"]
        widgets = {
            "titulo": forms.TextInput(attrs={"placeholder": "O que aconteceu?"}),
            "data_hora": forms.DateTimeInput(
                attrs={"type": "datetime-local"}, format="%Y-%m-%dT%H:%M"
            ),
            "descricao": forms.Textarea(
                attrs={"rows": 3, "placeholder": "Detalhes (opcional)"}
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["data_hora"].input_formats = ["%Y-%m-%dT%H:%M"]
        self.fields["descricao"].required = False

    def clean_data_hora(self):
        dt = self.cleaned_data.get("data_hora")
        if dt and timezone.is_naive(dt):
            dt = timezone.make_aware(dt, timezone.get_current_timezone())
        # RN: não é permitido registrar anotações em data/hora futura.
        if dt and dt > timezone.now():
            raise forms.ValidationError(
                "Não é permitido registrar anotações em data/hora futura."
            )
        return dt
