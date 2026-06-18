"""
Camada de Services do app pacientes (seção 2.6.5).
"""

from django.db import transaction
from django.db.models import Q

from .models import Paciente, Participacao


class PacienteService:
    """Regras de negócio relacionadas a pacientes."""

    @staticmethod
    @transaction.atomic
    def criar_paciente(*, familiar, form):
        """
        Cria um paciente a partir de um PacienteForm válido, definindo o
        familiar logado como responsável e registrando também sua
        participação (responsável) com permissão de escrita.
        """
        paciente = form.save(commit=False)
        paciente.familiar_responsavel = familiar
        paciente.save()

        Participacao.objects.create(
            usuario=familiar,
            paciente=paciente,
            tipo_participacao=Participacao.Tipo.FAMILIAR,
            status_convite=Participacao.Status.ACEITO,
            permissao_leitura=True,
            permissao_escrita=True,
        )
        return paciente

    @staticmethod
    def pacientes_do_usuario(usuario, busca="", modo="familiar"):
        """
        Retorna os pacientes vinculados ao usuário conforme o MODO escolhido na
        tela de pacientes (não mais o tipo da conta):

        - modo "familiar": pacientes em que é o responsável OU possui uma
          participação de familiar aceita (compartilhamento — RN06).
        - modo "cuidador": pacientes em que possui uma participação de cuidador
          aceita.
        """
        if modo == Participacao.Tipo.CUIDADOR:
            qs = Paciente.objects.filter(
                participacoes__usuario=usuario,
                participacoes__tipo_participacao=Participacao.Tipo.CUIDADOR,
                participacoes__status_convite=Participacao.Status.ACEITO,
                ativo=True,
            )
        else:
            qs = Paciente.objects.filter(
                Q(familiar_responsavel=usuario)
                | Q(
                    participacoes__usuario=usuario,
                    participacoes__tipo_participacao=Participacao.Tipo.FAMILIAR,
                    participacoes__status_convite=Participacao.Status.ACEITO,
                ),
                ativo=True,
            )

        if busca:
            qs = qs.filter(nome__icontains=busca)

        return qs.distinct()

    @staticmethod
    def paciente_acessivel(usuario, pk):
        """
        Retorna o paciente se o usuário tem QUALQUER acesso a ele (responsável,
        familiar aceito ou cuidador aceito); senão None. É permissivo de
        propósito: as telas internas valem para os dois modos.
        """
        return (
            Paciente.objects.filter(
                Q(familiar_responsavel=usuario)
                | Q(
                    participacoes__usuario=usuario,
                    participacoes__status_convite=Participacao.Status.ACEITO,
                ),
                ativo=True,
                pk=pk,
            )
            .distinct()
            .first()
        )

    @staticmethod
    def equipe_do_paciente(paciente):
        """Retorna os familiares e cuidadores vinculados ao paciente."""
        from django.contrib.auth import get_user_model

        Usuario = get_user_model()
        cuidadores = Usuario.objects.filter(
            participacoes__paciente=paciente,
            participacoes__tipo_participacao=Participacao.Tipo.CUIDADOR,
            participacoes__status_convite=Participacao.Status.ACEITO,
        ).distinct()
        familiares = Usuario.objects.filter(
            Q(pacientes_responsavel=paciente)
            | Q(
                participacoes__paciente=paciente,
                participacoes__tipo_participacao=Participacao.Tipo.FAMILIAR,
                participacoes__status_convite=Participacao.Status.ACEITO,
            )
        ).distinct()
        return {"cuidadores": cuidadores, "familiares": familiares}
