"""
Camada de Services do app ponto.

Concentra o check-in / check-out do cuidador e o histórico de plantões
finalizados. Regras de negócio:
- RN05: um cuidador só pode ter um plantão ABERTO por vez;
- só existe um plantão por (paciente, cuidador, dia).
"""

from datetime import datetime
from decimal import Decimal

from django.utils import timezone
from geopy.distance import geodesic

from .models import Plantao

# Quantos plantões finalizados o histórico mostra.
HISTORICO_LIMITE = 7

DIAS_SEMANA = [
    "Segunda", "Terça", "Quarta", "Quinta", "Sexta", "Sábado", "Domingo",
]
MESES_PT = [
    "janeiro", "fevereiro", "março", "abril", "maio", "junho",
    "julho", "agosto", "setembro", "outubro", "novembro", "dezembro",
]


class PlantaoAbertoError(Exception):
    """Já existe um plantão aberto (não pode iniciar outro) — RN05."""


class SemPlantaoAbertoError(Exception):
    """Não há plantão aberto para finalizar."""


class ForaDoLocalError(Exception):
    """Check-in fora do raio permitido da residência (RN01 - GPS)."""


def _minutos(entrada, saida):
    """Minutos trabalhados entre dois horários (trata virada de meia-noite)."""
    e = entrada.hour * 60 + entrada.minute
    s = saida.hour * 60 + saida.minute
    if s < e:  # turno que cruza a meia-noite (ex.: 18:00 → 06:00)
        s += 24 * 60
    return s - e


def formatar_minutos(minutos):
    """Ex.: 705 -> '11h 45m'."""
    if minutos is None or minutos < 0:
        return "—"
    return f"{minutos // 60}h {minutos % 60:02d}m"


def rotulo_data(dia):
    """Ex.: ('Segunda', '16 de junho')."""
    return DIAS_SEMANA[dia.weekday()], f"{dia.day} de {MESES_PT[dia.month - 1]}"


def turno_label(hora):
    """Turno a partir da hora de entrada: Manhã / Tarde / Noite."""
    if hora is None:
        return ""
    if hora.hour < 12:
        return "Manhã"
    if hora.hour < 18:
        return "Tarde"
    return "Noite"


def _plantao_minutos(p):
    if p.hora_entrada and p.hora_saida:
        return _minutos(p.hora_entrada, p.hora_saida)
    return 0


def _nome(usuario):
    return (usuario.get_full_name() or usuario.email) if usuario else "—"


