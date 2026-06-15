from django.contrib import admin

from .models import Paciente, Participacao


@admin.register(Paciente)
class PacienteAdmin(admin.ModelAdmin):
    list_display = ("nome", "data_nascimento", "familiar_responsavel", "ativo")
    list_filter = ("ativo",)
    search_fields = ("nome", "cpf")


@admin.register(Participacao)
class ParticipacaoAdmin(admin.ModelAdmin):
    list_display = ("usuario", "paciente", "tipo_participacao", "status_convite")
    list_filter = ("tipo_participacao", "status_convite")
    search_fields = ("usuario__email", "paciente__nome")
