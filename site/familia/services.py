"""Camada de Services do app familia."""

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.urls import reverse
from django.utils import timezone

from .models import MembroFamilia


class MembroFamiliaService:
    """Regras de negócio dos membros/convites de família de um paciente."""

    @staticmethod
    def membros(paciente, status=None):
        """Membros do paciente, opcionalmente filtrados por status."""
        qs = MembroFamilia.objects.filter(paciente=paciente)
        if status in (MembroFamilia.Status.PENDENTE, MembroFamilia.Status.ACEITO):
            qs = qs.filter(status=status)
        return list(qs)

    @staticmethod
    def contagens(paciente):
        """Totais por status, para o menu suspenso de filtro."""
        membros = MembroFamilia.objects.filter(paciente=paciente)
        aceitos = sum(1 for m in membros if m.status == MembroFamilia.Status.ACEITO)
        pendentes = sum(1 for m in membros if m.status == MembroFamilia.Status.PENDENTE)
        return {"todos": len(membros), "aceitos": aceitos, "pendentes": pendentes}

    @staticmethod
    def membro_acessivel(paciente, pk):
        return MembroFamilia.objects.filter(paciente=paciente, pk=pk).first()

    @staticmethod
    def convidar(*, paciente, form, convidado_por, request=None):
        """Cria o membro (pendente) e envia o convite por e-mail."""
        membro = form.save(commit=False)
        membro.paciente = paciente
        membro.convidado_por = convidado_por
        membro.status = MembroFamilia.Status.PENDENTE
        membro.save()
        MembroFamiliaService._enviar_convite(membro, request)
        return membro

    @staticmethod
    def reenviar(*, membro, request=None):
        """Reenvia o convite (gera novo registro de data) por e-mail."""
        MembroFamiliaService._enviar_convite(membro, request)
        return membro

    @staticmethod
    def remover(*, paciente, pk):
        apagados, _ = MembroFamilia.objects.filter(paciente=paciente, pk=pk).delete()
        return apagados > 0

    @staticmethod
    def aceitar(token):
        """
        Aceita o convite identificado pelo token. Marca como aceito, grava a
        data e, se houver conta com o mesmo e-mail, vincula o usuário.
        Retorna o membro ou None.
        """
        membro = MembroFamilia.objects.filter(token=token).first()
        if not membro:
            return None
        if membro.status != MembroFamilia.Status.ACEITO:
            membro.status = MembroFamilia.Status.ACEITO
            membro.data_resposta = timezone.now()
            if not membro.usuario:
                Usuario = get_user_model()
                membro.usuario = Usuario.objects.filter(email__iexact=membro.email).first()
            membro.save()
        return membro

    @staticmethod
    def _enviar_convite(membro, request):
        """Envia o e-mail de convite com o link de aceite."""
        caminho = reverse("familia:aceitar", args=[membro.token])
        link = request.build_absolute_uri(caminho) if request else caminho
        send_mail(
            subject="CuidaCare — Convite para a família",
            message=(
                f"Olá, {membro.nome}!\n\n"
                f"Você foi convidado(a) para acompanhar o cuidado de "
                f"{membro.paciente.nome} no CuidaCare, como {membro.vinculo}.\n\n"
                f"Para aceitar o convite, acesse o link abaixo:\n{link}\n\n"
                f"Se você não esperava este convite, basta ignorar este e-mail.\n\n"
                f"Equipe CuidaCare"
            ),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[membro.email],
            fail_silently=True,
        )
