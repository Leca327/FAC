from django.contrib import admin

from .models import Medicamento


@admin.register(Medicamento)
class MedicamentoAdmin(admin.ModelAdmin):
    list_display = (
        "nome", "dosagem", "paciente", "data_inicio", "data_fim", "status",
    )
    list_filter = ("status", "forma_farmaceutica")
    search_fields = ("nome", "paciente__nome", "medico")