class PontoService:
    """Regras de negócio do ponto (plantões) de um cuidador."""

    @staticmethod
    def plantao_de_hoje(paciente, cuidador):
        return Plantao.objects.filter(
            paciente=paciente, cuidador=cuidador, data_plantao=timezone.localdate()
        ).first()

    # Observação registrada quando o check-in é feito sem localização.
    OBS_SEM_LOCAL = "Marcado sem Localização"

    @staticmethod
    def _validar_local(paciente, latitude, longitude):
        """
        RN01: valida que o cuidador está dentro do raio da residência.

        Retorna a tupla (gps, observacao):
        - paciente sem coordenadas → ("", "") (validação não se aplica);
        - localização indisponível → ("", "Marcado sem Localização")
          (o ponto é marcado mesmo assim, com a observação);
        - dentro do raio → ("lat,long", "");
        - fora do raio → levanta ForaDoLocalError (este caso bloqueia).
        """
        if paciente.latitude_gps is None or paciente.longitude_gps is None:
            return "", ""
        if latitude is None or longitude is None:
            return "", PontoService.OBS_SEM_LOCAL
        destino = (float(paciente.latitude_gps), float(paciente.longitude_gps))
        atual = (float(latitude), float(longitude))
        distancia = geodesic(destino, atual).meters
        raio = float(paciente.raio_validacao_gps or 100)
        if distancia > raio:
            raise ForaDoLocalError(
                f"Você está a {int(distancia)} m do paciente (limite {int(raio)} m). "
                "Aproxime-se da residência para fazer o check-in."
            )
        return f"{latitude},{longitude}", ""

    @staticmethod
    def check_in(*, paciente, cuidador, latitude=None, longitude=None):
        """Inicia o plantão de hoje (check-in), validando o GPS (RN01)."""
        hoje = timezone.localdate()
        # RN05: um plantão aberto por cuidador por vez.
        if Plantao.objects.filter(
            cuidador=cuidador, status=Plantao.Status.ABERTO
        ).exists():
            raise PlantaoAbertoError(
                "Você já tem um plantão aberto. Finalize-o antes de iniciar outro."
            )
        if Plantao.objects.filter(
            paciente=paciente, cuidador=cuidador, data_plantao=hoje
        ).exists():
            raise PlantaoAbertoError(
                "Já existe um ponto registrado para você hoje neste paciente."
            )
        # RN01: check-in só é permitido na residência do paciente — mas se a
        # localização não puder ser obtida, marca mesmo assim com observação.
        gps, observacao = PontoService._validar_local(paciente, latitude, longitude)
        return Plantao.objects.create(
            paciente=paciente,
            cuidador=cuidador,
            data_plantao=hoje,
            hora_entrada=timezone.localtime().time().replace(second=0, microsecond=0),
            localizacao_gps_entrada=gps,
            observacoes=observacao,
            status=Plantao.Status.ABERTO,
        )

    @staticmethod
    def check_out(*, paciente, cuidador):
        """Finaliza o plantão aberto de hoje (check-out)."""
        plantao = Plantao.objects.filter(
            paciente=paciente,
            cuidador=cuidador,
            data_plantao=timezone.localdate(),
            status=Plantao.Status.ABERTO,
        ).first()
        if not plantao:
            raise SemPlantaoAbertoError("Não há plantão aberto para finalizar.")
        saida = timezone.localtime().time().replace(second=0, microsecond=0)
        plantao.hora_saida = saida
        plantao.status = Plantao.Status.FECHADO
        if plantao.hora_entrada:
            mins = _minutos(plantao.hora_entrada, saida)
            plantao.duracao_horas = Decimal(mins) / Decimal(60)
        plantao.save()
        return plantao

    @staticmethod
    def editar_hoje(*, paciente, cuidador, entrada, saida=None):
        """
        Edita os horários do ponto de HOJE (somente o do dia atual).
        `entrada` é obrigatória. Se `saida` for informada, fecha o plantão e
        recalcula a duração; senão, mantém aberto (sem saída).
        """
        plantao = PontoService.plantao_de_hoje(paciente, cuidador)
        if plantao is None:
            raise SemPlantaoAbertoError("Não há ponto de hoje para editar.")
        plantao.hora_entrada = entrada
        if saida:
            plantao.hora_saida = saida
            plantao.status = Plantao.Status.FECHADO
            plantao.duracao_horas = Decimal(_minutos(entrada, saida)) / Decimal(60)
        else:
            plantao.hora_saida = None
            plantao.status = Plantao.Status.ABERTO
            plantao.duracao_horas = None
        plantao.save()
        return plantao

    @staticmethod
    def estado_hoje(paciente, cuidador):
        """
        Estado do ponto de hoje para o cartão principal:
        situacao = 'sem_ponto' | 'aberto' | 'fechado', com horários e minutos.
        """
        plantao = PontoService.plantao_de_hoje(paciente, cuidador)
        if plantao is None:
            return {"situacao": "sem_ponto", "plantao": None}
        if plantao.is_aberto:
            agora = timezone.localtime().time().replace(microsecond=0)
            mins = _minutos(plantao.hora_entrada, agora) if plantao.hora_entrada else None
            return {
                "situacao": "aberto",
                "plantao": plantao,
                "entrada": plantao.hora_entrada,
                "trabalhadas": formatar_minutos(mins),
                "observacoes": plantao.observacoes,
            }
        # fechado
        mins = (
            _minutos(plantao.hora_entrada, plantao.hora_saida)
            if plantao.hora_entrada and plantao.hora_saida
            else None
        )
        return {
            "situacao": "fechado",
            "plantao": plantao,
            "entrada": plantao.hora_entrada,
            "saida": plantao.hora_saida,
            "trabalhadas": formatar_minutos(mins),
            "observacoes": plantao.observacoes,
        }

    @staticmethod
    def historico_finalizados(paciente, cuidador, inicio=None, fim=None,
                              limite=HISTORICO_LIMITE):
        """
        Os últimos `limite` plantões FINALIZADOS do cuidador neste paciente,
        opcionalmente filtrados por intervalo de datas. Cada item já vem com
        rótulo de dia e horas formatadas para a tela.
        """
        qs = Plantao.objects.filter(
            paciente=paciente, cuidador=cuidador, status=Plantao.Status.FECHADO
        )
        if inicio:
            qs = qs.filter(data_plantao__gte=inicio)
        if fim:
            qs = qs.filter(data_plantao__lte=fim)

        itens = []
        for p in qs.order_by("-data_plantao")[:limite]:
            dia_semana, data_label = rotulo_data(p.data_plantao)
            mins = (
                _minutos(p.hora_entrada, p.hora_saida)
                if p.hora_entrada and p.hora_saida
                else None
            )
            itens.append({
                "plantao": p,
                "dia_semana": dia_semana,
                "data_label": data_label,
                "entrada": p.hora_entrada,
                "saida": p.hora_saida,
                "horas": formatar_minutos(mins),
                "observacoes": p.observacoes,
            })
        return itens


