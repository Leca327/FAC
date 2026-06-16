"""
Camada de Services do app medicamentos (seção 2.6.5).
"""

from datetime import date

from django.db.models import Q

from .models import Medicamento

# Campo booleano do model correspondente a cada dia da semana (0 = segunda).
CAMPO_DIA = ["seg", "ter", "qua", "qui", "sex", "sab", "dom"]


class MedicamentoService:
    """Regras de negócio relacionadas aos medicamentos de um paciente."""

    ORDENS = {
        "nome": ("nome",),
        "recentes": ("-data_criacao",),
    }

    @staticmethod
    def medicamentos_do_dia(paciente, dia=None):
        """
        Medicamentos ativos a serem tomados no dia informado (padrão: hoje):
        status ativo, período vigente e marcado para o dia da semana.
        """
        dia = dia or date.today()
        campo_hoje = CAMPO_DIA[dia.weekday()]
        return list(
            Medicamento.objects.filter(
                Q(data_fim__isnull=True) | Q(data_fim__gte=dia),
                paciente=paciente,
                status=Medicamento.Status.ATIVO,
                data_inicio__lte=dia,
                **{campo_hoje: True},
            ).order_by("horarios", "nome")
        )

    @staticmethod
    def medicamentos_do_paciente(paciente, busca="", ordenar="nome"):
        """
        Retorna os medicamentos do paciente, aplicando busca por nome e
        ordenação escolhidas na barra de ferramentas.
        """
        qs = Medicamento.objects.filter(paciente=paciente)

        if busca:
            qs = qs.filter(nome__icontains=busca)

        ordem = MedicamentoService.ORDENS.get(ordenar, MedicamentoService.ORDENS["nome"])
        return list(qs.order_by(*ordem))

    @staticmethod
    def medicamento_acessivel(paciente, pk):
        """Retorna o medicamento do paciente, ou None se não existir."""
        return Medicamento.objects.filter(paciente=paciente, pk=pk).first()

    @staticmethod
    def criar_medicamento(*, paciente, form):
        """Cria um medicamento vinculado ao paciente a partir de um form válido."""
        medicamento = form.save(commit=False)
        medicamento.paciente = paciente
        medicamento.save()
        return medicamento

    @staticmethod
    def deletar_medicamento(*, paciente, pk):
        """Remove um medicamento do paciente. Retorna True se removeu."""
        deletados, _ = Medicamento.objects.filter(
            paciente=paciente, pk=pk
        ).delete()
        return deletados > 0
