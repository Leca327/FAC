"""Rotas do app medicamentos (escopo por paciente)."""

from django.urls import path

from .views import (
    DeletarMedicamentoView,
    EditarMedicamentoView,
    MedicamentosPacienteView,
    NovoMedicamentoView,
)

app_name = "medicamentos"

urlpatterns = [
    path("paciente/<int:pk>/", MedicamentosPacienteView.as_view(), name="lista"),
    path("paciente/<int:pk>/novo/", NovoMedicamentoView.as_view(), name="novo"),
    path(
        "paciente/<int:pk>/<int:medicamento_id>/editar/",
        EditarMedicamentoView.as_view(),
        name="editar",
    ),
    path(
        "paciente/<int:pk>/<int:medicamento_id>/deletar/",
        DeletarMedicamentoView.as_view(),
        name="deletar",
    ),
]
