"""
Rotas principais do projeto CuidaCare (seção 2.6.1).

Cada app registra suas próprias URLs e elas são incluídas aqui.
"""

from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    # Páginas públicas (landing page / home)
    path("", include("core.urls")),
    # Autenticação e registro
    path("conta/", include("usuarios.urls")),
    # Pacientes (tela gerencial)
    path("pacientes/", include("pacientes.urls")),
    # Medicamentos do paciente
    path("medicamentos/", include("medicamentos.urls")),
    # Médicos do paciente
    path("medicos/", include("medicos.urls")),
    # Apps do projeto (habilitados conforme implementados):
    # path("agenda/", include("agenda.urls")),
    # path("ponto/", include("ponto.urls")),
    # path("diario/", include("diario.urls")),
]
