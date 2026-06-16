"""
Camada de Services do app medicos (seção 2.6.5).
"""

from django.db.models import Q

from .models import Medico


class MedicoService:
    """Regras de negócio relacionadas aos médicos de um paciente."""

    ORDENS = {
        "nome": ("nome",),
        "recentes": ("-data_criacao",),
    }

    @staticmethod
    def medicos_do_paciente(paciente, busca="", ordenar="nome"):
        """
        Retorna os médicos do paciente, aplicando busca (por nome ou
        especialidade) e ordenação escolhidas na barra de ferramentas.
        """
        qs = Medico.objects.filter(paciente=paciente)

        if busca:
            qs = qs.filter(Q(nome__icontains=busca) | Q(especialidade__icontains=busca))

        ordem = MedicoService.ORDENS.get(ordenar, MedicoService.ORDENS["nome"])
        return list(qs.order_by(*ordem))

    @staticmethod
    def medico_acessivel(paciente, pk):
        """Retorna o médico do paciente, ou None se não existir."""
        return Medico.objects.filter(paciente=paciente, pk=pk).first()

    @staticmethod
    def criar_medico(*, paciente, form):
        """Cria um médico vinculado ao paciente a partir de um form válido."""
        medico = form.save(commit=False)
        medico.paciente = paciente
        medico.save()
        return medico

    @staticmethod
    def deletar_medico(*, paciente, pk):
        """Remove um médico do paciente. Retorna True se removeu."""
        deletados, _ = Medico.objects.filter(paciente=paciente, pk=pk).delete()
        return deletados > 0
