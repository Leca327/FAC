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
    def pacientes_do_usuario(usuario, busca=""):
        """
        Retorna os pacientes vinculados ao usuário, conforme o seu tipo:

        - Familiar: pacientes em que ele é o responsável OU em que possui
          uma participação aceita (compartilhamento — RN06).
        - Cuidador: pacientes em que possui uma participação de cuidador aceita.
        """
        if usuario.is_familiar:
            qs = Paciente.objects.filter(
                Q(familiar_responsavel=usuario)
                | Q(
                    participacoes__usuario=usuario,
                    participacoes__status_convite=Participacao.Status.ACEITO,
                ),
                ativo=True,
            )
        else:
            qs = Paciente.objects.filter(
                participacoes__usuario=usuario,
                participacoes__tipo_participacao=Participacao.Tipo.CUIDADOR,
                participacoes__status_convite=Participacao.Status.ACEITO,
                ativo=True,
            )

        if busca:
            qs = qs.filter(nome__icontains=busca)

        return qs.distinct()

    @staticmethod
    def paciente_acessivel(usuario, pk):
        """Retorna o paciente se o usuário tem acesso a ele; senão None."""
        return PacienteService.pacientes_do_usuario(usuario).filter(pk=pk).first()

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
