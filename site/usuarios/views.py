"""
Views do app usuarios (seção 2.6.4): autenticação e registro.
"""

from django.contrib import messages
from django.contrib.auth import login, logout, update_session_auth_hash
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.views import View

from .forms import CadastroForm, LoginForm, PerfilForm, RedefinirSenhaForm
from .services import UsuarioService


class LoginView(View):
    """Autenticação de usuários (GET renderiza, POST valida)."""

    template_name = "usuarios/login.html"

    def get(self, request):
        if request.user.is_authenticated:
            return redirect("core:home")
        return render(request, self.template_name, {"form": LoginForm()})

    def post(self, request):
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            usuario = form.get_user()
            login(request, usuario)
            # Senha temporária (recuperação) → força a redefinição
            if usuario.senha_temporaria:
                messages.info(request, "Por segurança, defina uma nova senha.")
                return redirect("usuarios:redefinir_senha")
            # Sem mensagem de "login com sucesso": a própria home já confirma.
            return redirect(request.GET.get("next") or "core:home")
        return render(request, self.template_name, {"form": form})


class CadastroView(View):
    """Criação de conta para Familiar ou Cuidador (RF02 / RF04)."""

    template_name = "usuarios/cadastro.html"

    def get(self, request):
        if request.user.is_authenticated:
            return redirect("core:home")
        return render(request, self.template_name, {"form": CadastroForm()})

    def post(self, request):
        form = CadastroForm(request.POST)
        if form.is_valid():
            dados = form.cleaned_data
            usuario = UsuarioService.criar_usuario(
                email=dados["email"],
                password=dados["password"],
                first_name=dados["first_name"],
                last_name=dados["last_name"],
                tipo_usuario=dados["tipo_usuario"],
                cpf=dados.get("cpf"),
                cep=dados.get("cep", ""),
                telefone=dados.get("telefone", ""),
                endereco=dados.get("endereco", ""),
            )
            login(request, usuario)
            messages.success(request, "Conta criada com sucesso! Bem-vindo(a) ao CuidaCare.")
            return redirect("core:home")
        return render(request, self.template_name, {"form": form})


class RedefinirSenhaView(View):
    """
    Define uma nova senha (fecha o ciclo de 'esqueci minha senha').
    Requer usuário autenticado — normalmente acessada logo após o login
    com a senha temporária recebida por e-mail.
    """

    template_name = "usuarios/redefinir_senha.html"

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect("usuarios:login")
        return super().dispatch(request, *args, **kwargs)

    def get(self, request):
        return render(request, self.template_name, {"form": RedefinirSenhaForm()})

    def post(self, request):
        form = RedefinirSenhaForm(request.POST)
        if form.is_valid():
            usuario = request.user
            usuario.set_password(form.cleaned_data["password"])
            usuario.senha_temporaria = False
            usuario.save(update_fields=["password", "senha_temporaria"])
            # Mantém o usuário logado após a troca de senha
            update_session_auth_hash(request, usuario)
            messages.success(request, "Senha redefinida com sucesso!")
            return redirect("core:home")
        return render(request, self.template_name, {"form": form})


class RecuperarSenhaView(View):
    """
    Recuperação de senha via popup (AJAX): recebe o e-mail e dispara o
    envio de uma nova senha temporária. Sempre responde de forma genérica
    para não revelar se o e-mail está ou não cadastrado.
    """

    def post(self, request):
        email = (request.POST.get("email") or "").strip()
        try:
            validate_email(email)
        except ValidationError:
            return JsonResponse(
                {"ok": False, "erro": "Informe um e-mail válido."}, status=400
            )

        UsuarioService.recuperar_senha(email)

        return JsonResponse({
            "ok": True,
            "mensagem": (
                "Se este e-mail estiver cadastrado, enviamos uma nova senha "
                "temporária para a sua caixa de entrada."
            ),
        })


class PerfilView(View):
    """Tela 'Meu Perfil': vê e edita os próprios dados."""

    template_name = "usuarios/perfil.html"

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect("usuarios:login")
        return super().dispatch(request, *args, **kwargs)

    @staticmethod
    def _papeis(user):
        """
        Papéis exibidos no perfil — vêm das participações ACEITAS: se o usuário
        tem algum paciente como familiar e/ou como cuidador. Sem participações,
        cai no tipo da conta.
        """
        from pacientes.models import Participacao

        tipos = set(
            user.participacoes
            .filter(status_convite=Participacao.Status.ACEITO)
            .values_list("tipo_participacao", flat=True)
        )
        if not tipos:
            tipos = {user.tipo_usuario}
        rotulos = dict(Participacao.Tipo.choices)
        ordem = [Participacao.Tipo.FAMILIAR, Participacao.Tipo.CUIDADOR]
        return [rotulos[t] for t in ordem if t in tipos]

    def get(self, request):
        return render(request, self.template_name, {
            "form": PerfilForm(instance=request.user),
            "papeis": self._papeis(request.user),
        })

    def post(self, request):
        form = PerfilForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Perfil atualizado com sucesso!")
            return redirect("usuarios:perfil")
        messages.error(request, "Não foi possível salvar. Verifique os campos destacados.")
        return render(request, self.template_name, {
            "form": form,
            "papeis": self._papeis(request.user),
            "abrir_edicao": True,
        })


class RemoverFotoView(View):
    """Remove a foto de perfil do próprio usuário."""

    def post(self, request):
        if not request.user.is_authenticated:
            return redirect("usuarios:login")
        if request.user.foto:
            request.user.foto.delete(save=True)
            messages.success(request, "Foto removida.")
        return redirect("usuarios:perfil")


class DeletarContaView(View):
    """Exclui a própria conta (ação irreversível)."""

    def post(self, request):
        if not request.user.is_authenticated:
            return redirect("usuarios:login")
        usuario = request.user
        logout(request)
        usuario.delete()
        messages.info(request, "Sua conta foi excluída.")
        return redirect("core:home")


class LogoutView(View):
    """Encerra a sessão do usuário."""

    def post(self, request):
        logout(request)
        messages.info(request, "Você saiu da sua conta.")
        return redirect("core:home")

    # Permite logout via link (GET) também
    def get(self, request):
        logout(request)
        return redirect("core:home")
