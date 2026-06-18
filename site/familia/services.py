"""
Camada de Services da Equipe do paciente.

A Equipe (familiares e cuidadores) é armazenada na tabela única
``pacientes.Participacao``, que intermedeia usuário e paciente. Só é possível
convidar quem já possui conta no CuidaCare; o convite fica "Pendente" até a
pessoa aceitar pelo link enviado por e-mail, quando passa a "Aceito".
"""

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.db import IntegrityError
from django.urls import reverse
from django.utils import timezone

from pacientes.models import Participacao


class ContaInexistenteError(Exception):
    """Levantado quando o e-mail convidado não pertence a nenhuma conta."""


class JaNaEquipeError(Exception):
    """Levantado quando o usuário já participa da equipe do paciente."""


class EquipeService:
    """Regras de negócio da equipe (familiares/cuidadores) de um paciente."""

    @staticmethod
    def membros(paciente, tipo=None, status=None):
        """
        Participações do paciente (lista única da Equipe), com filtros opcionais
        por tipo (familiar/cuidador) e por status (pendente/aceito).
        """
        qs = (
            Participacao.objects.filter(paciente=paciente)
            .select_related("usuario")
            .order_by("tipo_participacao", "status_convite", "usuario__first_name", "usuario__email")
        )
        if tipo in (Participacao.Tipo.FAMILIAR, Participacao.Tipo.CUIDADOR):
            qs = qs.filter(tipo_participacao=tipo)
        if status in (Participacao.Status.PENDENTE, Participacao.Status.ACEITO):
            qs = qs.filter(status_convite=status)
        return list(qs)

    @staticmethod
    def contagens(paciente):
        """Totais por tipo (para o menu suspenso Todos/Família/Cuidador)."""
        membros = list(Participacao.objects.filter(paciente=paciente))
        familia = sum(1 for m in membros if m.tipo_participacao == Participacao.Tipo.FAMILIAR)
        cuidador = sum(1 for m in membros if m.tipo_participacao == Participacao.Tipo.CUIDADOR)
        return {"todos": len(membros), "familia": familia, "cuidador": cuidador}

    @staticmethod
    def membro_acessivel(paciente, pk):
        return Participacao.objects.filter(paciente=paciente, pk=pk).first()

    @staticmethod
    def convidar(*, paciente, tipo, email, vinculo="", convidado_por, request=None):
        """
        Convida um usuário (que já deve ter conta) para a equipe do paciente.

        Levanta ContaInexistenteError se não houver conta com o e-mail, ou
        JaNaEquipeError se o usuário já participa do paciente.
        """
        Usuario = get_user_model()
        usuario = Usuario.objects.filter(email__iexact=email.strip()).first()
        if not usuario:
            raise ContaInexistenteError(email)

        cuidador = tipo == Participacao.Tipo.CUIDADOR
        try:
            participacao = Participacao.objects.create(
                usuario=usuario,
                paciente=paciente,
                tipo_participacao=tipo,
                vinculo="" if cuidador else vinculo,
                status_convite=Participacao.Status.PENDENTE,
                permissao_leitura=True,
                permissao_escrita=cuidador,
            )
        except IntegrityError:
            raise JaNaEquipeError(email)

        EquipeService._enviar_convite(participacao, request)
        return participacao

    @staticmethod
    def reenviar(*, participacao, request=None):
        EquipeService._enviar_convite(participacao, request)
        return participacao

    @staticmethod
    def editar_vinculo(*, participacao, vinculo):
        participacao.vinculo = vinculo
        participacao.save(update_fields=["vinculo"])
        return participacao

    @staticmethod
    def remover(*, paciente, pk):
        apagados, _ = Participacao.objects.filter(paciente=paciente, pk=pk).delete()
        return apagados > 0

    @staticmethod
    def convites_pendentes(usuario):
        """Convites pendentes recebidos por este usuário (para o sininho)."""
        return list(
            Participacao.objects.filter(
                usuario=usuario, status_convite=Participacao.Status.PENDENTE
            )
            .select_related("paciente")
            .order_by("-data_convite")
        )

    @staticmethod
    def responder(*, participacao, usuario, aceitar):
        """
        Responde a um convite recebido (do próprio usuário). Aceitar marca como
        aceito; recusar apaga o vínculo. Retorna True se respondeu.
        """
        if participacao.usuario_id != usuario.id:
            return False
        if participacao.status_convite != Participacao.Status.PENDENTE:
            return False
        if aceitar:
            participacao.status_convite = Participacao.Status.ACEITO
            participacao.data_resposta = timezone.now()
            participacao.save(update_fields=["status_convite", "data_resposta"])
        else:
            participacao.delete()
        return True

    @staticmethod
    def aceitar(token):
        """Aceita o convite identificado pelo token. Retorna a participação ou None."""
        participacao = (
            Participacao.objects.select_related("usuario", "paciente")
            .filter(token=token)
            .first()
        )
        if not participacao:
            return None
        if participacao.status_convite != Participacao.Status.ACEITO:
            participacao.status_convite = Participacao.Status.ACEITO
            participacao.data_resposta = timezone.now()
            participacao.save(update_fields=["status_convite", "data_resposta"])
        return participacao

    @staticmethod
    def _enviar_convite(participacao, request):
        """Envia o e-mail de convite com o link de aceite."""
        caminho = reverse("equipe:aceitar", args=[participacao.token])
        link = request.build_absolute_uri(caminho) if request else caminho
        if participacao.tipo_participacao == Participacao.Tipo.CUIDADOR:
            papel = "cuidador(a)"
        else:
            papel = participacao.vinculo or "familiar"
        send_mail(
            subject="CuidaCare — Convite para a equipe do paciente",
            message=(
                f"Olá, {participacao.nome}!\n\n"
                f"Você foi convidado(a) para a equipe de cuidado de "
                f"{participacao.paciente.nome} no CuidaCare, como {papel}.\n\n"
                f"Para aceitar o convite, acesse o link abaixo:\n{link}\n\n"
                f"Se você não esperava este convite, basta ignorar este e-mail.\n\n"
                f"Equipe CuidaCare"
            ),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[participacao.email],
            fail_silently=True,
        )
