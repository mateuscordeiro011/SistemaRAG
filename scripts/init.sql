-- Script de Inicialização - SistemaRAG
-- Versão: 1.0
-- Data: 2024

-- Criar banco de dados
CREATE DATABASE IF NOT EXISTS sistema_rag;
USE sistema_rag;

-- ============================================
-- 1. TABELAS INDEPENDENTES (sem FK)
-- ============================================

-- Tabela de clientes
CREATE TABLE IF NOT EXISTS clientes (
  id INT PRIMARY KEY AUTO_INCREMENT,
  nome_cliente VARCHAR(255) NOT NULL UNIQUE,
  email VARCHAR(255),
  telefone VARCHAR(20),
  data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  ativo BOOLEAN DEFAULT TRUE,
  INDEX idx_nome (nome_cliente),
  INDEX idx_ativo (ativo)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Tabela de usuários/operadores
CREATE TABLE IF NOT EXISTS usuarios (
  id INT PRIMARY KEY AUTO_INCREMENT,
  cliente_id INT NOT NULL,
  nome VARCHAR(255) NOT NULL,
  email VARCHAR(255) UNIQUE,
  senha_hash VARCHAR(255) NOT NULL,
  papel ENUM('admin', 'operador', 'leitor') DEFAULT 'operador',
  ativo BOOLEAN DEFAULT TRUE,
  criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (cliente_id) REFERENCES clientes(id) ON DELETE CASCADE,
  INDEX idx_cliente (cliente_id),
  INDEX idx_papel (papel)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================
-- 2. TABELAS DE DOCUMENTOS/MÍDIA (sem FK)
-- ============================================

-- Tabela de documentos/mídia
CREATE TABLE IF NOT EXISTS midia_documentos (
  id INT PRIMARY KEY AUTO_INCREMENT,
  cliente_id INT NOT NULL,
  nome_original VARCHAR(255) NOT NULL,
  nome_armazenado VARCHAR(255) NOT NULL,
  caminho_arquivo VARCHAR(500),
  tipo_documento ENUM('pdf', 'docx', 'txt', 'md', 'outro') DEFAULT 'outro',
  tamanho_bytes BIGINT,
  status ENUM('ENVIADO', 'PROCESSANDO', 'INDEXADO', 'ERRO', 'DELETADO') DEFAULT 'ENVIADO',
  mensagem_erro TEXT,
  criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  atualizado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  deletado BOOLEAN DEFAULT FALSE,
  FOREIGN KEY (cliente_id) REFERENCES clientes(id) ON DELETE CASCADE,
  INDEX idx_cliente (cliente_id),
  INDEX idx_status (status),
  INDEX idx_criado (criado_em),
  FULLTEXT INDEX ft_nome (nome_original)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================
-- 3. TABELAS DE CHUNKS E EMBEDDINGS
-- ============================================

-- Tabela de chunks (pedaços de documento)
CREATE TABLE IF NOT EXISTS chunks (
  id INT PRIMARY KEY AUTO_INCREMENT,
  cliente_id INT NOT NULL,
  midia_documento_id INT NOT NULL,
  numero_pagina INT,
  conteudo_texto LONGTEXT NOT NULL,
  embedding_vector LONGBLOB,  -- Armazena embedding em binário
  tamanho_token INT,
  hash_conteudo VARCHAR(64),  -- SHA256 para deduplicação
  criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  deletado BOOLEAN DEFAULT FALSE,
  FOREIGN KEY (cliente_id) REFERENCES clientes(id) ON DELETE CASCADE,
  FOREIGN KEY (midia_documento_id) REFERENCES midia_documentos(id) ON DELETE CASCADE,
  INDEX idx_cliente (cliente_id),
  INDEX idx_documento (midia_documento_id),
  INDEX idx_hash (hash_conteudo),
  INDEX idx_deletado (deletado),
  UNIQUE KEY uk_hash_cliente (hash_conteudo, cliente_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================
-- 4. TABELAS DE MENSAGENS/ATENDIMENTO
-- ============================================

-- Tabela de mensagens de atendimento
CREATE TABLE IF NOT EXISTS mensagens_atendimento (
  id INT PRIMARY KEY AUTO_INCREMENT,
  cliente_id INT NOT NULL,
  usuario_id INT,
  pergunta TEXT NOT NULL,
  resposta LONGTEXT,
  canal ENUM('whatsapp', 'email', 'web', 'teste') DEFAULT 'web',
  status ENUM(
    'RECEBIDA',
    'PROCESSANDO_RAG',
    'AGUARDANDO_APROVACAO',
    'ENVIADA_AUTOMATICA',
    'ENVIADA_MANUAL',
    'REJEITADA',
    'ERRO_ENVIO'
  ) DEFAULT 'RECEBIDA',
  score_relevancia FLOAT,
  requer_aprovacao BOOLEAN DEFAULT TRUE,
  motivo_rejeicao TEXT,
  tentativas_envio INT DEFAULT 0,
  ultima_tentativa TIMESTAMP NULL,
  criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  processado_em TIMESTAMP NULL,
  enviado_em TIMESTAMP NULL,
  FOREIGN KEY (cliente_id) REFERENCES clientes(id) ON DELETE CASCADE,
  FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE SET NULL,
  INDEX idx_cliente (cliente_id),
  INDEX idx_status (status),
  INDEX idx_canal (canal),
  INDEX idx_criado (criado_em),
  INDEX idx_score (score_relevancia),
  FULLTEXT INDEX ft_pergunta_resposta (pergunta, resposta)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Tabela de rastreamento de chunks consultados (NOVO - para rastreabilidade)
CREATE TABLE IF NOT EXISTS resposta_chunks (
  id INT PRIMARY KEY AUTO_INCREMENT,
  mensagem_id INT NOT NULL,
  chunk_id INT NOT NULL,
  relevancia_score FLOAT NOT NULL,
  posicao INT NOT NULL,  -- Ordem de uso na resposta
  criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (mensagem_id) REFERENCES mensagens_atendimento(id) ON DELETE CASCADE,
  FOREIGN KEY (chunk_id) REFERENCES chunks(id) ON DELETE CASCADE,
  INDEX idx_mensagem (mensagem_id),
  INDEX idx_chunk (chunk_id),
  INDEX idx_relevancia (relevancia_score)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================
-- 5. TABELAS DE LOGS/AUDITORIA
-- ============================================

-- Tabela de logs de sistema
CREATE TABLE IF NOT EXISTS logs (
  id INT PRIMARY KEY AUTO_INCREMENT,
  cliente_id INT NOT NULL,
  mensagem_id INT,
  tipo ENUM('INFO', 'WARN', 'ERROR', 'DEBUG') DEFAULT 'INFO',
  descricao TEXT,
  dados_json JSON,
  origem VARCHAR(255),  -- Qual endpoint/função originou
  ip_origem VARCHAR(45),  -- IPv4 ou IPv6
  criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (cliente_id) REFERENCES clientes(id) ON DELETE CASCADE,
  FOREIGN KEY (mensagem_id) REFERENCES mensagens_atendimento(id) ON DELETE SET NULL,
  INDEX idx_cliente (cliente_id),
  INDEX idx_tipo (tipo),
  INDEX idx_criado (criado_em),
  INDEX idx_mensagem (mensagem_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Tabela de auditoria de alterações
CREATE TABLE IF NOT EXISTS auditoria (
  id INT PRIMARY KEY AUTO_INCREMENT,
  usuario_id INT,
  tabela_afetada VARCHAR(100),
  registro_id INT,
  operacao ENUM('INSERT', 'UPDATE', 'DELETE') NOT NULL,
  valores_antigos JSON,
  valores_novos JSON,
  ip_usuario VARCHAR(45),
  user_agent VARCHAR(500),
  criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE SET NULL,
  INDEX idx_usuario (usuario_id),
  INDEX idx_operacao (operacao),
  INDEX idx_criado (criado_em),
  INDEX idx_tabela (tabela_afetada)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================
-- 6. TABELAS DE CONFIGURAÇÃO
-- ============================================

-- Tabela de configurações por cliente
CREATE TABLE IF NOT EXISTS configuracoes (
  id INT PRIMARY KEY AUTO_INCREMENT,
  cliente_id INT NOT NULL UNIQUE,
  limiar_confianca FLOAT DEFAULT 0.75,
  max_chunks_resposta INT DEFAULT 5,
  modelo_embedding VARCHAR(100) DEFAULT 'sentence-transformers/all-MiniLM-L6-v2',
  modelo_rag VARCHAR(100) DEFAULT 'llama2',
  timeout_processamento INT DEFAULT 30,  -- segundos
  max_tentativas_envio INT DEFAULT 3,
  intervalo_retry_segundos INT DEFAULT 300,
  ativo BOOLEAN DEFAULT TRUE,
  criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  atualizado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  FOREIGN KEY (cliente_id) REFERENCES clientes(id) ON DELETE CASCADE,
  INDEX idx_cliente (cliente_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================
-- 7. VIEWS ÚTEIS
-- ============================================

-- View: Últimas mensagens por cliente
CREATE OR REPLACE VIEW vw_ultimas_mensagens AS
SELECT 
  m.id,
  m.cliente_id,
  m.pergunta,
  m.resposta,
  m.status,
  m.canal,
  m.score_relevancia,
  m.criado_em,
  COUNT(rc.id) as total_chunks_consultados
FROM mensagens_atendimento m
LEFT JOIN resposta_chunks rc ON m.id = rc.mensagem_id
WHERE m.deletado = FALSE
GROUP BY m.id
ORDER BY m.criado_em DESC;

-- View: Fila de aprovação
CREATE OR REPLACE VIEW vw_fila_aprovacao AS
SELECT 
  m.id,
  m.cliente_id,
  m.pergunta,
  m.resposta,
  m.score_relevancia,
  m.criado_em,
  c.nome_cliente
FROM mensagens_atendimento m
JOIN clientes c ON m.cliente_id = c.id
WHERE m.status = 'AGUARDANDO_APROVACAO'
  AND m.requer_aprovacao = TRUE
ORDER BY m.score_relevancia ASC, m.criado_em ASC;

-- View: Estatísticas de processamento
CREATE OR REPLACE VIEW vw_estatisticas_processamento AS
SELECT 
  c.id,
  c.nome_cliente,
  COUNT(m.id) as total_mensagens,
  SUM(CASE WHEN m.status = 'ENVIADA_AUTOMATICA' THEN 1 ELSE 0 END) as enviadas_automaticas,
  SUM(CASE WHEN m.status = 'ENVIADA_MANUAL' THEN 1 ELSE 0 END) as enviadas_manual,
  SUM(CASE WHEN m.status = 'AGUARDANDO_APROVACAO' THEN 1 ELSE 0 END) as aguardando_aprovacao,
  SUM(CASE WHEN m.status = 'REJEITADA' THEN 1 ELSE 0 END) as rejeitadas,
  AVG(m.score_relevancia) as score_medio,
  COUNT(md.id) as total_documentos,
  COUNT(ch.id) as total_chunks
FROM clientes c
LEFT JOIN mensagens_atendimento m ON c.id = m.cliente_id
LEFT JOIN midia_documentos md ON c.id = md.cliente_id
LEFT JOIN chunks ch ON c.id = ch.cliente_id
WHERE c.ativo = TRUE
GROUP BY c.id;

-- ============================================
-- 8. TRIGGERS PARA AUDITORIA
-- ============================================

DELIMITER //

-- Trigger: Log de alterações em mensagens
CREATE TRIGGER tr_log_mensagem_alteracao
AFTER UPDATE ON mensagens_atendimento
FOR EACH ROW
BEGIN
  INSERT INTO auditoria (
    tabela_afetada,
    registro_id,
    operacao,
    valores_antigos,
    valores_novos
  ) VALUES (
    'mensagens_atendimento',
    OLD.id,
    'UPDATE',
    JSON_OBJECT(
      'status', OLD.status,
      'resposta', OLD.resposta,
      'score_relevancia', OLD.score_relevancia
    ),
    JSON_OBJECT(
      'status', NEW.status,
      'resposta', NEW.resposta,
      'score_relevancia', NEW.score_relevancia
    )
  );
END //

-- Trigger: Log quando documento é deletado
CREATE TRIGGER tr_log_documento_deletado
BEFORE UPDATE ON midia_documentos
FOR EACH ROW
BEGIN
  IF NEW.deletado = TRUE AND OLD.deletado = FALSE THEN
    INSERT INTO logs (cliente_id, tipo, descricao, origem)
    VALUES (OLD.cliente_id, 'INFO', CONCAT('Documento deletado: ', OLD.nome_original), 'documento_delete');
  END IF;
END //

DELIMITER ;

-- ============================================
-- 9. INSERÇÕES DE DADOS INICIAIS (OPCIONAL)
-- ============================================

-- Cliente de teste
INSERT IGNORE INTO clientes (nome_cliente, email) 
VALUES ('cliente_teste', 'teste@exemplo.com');

-- Configuração padrão do cliente de teste
INSERT IGNORE INTO configuracoes (cliente_id, limiar_confianca) 
SELECT id, 0.75 FROM clientes WHERE nome_cliente = 'cliente_teste';

-- ============================================
-- 10. PROCEDURES ÚTEIS
-- ============================================

DELIMITER //

-- Procedure: Limpar mensagens antigas
CREATE PROCEDURE sp_limpar_mensagens_antigas(IN dias_retencao INT)
BEGIN
  DELETE FROM resposta_chunks
  WHERE mensagem_id IN (
    SELECT id FROM mensagens_atendimento
    WHERE criado_em < DATE_SUB(NOW(), INTERVAL dias_retencao DAY)
    AND status IN ('ENVIADA_AUTOMATICA', 'ENVIADA_MANUAL', 'REJEITADA')
  );
  
  DELETE FROM mensagens_atendimento
  WHERE criado_em < DATE_SUB(NOW(), INTERVAL dias_retencao DAY)
  AND status IN ('ENVIADA_AUTOMATICA', 'ENVIADA_MANUAL', 'REJEITADA');
END //

-- Procedure: Obter estatísticas de um cliente
CREATE PROCEDURE sp_stats_cliente(IN p_cliente_id INT)
BEGIN
  SELECT 
    COUNT(*) as total_mensagens,
    SUM(CASE WHEN status = 'ENVIADA_AUTOMATICA' THEN 1 ELSE 0 END) as enviadas_automaticas,
    SUM(CASE WHEN status = 'AGUARDANDO_APROVACAO' THEN 1 ELSE 0 END) as na_fila,
    AVG(score_relevancia) as score_medio
  FROM mensagens_atendimento
  WHERE cliente_id = p_cliente_id;
END //

DELIMITER ;

-- ============================================
-- FIM DO SCRIPT
-- ============================================