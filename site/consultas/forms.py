"""
Formulários do app consultas.

O agendamento captura os dados do compromisso (tipo, título, profissional/
local, CRM/convênio, observação) e a data + hora separadas, combinadas em
`data_hora` no save. O resultado é preenchido à parte, no popup de "marcar
como realizada".
"""

from datetime import datetime

from django import forms
from django.utils import timezone

from medicos.models import Medico

from .models import Consulta


class ConsultaForm(forms.ModelForm):
    """Cadastro/edição de uma consulta ou exame (popup "Novo Agendamento")."""

    data = forms.DateField(widget=forms.DateInput(attrs={"type": "date"}))
    hora = forms.TimeField(widget=forms.TimeInput(attrs={"type": "time"}))

    class Meta:
        model = Consulta
        fields = ["titulo", "medico", "observacao"]
        widgets = {
            "titulo": forms.TextInput(attrs={"placeholder": "Ex.: Eletrocardiograma, Ultrassom"}),
            "observacao": forms.Textarea(attrs={"rows": 2, "placeholder": "Ex.: Comparecer em jejum."}),
        }

    def __init__(self, *args, paciente=None, **kwargs):
        super().__init__(*args, **kwargs)
        # Médico/clínica: só os cadastrados deste paciente.
        if paciente is not None:
            self.fields["medico"].queryset = Medico.objects.filter(
                paciente=paciente
            ).order_by("nome")
        self.fields["medico"].empty_label = "Selecione um médico/clínica…"
        # Ao editar, preenche data/hora a partir da instância (em horário local).
        if self.instance and self.instance.pk and self.instance.data_hora:
            local = timezone.localtime(self.instance.data_hora)
            self.fields["data"].initial = local.date()
            self.fields["hora"].initial = local.time()
        # Título é obrigatório só para exames (clínica/laboratório); para
        # médico ele some e vira a especialidade. Validação fica no clean().
        obrigatorios = {"medico", "data", "hora"}
        for nome, campo in self.fields.items():
            campo.required = nome in obrigatorios

    def clean(self):
        cleaned = super().clean()
        medico = cleaned.get("medico")
        titulo = (cleaned.get("titulo") or "").strip()
        if medico:
            if medico.tipo == Medico.Tipo.MEDICO:
                # Consulta: o título é a especialidade do médico.
                cleaned["titulo"] = medico.especialidade or medico.nome
            else:
                # Clínica/laboratório: exame — precisa do nome do exame.
                if not titulo:
                    self.add_error("titulo", "Informe qual exame.")
                cleaned["titulo"] = titulo
        return cleaned

    def save(self, commit=True):
        consulta = super().save(commit=False)
        # tipo derivado do médico: médico → consulta; clínica/lab → exame.
        medico = self.cleaned_data.get("medico")
        if medico and medico.tipo == Medico.Tipo.MEDICO:
            consulta.tipo = Consulta.Tipo.CONSULTA
        else:
            consulta.tipo = Consulta.Tipo.EXAME
        naive = datetime.combine(self.cleaned_data["data"], self.cleaned_data["hora"])
        consulta.data_hora = timezone.make_aware(
            naive, timezone.get_current_timezone()
        )
        if commit:
            consulta.save()
        return consulta
