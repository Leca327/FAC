from django.contrib import admin

from .models import Plantao


@admin.register(Plantao)
class PlantaoAdmin(admin.ModelAdmin):
    list_display = ("cuidador", "paciente", "data_plantao", "hora_entrada",
                    "hora_saida", "status", "duracao_horas")
    list_filter = ("status", "data_plantao")
    search_fields = ("cuidador__email", "paciente__nome")
