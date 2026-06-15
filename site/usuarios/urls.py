"""Rotas do app usuarios."""

from django.urls import path

from .views import (
    CadastroView,
    LoginView,
    LogoutView,
    RecuperarSenhaView,
    RedefinirSenhaView,
)

app_name = "usuarios"

urlpatterns = [
    path("login/", LoginView.as_view(), name="login"),
    path("cadastro/", CadastroView.as_view(), name="cadastro"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("recuperar-senha/", RecuperarSenhaView.as_view(), name="recuperar_senha"),
    path("redefinir-senha/", RedefinirSenhaView.as_view(), name="redefinir_senha"),
]
