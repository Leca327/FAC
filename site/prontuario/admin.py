from django.contrib import admin

from .models import Anotacao


@admin.register(Anotacao)
class AnotacaoAdmin(admin.ModelAdmin):
    list_display = ("titulo", "paciente", "data_hora", "autor")
    list_filter = ("data_hora",)
    search_fields = ("titulo", "descricao")
