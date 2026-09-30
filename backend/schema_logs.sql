-- ============================================================================
-- SCHEMA SQL PARA LOGS DO SISTEMA
-- Adicionar ao arquivo backend/schema.sql
-- ============================================================================

-- Tabela para armazenar logs do sistema em tempo real
CREATE TABLE IF NOT EXISTS system_logs (
    id BIGINT AUTO_INCREMENT PRIMARY KEY COMMENT 'ID único do log',
    log_id VARCHAR(100) UNIQUE NOT NULL COMMENT 'ID único do log (timestamp)',
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT 'Quando o evento ocorreu',
    level ENUM('error', 'success', 'warning', 'info') NOT NULL COMMENT 'Severidade do log',
    channel VARCHAR(50) NOT NULL COMMENT 'Canal: rag, mysql, whatsapp, outlook, general',
    module VARCHAR(100) NOT NULL COMMENT 'Módulo do sistema que gerou o log',
    message TEXT NOT NULL COMMENT 'Mensagem descritiva do evento',
    duration_ms INT DEFAULT 0 COMMENT 'Tempo de execução em milissegundos',
    details JSON COMMENT 'Detalhes adicionais em JSON',
    
    -- Índices para performance
    INDEX idx_timestamp (timestamp DESC),
    INDEX idx_level (level),
    INDEX idx_channel (channel),
    INDEX idx_module (module),
    INDEX idx_created_date (DATE(timestamp)),
    INDEX idx_level_channel (level, channel),
    
    -- Constraint para evitar duplicatas
    UNIQUE KEY unique_log_id (log_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='Logs de todas as operações do sistema em tempo real';

-- ============================================================================
-- Tabela de estatísticas agregadas (atualizada diariamente)
-- ============================================================================

CREATE TABLE IF NOT EXISTS log_statistics (
    id INT AUTO_INCREMENT PRIMARY KEY,
    stat_date DATE NOT NULL COMMENT 'Data das estatísticas',
    level ENUM('error', 'success', 'warning', 'info') COMMENT 'Nível do log',
    channel VARCHAR(50) COMMENT 'Canal do log',
    total_count INT DEFAULT 0 COMMENT 'Total de logs nesta categoria',
    avg_duration_ms FLOAT DEFAULT 0 COMMENT 'Duração média em ms',
    max_duration_ms INT DEFAULT 0 COMMENT 'Duração máxima em ms',
    min_duration_ms INT DEFAULT 0 COMMENT 'Duração mínima em ms',
    
    -- Índices
    INDEX idx_stat_date (stat_date),
    INDEX idx_level_channel (stat_date, level, channel),
    UNIQUE KEY unique_stat (stat_date, level, channel)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='Estatísticas agregadas de logs por dia';

-- ============================================================================
-- Tabela de alertas (opcional - para configurar alertas automáticos)
-- ============================================================================

CREATE TABLE IF NOT EXISTS log_alerts (
    id INT AUTO_INCREMENT PRIMARY KEY,
    alert_name VARCHAR(100) NOT NULL COMMENT 'Nome do alerta',
    condition VARCHAR(200) NOT NULL COMMENT 'Condição que dispara o alerta',
    threshold INT DEFAULT 0 COMMENT 'Limiar para disparo',
    is_active BOOLEAN DEFAULT TRUE COMMENT 'Se o alerta está ativo',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    INDEX idx_active (is_active),
    INDEX idx_alert_name (alert_name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='Configurações de alertas automáticos';

-- ============================================================================
-- Tabela de eventos de alerta disparados
-- ============================================================================

CREATE TABLE IF NOT EXISTS alert_events (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    alert_id INT NOT NULL COMMENT 'FK para log_alerts',
    triggered_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT 'Quando foi disparado',
    message TEXT COMMENT 'Mensagem do alerta',
    resolved_at DATETIME COMMENT 'Quando foi resolvido',
    resolution_note TEXT COMMENT 'Nota de resolução',
    
    FOREIGN KEY (alert_id) REFERENCES log_alerts(id) ON DELETE CASCADE,
    INDEX idx_triggered_at (triggered_at DESC),
    INDEX idx_resolved_at (resolved_at),
    INDEX idx_alert_id (alert_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='Eventos de alertas disparados';

-- ============================================================================
-- VIEWS ÚTEIS PARA ANÁLISE
-- ============================================================================

-- View: Últimos 24 horas de logs
CREATE OR REPLACE VIEW vw_logs_24h AS
SELECT 
    id,
    log_id,
    timestamp,
    level,
    channel,
    module,
    message,
    duration_ms,
    details
FROM system_logs
WHERE timestamp >= DATE_SUB(NOW(), INTERVAL 24 HOUR)
ORDER BY timestamp DESC;

-- View: Logs por nível (agregado)
CREATE OR REPLACE VIEW vw_logs_by_level AS
SELECT 
    level,
    COUNT(*) as total,
    AVG(duration_ms) as avg_duration,
    MIN(duration_ms) as min_duration,
    MAX(duration_ms) as max_duration,
    DATE(timestamp) as log_date
FROM system_logs
WHERE timestamp >= DATE_SUB(NOW(), INTERVAL 7 DAY)
GROUP BY DATE(timestamp), level
ORDER BY log_date DESC, total DESC;

-- View: Logs por canal
CREATE OR REPLACE VIEW vw_logs_by_channel AS
SELECT 
    channel,
    COUNT(*) as total,
    COUNT(CASE WHEN level = 'error' THEN 1 END) as error_count,
    AVG(duration_ms) as avg_duration_ms
FROM system_logs
WHERE timestamp >= DATE_SUB(NOW(), INTERVAL 24 HOUR)
GROUP BY channel
ORDER BY error_count DESC, total DESC;

-- View: Módulos com erros
CREATE OR REPLACE VIEW vw_error_modules AS
SELECT 
    module,
    COUNT(*) as error_count,
    AVG(duration_ms) as avg_duration,
    DATE(timestamp) as log_date
FROM system_logs
WHERE level = 'error' 
AND timestamp >= DATE_SUB(NOW(), INTERVAL 24 HOUR)
GROUP BY module, DATE(timestamp)
ORDER BY error_count DESC;

-- View: Taxa de erro por canal (últimas 24h)
CREATE OR REPLACE VIEW vw_error_rate_by_channel AS
SELECT 
    channel,
    COUNT(*) as total_logs,
    COUNT(CASE WHEN level = 'error' THEN 1 END) as error_count,
    ROUND(100.0 * COUNT(CASE WHEN level = 'error' THEN 1 END) / COUNT(*), 2) as error_rate_percent
FROM system_logs
WHERE timestamp >= DATE_SUB(NOW(), INTERVAL 24 HOUR)
GROUP BY channel
ORDER BY error_rate_percent DESC;

-- ============================================================================
-- STORED PROCEDURES ÚTEIS
-- ============================================================================

-- Procedure: Limpar logs antigos
DELIMITER $$

CREATE PROCEDURE sp_cleanup_old_logs(IN days_to_keep INT)
BEGIN
    DECLARE deleted_count INT;
    
    DELETE FROM system_logs 
    WHERE timestamp < DATE_SUB(NOW(), INTERVAL days_to_keep DAY);
    
    SET deleted_count = ROW_COUNT();
    
    SELECT CONCAT('Deletados ', deleted_count, ' logs com mais de ', days_to_keep, ' dias') as result;
END$$

DELIMITER ;

-- Uso: CALL sp_cleanup_old_logs(30);  -- Manter últimos 30 dias

-- ============================================================================
-- Procedure: Gerar relatório diário de estatísticas
-- ============================================================================

DELIMITER $$

CREATE PROCEDURE sp_generate_daily_stats()
BEGIN
    INSERT INTO log_statistics (stat_date, level, channel, total_count, avg_duration_ms, max_duration_ms, min_duration_ms)
    SELECT 
        DATE(timestamp) as stat_date,
        level,
        channel,
        COUNT(*) as total_count,
        AVG(duration_ms) as avg_duration_ms,
        MAX(duration_ms) as max_duration_ms,
        MIN(duration_ms) as min_duration_ms
    FROM system_logs
    WHERE DATE(timestamp) = CURDATE()
    GROUP BY DATE(timestamp), level, channel
    ON DUPLICATE KEY UPDATE
        total_count = VALUES(total_count),
        avg_duration_ms = VALUES(avg_duration_ms),
        max_duration_ms = VALUES(max_duration_ms),
        min_duration_ms = VALUES(min_duration_ms);
END$$

DELIMITER ;

-- Uso: CALL sp_generate_daily_stats();  -- Executar diariamente via cron

-- ============================================================================
-- Procedure: Obter logs com filtros avançados
-- ============================================================================

DELIMITER $$

CREATE PROCEDURE sp_get_filtered_logs(
    IN p_level VARCHAR(50),
    IN p_channel VARCHAR(50),
    IN p_module VARCHAR(100),
    IN p_hours_back INT,
    IN p_limit INT
)
BEGIN
    SELECT 
        log_id,
        timestamp,
        level,
        channel,
        module,
        message,
        duration_ms,
        details
    FROM system_logs
    WHERE 1=1
        AND (p_level IS NULL OR level = p_level)
        AND (p_channel IS NULL OR channel = p_channel)
        AND (p_module IS NULL OR module LIKE CONCAT('%', p_module, '%'))
        AND timestamp >= DATE_SUB(NOW(), INTERVAL p_hours_back HOUR)
    ORDER BY timestamp DESC
    LIMIT p_limit;
END$$

DELIMITER ;

-- Uso: CALL sp_get_filtered_logs('error', NULL, 'RAG', 24, 100);

-- ============================================================================
-- Procedure: Alertar sobre taxa de erro alta
-- ============================================================================

DELIMITER $$

CREATE PROCEDURE sp_check_error_threshold(IN error_threshold FLOAT)
BEGIN
    SELECT 
        channel,
        COUNT(*) as total_logs,
        COUNT(CASE WHEN level = 'error' THEN 1 END) as error_count,
        ROUND(100.0 * COUNT(CASE WHEN level = 'error' THEN 1 END) / COUNT(*), 2) as error_rate_percent
    FROM system_logs
    WHERE timestamp >= DATE_SUB(NOW(), INTERVAL 1 HOUR)
    GROUP BY channel
    HAVING error_rate_percent > error_threshold
    ORDER BY error_rate_percent DESC;
END$$

DELIMITER ;

-- Uso: CALL sp_check_error_threshold(30);  -- Alertar se taxa > 30%

-- ============================================================================
-- EXEMPLOS DE QUERIES ÚTEIS
-- ============================================================================

-- Top 10 operações mais lentas
SELECT 
    module,
    message,
    duration_ms,
    timestamp
FROM system_logs
WHERE timestamp >= DATE_SUB(NOW(), INTERVAL 24 HOUR)
ORDER BY duration_ms DESC
LIMIT 10;

-- Erros nos últimos 1 hora
SELECT 
    timestamp,
    channel,
    module,
    message,
    duration_ms
FROM system_logs
WHERE level = 'error'
AND timestamp >= DATE_SUB(NOW(), INTERVAL 1 HOUR)
ORDER BY timestamp DESC;

-- Taxa de sucesso vs erro por canal
SELECT 
    channel,
    COUNT(*) as total,
    COUNT(CASE WHEN level = 'success' THEN 1 END) as success_count,
    COUNT(CASE WHEN level = 'error' THEN 1 END) as error_count,
    ROUND(100.0 * COUNT(CASE WHEN level = 'success' THEN 1 END) / COUNT(*), 2) as success_rate_percent
FROM system_logs
WHERE timestamp >= DATE_SUB(NOW(), INTERVAL 24 HOUR)
GROUP BY channel
ORDER BY success_rate_percent DESC;

-- Módulos com problema (muitos erros)
SELECT 
    module,
    COUNT(*) as error_count,
    AVG(duration_ms) as avg_duration,
    MIN(timestamp) as first_error,
    MAX(timestamp) as last_error
FROM system_logs
WHERE level = 'error'
AND timestamp >= DATE_SUB(NOW(), INTERVAL 24 HOUR)
GROUP BY module
ORDER BY error_count DESC;

-- Detalhes de um erro específico
SELECT 
    *
FROM system_logs
WHERE log_id = 'log_1234567890.123'
\G  -- Formatar em colunas

-- Contar logs por hora
SELECT 
    DATE_FORMAT(timestamp, '%Y-%m-%d %H:00:00') as hour,
    COUNT(*) as log_count,
    COUNT(CASE WHEN level = 'error' THEN 1 END) as error_count
FROM system_logs
WHERE timestamp >= DATE_SUB(NOW(), INTERVAL 24 HOUR)
GROUP BY DATE_FORMAT(timestamp, '%Y-%m-%d %H:00:00')
ORDER BY hour DESC;

-- ============================================================================
-- MANUTENÇÃO E PERFORMANCE
-- ============================================================================

-- Analisar tabela (otimizar performance)
ANALYZE TABLE system_logs;
ANALYZE TABLE log_statistics;
ANALYZE TABLE alert_events;

-- Ver índices da tabela
SHOW INDEX FROM system_logs;

-- Verificar tamanho da tabela
SELECT 
    table_name,
    ROUND(((data_length + index_length) / 1024 / 1024), 2) as size_mb
FROM information_schema.tables
WHERE table_name IN ('system_logs', 'log_statistics', 'alert_events');

-- Contar registros
SELECT 
    'system_logs' as table_name,
    COUNT(*) as record_count
FROM system_logs
UNION ALL
SELECT 
    'log_statistics',
    COUNT(*)
FROM log_statistics
UNION ALL
SELECT 
    'alert_events',
    COUNT(*)
FROM alert_events;
