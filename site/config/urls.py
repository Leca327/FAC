"""
Rotas principais do projeto CuidaCare (seção 2.6.1).

Cada app registra suas próprias URLs e elas são incluídas aqui.
"""

from django.conf import settings
from django.conf.urls.static import static
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
    # Consultas e exames do paciente
    path("consultas/", include("consultas.urls")),
    # Equipe do paciente (familiares e cuidadores)
    path("equipe/", include("familia.urls")),
    # Escala de cuidadores do paciente
    path("escala/", include("escala.urls")),
    # Prontuário: linha do tempo diária do paciente
    path("prontuario/", include("prontuario.urls")),
    # Ponto: check-in/check-out do cuidador
    path("ponto/", include("ponto.urls")),
    # Apps do projeto (habilitados conforme implementados):
    # path("agenda/", include("agenda.urls")),
    # path("ponto/", include("ponto.urls")),
    # path("diario/", include("diario.urls")),
]

# Em desenvolvimento, serve os uploads (ex.: fotos de perfil) do MEDIA_ROOT.
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
