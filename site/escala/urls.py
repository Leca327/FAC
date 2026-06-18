"""Rotas do app escala."""

from django.urls import path

from .views import AlterarDiaView, EditarPadraoView, EscalaView

app_name = "escala"

urlpatterns = [
    path("paciente/<int:pk>/", EscalaView.as_view(), name="semanal"),
    path("paciente/<int:pk>/padrao/editar/", EditarPadraoView.as_view(), name="editar_padrao"),
    path("paciente/<int:pk>/dia/alterar/", AlterarDiaView.as_view(), name="alterar_dia"),
]
