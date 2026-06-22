"""
Configurações do Django para o projeto CuidaCare.

Conforme seção 2.6 da documentação:
- Padrão MVT + camada de Services
- SQLite em desenvolvimento / PostgreSQL em produção
- Diferenciação de ambientes via variável ENVIRONMENT
- Camadas de segurança (CSRF, XSS, sessões seguras, HTTPS em produção)
"""

from pathlib import Path
import os
import dj_database_url  # <-- NOVO: para usar DATABASE_URL

from dotenv import load_dotenv

# Carrega variáveis do arquivo .env (não versionado)
load_dotenv()

# BASE_DIR aponta para a raiz do projeto (onde está o manage.py)
BASE_DIR = Path(__file__).resolve().parent.parent

# ------------------------------------------------------------------
# Ambiente: development | staging | production
# ------------------------------------------------------------------
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
DEBUG = ENVIRONMENT == "development"

# Em desenvolvimento usamos uma chave padrão; em produção deve vir do .env
SECRET_KEY = os.getenv(
    "SECRET_KEY",
    "django-insecure-dev-key-troque-em-producao-cuidacare-2026",
)

# ALLOWED_HOSTS: adiciona dinamicamente o hostname do Render
ALLOWED_HOSTS = os.getenv("ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")
RENDER_EXTERNAL_HOSTNAME = os.getenv("RENDER_EXTERNAL_HOSTNAME")
if RENDER_EXTERNAL_HOSTNAME:
    ALLOWED_HOSTS.append(RENDER_EXTERNAL_HOSTNAME)

# ------------------------------------------------------------------
# Aplicações
# ------------------------------------------------------------------
DJANGO_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
]

# Apps do projeto (seção 2.6.1) — habilitados conforme forem implementados
LOCAL_APPS = [
    "core",          # Páginas públicas (landing page / home)
    "usuarios",      # Autenticação, registro e perfis (seção 2.6.1)
    "pacientes",     # Cadastro de pacientes e participações (seção 2.6.1)
    "medicamentos",  # Medicamentos agendados do paciente (seção 2.6.1)
    "medicos",       # Médicos/clínicas/laboratórios do paciente
    "consultas",     # Consultas e exames do paciente
    "familia",       # Membros da família e convites do paciente
    "escala",        # Escala de cuidadores do paciente
    "prontuario",    # Prontuário: linha do tempo diária do paciente
    "ponto",         # Ponto: check-in/check-out do cuidador (plantões)
    # "agenda",
]

INSTALLED_APPS = DJANGO_APPS + LOCAL_APPS

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",   # <-- NOVO: WhiteNoise para arquivos estáticos
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        # Templates compartilhadas na raiz (seção 2.7.1: base.html)
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "familia.context_processors.convites",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

# ------------------------------------------------------------------
# Banco de dados (seção 2.6.8)
# ------------------------------------------------------------------
if ENVIRONMENT == "production":
    # Em produção, usa DATABASE_URL (fornecido pelo Render ou outro PaaS)
    DATABASES = {
        'default': dj_database_url.config(
            default=os.getenv('DATABASE_URL'),
            conn_max_age=600,
            ssl_require=True
        )
    }
else:
    # Desenvolvimento: MySQL local (XAMPP) com o banco cuidacare_db.
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.mysql",
            "NAME": os.getenv("DB_NAME", "cuidacare_db"),
            "USER": os.getenv("DB_USER", "root"),
            "PASSWORD": os.getenv("DB_PASSWORD", "root"),
            "HOST": os.getenv("DB_HOST", "127.0.0.1"),
            "PORT": os.getenv("DB_PORT", "3306"),
            "OPTIONS": {
                "charset": "utf8mb4",
            },
        }
    }

# ------------------------------------------------------------------
# Validação de senhas (hash PBKDF2 com salt — seção 2.6.2)
# ------------------------------------------------------------------
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# ------------------------------------------------------------------
# Internacionalização
# ------------------------------------------------------------------
LANGUAGE_CODE = "pt-br"
TIME_ZONE = "America/Sao_Paulo"
USE_I18N = True
USE_TZ = True

# ------------------------------------------------------------------
# Arquivos estáticos e de mídia (seção 2.7)
# ------------------------------------------------------------------
STATIC_URL = "static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"  # <-- NOVO

MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ------------------------------------------------------------------
# Autenticação (seção 2.6.2) — modelo de usuário customizado
# ------------------------------------------------------------------
AUTH_USER_MODEL = "usuarios.Usuario"

LOGIN_URL = "usuarios:login"
LOGIN_REDIRECT_URL = "core:home"
LOGOUT_REDIRECT_URL = "core:home"

# ------------------------------------------------------------------
# E-mail (recuperação de senha)
# ------------------------------------------------------------------
# Em desenvolvimento, os e-mails são "impressos" no terminal do servidor
# (console). Para envio real, defina EMAIL_BACKEND e as credenciais SMTP
# no arquivo .env (ex.: Gmail com senha de app).
EMAIL_BACKEND = os.getenv(
    "EMAIL_BACKEND", "django.core.mail.backends.console.EmailBackend"
)
EMAIL_HOST = os.getenv("EMAIL_HOST", "smtp.gmail.com")
EMAIL_PORT = int(os.getenv("EMAIL_PORT", "587"))
EMAIL_USE_TLS = os.getenv("EMAIL_USE_TLS", "True") == "True"
EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER", "")
EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD", "")
DEFAULT_FROM_EMAIL = os.getenv(
    "DEFAULT_FROM_EMAIL", "CuidaCare <nao-responda@cuidacare.com.br>"
)

# ------------------------------------------------------------------
# Segurança (seção 2.6.7) — ativada apenas em produção
# ------------------------------------------------------------------
if ENVIRONMENT == "production":
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = "DENY"
