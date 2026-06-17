"""Rotas do app medicamentos (escopo por paciente)."""

from django.urls import path

from .views import (
    AdicionarRotinaView,
    DeletarMedicamentoView,
    EditarMedicamentoView,
    EditarRotinaView,
    MarcarDoseView,
    MedicacaoDiariaView,
    MedicamentosPacienteView,
    NovoMedicamentoView,
    RemoverRotinaView,
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
    # Medicação Diária (rotina por período)
    path("paciente/<int:pk>/diaria/", MedicacaoDiariaView.as_view(), name="diaria"),
    path(
        "paciente/<int:pk>/diaria/marcar/",
        MarcarDoseView.as_view(),
        name="marcar_dose",
    ),
    path(
        "paciente/<int:pk>/diaria/adicionar/",
        AdicionarRotinaView.as_view(),
        name="rotina_adicionar",
    ),
    path(
        "paciente/<int:pk>/diaria/<int:medicamento_id>/editar/",
        EditarRotinaView.as_view(),
        name="rotina_editar",
    ),
    path(
        "paciente/<int:pk>/diaria/<int:medicamento_id>/remover/",
        RemoverRotinaView.as_view(),
        name="rotina_remover",
    ),
]
