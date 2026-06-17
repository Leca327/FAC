"""Rotas do app familia."""

from django.urls import path

from .views import (
    AceitarConviteView,
    ConvidarMembroView,
    EditarMembroView,
    FamiliaView,
    ReenviarConviteView,
    RemoverMembroView,
)

app_name = "familia"

urlpatterns = [
    path("paciente/<int:pk>/", FamiliaView.as_view(), name="lista"),
    path("paciente/<int:pk>/convidar/", ConvidarMembroView.as_view(), name="convidar"),
    path(
        "paciente/<int:pk>/<int:membro_id>/editar/",
        EditarMembroView.as_view(),
        name="editar",
    ),
    path(
        "paciente/<int:pk>/<int:membro_id>/remover/",
        RemoverMembroView.as_view(),
        name="remover",
    ),
    path(
        "paciente/<int:pk>/<int:membro_id>/reenviar/",
        ReenviarConviteView.as_view(),
        name="reenviar",
    ),
    # Aceite público (link do e-mail)
    path("convite/<str:token>/aceitar/", AceitarConviteView.as_view(), name="aceitar"),
]
