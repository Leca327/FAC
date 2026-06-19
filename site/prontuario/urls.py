"""Rotas do app prontuario (escopo por paciente)."""

from django.urls import path

from .views import AdicionarAnotacaoView, ProntuarioView

app_name = "prontuario"

urlpatterns = [
    path("paciente/<int:pk>/", ProntuarioView.as_view(), name="diario"),
    path(
        "paciente/<int:pk>/anotacao/nova/",
        AdicionarAnotacaoView.as_view(),
        name="anotacao_nova",
    ),
]
