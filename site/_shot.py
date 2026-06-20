# -*- coding: utf-8 -*-
import os, django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()
from django.test import Client
from django.urls import reverse
from pacientes.models import Paciente
pac = Paciente.objects.get(cpf="55555555555")
cli = Client(); cli.login(email="maria.souza@teste.com", password="Teste@123")
r = cli.get(reverse("pacientes:agenda", args=[pac.pk]), SERVER_NAME="localhost")
print("STATUS", r.status_code)
html = r.content.decode("utf-8")
base = os.path.abspath("static").replace("\\", "/")
html = html.replace('href="/static/', f'href="file:///{base}/').replace('src="/static/', f'src="file:///{base}/')
out = os.path.join(os.environ.get("TEMP", "."), "agenda.html")
open(out, "w", encoding="utf-8").write(html)
print(out)
