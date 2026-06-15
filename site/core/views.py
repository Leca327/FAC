"""
Views do app core — páginas públicas do CuidaCare.

A tela principal (landing page) é renderizada com contexto fornecido pela
view, seguindo o padrão MVT do Django (seção 2.6.4 / 2.7.5): os dados de
exibição são passados pelo contexto e consumidos pelos templates.
"""

from datetime import date

from django.views.generic import TemplateView


class TermosView(TemplateView):
    """Página pública com os Termos de Uso da plataforma."""

    template_name = "core/termos.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["data_atualizacao"] = date(2026, 6, 14)
        return context


class HomeView(TemplateView):
    """Tela principal (landing page) pública do CuidaCare."""

    template_name = "core/home.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Seção "Como funciona" — 3 passos
        context["passos"] = [
            {
                "numero": "01",
                "titulo": "Cadastre o paciente",
                "descricao": (
                    "Crie o perfil com histórico de saúde, diagnósticos, "
                    "medicações em uso e contatos de emergência da família."
                ),
            },
            {
                "numero": "02",
                "titulo": "Adicione a cuidadora",
                "descricao": (
                    "A cuidadora bate ponto, registra as atividades do dia e "
                    "comunica ocorrências diretamente pelo sistema."
                ),
            },
            {
                "numero": "03",
                "titulo": "Acompanhe em tempo real",
                "descricao": (
                    "A família acessa o dashboard com atividades, medicações, "
                    "agenda e histórico completo do paciente."
                ),
            },
        ]

        # Seção "Para quem é" — perfis de usuário
        context["perfis"] = [
            {
                "titulo": "Família",
                "destaque": False,
                "descricao": (
                    "Paz de espírito sabendo o que acontece com seu ente "
                    "querido a qualquer hora do dia."
                ),
                "itens": [
                    "Acompanhamento em tempo real",
                    "Histórico de atividades e saúde",
                    "Alertas e notificações",
                    "Agenda médica unificada",
                ],
            },
            {
                "titulo": "Cuidadora",
                "destaque": True,
                "descricao": (
                    "Registre atividades, bata ponto e comunique ocorrências "
                    "de forma simples e transparente."
                ),
                "itens": [
                    "Registro de ponto digital",
                    "Diário de atividades do dia",
                    "Gestão de medicações",
                    "Comunicação com a família",
                ],
            },
            {
                "titulo": "Equipe Médica",
                "destaque": False,
                "descricao": (
                    "Acesse o histórico completo e mantenha a agenda de "
                    "consultas sempre atualizada."
                ),
                "itens": [
                    "Prontuário digital completo",
                    "Sinais vitais e evolução",
                    "Gestão de médicos (CRUD)",
                    "Agenda de consultas e exames",
                ],
            },
        ]

        # Métricas (seção de prova social)
        context["metricas"] = [
            {"valor": "2.000+", "rotulo": "Famílias atendidas"},
            {"valor": "98%", "rotulo": "Satisfação dos usuários"},
            {"valor": "500+", "rotulo": "Cuidadoras cadastradas"},
            {"valor": "24/7", "rotulo": "Acesso à plataforma"},
        ]

        return context
