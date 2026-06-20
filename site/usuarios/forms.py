"""
Formulários do app usuarios (login e cadastro).

As validações de frontend (seção 2.7.7) são duplicadas aqui no backend
(seção 2.6.6) para garantir segurança.
"""

from django import forms
from django.contrib.auth import authenticate

from .models import Usuario


class LoginForm(forms.Form):
    """Formulário de autenticação por e-mail e senha."""

    email = forms.EmailField(
        label="E-mail",
        widget=forms.EmailInput(attrs={"placeholder": "seu@email.com", "autofocus": True}),
    )
    password = forms.CharField(
        label="Senha",
        widget=forms.PasswordInput(attrs={"placeholder": "Sua senha", "class": "js-password"}),
    )

    def __init__(self, request=None, *args, **kwargs):
        self.request = request
        self.user = None
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned = super().clean()
        email = cleaned.get("email")
        password = cleaned.get("password")

        if email and password:
            self.user = authenticate(self.request, username=email, password=password)
            if self.user is None:
                raise forms.ValidationError("E-mail ou senha inválidos.")
            if not self.user.is_active:
                raise forms.ValidationError("Esta conta está desativada.")
        return cleaned

    def get_user(self):
        return self.user


class RedefinirSenhaForm(forms.Form):
    """Define uma nova senha (usado após login com senha temporária)."""

    password = forms.CharField(
        label="Senha", min_length=8,
        widget=forms.PasswordInput(attrs={"class": "js-password", "placeholder": "Nova senha"}),
    )
    confirmar_senha = forms.CharField(
        label="Confirme sua senha",
        widget=forms.PasswordInput(attrs={"class": "js-password", "placeholder": "Repita a nova senha"}),
    )

    def clean(self):
        cleaned = super().clean()
        senha = cleaned.get("password")
        confirmar = cleaned.get("confirmar_senha")
        if senha and confirmar and senha != confirmar:
            self.add_error("confirmar_senha", "As senhas não coincidem.")
        return cleaned


