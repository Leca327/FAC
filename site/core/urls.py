"""Rotas do app core (páginas públicas)."""

from django.urls import path

from .views import HomeView, TermosView

app_name = "core"

urlpatterns = [
    path("", HomeView.as_view(), name="home"),
    path("termos/", TermosView.as_view(), name="termos"),
]
