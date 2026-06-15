"""
Configuração ASGI do projeto CuidaCare.

Expõe o callable ASGI como uma variável de módulo chamada ``application``.
"""

import os

from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

application = get_asgi_application()
