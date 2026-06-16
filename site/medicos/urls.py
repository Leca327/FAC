"""Rotas do app medicos (escopo por paciente)."""

from django.urls import path

from .views import (
    DeletarMedicoView,
    EditarMedicoView,
    MedicosPacienteView,
    NovoMedicoView,
)

app_name = "medicos"

urlpatterns = [
    path("paciente/<int:pk>/", MedicosPacienteView.as_view(), name="lista"),
    path("paciente/<int:pk>/novo/", NovoMedicoView.as_view(), name="novo"),
    path(
        "paciente/<int:pk>/<int:medico_id>/editar/",
        EditarMedicoView.as_view(),
        name="editar",
    ),
    path(
        "paciente/<int:pk>/<int:medico_id>/deletar/",
        DeletarMedicoView.as_view(),
        name="deletar",
    ),
]
