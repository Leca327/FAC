"""Rotas do app pacientes."""

from django.urls import path

from .views import (
    AgendaPacienteView,
    NovoPacienteView,
    PacientesDashboardView,
    VisaoGeralPacienteView,
)

app_name = "pacientes"

urlpatterns = [
    path("", PacientesDashboardView.as_view(), name="dashboard"),
    path("novo/", NovoPacienteView.as_view(), name="novo"),
    path("<int:pk>/", VisaoGeralPacienteView.as_view(), name="visao_geral"),
    path("<int:pk>/agenda/", AgendaPacienteView.as_view(), name="agenda"),
]
