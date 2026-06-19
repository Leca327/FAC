"""Rotas do app ponto (escopo por paciente)."""

from django.urls import path

from .views import (
    CheckInView,
    CheckOutView,
    EditarPlantaoView,
    EditarPontoView,
    ExcluirPlantaoView,
    MonitoramentoView,
    PontoView,
    RelatorioCSVView,
)

app_name = "ponto"

urlpatterns = [
    # Cuidador
    path("paciente/<int:pk>/", PontoView.as_view(), name="meu"),
    path("paciente/<int:pk>/check-in/", CheckInView.as_view(), name="check_in"),
    path("paciente/<int:pk>/check-out/", CheckOutView.as_view(), name="check_out"),
    path("paciente/<int:pk>/editar/", EditarPontoView.as_view(), name="editar"),
    # Familiar (monitoramento)
    path("paciente/<int:pk>/monitoramento/", MonitoramentoView.as_view(), name="monitoramento"),
    path("paciente/<int:pk>/relatorio.csv", RelatorioCSVView.as_view(), name="relatorio_csv"),
    path("paciente/<int:pk>/plantao/<int:plantao_id>/editar/", EditarPlantaoView.as_view(), name="plantao_editar"),
    path("paciente/<int:pk>/plantao/<int:plantao_id>/excluir/", ExcluirPlantaoView.as_view(), name="plantao_excluir"),
]
