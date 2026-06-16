from django.contrib import admin

from .models import Medico


@admin.register(Medico)
class MedicoAdmin(admin.ModelAdmin):
    list_display = ("nome", "tipo", "especialidade", "paciente", "telefone")
    list_filter = ("tipo",)
    search_fields = ("nome", "especialidade", "paciente__nome")
