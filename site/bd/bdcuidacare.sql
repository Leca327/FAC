-- =====================================================
-- BANCO DE DADOS: CUIDACARE
-- MYSQL 8.0+
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
  `telefone` VARCHAR(11),
  `endereco` VARCHAR(255),
  `data_criacao` DATETIME DEFAULT CURRENT_TIMESTAMP,
  `ativo` BOOLEAN DEFAULT TRUE,
  `is_staff` BOOLEAN DEFAULT FALSE,
  `is_superuser` BOOLEAN DEFAULT FALSE,
  `last_login` DATETIME NULL,
  
  INDEX idx_email (email),
  INDEX idx_tipo (tipo_usuario),
  INDEX idx_cpf (cpf)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- =====================================================
-- TABELA: FAMILIAR (Especialização de User)
-- =====================================================

CREATE TABLE `familiar` (
  `id` INT PRIMARY KEY,
  `vinculo` VARCHAR(100),  -- pai, filho, cônjuge, etc
  `usuario_id` INT UNIQUE NOT NULL,
  
  FOREIGN KEY (usuario_id) REFERENCES usuario(id) ON DELETE CASCADE,
  FOREIGN KEY (id) REFERENCES usuario(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- =====================================================
-- TABELA: CUIDADOR (Especialização de User)
-- =====================================================

CREATE TABLE `cuidador` (
  `id` INT PRIMARY KEY,
  `numero_registro` VARCHAR(50) UNIQUE,
  `especialidade` VARCHAR(150),
  `data_ultima_atividade` DATETIME,
  `usuario_id` INT UNIQUE NOT NULL,
  
  FOREIGN KEY (usuario_id) REFERENCES usuario(id) ON DELETE CASCADE,
  FOREIGN KEY (id) REFERENCES usuario(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- =====================================================
-- TABELA: PACIENTE
-- =====================================================

CREATE TABLE `paciente` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `nome` VARCHAR(255) NOT NULL,
  `cpf` VARCHAR(11) UNIQUE,
  `data_nascimento` DATE NOT NULL,
  `endereco` VARCHAR(255),
  `telefone` VARCHAR(11),
  `familiar_responsavel_id` INT NOT NULL,
  `condicoes_saude` TEXT,
  `alergias` TEXT,
  `foto` VARCHAR(255),
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
-- TABELA: PARTICIPACAO (Gerencia - Usuário e Paciente)
-- =====================================================

CREATE TABLE `participacao` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `usuario_id` INT NOT NULL,
  `paciente_id` INT NOT NULL,
  `tipo_participacao` ENUM('familiar', 'cuidador') NOT NULL,
  `status_convite` ENUM('pendente', 'aceito', 'rejeitado') DEFAULT 'pendente',
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
-- TABELA: CONSULTA (Marcar)
-- =====================================================

CREATE TABLE `consulta` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `paciente_id` INT NOT NULL,
  `medico_id` INT NOT NULL,
  `tipo_consulta` VARCHAR(100),  -- consulta, exame, ultrassom, etc
  `data_hora` DATETIME NOT NULL,
  `local` VARCHAR(255),
  `motivo` TEXT,
  `resultado` TEXT,
  `status` ENUM('agendada', 'realizada', 'cancelada') DEFAULT 'agendada',
  `proximo_agendamento` DATE,
  `familiar_marcou_id` INT NOT NULL,
  `data_criacao` DATETIME DEFAULT CURRENT_TIMESTAMP,
  
  FOREIGN KEY (paciente_id) REFERENCES paciente(id) ON DELETE CASCADE,
  FOREIGN KEY (medico_id) REFERENCES medico(id) ON DELETE RESTRICT,
  FOREIGN KEY (familiar_marcou_id) REFERENCES usuario(id) ON DELETE RESTRICT,
  INDEX idx_paciente (paciente_id),
  INDEX idx_data (data_hora),
  INDEX idx_status (status)
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
-- TABELA: DIARIO_PLANTAO (Registra e Possui)
-- =====================================================

CREATE TABLE `diario_plantao` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `plantao_id` INT NOT NULL,
  `cuidador_id` INT NOT NULL,
  `tipo_registro` ENUM('ocorrencia', 'medicacao', 'observacao', 'atividade') NOT NULL,
  `descricao` TEXT NOT NULL,
  `data_hora` DATETIME DEFAULT CURRENT_TIMESTAMP,
  `data_hora_edicao` DATETIME,
  `editavel` BOOLEAN DEFAULT TRUE,  -- desabilita edição após plantão fechado
  
  FOREIGN KEY (plantao_id) REFERENCES plantao(id) ON DELETE CASCADE,
  FOREIGN KEY (cuidador_id) REFERENCES usuario(id) ON DELETE RESTRICT,
  INDEX idx_plantao (plantao_id),
  INDEX idx_tipo (tipo_registro),
  INDEX idx_data_hora (data_hora)
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
-- ÍNDICES ADICIONAIS PARA PERFORMANCE
-- =====================================================

CREATE INDEX idx_usuario_ativo ON usuario(ativo);
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
  f.id as familiar_id,
  u.email as familiar_email
FROM paciente p
INNER JOIN usuario u ON p.familiar_responsavel_id = u.id
INNER JOIN familiar f ON f.usuario_id = u.id
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
  mc.nome as medico,
  mc.especialidade,
  c.data_hora,
  c.local,
  c.tipo_consulta,
  DATEDIFF(c.data_hora, NOW()) as dias_para_consulta
FROM consulta c
INNER JOIN paciente p ON c.paciente_id = p.id
INNER JOIN medico mc ON c.medico_id = mc.id
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

-- Trigger: Desabilitar edição do diário quando plantão é fechado
DELIMITER $$

CREATE TRIGGER trg_desabilitar_edicao_diario
AFTER UPDATE ON plantao
FOR EACH ROW
BEGIN
  IF NEW.status = 'fechado' AND OLD.status != 'fechado' THEN
    UPDATE diario_plantao
    SET editavel = FALSE
    WHERE plantao_id = NEW.id;
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

-- Inserir familiar
INSERT INTO familiar (id, vinculo, usuario_id) VALUES (1, 'filha', 1);

-- Inserir cuidador
INSERT INTO cuidador (id, numero_registro, especialidade, usuario_id) VALUES (2, 'COREN123456', 'Enfermagem', 2);

-- Inserir paciente
INSERT INTO paciente (nome, cpf, data_nascimento, familiar_responsavel_id, endereco, condicoes_saude, alergias)
VALUES ('Conceição Silva', '11111111111', '1950-05-15', 1, 'Rua C, 789', 'Diabetes', 'Penicilina');

-- Inserir médico (vinculado ao paciente)
INSERT INTO medico (paciente_id, nome, tipo, crm_cnpj, especialidade, telefone, email, endereco, cidade, uf)
VALUES (1, 'Dr. Carlos', 'medico', '123456/SP', 'Cardiologia', '21988888888', 'carlos@clinica.com', 'Av. Paulista, 1000', 'São Paulo', 'SP');

-- Inserir consulta
INSERT INTO consulta (paciente_id, medico_id, tipo_consulta, data_hora, local, motivo, familiar_marcou_id)
VALUES (1, 1, 'Consulta de Rotina', '2026-06-20 14:00:00', 'Clínica Centro', 'Acompanhamento Cardiológico', 1);

-- Inserir medicamento (modelo enxuto: já com posologia e período de uso)
INSERT INTO medicamento (paciente_id, nome, dosagem, forma_farmaceutica, frequencia, horarios, quantidade_dose, medico, data_inicio, data_fim, observacoes, status)
VALUES (1, 'Losartana', '50mg', 'Comprimido', '2x ao dia', '08:00,20:00', '1 comprimido', 'Dr. Carlos', '2026-01-01', NULL, 'Apenas em caso de dor ou febre', 'ativo');

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

-- Testar view
SELECT * FROM vw_medicamentos_ativos;

-- =====================================================
-- FIM DO SCRIPT - TUDO OK!
-- =====================================================