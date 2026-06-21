-- =====================================================
-- BANCO DE DADOS: CUIDACARE
-- MYSQL 8.0+
-- =====================================================
-- ATENCAO: este script cria TODO o schema da aplicacao (tabelas, views,
-- procedures, triggers) + dados de exemplo, mas NAO cria as tabelas
-- internas do Django (django_migrations, django_session, django_content_type,
-- auth_*). Essas sao criadas pelo "migrate". Importar este .sql NAO basta
-- para o site rodar -> siga o "MANUAL_CRIANDO_O_BANCO.txt" (na raiz).
-- =====================================================

CREATE DATABASE IF NOT EXISTS cuidacare_db 
CHARACTER SET utf8mb4 
COLLATE utf8mb4_unicode_ci;

USE cuidacare_db;

-- =====================================================
-- TABELA: USER (Superclasse - Familiar e Cuidador)
-- =====================================================

CREATE TABLE `usuario` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `email` VARCHAR(255) UNIQUE NOT NULL,
  `password` VARCHAR(255) NOT NULL,
  `first_name` VARCHAR(150),
  `last_name` VARCHAR(150),
  `tipo_usuario` ENUM('familiar', 'cuidador') NOT NULL,
  `cpf` VARCHAR(11) UNIQUE,
  `rg` VARCHAR(20) NOT NULL DEFAULT '',
  `data_nascimento` DATE NULL,
  `genero` VARCHAR(15) NOT NULL DEFAULT '',
  `estado_civil` VARCHAR(15) NOT NULL DEFAULT '',
  `telefone` VARCHAR(11) NOT NULL DEFAULT '',
  `whatsapp` VARCHAR(11) NOT NULL DEFAULT '',
  `endereco` VARCHAR(255) NOT NULL DEFAULT '',
  `complemento` VARCHAR(100) NOT NULL DEFAULT '',
  `cidade` VARCHAR(100) NOT NULL DEFAULT '',
  `estado` VARCHAR(2) NOT NULL DEFAULT '',
  `cep` VARCHAR(8) NOT NULL DEFAULT '',
  `pais` VARCHAR(60) NOT NULL DEFAULT 'Brasil',
  `foto` VARCHAR(100) NULL,
  `data_criacao` DATETIME DEFAULT CURRENT_TIMESTAMP,
  -- Campo extra do fluxo de recuperação de senha (model usuarios.Usuario)
  `senha_temporaria` BOOLEAN NOT NULL DEFAULT FALSE,
  -- Campos herdados do AbstractUser do Django
  `is_active` BOOLEAN NOT NULL DEFAULT TRUE,
  `is_staff` BOOLEAN NOT NULL DEFAULT FALSE,
  `is_superuser` BOOLEAN NOT NULL DEFAULT FALSE,
  `date_joined` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `last_login` DATETIME NULL,

  INDEX idx_email (email),
  INDEX idx_tipo (tipo_usuario),
  INDEX idx_cpf (cpf)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- =====================================================
