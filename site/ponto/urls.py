"""Rotas do app ponto (escopo por paciente)."""

from django.urls import path

from .views import CheckInView, CheckOutView, EditarPontoView, PontoView

app_name = "ponto"

urlpatterns = [
    path("paciente/<int:pk>/", PontoView.as_view(), name="meu"),
    path("paciente/<int:pk>/check-in/", CheckInView.as_view(), name="check_in"),
    path("paciente/<int:pk>/check-out/", CheckOutView.as_view(), name="check_out"),
    path("paciente/<int:pk>/editar/", EditarPontoView.as_view(), name="editar"),
]
