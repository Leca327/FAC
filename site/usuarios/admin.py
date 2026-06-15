"""Configuração do admin para os modelos de usuário."""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import Cuidador, Familiar, Usuario


@admin.register(Usuario)
class UsuarioAdmin(BaseUserAdmin):
    ordering = ("email",)
    list_display = ("email", "first_name", "last_name", "tipo_usuario", "is_staff")
    list_filter = ("tipo_usuario", "is_staff", "is_active")
    search_fields = ("email", "first_name", "last_name", "cpf")

    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Dados pessoais", {"fields": ("first_name", "last_name", "cpf",
                                       "telefone", "endereco", "cep")}),
        ("Tipo", {"fields": ("tipo_usuario",)}),
        ("Permissões", {"fields": ("is_active", "is_staff", "is_superuser",
                                   "groups", "user_permissions")}),
        ("Datas", {"fields": ("last_login", "data_criacao")}),
    )
    readonly_fields = ("data_criacao",)
    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": ("email", "tipo_usuario", "password1", "password2"),
        }),
    )


admin.site.register(Familiar)
admin.site.register(Cuidador)
