"""
Context processor da Equipe: disponibiliza os convites pendentes do usuário
logado para o sininho de notificações da navbar (em todas as páginas).
"""

from .services import EquipeService


def convites(request):
    usuario = getattr(request, "user", None)
    if not usuario or not usuario.is_authenticated:
        return {"convites_pendentes": []}
    return {"convites_pendentes": EquipeService.convites_pendentes(usuario)}
