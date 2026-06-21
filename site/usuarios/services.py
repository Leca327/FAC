"""
Camada de Services do app usuarios (seção 2.6.5).

Encapsula a lógica de negócio relacionada a usuários, mantendo as views
limpas e facilitando reuso e testes.
"""

from django.conf import settings
from django.core.mail import send_mail
from django.db import transaction
from django.utils.crypto import get_random_string

from .models import Usuario


class UsuarioService:
    """Regras de negócio de usuários."""

    @staticmethod
    @transaction.atomic
    def criar_usuario(*, email, password, first_name, last_name,
                      tipo_usuario=Usuario.Tipo.FAMILIAR,
                      cpf=None, cep="", telefone="", endereco="",
                      complemento="", cidade="", estado=""):
        """
        Cria um Usuario (tabela única — sem especialização).

        ``tipo_usuario`` nasce como ``FAMILIAR`` por padrão: o papel efetivo
        de cada pessoa vem do vínculo com o paciente (``Participacao``), seja
        ao cadastrar um paciente (vira criador/familiar) ou ao aceitar um
        convite (familiar ou cuidador).
        """
        return Usuario.objects.create_user(
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
            tipo_usuario=tipo_usuario,
            cpf=cpf or None,
            cep=cep,
            telefone=telefone,
            endereco=endereco,
            complemento=complemento,
            cidade=cidade,
            estado=estado,
        )

    @staticmethod
    def email_disponivel(email):
        """Retorna True se o e-mail ainda não estiver cadastrado."""
        return not Usuario.objects.filter(email__iexact=email).exists()

    @staticmethod
    def recuperar_senha(email):
        """
        Gera uma nova senha temporária para o usuário e a envia por e-mail.

        Como a senha é armazenada com hash (irreversível), não é possível
        recuperar a senha original — por isso geramos uma nova temporária.
        Retorna True se o e-mail foi enviado; False se não há conta com esse
        e-mail (a view não deve revelar isso ao usuário, para evitar
        enumeração de contas).
        """
        try:
            usuario = Usuario.objects.get(email__iexact=email, is_active=True)
        except Usuario.DoesNotExist:
            return False

        # Senha temporária legível (sem caracteres ambíguos)
        nova_senha = get_random_string(
            10, allowed_chars="ABCDEFGHJKLMNPQRSTUVWXYZ23456789abcdefghijkmnpqrstuvwxyz"
        )
        usuario.set_password(nova_senha)
        usuario.senha_temporaria = True
        usuario.save(update_fields=["password", "senha_temporaria"])

        nome = usuario.first_name or "usuário(a)"
        send_mail(
            subject="CuidaCare — Recuperação de senha",
            message=(
                f"Olá, {nome}!\n\n"
                f"Recebemos uma solicitação de recuperação de senha para a sua conta.\n"
                f"Sua nova senha temporária é: {nova_senha}\n\n"
                f"Por segurança, recomendamos que você acesse a plataforma e altere "
                f"esta senha assim que possível.\n\n"
                f"Se não foi você quem solicitou, entre em contato conosco.\n\n"
                f"Equipe CuidaCare"
            ),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[usuario.email],
            fail_silently=False,
        )
        return True
