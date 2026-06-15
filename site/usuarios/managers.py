"""
Manager customizado do modelo Usuario (seção 2.6.2).

Como a autenticação é feita por e-mail (e não por username), o manager
padrão do Django precisa ser substituído para criar usuários e superusuários
a partir do campo de e-mail.
"""

from django.contrib.auth.base_user import BaseUserManager
from django.utils.translation import gettext_lazy as _


class UsuarioManager(BaseUserManager):
    """Manager para o modelo Usuario com login por e-mail."""

    use_in_migrations = True

    def _create_user(self, email, password, **extra_fields):
        if not email:
            raise ValueError(_("O e-mail é obrigatório."))
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        # set_password gera o hash PBKDF2 com salt (seção 2.6.2)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("tipo_usuario", "familiar")

        if extra_fields.get("is_staff") is not True:
            raise ValueError(_("Superusuário precisa ter is_staff=True."))
        if extra_fields.get("is_superuser") is not True:
            raise ValueError(_("Superusuário precisa ter is_superuser=True."))

        return self._create_user(email, password, **extra_fields)
