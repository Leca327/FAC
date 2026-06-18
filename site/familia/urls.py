"""Rotas da Equipe do paciente."""

from django.urls import path

from .views import (
    AceitarConviteView,
    ConvidarMembroView,
    EditarMembroView,
    EquipeView,
    ReenviarConviteView,
    RemoverMembroView,
    ResponderConviteView,
)

app_name = "equipe"

urlpatterns = [
    path("paciente/<int:pk>/", EquipeView.as_view(), name="lista"),
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
    # Responder convite pelo sininho (aceitar/recusar)
    path("convite/<int:pk>/responder/", ResponderConviteView.as_view(), name="responder"),
    # Aceite público (link do e-mail)
    path("convite/<str:token>/aceitar/", AceitarConviteView.as_view(), name="aceitar"),
]
