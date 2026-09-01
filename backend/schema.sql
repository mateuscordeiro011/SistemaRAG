-- ============================================
-- RAG SYSTEM DATABASE SCHEMA
-- ============================================
-- Este schema define a estrutura completa do sistema:
-- - Clientes/Empresas
-- - Documentos de conhecimento
-- - Embeddings vetoriais
-- - Mensagens de atendimento com histórico

USE rag_system_db;

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
    tipo_arquivo VARCHAR(50) NOT NULL, -- PDF, DOCX, XLSX, TXT
    caminho_arquivo VARCHAR(500) NOT NULL,
    tamanho_bytes INT,
    hash_arquivo VARCHAR(255) UNIQUE, -- Para evitar duplicatas
    conteudo_texto LONGTEXT,
    total_chunks INT DEFAULT 0,
    total_embeddings INT DEFAULT 0,
    
    -- MULTIMODALIDADE: Campos para suporte a imagens e mídia
    contem_imagens BOOLEAN DEFAULT FALSE, -- Indica se o documento contém imagens/diagramas
    total_imagens INT DEFAULT 0, -- Contador de imagens extraídas
    metadata_midia JSON, -- Armazena dados sobre mídia: {imagens: [{pagina: 1, tipo: "diagram", tamanho: 100000}]}
    
    status VARCHAR(50) DEFAULT 'PROCESSANDO', -- PROCESSANDO, SUCESSO, ERRO
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
-- 3.5 TABELA: MIDIA_DOCUMENTOS (Imagens e Anexos Extraídos)
-- ============================================
CREATE TABLE IF NOT EXISTS midia_documentos (
    id INT PRIMARY KEY AUTO_INCREMENT,
    documento_id INT NOT NULL,
    tipo_midia VARCHAR(50) NOT NULL, -- image, diagram, table, chart, etc
    caminho_arquivo VARCHAR(500) NOT NULL, -- Caminho relativo ao servidor
    url_publica VARCHAR(1000), -- URL acessível externamente (para WhatsApp/Outlook)
    nome_arquivo VARCHAR(255),
    tamanho_bytes INT,
    mime_type VARCHAR(100), -- image/png, image/jpeg, etc
    pagina INT, -- Página do documento onde a mídia foi extraída
    descricao TEXT, -- Descrição automática ou manual da imagem
    score_relevancia DECIMAL(5, 4) DEFAULT 0, -- Score de relevância para a query (0.0-1.0)
    data_extracao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    data_atualizacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (documento_id) REFERENCES documentos(id) ON DELETE CASCADE,
    INDEX idx_documento_id (documento_id),
    INDEX idx_tipo_midia (tipo_midia),
    INDEX idx_pagina (pagina),
    INDEX idx_relevancia (score_relevancia)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================
-- 4. TABELA: EMBEDDINGS (Vector Storage - Serializado em JSON)
-- Nota: Para máximo desempenho em produção, considere usar pgvector (PostgreSQL)
-- ou Pinecone/Weaviate para embeddings de alta dimensão
-- ============================================
CREATE TABLE IF NOT EXISTS embeddings (
    id INT PRIMARY KEY AUTO_INCREMENT,
    chunk_id INT NOT NULL UNIQUE,
    vetor LONGBLOB NOT NULL, -- Armazenado como numpy array serializado (pickle)
    dimensao INT NOT NULL, -- Ex: 1536 para OpenAI embeddings
    modelo VARCHAR(100) NOT NULL, -- Ex: text-embedding-ada-002
    data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (chunk_id) REFERENCES chunks(id) ON DELETE CASCADE,
    INDEX idx_chunk_id (chunk_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================
-- 5. TABELA: CANAIS (Communication Channels)
-- ============================================
CREATE TABLE IF NOT EXISTS canais (
    id INT PRIMARY KEY AUTO_INCREMENT,
    nome VARCHAR(100) NOT NULL UNIQUE, -- WhatsApp, Outlook, Email, etc
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
-- Status flow: RECEBIDA → PROCESSANDO → AGUARDANDO_APROVACAO → APROVADA/REJEITADA → ENVIADA/DESCARTADA
-- ============================================
CREATE TABLE IF NOT EXISTS mensagens_atendimento (
    id INT PRIMARY KEY AUTO_INCREMENT,
    cliente_id INT NOT NULL,
    canal_id INT NOT NULL,
    identificador_externo VARCHAR(255), -- WhatsApp message ID, Outlook message ID, etc
    
    -- Entrada (Pergunta)
    pergunta TEXT NOT NULL,
    idioma VARCHAR(10) DEFAULT 'pt-BR',
    
    -- Processamento RAG
    chunks_recuperados INT DEFAULT 0,
    score_relevancia DECIMAL(5, 4) DEFAULT 0, -- 0.0 a 1.0
    tempo_processamento_ms INT DEFAULT 0,
    
    -- Resposta IA (Antes da Aprovação)
    resposta_ia TEXT,
    resposta_editada TEXT, -- Resposta após edição do operador
    modelo_ia VARCHAR(100) DEFAULT 'gpt-3.5-turbo',
    tokens_prompt INT DEFAULT 0,
    tokens_completion INT DEFAULT 0,
    custo_api DECIMAL(10, 6) DEFAULT 0,
    
    -- MULTIMODALIDADE: Campos para imagens e anexos
    imagem_url VARCHAR(1000), -- URL da imagem sugerida pela IA
    imagem_sugerida_id INT, -- FK para midia_documentos
    imagem_aprovada BOOLEAN DEFAULT FALSE, -- Operador aprovou a imagem sugerida
    anexos_gerados JSON, -- Array de URLs/caminhos de anexos aprovados: [{url: "...", tipo: "image", descricao: "..."}]
    necessita_visual BOOLEAN DEFAULT FALSE, -- Flag se a IA identificou que a resposta precisa de elemento visual
    
    -- Aprovação Humana
    status VARCHAR(50) DEFAULT 'RECEBIDA', -- RECEBIDA, PROCESSANDO, AGUARDANDO_APROVACAO, APROVADA, REJEITADA, ENVIADA, ERRO
    operador_id INT, -- ID do usuário que aprovou/rejeitou
    motivo_rejeicao VARCHAR(500),
    data_aprovacao TIMESTAMP NULL,
    
    -- Feedback & Análise
    feedback_usuario VARCHAR(500),
    score_satisfacao INT DEFAULT 0, -- 1-5
    
    -- Timestamps
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
-- 7. TABELA: AUDITORIA
-- ============================================
CREATE TABLE IF NOT EXISTS auditoria (
    id INT PRIMARY KEY AUTO_INCREMENT,
    mensagem_atendimento_id INT,
    acao VARCHAR(100) NOT NULL, -- CRIAÇÃO, EDIÇÃO, APROVAÇÃO, REJEIÇÃO, ENVIO
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
-- 8. TABELA: USUARIOS (Para controle de aprovações)
-- ============================================
CREATE TABLE IF NOT EXISTS usuarios (
    id INT PRIMARY KEY AUTO_INCREMENT,
    username VARCHAR(100) NOT NULL UNIQUE,
    email VARCHAR(255) NOT NULL UNIQUE,
    senha_hash VARCHAR(255) NOT NULL,
    nome_completo VARCHAR(255),
    papel VARCHAR(50) DEFAULT 'operador', -- admin, supervisor, operador
    ativo BOOLEAN DEFAULT TRUE,
    data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ultimo_login TIMESTAMP NULL,
    INDEX idx_username (username),
    INDEX idx_papel (papel)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================
-- 9. TABELA: ESTATISTICAS (Pré-computadas para Dashboard)
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
-- VIEWS ÚTEIS PARA CONSULTAS COMUNS
-- ============================================

-- View: Fila de Aprovação Pendente
CREATE OR REPLACE VIEW vw_fila_aprovacao AS
SELECT 
    m.id,
    c.nome as cliente,
    c.empresa,
    ch.nome as canal,
    m.pergunta,
    m.resposta_ia,
    m.status,
    m.data_recebimento,
    m.tempo_processamento_ms,
    m.score_relevancia,
    m.chunks_recuperados
FROM mensagens_atendimento m
JOIN clientes c ON m.cliente_id = c.id
JOIN canais ch ON m.canal_id = ch.id
WHERE m.status = 'AGUARDANDO_APROVACAO'
ORDER BY m.data_recebimento ASC;

-- View: Documentos Processados por Cliente
CREATE OR REPLACE VIEW vw_documentos_cliente AS
SELECT 
    c.id,
    c.nome,
    c.empresa,
    COUNT(d.id) as total_documentos,
    SUM(d.total_chunks) as total_chunks,
    SUM(d.total_embeddings) as total_embeddings,
    SUM(d.tamanho_bytes) as tamanho_total_bytes,
    MAX(d.data_processamento) as ultimo_processamento
FROM clientes c
LEFT JOIN documentos d ON c.id = d.cliente_id AND d.status = 'SUCESSO'
GROUP BY c.id, c.nome, c.empresa;

-- View: Estatísticas de Performance
CREATE OR REPLACE VIEW vw_performance_ia AS
SELECT 
    DATE(m.data_recebimento) as data,
    COUNT(*) as total_mensagens,
    SUM(CASE WHEN m.status = 'APROVADA' THEN 1 ELSE 0 END) as aprovadas,
    SUM(CASE WHEN m.status = 'REJEITADA' THEN 1 ELSE 0 END) as rejeitadas,
    ROUND(AVG(m.tempo_processamento_ms), 2) as tempo_medio_ms,
    ROUND(AVG(m.score_relevancia), 3) as relevancia_media,
    ROUND(AVG(m.score_satisfacao), 2) as satisfacao_media,
    SUM(m.tokens_prompt + m.tokens_completion) as total_tokens
FROM mensagens_atendimento m
WHERE m.status IN ('APROVADA', 'REJEITADA', 'ENVIADA')
GROUP BY DATE(m.data_recebimento)
ORDER BY data DESC;

-- ============================================
-- ÍNDICES ADICIONAIS PARA PERFORMANCE
-- ============================================
ALTER TABLE mensagens_atendimento ADD FULLTEXT INDEX ft_pergunta (pergunta);
ALTER TABLE chunks ADD FULLTEXT INDEX ft_conteudo (conteudo);

-- ============================================
-- COMENTÁRIOS E DOCUMENTAÇÃO
-- ============================================
ALTER TABLE documentos COMMENT = 'Armazena metadados dos documentos de conhecimento com suporte a multimodalidade (textos e imagens)';
ALTER TABLE chunks COMMENT = 'Fragmentos dos documentos processados para RAG (Retrieval Augmented Generation)';
ALTER TABLE midia_documentos COMMENT = 'Imagens, diagramas e gráficos extraídos dos documentos para consulta multimodal';
ALTER TABLE embeddings COMMENT = 'Vetores de embeddings de alta dimensão para busca semântica';
ALTER TABLE mensagens_atendimento COMMENT = 'Log completo de todas as interações com histórico de aprovação, suportando anexos visuais';

COMMIT;