-- TABELAS DE LIGAÇÃO M2M do usuário (AbstractUser do Django)
-- group_id/permission_id referenciam auth_group/auth_permission,
-- tabelas criadas pelo `migrate` do Django (por isso sem FK aqui,
-- para não depender da ordem de importação).
-- =====================================================
CREATE TABLE `usuario_groups` (
  `id` BIGINT AUTO_INCREMENT PRIMARY KEY,
  `usuario_id` INT NOT NULL,
  `group_id` INT NOT NULL,
  UNIQUE KEY `usuario_groups_usuario_id_group_id_uniq` (`usuario_id`, `group_id`),
  FOREIGN KEY (usuario_id) REFERENCES usuario(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `usuario_user_permissions` (
  `id` BIGINT AUTO_INCREMENT PRIMARY KEY,
  `usuario_id` INT NOT NULL,
  `permission_id` INT NOT NULL,
  UNIQUE KEY `usuario_user_perms_usuario_id_permission_id_uniq` (`usuario_id`, `permission_id`),
  FOREIGN KEY (usuario_id) REFERENCES usuario(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- (Observação: NÃO há mais as tabelas de especialização `familiar` e
--  `cuidador`. Tudo fica em `usuario`; o papel de cada um em relação a um
--  paciente — familiar/cuidador e o vínculo — vive em `participacao`.)

-- =====================================================
-- TABELA: PACIENTE
-- =====================================================

CREATE TABLE `paciente` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `nome` VARCHAR(255) NOT NULL,
  `cpf` VARCHAR(11) UNIQUE,
  `data_nascimento` DATE NOT NULL,
  `endereco` VARCHAR(255),            -- rua
  `complemento` VARCHAR(100) NOT NULL DEFAULT '',
  `cidade` VARCHAR(100) NOT NULL DEFAULT '',
  `estado` VARCHAR(2) NOT NULL DEFAULT '',
  `cep` VARCHAR(8) NOT NULL DEFAULT '',
  `pais` VARCHAR(60) NOT NULL DEFAULT 'Brasil',
  `telefone` VARCHAR(11),
  `familiar_responsavel_id` INT NOT NULL,
  `condicoes_saude` TEXT,
  `alergias` TEXT,
  `foto` VARCHAR(100),            -- caminho do arquivo (FileField upload_to=pacientes/)
  `latitude_gps` DECIMAL(10, 8),
  `longitude_gps` DECIMAL(11, 8),
  `raio_validacao_gps` FLOAT DEFAULT 100,  -- em metros
  `data_criacao` DATETIME DEFAULT CURRENT_TIMESTAMP,
  `ativo` BOOLEAN DEFAULT TRUE,
  
  FOREIGN KEY (familiar_responsavel_id) REFERENCES usuario(id) ON DELETE CASCADE,
  INDEX idx_familiar (familiar_responsavel_id),
  INDEX idx_nome (nome),
  INDEX idx_cpf (cpf)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- =====================================================
-- TABELA: PARTICIPACAO (tela "Equipe" — vínculo Usuário ↔ Paciente)
-- Tabela ÚNICA que intermedeia usuário e paciente para toda a equipe
-- (familiares e cuidadores). Também governa o controle de acesso. O convite
-- só é criado para quem já tem conta; fica 'pendente' até a pessoa aceitar
-- pelo link do e-mail (token), quando vira 'aceito'.
-- =====================================================

CREATE TABLE `participacao` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `usuario_id` INT NOT NULL,
  `paciente_id` INT NOT NULL,
  `tipo_participacao` ENUM('familiar', 'cuidador') NOT NULL,
  `vinculo` VARCHAR(100) DEFAULT '',          -- Filha, Marido... (só p/ tipo familiar)
  `status_convite` ENUM('pendente', 'aceito', 'rejeitado') DEFAULT 'pendente',
  `token` VARCHAR(40) NOT NULL UNIQUE,        -- link de aceite do convite
  `data_convite` DATETIME DEFAULT CURRENT_TIMESTAMP,
  `data_resposta` DATETIME,
  `permissao_leitura` BOOLEAN DEFAULT TRUE,
  `permissao_escrita` BOOLEAN DEFAULT FALSE,

  FOREIGN KEY (usuario_id) REFERENCES usuario(id) ON DELETE CASCADE,
  FOREIGN KEY (paciente_id) REFERENCES paciente(id) ON DELETE CASCADE,
  UNIQUE KEY unique_participacao (usuario_id, paciente_id),
  INDEX idx_status (status_convite),
  INDEX idx_usuario (usuario_id),
  INDEX idx_paciente (paciente_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- =====================================================
-- TABELA: MEDICO (médico, clínica ou laboratório do paciente)
-- (Antes `medico_clinica`, global; agora vinculado ao paciente,
--  conforme a tela "Médicos". Todos os campos aparecem na tela.)
-- =====================================================

CREATE TABLE `medico` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `paciente_id` INT NOT NULL,
  `nome` VARCHAR(255) NOT NULL,
  `tipo` ENUM('medico', 'clinica', 'laboratorio') NOT NULL DEFAULT 'medico',
  `especialidade` VARCHAR(150),
  `crm_cnpj` VARCHAR(50),
  `telefone` VARCHAR(11),
  `email` VARCHAR(255),
  `endereco` VARCHAR(255),
  `cidade` VARCHAR(100),
  `uf` VARCHAR(2),
  `data_criacao` DATETIME DEFAULT CURRENT_TIMESTAMP,

  FOREIGN KEY (paciente_id) REFERENCES paciente(id) ON DELETE CASCADE,
  INDEX idx_paciente (paciente_id),
  INDEX idx_nome (nome),
  INDEX idx_especialidade (especialidade),
  INDEX idx_tipo (tipo)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- =====================================================
-- TABELA: CONSULTA (Marcar) — tela "Consultas e Exames"
-- Ajustes em relação ao DER original:
--   - `motivo` virou `observacao`;
--   - removido `proximo_agendamento`;
--   - `familiar_marcou_id` virou `agendada_por_id` (familiar OU cuidador);
--   - adicionados `realizada_por_id` + `realizada_em` (quem marcou como
--     realizada e quando — mesma lógica de medicamento_tomado);
--   - o médico/clínica é ESCOLHIDO entre os cadastrados do paciente
--     (FK `medico_id` → tabela `medico`); nome, CRM/CNPJ e endereço vêm
--     de lá (sem campos próprios de profissional/local). Sem convênio.
-- =====================================================

CREATE TABLE `consulta` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `paciente_id` INT NOT NULL,
  `medico_id` INT,                       -- médico/clínica escolhido (FK)
  `tipo` ENUM('consulta', 'exame') DEFAULT 'consulta',  -- categoria/ícone
  `titulo` VARCHAR(255) NOT NULL,        -- Cardiologia / Eletrocardiograma
  `data_hora` DATETIME NOT NULL,
  `observacao` TEXT,                     -- (substitui o antigo `motivo`)
  `status` ENUM('agendada', 'realizada', 'cancelada') DEFAULT 'agendada',
  `resultado` TEXT,                      -- preenchido ao marcar como realizada
  `agendada_por_id` INT,                 -- quem agendou (familiar ou cuidador)
  `realizada_por_id` INT,                -- quem marcou como realizada
  `realizada_em` DATETIME DEFAULT NULL,  -- quando foi marcada como realizada
  `data_criacao` DATETIME DEFAULT CURRENT_TIMESTAMP,

  FOREIGN KEY (paciente_id) REFERENCES paciente(id) ON DELETE CASCADE,
  FOREIGN KEY (medico_id) REFERENCES medico(id) ON DELETE SET NULL,
  FOREIGN KEY (agendada_por_id) REFERENCES usuario(id) ON DELETE SET NULL,
  FOREIGN KEY (realizada_por_id) REFERENCES usuario(id) ON DELETE SET NULL,
  INDEX idx_consulta_pac_data (paciente_id, data_hora),
  INDEX idx_consulta_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- =====================================================
-- TABELA: MEDICAMENTO
-- Modelo enxuto: apenas os campos exibidos na tela "Medicamentos".
-- (Consolidou as antigas tabelas `medicamento` + `prescricao_medicamento`,
--  removendo princípio ativo, laboratório e a FK para médico_clínica —
--  o médico passou a ser um simples campo de texto.)
-- A tela "Medicamentos" cadastra apenas o remédio (nome, dosagem, forma,
--  médico). Os campos de posologia/agenda (frequência, horários, quantidade,
--  período e dias da semana) são preenchidos na tela "Medicação Diária",
--  por isso ficam opcionais aqui.
-- =====================================================

CREATE TABLE `medicamento` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `paciente_id` INT NOT NULL,
  `nome` VARCHAR(255) NOT NULL,             -- remédio (ex: Losartana)
  `dosagem` VARCHAR(50) NOT NULL,           -- ex: 50mg
  `forma_farmaceutica` VARCHAR(100),        -- comprimido, líquido, etc
  `frequencia` VARCHAR(100),                -- 2x ao dia, a cada 6h
  `horarios` VARCHAR(255),                  -- 08:00,20:00 (separados por vírgula)
  `quantidade_dose` VARCHAR(50),            -- 1 comprimido, 10ml, etc
  `medico` VARCHAR(255),                    -- texto (ex: Dr. Carlos)
  `data_inicio` DATE,                       -- definido na Medicação Diária
  `data_fim` DATE,                          -- NULL = contínuo
  -- Controle por dia da semana (segunda a domingo)
  `seg` BOOLEAN DEFAULT TRUE,
  `ter` BOOLEAN DEFAULT TRUE,
  `qua` BOOLEAN DEFAULT TRUE,
  `qui` BOOLEAN DEFAULT TRUE,
  `sex` BOOLEAN DEFAULT TRUE,
  `sab` BOOLEAN DEFAULT TRUE,
  `dom` BOOLEAN DEFAULT TRUE,
  `observacoes` TEXT,
  `status` ENUM('ativo', 'descontinuado') DEFAULT 'ativo',
  `data_criacao` DATETIME DEFAULT CURRENT_TIMESTAMP,

  FOREIGN KEY (paciente_id) REFERENCES paciente(id) ON DELETE CASCADE,
  INDEX idx_paciente (paciente_id),
  INDEX idx_nome (nome),
  INDEX idx_status (status),
  INDEX idx_data_inicio (data_inicio)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- =====================================================
-- TABELA: MEDICAMENTO_TOMADO
-- Registra se uma dose de medicamento foi tomada, na tela "Medicação Diária".
-- Cada linha = uma dose única (medicamento + dia + horário previsto) e guarda:
--   `tomado`           -> se a pessoa tomou (booleano);
--   `horario_previsto` -> a hora em que a dose DEVERIA ser tomada;
--   `tomado_em`        -> a data/hora em que foi MARCADA como tomada;
--   `marcado_por_id`   -> QUEM marcou (familiar ou cuidador).
-- É o que permite derivar o status da rotina:
--   existe registro tomado                 -> 'Tomado'
--   não tomado e o horário já passou        -> 'Atrasado'
--   não tomado e o horário ainda não chegou -> 'Pendente'
-- =====================================================

CREATE TABLE `medicamento_tomado` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `medicamento_id` INT NOT NULL,
  `data` DATE NOT NULL,                       -- dia da dose
  `horario_previsto` VARCHAR(5) NOT NULL,     -- hora que deveria ser tomada (HH:MM)
  `tomado` BOOLEAN NOT NULL DEFAULT TRUE,     -- se a pessoa tomou
  `tomado_em` DATETIME DEFAULT NULL,          -- quando foi marcada como tomada
  `marcado_por_id` INT DEFAULT NULL,          -- quem marcou (familiar ou cuidador)

  FOREIGN KEY (medicamento_id) REFERENCES medicamento(id) ON DELETE CASCADE,
  FOREIGN KEY (marcado_por_id) REFERENCES usuario(id) ON DELETE SET NULL,
  UNIQUE KEY uq_tomado_med_data_horario (medicamento_id, data, horario_previsto),
  INDEX idx_tomado_med_data (medicamento_id, data)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- =====================================================
-- TABELA: PLANTAO (Realiza)
-- =====================================================

CREATE TABLE `plantao` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `paciente_id` INT NOT NULL,
  `cuidador_id` INT NOT NULL,
  `data_plantao` DATE NOT NULL,
  `hora_entrada` TIME,
  `hora_saida` TIME,
  `localizacao_gps_entrada` VARCHAR(100),  -- latitude,longitude
  `status` ENUM('aberto', 'fechado', 'cancelado') DEFAULT 'fechado',
  `duracao_horas` DECIMAL(5, 2),  -- calculado automaticamente
  `observacoes` TEXT,
  `data_criacao` DATETIME DEFAULT CURRENT_TIMESTAMP,
  
  FOREIGN KEY (paciente_id) REFERENCES paciente(id) ON DELETE CASCADE,
  FOREIGN KEY (cuidador_id) REFERENCES usuario(id) ON DELETE RESTRICT,
  INDEX idx_paciente (paciente_id),
  INDEX idx_cuidador (cuidador_id),
  INDEX idx_data (data_plantao),
  INDEX idx_status (status),
  UNIQUE KEY unique_plantao_aberto (paciente_id, cuidador_id, data_plantao)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- =====================================================
-- TABELA: ATIVIDADE (Feed de atividades)
-- =====================================================

CREATE TABLE `atividade` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `paciente_id` INT NOT NULL,
  `usuario_id` INT NOT NULL,
  `tipo` VARCHAR(100),  -- medicamento, consulta, plantao_aberto, anotacao, etc
  `descricao` TEXT,
  `data_hora` DATETIME DEFAULT CURRENT_TIMESTAMP,
  
  FOREIGN KEY (paciente_id) REFERENCES paciente(id) ON DELETE CASCADE,
  FOREIGN KEY (usuario_id) REFERENCES usuario(id) ON DELETE RESTRICT,
  INDEX idx_paciente (paciente_id),
  INDEX idx_data_hora (data_hora)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- =====================================================
-- ESCALA DE CUIDADORES (tela "Escala")
-- O padrão de cada turno gera a escala; pode ser rodízio (N dias por pessoa
-- a partir de uma data) ou por dia da semana. Exceções pontuais sobrepõem.
-- =====================================================

CREATE TABLE `padrao_turno` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `paciente_id` INT NOT NULL,
  `turno` ENUM('manha', 'tarde', 'noite') NOT NULL,
  `tipo_padrao` ENUM('rodizio', 'semanal') NOT NULL DEFAULT 'rodizio',
  `dias_por_pessoa` SMALLINT UNSIGNED NOT NULL DEFAULT 1,   -- só rodízio
  `data_inicio` DATE DEFAULT NULL,                          -- âncora do rodízio

  FOREIGN KEY (paciente_id) REFERENCES paciente(id) ON DELETE CASCADE,
  UNIQUE KEY unique_padrao_turno (paciente_id, turno)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `rodizio_item` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `padrao_id` INT NOT NULL,
  `ordem` SMALLINT UNSIGNED NOT NULL DEFAULT 0,
  `cuidador_id` INT NOT NULL,

  FOREIGN KEY (padrao_id) REFERENCES padrao_turno(id) ON DELETE CASCADE,
  FOREIGN KEY (cuidador_id) REFERENCES usuario(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `semanal_item` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `padrao_id` INT NOT NULL,
  `dia_semana` SMALLINT UNSIGNED NOT NULL,   -- 0=Seg ... 6=Dom
  `cuidador_id` INT DEFAULT NULL,            -- NULL = folga

  FOREIGN KEY (padrao_id) REFERENCES padrao_turno(id) ON DELETE CASCADE,
  FOREIGN KEY (cuidador_id) REFERENCES usuario(id) ON DELETE SET NULL,
  UNIQUE KEY unique_semanal_dia (padrao_id, dia_semana)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `excecao_dia` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `paciente_id` INT NOT NULL,
  `data` DATE NOT NULL,
  `turno` ENUM('manha', 'tarde', 'noite') NOT NULL,
  `cuidador_id` INT DEFAULT NULL,            -- NULL = folga

  FOREIGN KEY (paciente_id) REFERENCES paciente(id) ON DELETE CASCADE,
  FOREIGN KEY (cuidador_id) REFERENCES usuario(id) ON DELETE SET NULL,
  UNIQUE KEY unique_excecao_dia (paciente_id, data, turno)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- =====================================================
-- TABELA: ANOTACAO (Prontuário - anotações manuais do dia)
-- A linha do tempo do prontuário também agrega medicamentos tomados e
-- consultas realizadas, mas esses vêm das tabelas medicamento_tomado e
-- consulta; aqui ficam apenas as anotações registradas manualmente.
-- =====================================================
CREATE TABLE `anotacao` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `paciente_id` INT NOT NULL,
  `data_hora` DATETIME(6) NOT NULL,
  `titulo` VARCHAR(255) NOT NULL,
  `descricao` TEXT,
  `autor_id` INT DEFAULT NULL,                -- quem registrou (familiar/cuidador)
  `data_criacao` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),

  INDEX idx_anotacao_pac_data (paciente_id, data_hora),
  FOREIGN KEY (paciente_id) REFERENCES paciente(id) ON DELETE CASCADE,
  FOREIGN KEY (autor_id) REFERENCES usuario(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- =====================================================
-- ÍNDICES ADICIONAIS PARA PERFORMANCE
-- =====================================================

CREATE INDEX idx_usuario_ativo ON usuario(is_active);
CREATE INDEX idx_paciente_ativo ON paciente(ativo);
CREATE INDEX idx_participacao_usuario_paciente ON participacao(usuario_id, paciente_id);
CREATE INDEX idx_plantao_cuidador_data ON plantao(cuidador_id, data_plantao);
CREATE INDEX idx_medicamento_status ON medicamento(status, data_inicio);

-- =====================================================
-- VIEWS ÚTEIS (CORRIGIDAS)
-- =====================================================

-- View: Pacientes de um familiar
CREATE OR REPLACE VIEW vw_pacientes_familiar AS
SELECT 
  p.id,
  p.nome,
  p.data_nascimento,
  p.endereco,
  u.id as familiar_id,
  u.email as familiar_email
FROM paciente p
INNER JOIN usuario u ON p.familiar_responsavel_id = u.id
WHERE p.ativo = TRUE;

-- View: Medicamentos ativos de um paciente (CORRIGIDA)
CREATE OR REPLACE VIEW vw_medicamentos_ativos AS
SELECT
  m.id,
  p.id as paciente_id,
  p.nome as paciente,
  m.nome as medicamento,
  m.dosagem,
  m.frequencia,
  m.horarios,
  m.quantidade_dose,
  m.medico,
  m.data_inicio,
  m.data_fim
FROM medicamento m
INNER JOIN paciente p ON m.paciente_id = p.id
WHERE m.status = 'ativo' AND (m.data_fim IS NULL OR m.data_fim >= CURDATE());

-- View: Próximas consultas (CORRIGIDA)
CREATE OR REPLACE VIEW vw_proximas_consultas AS
SELECT
  c.id,
  c.paciente_id,
  p.nome as paciente,
  c.tipo,
  c.titulo,
  md.nome as profissional,
  c.data_hora,
  c.observacao,
  DATEDIFF(c.data_hora, NOW()) as dias_para_consulta
FROM consulta c
INNER JOIN paciente p ON c.paciente_id = p.id
LEFT JOIN medico md ON c.medico_id = md.id
WHERE c.status = 'agendada' AND c.data_hora >= NOW()
ORDER BY c.data_hora ASC;

-- View: Horas trabalhadas por cuidador (mensal) (CORRIGIDA)
CREATE OR REPLACE VIEW vw_horas_trabalhadas_mes AS
SELECT 
  YEAR(pl.data_plantao) as ano,
  MONTH(pl.data_plantao) as mes,
  pl.cuidador_id,
  u.first_name as cuidador_nome,
  u.email as cuidador_email,
  COUNT(DISTINCT pl.id) as total_plantoes,
  COALESCE(SUM(CAST(pl.duracao_horas AS DECIMAL(10,2))), 0) as total_horas
FROM plantao pl
INNER JOIN usuario u ON pl.cuidador_id = u.id
WHERE pl.status = 'fechado'
GROUP BY YEAR(pl.data_plantao), MONTH(pl.data_plantao), pl.cuidador_id, u.first_name, u.email;

-- =====================================================
-- STORED PROCEDURES
-- =====================================================

-- Procedure: Calcular duração do plantão
DELIMITER $$

CREATE PROCEDURE sp_calcular_duracao_plantao(IN plantao_id INT)
BEGIN
  UPDATE plantao
  SET duracao_horas = (TIME_TO_SEC(TIMEDIFF(hora_saida, hora_entrada)) / 3600)
  WHERE id = plantao_id AND hora_saida IS NOT NULL AND hora_entrada IS NOT NULL;
END$$

DELIMITER ;

-- =====================================================
-- TRIGGERS (CORRIGIDOS)
-- =====================================================

-- Trigger: Calcular duração quando plantão é fechado (USAR BEFORE UPDATE)
DELIMITER $$

CREATE TRIGGER trg_calcular_duracao_plantao
BEFORE UPDATE ON plantao
FOR EACH ROW
BEGIN
  IF NEW.status = 'fechado' AND OLD.status != 'fechado' AND NEW.hora_saida IS NOT NULL AND NEW.hora_entrada IS NOT NULL THEN
    SET NEW.duracao_horas = (TIME_TO_SEC(TIMEDIFF(NEW.hora_saida, NEW.hora_entrada)) / 3600);
  END IF;
END$$

DELIMITER ;

-- Trigger: Registrar atividade quando plantão é aberto (USAR AFTER UPDATE)
DELIMITER $$

CREATE TRIGGER trg_registrar_atividade_plantao_aberto
AFTER UPDATE ON plantao
FOR EACH ROW
BEGIN
  IF NEW.status = 'aberto' AND OLD.status != 'aberto' THEN
    INSERT INTO atividade (paciente_id, usuario_id, tipo, descricao, data_hora)
    VALUES (NEW.paciente_id, NEW.cuidador_id, 'plantao_aberto', 
            CONCAT('Plantão aberto por ', (SELECT first_name FROM usuario WHERE id = NEW.cuidador_id)), 
            NOW());
  END IF;
END$$

DELIMITER ;

-- =====================================================
-- CONSTRAINTS E VALIDAÇÕES
-- =====================================================

-- Validação: Consulta deve ser no futuro (comentado para permitir testes)
-- ALTER TABLE consulta 
-- ADD CONSTRAINT chk_consulta_data CHECK (data_hora >= NOW());

-- Validação: Data fim do medicamento deve ser posterior a data início
ALTER TABLE medicamento
ADD CONSTRAINT chk_medicamento_datas CHECK (data_fim IS NULL OR data_fim >= data_inicio);

-- Validação: Hora de saída deve ser posterior a hora de entrada
ALTER TABLE plantao 
ADD CONSTRAINT chk_plantao_horas CHECK (hora_saida IS NULL OR hora_entrada IS NULL OR hora_saida > hora_entrada);

-- =====================================================
-- DADOS DE EXEMPLO
-- =====================================================

-- Inserir um usuário familiar
INSERT INTO usuario (email, password, first_name, last_name, tipo_usuario, cpf, telefone, endereco)
VALUES ('maria@example.com', 'senha_hash_aqui', 'Maria', 'Silva', 'familiar', '12345678901', '21987654321', 'Rua A, 123');

-- Inserir um usuário cuidador
INSERT INTO usuario (email, password, first_name, last_name, tipo_usuario, cpf, telefone, endereco)
VALUES ('joao@example.com', 'senha_hash_aqui', 'João', 'Santos', 'cuidador', '98765432101', '21912345678', 'Rua B, 456');

-- Inserir paciente
INSERT INTO paciente (nome, cpf, data_nascimento, familiar_responsavel_id, endereco, condicoes_saude, alergias)
VALUES ('Conceição Silva', '11111111111', '1950-05-15', 1, 'Rua C, 789', 'Diabetes', 'Penicilina');

-- Inserir médico (id 1) e laboratório (id 2), vinculados ao paciente
INSERT INTO medico (paciente_id, nome, tipo, crm_cnpj, especialidade, telefone, email, endereco, cidade, uf)
VALUES (1, 'Dr. Carlos Silva', 'medico', '123456/SP', 'Cardiologia', '21988888888', 'carlos@clinica.com', 'Av. Paulista, 1000', 'São Paulo', 'SP');
INSERT INTO medico (paciente_id, nome, tipo, crm_cnpj, especialidade, telefone, email, endereco, cidade, uf)
VALUES (1, 'Laboratório São Lucas', 'laboratorio', '12.345.678/0001-90', 'Exames', '2133334444', 'contato@saolucas.com', 'Rua das Flores, 50', 'São Paulo', 'SP');

-- Inserir consulta (médico escolhido = id 1; agendada pela cuidadora, usuario id 2)
INSERT INTO consulta (paciente_id, medico_id, tipo, titulo, data_hora, observacao, status, agendada_por_id)
VALUES (1, 1, 'consulta', 'Cardiologia', '2026-06-20 14:30:00', 'Acompanhamento cardiológico de rotina', 'agendada', 2);

-- Inserir exame (laboratório escolhido = id 2)
INSERT INTO consulta (paciente_id, medico_id, tipo, titulo, data_hora, observacao, status, agendada_por_id)
VALUES (1, 2, 'exame', 'Eletrocardiograma', '2026-06-25 09:00:00', 'Comparecer em jejum. Levar documentos pessoais e cartão de convênio.', 'agendada', 1);

-- Inserir a EQUIPE do paciente (participacao — exige contas já cadastradas):
--   - o familiar responsável (usuario 1) como familiar, vínculo Filha (aceito);
--   - a cuidadora (usuario 2) como cuidador (aceito, com permissão de escrita).
INSERT INTO participacao (usuario_id, paciente_id, tipo_participacao, vinculo, status_convite, token, data_resposta, permissao_leitura, permissao_escrita)
VALUES (1, 1, 'familiar', 'Filha', 'aceito', 'tok_familiar_0001', NOW(), TRUE, TRUE);
INSERT INTO participacao (usuario_id, paciente_id, tipo_participacao, vinculo, status_convite, token, data_resposta, permissao_leitura, permissao_escrita)
VALUES (2, 1, 'cuidador', '', 'aceito', 'tok_cuidador_0002', NOW(), TRUE, TRUE);

-- Inserir medicamento (modelo enxuto: já com posologia e período de uso)
INSERT INTO medicamento (paciente_id, nome, dosagem, forma_farmaceutica, frequencia, horarios, quantidade_dose, medico, data_inicio, data_fim, observacoes, status)
VALUES (1, 'Losartana', '50mg', 'Comprimido', '2x ao dia', '08:00,20:00', '1 comprimido', 'Dr. Carlos', '2026-01-01', NULL, 'Tomar com água, de manhã', 'ativo');

-- Registrar uma dose como tomada (dose prevista p/ 08:00 de hoje da Losartana),
-- marcada pela cuidadora (usuario id 2)
INSERT INTO medicamento_tomado (medicamento_id, data, horario_previsto, tomado, tomado_em, marcado_por_id)
VALUES (1, CURDATE(), '08:00', TRUE, NOW(), 2);

-- =====================================================
-- VERIFICAÇÃO FINAL
-- =====================================================

SELECT 'Banco de dados criado com sucesso!' as status;

-- Ver tabelas criadas
SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_SCHEMA = 'cuidacare_db' ORDER BY TABLE_NAME;

-- Ver dados de exemplo
SELECT COUNT(*) as total_usuarios FROM usuario;
SELECT COUNT(*) as total_pacientes FROM paciente;
SELECT COUNT(*) as total_medicamentos FROM medicamento;
SELECT COUNT(*) as total_doses_tomadas FROM medicamento_tomado WHERE tomado = TRUE;

-- Testar view
SELECT * FROM vw_medicamentos_ativos;

-- =====================================================
-- FIM DO SCRIPT - TUDO OK!
-- =====================================================