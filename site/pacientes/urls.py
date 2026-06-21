"""Rotas do app pacientes."""

from django.urls import path

from .views import (
    AgendaPacienteView,
    ExcluirPacienteView,
    NovoPacienteView,
    PacientesDashboardView,
    PerfilPacienteView,
    VisaoGeralPacienteView,
)

app_name = "pacientes"

urlpatterns = [
    path("", PacientesDashboardView.as_view(), name="dashboard"),
    path("novo/", NovoPacienteView.as_view(), name="novo"),
    path("<int:pk>/excluir/", ExcluirPacienteView.as_view(), name="excluir"),
    path("<int:pk>/", VisaoGeralPacienteView.as_view(), name="visao_geral"),
    path("<int:pk>/agenda/", AgendaPacienteView.as_view(), name="agenda"),
    path("<int:pk>/perfil/", PerfilPacienteView.as_view(), name="perfil"),
]
