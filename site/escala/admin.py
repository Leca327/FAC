from django.contrib import admin

from .models import ExcecaoDia, PadraoTurno, RodizioItem, SemanalItem


class RodizioItemInline(admin.TabularInline):
    model = RodizioItem
    extra = 0


class SemanalItemInline(admin.TabularInline):
    model = SemanalItem
    extra = 0


@admin.register(PadraoTurno)
class PadraoTurnoAdmin(admin.ModelAdmin):
    list_display = ("paciente", "turno", "tipo_padrao", "dias_por_pessoa", "data_inicio")
    list_filter = ("turno", "tipo_padrao")
    inlines = [RodizioItemInline, SemanalItemInline]


@admin.register(ExcecaoDia)
class ExcecaoDiaAdmin(admin.ModelAdmin):
    list_display = ("paciente", "data", "turno", "cuidador")
    list_filter = ("turno",)
