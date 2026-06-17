"""Rotas do app consultas (escopo por paciente)."""

from django.urls import path

from .views import (
    ConsultasView,
    DeletarConsultaView,
    EditarConsultaView,
    MarcarRealizadaView,
    NovaConsultaView,
)

app_name = "consultas"

urlpatterns = [
    path("paciente/<int:pk>/", ConsultasView.as_view(), name="lista"),
    path("paciente/<int:pk>/nova/", NovaConsultaView.as_view(), name="nova"),
    path(
        "paciente/<int:pk>/<int:consulta_id>/editar/",
        EditarConsultaView.as_view(),
        name="editar",
    ),
    path(
        "paciente/<int:pk>/<int:consulta_id>/deletar/",
        DeletarConsultaView.as_view(),
        name="deletar",
    ),
    path(
        "paciente/<int:pk>/<int:consulta_id>/realizada/",
        MarcarRealizadaView.as_view(),
        name="realizada",
    ),
]