class PerfilForm(forms.ModelForm):
    """Edição dos dados do próprio usuário (tela 'Meu Perfil')."""

    class Meta:
        model = Usuario
        fields = [
            "foto",
            # Informações pessoais
            "first_name", "last_name", "cpf", "rg",
            "data_nascimento", "genero", "estado_civil",
            # Contato
            "email", "telefone", "whatsapp",
            # Endereço
            "endereco", "complemento", "cidade", "estado", "cep", "pais",
        ]
        labels = {
            "first_name": "Nome", "last_name": "Sobrenome", "email": "E-mail",
            "cpf": "CPF", "rg": "RG", "data_nascimento": "Data de nascimento",
            "genero": "Gênero", "estado_civil": "Estado civil",
            "telefone": "Telefone", "whatsapp": "WhatsApp",
            "endereco": "Rua", "complemento": "Complemento", "cidade": "Cidade",
            "estado": "Estado", "cep": "CEP", "pais": "País",
        }
        widgets = {
            "email": forms.EmailInput(),
            "cpf": forms.TextInput(attrs={
                "inputmode": "numeric", "maxlength": "11", "pattern": r"\d*",
                "class": "js-digits", "placeholder": "Somente números",
            }),
            "rg": forms.TextInput(attrs={"placeholder": "Ex.: 12.345.678-9"}),
            "data_nascimento": forms.DateInput(
                attrs={"type": "date"}, format="%Y-%m-%d"
            ),
            "telefone": forms.TextInput(attrs={
                "inputmode": "numeric", "maxlength": "11", "pattern": r"\d*",
                "class": "js-digits", "placeholder": "DDD + número",
            }),
            "whatsapp": forms.TextInput(attrs={
                "inputmode": "numeric", "maxlength": "11", "pattern": r"\d*",
                "class": "js-digits", "placeholder": "DDD + número",
            }),
            "endereco": forms.TextInput(attrs={"placeholder": "Rua e número"}),
            "complemento": forms.TextInput(attrs={"placeholder": "Apto, bloco..."}),
            "cidade": forms.TextInput(),
            "estado": forms.TextInput(attrs={"maxlength": "2", "placeholder": "UF"}),
            "cep": forms.TextInput(attrs={
                "inputmode": "numeric", "maxlength": "8", "pattern": r"\d*",
                "class": "js-digits",
            }),
            "pais": forms.TextInput(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Garante o formato aceito pelo input type=date ao exibir o valor atual.
        self.fields["data_nascimento"].input_formats = ["%Y-%m-%d"]
        # Rótulo amigável para a opção vazia dos selects.
        for nome in ("genero", "estado_civil"):
            opcoes = list(self.fields[nome].choices)
            if opcoes and opcoes[0][0] == "":
                opcoes[0] = ("", "Não informado")
                self.fields[nome].choices = opcoes

    def clean_email(self):
        email = self.cleaned_data["email"].lower()
        if Usuario.objects.filter(email__iexact=email).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError("Já existe uma conta com este e-mail.")
        return email

    def clean_cpf(self):
        cpf = (self.cleaned_data.get("cpf") or "").strip()
        if not cpf:
            return None  # o model permite CPF vazio (null)
        if not cpf.isdigit() or len(cpf) != 11:
            raise forms.ValidationError("O CPF deve conter 11 dígitos numéricos.")
        if Usuario.objects.filter(cpf=cpf).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError("Este CPF já está cadastrado.")
        return cpf

    def _validar_fone(self, valor):
        valor = (valor or "").strip()
        if valor and (not valor.isdigit() or len(valor) not in (10, 11)):
            raise forms.ValidationError(
                "Use 10 ou 11 dígitos numéricos (com DDD)."
            )
        return valor

    def clean_telefone(self):
        return self._validar_fone(self.cleaned_data.get("telefone"))

    def clean_whatsapp(self):
        return self._validar_fone(self.cleaned_data.get("whatsapp"))

    def clean_estado(self):
        return (self.cleaned_data.get("estado") or "").strip().upper()

    def clean_foto(self):
        foto = self.cleaned_data.get("foto")
        # Só valida quando um novo arquivo foi enviado.
        if foto and hasattr(foto, "content_type"):
            permitidos = {"image/jpeg", "image/png", "image/webp", "image/gif"}
            if foto.content_type not in permitidos:
                raise forms.ValidationError("Envie uma imagem JPG, PNG, WEBP ou GIF.")
            if foto.size > 5 * 1024 * 1024:
                raise forms.ValidationError("A imagem deve ter no máximo 5 MB.")
        return foto


class CadastroForm(forms.Form):
    """Formulário de criação de conta (Familiar ou Cuidador)."""

    tipo_usuario = forms.ChoiceField(
        choices=Usuario.Tipo.choices,
        initial=Usuario.Tipo.FAMILIAR,
        widget=forms.RadioSelect,
    )
    first_name = forms.CharField(label="Nome", max_length=150)
    last_name = forms.CharField(label="Sobrenome", max_length=150)
    email = forms.EmailField(label="E-mail")
    password = forms.CharField(
        label="Senha", min_length=8,
        widget=forms.PasswordInput(attrs={"class": "js-password"}),
    )
    confirmar_senha = forms.CharField(
        label="Confirmar Senha",
        widget=forms.PasswordInput(attrs={"class": "js-password"}),
    )
    cpf = forms.CharField(
        label="CPF", max_length=11, required=False,
        help_text="Apenas números (11 dígitos).",
        widget=forms.TextInput(attrs={
            "inputmode": "numeric",
            "maxlength": "11",
            "pattern": r"\d*",
            "class": "js-digits",
            "placeholder": "Somente números",
        }),
    )
    cep = forms.CharField(
        label="CEP", max_length=8, required=False,
        widget=forms.TextInput(attrs={
            "inputmode": "numeric",
            "maxlength": "8",
            "pattern": r"\d*",
            "class": "js-digits",
        }),
    )
    telefone = forms.CharField(
        label="Telefone", max_length=11,
        help_text="DDD + número (apenas dígitos).",
        widget=forms.TextInput(attrs={
            "inputmode": "numeric",
            "maxlength": "11",
            "pattern": r"\d*",
            "class": "js-digits",
            "placeholder": "Ex.: 21987654321",
        }),
    )
    endereco = forms.CharField(
        label="Endereço", max_length=255,
        widget=forms.TextInput(attrs={"placeholder": "Rua, número, bairro"}),
    )
    aceite_termos = forms.BooleanField(
        label="Ao cadastrar, concordo com os Termos de Uso.",
        error_messages={"required": "É preciso aceitar os Termos de Uso."},
    )

    def clean_email(self):
        email = self.cleaned_data["email"].lower()
        if Usuario.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("Já existe uma conta com este e-mail.")
        return email

    def clean_cpf(self):
        cpf = (self.cleaned_data.get("cpf") or "").strip()
        if not cpf:
            return cpf
        if not cpf.isdigit() or len(cpf) != 11:
            raise forms.ValidationError("O CPF deve conter 11 dígitos numéricos.")
        if Usuario.objects.filter(cpf=cpf).exists():
            raise forms.ValidationError("Este CPF já está cadastrado.")
        return cpf

    def clean_telefone(self):
        telefone = (self.cleaned_data.get("telefone") or "").strip()
        if not telefone.isdigit() or len(telefone) not in (10, 11):
            raise forms.ValidationError(
                "O telefone deve conter 10 ou 11 dígitos numéricos (com DDD)."
            )
        return telefone

    def clean(self):
        cleaned = super().clean()
        senha = cleaned.get("password")
        confirmar = cleaned.get("confirmar_senha")
        if senha and confirmar and senha != confirmar:
            self.add_error("confirmar_senha", "As senhas não coincidem.")
        return cleaned
