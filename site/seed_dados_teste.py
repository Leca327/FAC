# -*- coding: utf-8 -*-
"""
Seed de DADOS DE TESTE do CuidaCare (NAO faz parte do dump oficial).

Cria um cenario minimo e coerente para testar as telas prontas:
- 1 familiar responsavel + 3 cuidadoras ativas (participacao aceita);
- 1 paciente criado pela familia;
- 3 medicamentos, 3 medicos/clinicas e 5 consultas agendadas;
- escala dos 3 turnos (manha/tarde/noite) montada com as 3 cuidadoras.

Idempotente: pode ser rodado mais de uma vez sem duplicar.

Como rodar (dentro de site/, com o venv):
    .\\venv\\Scripts\\python.exe manage.py shell -c "exec(open('seed_dados_teste.py', encoding='utf-8').read())"
"""

from datetime import date, timedelta

from django.db import transaction
from django.utils import timezone

from consultas.models import Consulta
from escala.models import PadraoTurno, Turno
from escala.services import EscalaService, segunda_da_semana
from medicamentos.models import Medicamento, MedicamentoTomado
from medicos.models import Medico
from pacientes.models import Paciente, Participacao
from prontuario.models import Anotacao
from ponto.models import Plantao
from usuarios.models import Usuario

SENHA = "Teste@123"


def cria_usuario(email, nome, sobrenome, tipo, cpf, telefone):
    u = Usuario.objects.filter(email=email).first()
    if u:
        print(f"  = usuario ja existe: {email}")
        return u
    u = Usuario.objects.create_user(
        email=email,
        password=SENHA,
        first_name=nome,
        last_name=sobrenome,
        tipo_usuario=tipo,
        cpf=cpf,
        telefone=telefone,
    )
    print(f"  + usuario criado: {email} (senha: {SENHA})")
    return u