class MonitorService:
    """
    Monitoramento dos plantões (visão do familiar): painéis de resumo,
    plantões em aberto/do dia, relatório de horas do mês e gestão (editar/
    excluir) dos pontos registrados.
    """

    @staticmethod
    def cuidadores_equipe(paciente):
        from pacientes.services import PacienteService
        return list(PacienteService.equipe_do_paciente(paciente)["cuidadores"])

    @staticmethod
    def _item(p, agora=None):
        """Formata um plantão para exibição (cards/lista)."""
        mins = _plantao_minutos(p)
        decorrido = None
        if p.is_aberto and p.hora_entrada and agora is not None:
            decorrido = _minutos(p.hora_entrada, agora)
        return {
            "plantao": p,
            "cuidador_nome": _nome(p.cuidador),
            "turno": turno_label(p.hora_entrada),
            "entrada": p.hora_entrada,
            "saida": p.hora_saida,
            "status": p.status,
            "status_label": p.get_status_display(),
            "duracao": formatar_minutos(mins) if p.is_fechado else "—",
            "decorrido": formatar_minutos(decorrido) if decorrido is not None else "",
        }

    @staticmethod
    def em_plantao_agora(paciente):
        agora = timezone.localtime().time().replace(microsecond=0)
        qs = Plantao.objects.filter(
            paciente=paciente, status=Plantao.Status.ABERTO
        ).select_related("cuidador").order_by("hora_entrada")
        return [MonitorService._item(p, agora) for p in qs]

    @staticmethod
    def plantoes_do_dia(paciente, dia, cuidador_id=None):
        agora = timezone.localtime().time().replace(microsecond=0)
        qs = Plantao.objects.filter(
            paciente=paciente, data_plantao=dia
        ).select_related("cuidador")
        if cuidador_id:
            qs = qs.filter(cuidador_id=cuidador_id)
        # Mais recente primeiro (entrada mais tarde / inserido por último).
        return [MonitorService._item(p, agora) for p in qs.order_by("-hora_entrada", "-id")]

    @staticmethod
    def relatorio_mes(paciente, ano, mes):
        qs = Plantao.objects.filter(
            paciente=paciente, status=Plantao.Status.FECHADO,
            data_plantao__year=ano, data_plantao__month=mes,
        ).select_related("cuidador")
        agg = {}
        for p in qs:
            linha = agg.setdefault(p.cuidador_id, {"cuidador": _nome(p.cuidador),
                                                   "plantoes": 0, "minutos": 0})
            linha["plantoes"] += 1
            linha["minutos"] += _plantao_minutos(p)
        linhas = sorted(agg.values(), key=lambda x: x["cuidador"])
        for l in linhas:
            l["horas"] = formatar_minutos(l["minutos"])
        total_plantoes = sum(l["plantoes"] for l in linhas)
        total_min = sum(l["minutos"] for l in linhas)
        return {
            "linhas": linhas,
            "total_plantoes": total_plantoes,
            "total_horas": formatar_minutos(total_min),
            "total_minutos": total_min,
        }

    @staticmethod
    def resumo_mes(paciente, ano, mes):
        rel = MonitorService.relatorio_mes(paciente, ano, mes)
        return {
            "total_horas": rel["total_horas"],
            "num_cuidadores": len(MonitorService.cuidadores_equipe(paciente)),
            "num_plantoes": rel["total_plantoes"],
        }

    @staticmethod
    def editar_plantao(*, paciente, plantao_id, entrada, saida=None):
        """Edita um plantão do paciente (visão do familiar)."""
        plantao = Plantao.objects.filter(paciente=paciente, pk=plantao_id).first()
        if plantao is None:
            return None
        plantao.hora_entrada = entrada
        if saida:
            plantao.hora_saida = saida
            plantao.status = Plantao.Status.FECHADO
            plantao.duracao_horas = Decimal(_minutos(entrada, saida)) / Decimal(60)
        else:
            plantao.hora_saida = None
            plantao.status = Plantao.Status.ABERTO
            plantao.duracao_horas = None
        plantao.save()
        return plantao

    @staticmethod
    def excluir_plantao(*, paciente, plantao_id):
        apagados, _ = Plantao.objects.filter(
            paciente=paciente, pk=plantao_id
        ).delete()
        return apagados > 0
