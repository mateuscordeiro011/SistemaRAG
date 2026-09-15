-- ============================================
-- RAG SYSTEM - INIT.SQL
-- Script de inicialização da base de dados MySQL
-- Executado automaticamente quando o container MySQL é iniciado pela primeira vez
-- ============================================

-- Criar banco de dados se não existir
CREATE DATABASE IF NOT EXISTS sistema_rag 
    CHARACTER SET utf8mb4 
    COLLATE utf8mb4_unicode_ci;

-- Criar usuário e conceder permissões
CREATE USER IF NOT EXISTS 'rag_user'@'%' IDENTIFIED BY 'rag_password';
GRANT ALL PRIVILEGES ON sistema_rag.* TO 'rag_user'@'%';
FLUSH PRIVILEGES;

-- Usar o banco de dados
USE sistema_rag;

-- ============================================
-- 1. TABELA: CLIENTES (Tenants)
-- ============================================
CREATE TABLE IF NOT EXISTS clientes (
    id INT PRIMARY KEY AUTO_INCREMENT,
    nome VARCHAR(255) NOT NULL UNIQUE,
    empresa VARCHAR(255) NOT NULL,
    descricao TEXT,
    ativo BOOLEAN DEFAULT TRUE,
    data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    data_atualizacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_nome (nome),
    INDEX idx_ativo (ativo)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================
-- 2. TABELA: DOCUMENTOS (Knowledge Base Files)
-- ============================================
CREATE TABLE IF NOT EXISTS documentos (
    id INT PRIMARY KEY AUTO_INCREMENT,
    cliente_id INT NOT NULL,
    nome_arquivo VARCHAR(255) NOT NULL,
    tipo_arquivo VARCHAR(50) NOT NULL,
    caminho_arquivo VARCHAR(500) NOT NULL,
    tamanho_bytes INT,
    hash_arquivo VARCHAR(255) UNIQUE,
    conteudo_texto LONGTEXT,
    total_chunks INT DEFAULT 0,
    total_embeddings INT DEFAULT 0,
    contem_imagens BOOLEAN DEFAULT FALSE,
    total_imagens INT DEFAULT 0,
    metadata_midia JSON,
    status VARCHAR(50) DEFAULT 'PROCESSANDO',
    mensagem_erro TEXT,
    data_upload TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    data_processamento TIMESTAMP NULL,
    data_atualizacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (cliente_id) REFERENCES clientes(id) ON DELETE CASCADE,
    INDEX idx_cliente_id (cliente_id),
    INDEX idx_status (status),
    INDEX idx_hash (hash_arquivo),
    INDEX idx_contem_imagens (contem_imagens)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================
-- 3. TABELA: CHUNKS (Fragmentos de Documentos)
-- ============================================
CREATE TABLE IF NOT EXISTS chunks (
    id INT PRIMARY KEY AUTO_INCREMENT,
    documento_id INT NOT NULL,
    numero_chunk INT NOT NULL,
    conteudo TEXT NOT NULL,
    tamanho_caracteres INT,
    pagina INT,
    data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (documento_id) REFERENCES documentos(id) ON DELETE CASCADE,
    INDEX idx_documento_id (documento_id),
    INDEX idx_numero_chunk (numero_chunk),
    UNIQUE KEY uk_documento_chunk (documento_id, numero_chunk)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================
-- 4. TABELA: EMBEDDINGS (Vector Storage)
-- ============================================
CREATE TABLE IF NOT EXISTS embeddings (
    id INT PRIMARY KEY AUTO_INCREMENT,
    chunk_id INT NOT NULL UNIQUE,
    vetor LONGBLOB NOT NULL,
    dimensao INT NOT NULL,
    modelo VARCHAR(100) NOT NULL,
    data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (chunk_id) REFERENCES chunks(id) ON DELETE CASCADE,
    INDEX idx_chunk_id (chunk_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================
-- 5. TABELA: CANAIS (Communication Channels)
-- ============================================
CREATE TABLE IF NOT EXISTS canais (
    id INT PRIMARY KEY AUTO_INCREMENT,
    nome VARCHAR(100) NOT NULL UNIQUE,
    descricao VARCHAR(255),
    ativo BOOLEAN DEFAULT TRUE,
    data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Inserir canais padrão
INSERT IGNORE INTO canais (nome, descricao) VALUES
('WhatsApp', 'Mensagens via Meta Cloud API'),
('Outlook', 'Emails via Microsoft Graph API'),
('Email', 'Emails diretos'),
('Chat', 'Chat web integrado');

-- ============================================
-- 6. TABELA: MENSAGENS_ATENDIMENTO (Core Transaction Table)
-- ============================================
CREATE TABLE IF NOT EXISTS mensagens_atendimento (
    id INT PRIMARY KEY AUTO_INCREMENT,
    cliente_id INT NOT NULL,
    canal_id INT NOT NULL,
    identificador_externo VARCHAR(255),
    pergunta TEXT NOT NULL,
    idioma VARCHAR(10) DEFAULT 'pt-BR',
    chunks_recuperados INT DEFAULT 0,
    score_relevancia DECIMAL(5, 4) DEFAULT 0,
    tempo_processamento_ms INT DEFAULT 0,
    resposta_ia TEXT,
    resposta_editada TEXT,
    modelo_ia VARCHAR(100) DEFAULT 'gpt-3.5-turbo',
    tokens_prompt INT DEFAULT 0,
    tokens_completion INT DEFAULT 0,
    custo_api DECIMAL(10, 6) DEFAULT 0,
    imagem_url VARCHAR(1000),
    imagem_sugerida_id INT,
    imagem_aprovada BOOLEAN DEFAULT FALSE,
    anexos_gerados JSON,
    necessita_visual BOOLEAN DEFAULT FALSE,
    status VARCHAR(50) DEFAULT 'RECEBIDA',
    operador_id INT,
    motivo_rejeicao VARCHAR(500),
    data_aprovacao TIMESTAMP NULL,
    feedback_usuario VARCHAR(500),
    score_satisfacao INT DEFAULT 0,
    data_recebimento TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    data_processamento TIMESTAMP NULL,
    data_envio TIMESTAMP NULL,
    data_atualizacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (cliente_id) REFERENCES clientes(id) ON DELETE CASCADE,
    FOREIGN KEY (canal_id) REFERENCES canais(id),
    FOREIGN KEY (imagem_sugerida_id) REFERENCES midia_documentos(id) ON DELETE SET NULL,
    INDEX idx_cliente_id (cliente_id),
    INDEX idx_status (status),
    INDEX idx_data_recebimento (data_recebimento),
    INDEX idx_identificador_externo (identificador_externo),
    INDEX idx_operador_id (operador_id),
    INDEX idx_necessita_visual (necessita_visual)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================
-- 7. TABELA: MIDIA_DOCUMENTOS (Imagens e Anexos Extraídos)
-- ============================================
CREATE TABLE IF NOT EXISTS midia_documentos (
    id INT PRIMARY KEY AUTO_INCREMENT,
    documento_id INT NOT NULL,
    tipo_midia VARCHAR(50) NOT NULL,
    caminho_arquivo VARCHAR(500) NOT NULL,
    url_publica VARCHAR(1000),
    nome_arquivo VARCHAR(255),
    tamanho_bytes INT,
    mime_type VARCHAR(100),
    pagina INT,
    descricao TEXT,
    score_relevancia DECIMAL(5, 4) DEFAULT 0,
    data_extracao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    data_atualizacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (documento_id) REFERENCES documentos(id) ON DELETE CASCADE,
    INDEX idx_documento_id (documento_id),
    INDEX idx_tipo_midia (tipo_midia),
    INDEX idx_pagina (pagina),
    INDEX idx_relevancia (score_relevancia)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================
-- 8. TABELA: AUDITORIA
-- ============================================
CREATE TABLE IF NOT EXISTS auditoria (
    id INT PRIMARY KEY AUTO_INCREMENT,
    mensagem_atendimento_id INT,
    acao VARCHAR(100) NOT NULL,
    usuario_id INT,
    descricao TEXT,
    dados_anteriores JSON,
    dados_novos JSON,
    data_acao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (mensagem_atendimento_id) REFERENCES mensagens_atendimento(id) ON DELETE CASCADE,
    INDEX idx_mensagem_id (mensagem_atendimento_id),
    INDEX idx_data_acao (data_acao)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================
-- 9. TABELA: USUARIOS (Para controle de aprovações)
-- ============================================
CREATE TABLE IF NOT EXISTS usuarios (
    id INT PRIMARY KEY AUTO_INCREMENT,
    username VARCHAR(100) NOT NULL UNIQUE,
    email VARCHAR(255) NOT NULL UNIQUE,
    senha_hash VARCHAR(255) NOT NULL,
    nome_completo VARCHAR(255),
    papel VARCHAR(50) DEFAULT 'operador',
    ativo BOOLEAN DEFAULT TRUE,
    data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ultimo_login TIMESTAMP NULL,
    INDEX idx_username (username),
    INDEX idx_papel (papel)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================
-- 10. TABELA: ESTATISTICAS (Pré-computadas para Dashboard)
-- ============================================
CREATE TABLE IF NOT EXISTS estatisticas (
    id INT PRIMARY KEY AUTO_INCREMENT,
    cliente_id INT,
    data DATE NOT NULL,
    total_mensagens INT DEFAULT 0,
    mensagens_aprovadas INT DEFAULT 0,
    mensagens_rejeitadas INT DEFAULT 0,
    tempo_medio_processamento_ms INT DEFAULT 0,
    score_satisfacao_medio DECIMAL(3, 2) DEFAULT 0,
    total_tokens_utilisados INT DEFAULT 0,
    custo_total_api DECIMAL(10, 6) DEFAULT 0,
    data_atualizacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (cliente_id) REFERENCES clientes(id) ON DELETE CASCADE,
    INDEX idx_cliente_data (cliente_id, data),
    UNIQUE KEY uk_cliente_data (cliente_id, data)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================
-- ÍNDICES DE PERFORMANCE
-- ============================================
ALTER TABLE mensagens_atendimento ADD FULLTEXT INDEX ft_pergunta (pergunta);
ALTER TABLE chunks ADD FULLTEXT INDEX ft_conteudo (conteudo);

-- ============================================
-- DADOS INICIAIS PARA TESTE
-- ============================================
INSERT IGNORE INTO clientes (nome, empresa, descricao) VALUES
('Cliente Teste', 'Empresa Demo Ltda', 'Cliente de teste para desenvolvimento');

COMMIT;
