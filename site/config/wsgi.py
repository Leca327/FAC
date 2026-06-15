"""
Configuração WSGI do projeto CuidaCare.

Expõe o callable WSGI como uma variável de módulo chamada ``application``.
Usado pelo gunicorn em produção (seção 2.6.9).
"""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

application = get_wsgi_application()
