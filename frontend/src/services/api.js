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
      const response = await api.post('/api/documentos/upload', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
        onUploadProgress: (progressEvent) => {
          const percentCompleted = Math.round(
            (progressEvent.loaded * 100) / progressEvent.total
          );
          // Emitir progresso se necessário
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
      const response = await api.get('/api/documentos', {
        params: { cliente_id },
      });
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
      const response = await api.get(`/api/documentos/${documentoId}/status`);
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
      const response = await api.delete(`/api/documentos/${documentoId}`);
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
      const response = await api.post('/api/mensagens/enviar', {
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
      const response = await api.get('/api/mensagens/fila', {
        params: { cliente_id },
      });
      return response.data;
    } catch (error) {
      console.error('Erro ao obter fila:', error);
      throw error;
    }
  },

  /**
   * Aprova uma mensagem e envia a resposta
   * @param {number} mensagemId - ID da mensagem
   * @param {string} resposta - Resposta a ser enviada (pode ser editada)
   * @returns {Promise}
   */
  approve: async (mensagemId, resposta) => {
    try {
      const response = await api.post(
        `/api/mensagens/${mensagemId}/approve`,
        { resposta }
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
        `/api/mensagens/${mensagemId}/reject`,
        { motivo }
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
      const response = await api.get(`/api/mensagens/${mensagemId}`);
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
      const response = await api.get(
        `/api/mensagens/${mensagemId}/chunks-consultados`
      );
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
      const response = await api.get('/api/logs', {
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
      const response = await api.get(`/api/logs/mensagem/${mensagemId}`);
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
      const response = await api.get(`/api/logs/documento/${documentoId}`);
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
      const response = await api.get('/api/estatisticas/geral', {
        params: { cliente_id },
      });
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
      const response = await api.get('/api/estatisticas/periodo', {
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
      const response = await api.get('/api/estatisticas/top-documentos', {
        params: { cliente_id, limite },
      });
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
    try {
      const response = await api.get('/api/configuracoes', {
        params: { cliente_id },
      });
      return response.data;
    } catch (error) {
      console.error('Erro ao obter configurações:', error);
      throw error;
    }
  },

  /**
   * Atualiza configurações do cliente
   * @param {string} cliente_id - ID do cliente
   * @param {object} config - Novas configurações
   * @returns {Promise}
   */
  update: async (cliente_id, config) => {
    try {
      const response = await api.put('/api/configuracoes', {
        cliente_id,
        ...config,
      });
      return response.data;
    } catch (error) {
      console.error('Erro ao atualizar configurações:', error);
      throw error;
    }
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
   * Verifica conexão com banco de dados
   * @returns {Promise} Status do BD
   */
  checkDatabase: async () => {
    try {
      const response = await api.get('/health/db');
      return response.data;
    } catch (error) {
      console.error('Erro ao verificar BD:', error);
      throw error;
    }
  },
};

export default api;