@transaction.atomic
def seed():
    print("== Usuarios ==")
    familiar = cria_usuario(
        "maria.souza@teste.com", "Maria", "de Souza",
        Usuario.Tipo.FAMILIAR, "11111111111", "81999990001",
    )
    ana = cria_usuario(
        "ana.lima@teste.com", "Ana", "Lima",
        Usuario.Tipo.CUIDADOR, "22222222222", "81999990002",
    )
    joana = cria_usuario(
        "joana.ribeiro@teste.com", "Joana", "Ribeiro",
        Usuario.Tipo.CUIDADOR, "33333333333", "81999990003",
    )
    carla = cria_usuario(
        "carla.mendes@teste.com", "Carla", "Mendes",
        Usuario.Tipo.CUIDADOR, "44444444444", "81999990004",
    )
    cuidadoras = [ana, joana, carla]

    print("== Paciente ==")
    paciente, novo = Paciente.objects.get_or_create(
        cpf="55555555555",
        defaults=dict(
            nome="Antonio Pereira",
            data_nascimento=date(1944, 3, 12),
            endereco="Rua das Flores, 100 - Recife/PE",
            telefone="81999990005",
            familiar_responsavel=familiar,
            condicoes_saude="Hipertensao, diabetes tipo 2 e colesterol alto.",
            alergias="Dipirona.",
        ),
    )
    print(f"  {'+' if novo else '='} paciente: {paciente.nome} ({paciente.idade} anos)")

    print("== Participacoes (equipe) ==")
    # Familiar responsavel
    Participacao.objects.get_or_create(
        usuario=familiar, paciente=paciente,
        defaults=dict(
            tipo_participacao=Participacao.Tipo.FAMILIAR,
            vinculo="Filha",
            status_convite=Participacao.Status.ACEITO,
            permissao_leitura=True, permissao_escrita=True,
        ),
    )
    # 3 cuidadoras ATIVAS (participacao aceita)
    for c in cuidadoras:
        _, n = Participacao.objects.get_or_create(
            usuario=c, paciente=paciente,
            defaults=dict(
                tipo_participacao=Participacao.Tipo.CUIDADOR,
                status_convite=Participacao.Status.ACEITO,
                permissao_leitura=True, permissao_escrita=True,
            ),
        )
        print(f"  {'+' if n else '='} cuidadora ativa: {c.get_full_name()}")

    print("== Medicamentos (3) ==")
    meds = [
        dict(nome="Losartana", dosagem="50mg", forma_farmaceutica="Comprimido",
             frequencia="1x ao dia", horarios="08:00", quantidade_dose="1 comprimido",
             medico="Dr. Carlos Andrade", data_inicio=date.today() - timedelta(days=30)),
        dict(nome="Metformina", dosagem="850mg", forma_farmaceutica="Comprimido",
             frequencia="2x ao dia", horarios="08:00, 20:00", quantidade_dose="1 comprimido",
             medico="Dra. Helena Costa", data_inicio=date.today() - timedelta(days=60)),
        dict(nome="Sinvastatina", dosagem="20mg", forma_farmaceutica="Comprimido",
             frequencia="1x ao dia", horarios="22:00", quantidade_dose="1 comprimido",
             medico="Dr. Carlos Andrade", data_inicio=date.today() - timedelta(days=15)),
    ]
    for m in meds:
        _, n = Medicamento.objects.get_or_create(
            paciente=paciente, nome=m["nome"], dosagem=m["dosagem"],
            defaults={**m, "status": Medicamento.Status.ATIVO},
        )
        print(f"  {'+' if n else '='} {m['nome']} {m['dosagem']}")

    print("== Medicos/Clinicas (3) ==")
    med_cardio, _ = Medico.objects.get_or_create(
        paciente=paciente, nome="Dr. Carlos Andrade",
        defaults=dict(tipo=Medico.Tipo.MEDICO, especialidade="Cardiologia",
                      crm_cnpj="CRM-PE 12345", telefone="8133330001",
                      cidade="Recife", uf="PE"),
    )
    med_endo, _ = Medico.objects.get_or_create(
        paciente=paciente, nome="Dra. Helena Costa",
        defaults=dict(tipo=Medico.Tipo.MEDICO, especialidade="Endocrinologia",
                      crm_cnpj="CRM-PE 67890", telefone="8133330002",
                      cidade="Recife", uf="PE"),
    )
    lab, _ = Medico.objects.get_or_create(
        paciente=paciente, nome="Laboratorio Diagnostika",
        defaults=dict(tipo=Medico.Tipo.LABORATORIO, crm_cnpj="CNPJ 12.345.678/0001-90",
                      telefone="8133330003", cidade="Recife", uf="PE"),
    )
    print("  medicos/clinicas ok")

    print("== Consultas/Exames (5) ==")
    agora = timezone.localtime()
    consultas = [
        ("Cardiologia", Consulta.Tipo.CONSULTA, med_cardio, 5, 9, 30),
        ("Hemograma completo", Consulta.Tipo.EXAME, lab, 8, 7, 0),
        ("Endocrinologia", Consulta.Tipo.CONSULTA, med_endo, 12, 14, 0),
        ("Clinica Geral", Consulta.Tipo.CONSULTA, None, 18, 10, 0),
        ("Raio-X de torax", Consulta.Tipo.EXAME, lab, 25, 8, 30),
    ]
    for titulo, tipo, medico, dias, hh, mm in consultas:
        dh = (agora + timedelta(days=dias)).replace(hour=hh, minute=mm, second=0, microsecond=0)
        _, n = Consulta.objects.get_or_create(
            paciente=paciente, titulo=titulo, data_hora=dh,
            defaults=dict(tipo=tipo, medico=medico,
                          status=Consulta.Status.AGENDADA, agendada_por=familiar),
        )
        print(f"  {'+' if n else '='} {titulo} - {dh:%d/%m/%Y %H:%M}")

    print("== Escala (3 turnos x 3 cuidadoras) ==")
    segunda = segunda_da_semana(date.today())
    # Manha: rodizio de 2 em 2 dias -> Ana, Joana, Carla
    EscalaService.salvar_padrao(
        paciente=paciente, turno=Turno.MANHA, tipo=PadraoTurno.Tipo.RODIZIO,
        dias_por_pessoa=2, data_inicio=segunda,
        cuidadores_rodizio=[ana, joana, carla],
    )
    # Tarde: rodizio diario -> Carla, Ana, Joana
    EscalaService.salvar_padrao(
        paciente=paciente, turno=Turno.TARDE, tipo=PadraoTurno.Tipo.RODIZIO,
        dias_por_pessoa=1, data_inicio=segunda,
        cuidadores_rodizio=[carla, ana, joana],
    )
    # Noite: por dia da semana
    EscalaService.salvar_padrao(
        paciente=paciente, turno=Turno.NOITE, tipo=PadraoTurno.Tipo.SEMANAL,
        semanal={0: ana, 1: ana, 2: joana, 3: joana, 4: carla, 5: carla, 6: ana},
    )
    print("  escala montada (manha/tarde/noite)")

    print("== Prontuario (eventos de HOJE) ==")
    hoje = timezone.localdate()
    agora = timezone.now()
    local = timezone.localtime()
    # Doses tomadas hoje (entram na linha do tempo no horario indicado)
    doses_hoje = [("Losartana", "08:00"), ("Metformina", "08:00")]
    for nome, horario in doses_hoje:
        med = Medicamento.objects.filter(paciente=paciente, nome=nome).first()
        if med:
            _, n = MedicamentoTomado.objects.get_or_create(
                medicamento=med, data=hoje, horario_previsto=horario,
                defaults=dict(tomado=True, tomado_em=agora, marcado_por=ana),
            )
            print(f"  {'+' if n else '='} dose tomada: {nome} {horario}")
    # Uma consulta realizada hoje
    dh = local.replace(hour=10, minute=0, second=0, microsecond=0)
    _, n = Consulta.objects.get_or_create(
        paciente=paciente, titulo="Clinica Geral (retorno)", data_hora=dh,
        defaults=dict(tipo=Consulta.Tipo.CONSULTA, medico=med_cardio,
                      status=Consulta.Status.REALIZADA, agendada_por=familiar,
                      realizada_por=familiar, realizada_em=agora,
                      resultado="Paciente estavel, manter medicacao."),
    )
    print(f"  {'+' if n else '='} consulta realizada hoje")
    # Uma anotacao manual
    an_dh = local.replace(hour=9, minute=15, second=0, microsecond=0)
    _, n = Anotacao.objects.get_or_create(
        paciente=paciente, titulo="Paciente se alimentou bem no cafe da manha",
        data_hora=an_dh,
        defaults=dict(descricao="Aceitou toda a refeicao e tomou os liquidos.",
                      autor=ana),
    )
    print(f"  {'+' if n else '='} anotacao registrada")

    print("== Ponto (plantoes da Ana) ==")
    from decimal import Decimal
    import datetime as _dt
    # Coordenadas do paciente para ativar a validacao de GPS no check-in (RN01).
    paciente.latitude_gps = Decimal("-8.04760000")
    paciente.longitude_gps = Decimal("-34.87700000")
    paciente.raio_validacao_gps = 100
    paciente.save(update_fields=["latitude_gps", "longitude_gps", "raio_validacao_gps"])
    turnos = [("06:00", "18:00"), ("06:00", "12:00"), ("12:00", "18:00")]
    for i in range(1, 9):  # ultimos 8 dias finalizados
        d = hoje - timedelta(days=i)
        ent_s, sai_s = turnos[i % len(turnos)]
        ent = _dt.time.fromisoformat(ent_s)
        sai = _dt.time.fromisoformat(sai_s)
        mins = (sai.hour * 60 + sai.minute) - (ent.hour * 60 + ent.minute)
        _, n = Plantao.objects.get_or_create(
            paciente=paciente, cuidador=ana, data_plantao=d,
            defaults=dict(hora_entrada=ent, hora_saida=sai,
                          status=Plantao.Status.FECHADO,
                          duracao_horas=Decimal(mins) / Decimal(60)),
        )
    # Plantao ABERTO hoje (check-in feito, aguardando check-out)
    Plantao.objects.get_or_create(
        paciente=paciente, cuidador=ana, data_plantao=hoje,
        defaults=dict(hora_entrada=_dt.time(6, 0), status=Plantao.Status.ABERTO),
    )
    print("  plantoes criados (8 finalizados + 1 aberto hoje)")

    print("\nOK! Logins de teste (senha unica):")
    print(f"  Familiar : maria.souza@teste.com    / {SENHA}")
    print(f"  Cuidadora: ana.lima@teste.com       / {SENHA}")
    print(f"  Cuidadora: joana.ribeiro@teste.com  / {SENHA}")
    print(f"  Cuidadora: carla.mendes@teste.com   / {SENHA}")


seed()
