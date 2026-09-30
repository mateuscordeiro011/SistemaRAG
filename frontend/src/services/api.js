import axios from 'axios';

/**
 * Serviço de API para SistemaRAG
 * Centraliza todas as chamadas ao backend
 */

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// ==========================================
// INTERCEPTORES
// ==========================================

// Interceptor de resposta para tratamento de erros
api.interceptors.response.use(
  response => response,
  error => {
    if (error.response?.status === 401) {
      // Redirecionar para login se não autenticado
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

// ==========================================
// DOCUMENTOS - Upload e Gerenciamento
// ==========================================

export const documentoService = {
  /**
   * Faz upload de um arquivo
   * @param {File} file - Arquivo a ser enviado
   * @param {string} cliente_id - ID do cliente
   * @returns {Promise} Resposta com documento_id e status_url
   */
  upload: async (file, cliente_id) => {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('cliente_id', cliente_id);

    try {
      const response = await api.post('/documentos/upload', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
        onUploadProgress: (progressEvent) => {
          const percentCompleted = Math.round(
            (progressEvent.loaded * 100) / progressEvent.total
          );
          console.log(`Upload: ${percentCompleted}%`);
        },
      });
      return response.data;
    } catch (error) {
      console.error('Erro no upload:', error);
      throw error;
    }
  },

  /**
   * Lista documentos do cliente
   * @param {string} cliente_id - ID do cliente
   * @returns {Promise} Array de documentos
   */
  list: async (cliente_id) => {
    try {
      const response = await api.get('/documentos/cliente/' + cliente_id);
      return response.data;
    } catch (error) {
      console.error('Erro ao listar documentos:', error);
      throw error;
    }
  },

  /**
   * Obtém status de processamento de um documento
   * @param {number} documentoId - ID do documento
   * @returns {Promise} Status atual
   */
  getStatus: async (documentoId) => {
    try {
      const response = await api.get(`/documentos/${documentoId}/status`);
      return response.data;
    } catch (error) {
      console.error('Erro ao obter status:', error);
      throw error;
    }
  },

  /**
   * Deleta um documento
   * @param {number} documentoId - ID do documento
   * @returns {Promise}
   */
  delete: async (documentoId) => {
    try {
      const response = await api.delete(`/documentos/${documentoId}`);
      return response.data;
    } catch (error) {
      console.error('Erro ao deletar documento:', error);
      throw error;
    }
  },
};

// ==========================================
// MENSAGENS - Envio e Processamento
// ==========================================

export const mensagemService = {
  /**
   * Envia uma pergunta ao sistema RAG
   * @param {string} cliente_id - ID do cliente
   * @param {string} pergunta - Pergunta a ser processada
   * @param {string} canal - Canal (whatsapp, email, web)
   * @returns {Promise} Resposta processada
   */
  enviar: async (cliente_id, pergunta, canal = 'web') => {
    try {
      const response = await api.post('/mensagens/processar', {
        cliente_id,
        pergunta,
        canal,
      });
      return response.data;
    } catch (error) {
      console.error('Erro ao enviar pergunta:', error);
      throw error;
    }
  },

  /**
   * Lista todas as mensagens de um cliente
   * @param {string} cliente_id - ID do cliente
   * @param {object} filtros - Filtros opcionais (status, canal, etc)
   * @returns {Promise} Array de mensagens
   */
  list: async (cliente_id, filtros = {}) => {
    try {
      const response = await api.get('/api/mensagens', {
        params: {
          cliente_id,
          ...filtros,
        },
      });
      return response.data;
    } catch (error) {
      console.error('Erro ao listar mensagens:', error);
      throw error;
    }
  },

  /**
   * Obtém a fila de mensagens aguardando aprovação
   * @param {string} cliente_id - ID do cliente
   * @returns {Promise} Array de mensagens na fila
   */
  getQueue: async (cliente_id) => {
    try {
      const response = await api.get('/fila-aprovacao', {
        params: { cliente_id },
      });
      return response.data;
    } catch (error) {
      console.error('Erro ao obter fila:', error);
      throw error;
    }
  },

  /**
   * Aprova uma mensagem
   * @param {number} mensagemId - ID da mensagem
   * @param {string} resposta - Resposta a ser enviada (pode ser editada)
   * @returns {Promise}
   */
  approve: async (mensagemId, resposta) => {
    try {
      const response = await api.post(
        `/mensagens/${mensagemId}/aprovar`,
        { 
          aprovada: true,
          resposta_editada: resposta,
          operador_id: 1
        }
      );
      return response.data;
    } catch (error) {
      console.error('Erro ao aprovar mensagem:', error);
      throw error;
    }
  },

  /**
   * Rejeita uma mensagem
   * @param {number} mensagemId - ID da mensagem
   * @param {string} motivo - Motivo da rejeição
   * @returns {Promise}
   */
  reject: async (mensagemId, motivo) => {
    try {
      const response = await api.post(
        `/mensagens/${mensagemId}/aprovar`,
        { 
          aprovada: false,
          motivo_rejeicao: motivo,
          operador_id: 1
        }
      );
      return response.data;
    } catch (error) {
      console.error('Erro ao rejeitar mensagem:', error);
      throw error;
    }
  },

  /**
   * Obtém detalhes de uma mensagem
   * @param {number} mensagemId - ID da mensagem
   * @returns {Promise} Detalhes da mensagem
   */
  getDetails: async (mensagemId) => {
    try {
      const response = await api.get(`/mensagens/${mensagemId}/detalhes-completo`);
      return response.data;
    } catch (error) {
      console.error('Erro ao obter detalhes:', error);
      throw error;
    }
  },

  /**
   * Obtém chunks consultados para uma mensagem (rastreabilidade)
   * @param {number} mensagemId - ID da mensagem
   * @returns {Promise} Array de chunks com scores
   */
  getChunksConsultados: async (mensagemId) => {
    try {
      const response = await api.get(`/mensagens/${mensagemId}/chunks-consultados`);
      return response.data;
    } catch (error) {
      console.error('Erro ao obter chunks:', error);
      throw error;
    }
  },
};

// ==========================================
// LOGS - Auditoria e Monitoramento
// ==========================================

export const logService = {
  /**
   * Lista logs de um cliente
   * @param {string} cliente_id - ID do cliente
   * @param {object} filtros - Filtros (tipo, data, etc)
   * @returns {Promise} Array de logs
   */
  list: async (cliente_id, filtros = {}) => {
    try {
      const response = await api.get('/logs', {
        params: {
          cliente_id,
          ...filtros,
        },
      });
      return response.data;
    } catch (error) {
      console.error('Erro ao listar logs:', error);
      throw error;
    }
  },

  /**
   * Obtém logs de uma mensagem específica
   * @param {number} mensagemId - ID da mensagem
   * @returns {Promise} Array de logs associados
   */
  getByMensagem: async (mensagemId) => {
    try {
      const response = await api.get(`/logs/mensagem/${mensagemId}`);
      return response.data;
    } catch (error) {
      console.error('Erro ao obter logs:', error);
      throw error;
    }
  },

  /**
   * Obtém logs de um documento
   * @param {number} documentoId - ID do documento
   * @returns {Promise} Array de logs do processamento
   */
  getByDocumento: async (documentoId) => {
    try {
      const response = await api.get(`/logs/documento/${documentoId}`);
      return response.data;
    } catch (error) {
      console.error('Erro ao obter logs:', error);
      throw error;
    }
  },
};

// ==========================================
// ESTATÍSTICAS E DASHBOARDS
// ==========================================

export const estatisticasService = {
  /**
   * Obtém estatísticas gerais de um cliente
   * @param {string} cliente_id - ID do cliente
   * @returns {Promise} Objeto com estatísticas
   */
  getGeral: async (cliente_id) => {
    try {
      const response = await api.get('/clientes/' + cliente_id + '/statistics');
      return response.data;
    } catch (error) {
      console.error('Erro ao obter estatísticas:', error);
      throw error;
    }
  },

  /**
   * Obtém estatísticas por período
   * @param {string} cliente_id - ID do cliente
   * @param {string} dataInicio - Data de início (YYYY-MM-DD)
   * @param {string} dataFim - Data de fim (YYYY-MM-DD)
   * @returns {Promise} Dados agregados por período
   */
  getPorPeriodo: async (cliente_id, dataInicio, dataFim) => {
    try {
      const response = await api.get('/relatorios/diario', {
        params: { cliente_id, dataInicio, dataFim },
      });
      return response.data;
    } catch (error) {
      console.error('Erro ao obter estatísticas:', error);
      throw error;
    }
  },

  /**
   * Obtém ranking de documentos mais consultados
   * @param {string} cliente_id - ID do cliente
   * @param {number} limite - Número de top documentos
   * @returns {Promise} Array com ranking
   */
  getTopDocumentos: async (cliente_id, limite = 10) => {
    try {
      const response = await api.get('/clientes/' + cliente_id + '/statistics');
      return response.data;
    } catch (error) {
      console.error('Erro ao obter top documentos:', error);
      throw error;
    }
  },
};

// ==========================================
// CONFIGURAÇÕES
// ==========================================

export const configuracaoService = {
  /**
   * Obtém configurações do cliente
   * @param {string} cliente_id - ID do cliente
   * @returns {Promise} Objeto com configurações
   */
  get: async (cliente_id) => {
    // Endpoint não implementado no backend ainda
    console.warn('Endpoint /configuracoes não implementado no backend');
    return { 
      limiar_confianca: 0.75, 
      max_chunks_resposta: 5,
      modelo_embedding: 'text-embedding-ada-002',
      modelo_rag: 'gpt-3.5-turbo',
      timeout_processamento: 30
    };
  },

  /**
   * Atualiza configurações do cliente
   * @param {string} cliente_id - ID do cliente
   * @param {object} config - Novas configurações
   * @returns {Promise}
   */
  update: async (cliente_id, config) => {
    console.warn('Endpoint /configuracoes não implementado no backend');
    return { success: true };
  },
};

// ==========================================
// HEALTH CHECK
// ==========================================

export const healthService = {
  /**
   * Verifica saúde do servidor
   * @returns {Promise} Status do servidor
   */
  check: async () => {
    try {
      const response = await api.get('/health');
      return response.data;
    } catch (error) {
      console.error('Erro ao verificar saúde:', error);
      throw error;
    }
  },

  /**
   * Status rápido do sistema (< 1s)
   * @returns {Promise} Status rápido
   */
  quickStatus: async () => {
    try {
      const response = await api.get('/api/v1/health/quick-status');
      return response.data;
    } catch (error) {
      console.error('Erro ao verificar status rápido:', error);
      throw error;
    }
  },

  /**
   * Diagnóstico completo do sistema (2-5s)
   * @returns {Promise} Relatório completo
   */
  fullDiagnostic: async () => {
    try {
      const response = await api.get('/api/v1/health/full-diagnostic');
      return response.data;
    } catch (error) {
      console.error('Erro no diagnóstico completo:', error);
      throw error;
    }
  },

  /**
   * Teste de persistência do banco de dados
   * @returns {Promise} Resultado do teste
   */
  dbTest: async () => {
    try {
      const response = await api.get('/api/v1/health/db-test');
      return response.data;
    } catch (error) {
      console.error('Erro no teste de BD:', error);
      throw error;
    }
  },

  /**
   * Teste de disponibilidade do modelo de IA
   * @returns {Promise} Resultado do teste
   */
  aiModelTest: async () => {
    try {
      const response = await api.get('/api/v1/health/ai-model-test');
      return response.data;
    } catch (error) {
      console.error('Erro no teste de modelo IA:', error);
      throw error;
    }
  },
};

export default api;