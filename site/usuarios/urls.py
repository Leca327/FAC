"""Rotas do app usuarios."""

from django.urls import path

from .views import (
    CadastroView,
    DeletarContaView,
    LoginView,
    LogoutView,
    PerfilView,
    RecuperarSenhaView,
    RedefinirSenhaView,
)

app_name = "usuarios"

urlpatterns = [
    path("login/", LoginView.as_view(), name="login"),
    path("cadastro/", CadastroView.as_view(), name="cadastro"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("perfil/", PerfilView.as_view(), name="perfil"),
    path("perfil/excluir/", DeletarContaView.as_view(), name="excluir_conta"),
    path("recuperar-senha/", RecuperarSenhaView.as_view(), name="recuperar_senha"),
    path("redefinir-senha/", RedefinirSenhaView.as_view(), name="redefinir_senha"),
]
