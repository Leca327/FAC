"""
O app ``familia`` agora hospeda apenas a tela "Equipe" do paciente.

O vínculo usuário↔paciente (familiares e cuidadores) deixou de ter um modelo
próprio aqui — passou a ser a tabela única ``pacientes.Participacao``. Este
módulo permanece sem modelos.
"""

from django.utils.crypto import get_random_string


def _novo_token():
    # Mantido apenas porque a migração histórica 0001 referencia este helper.
    return get_random_string(40)
