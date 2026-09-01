// ============================================
// API SERVICE - AXIOS CONFIGURATION
// ============================================

import axios from 'axios';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

// Criar instância de axios com configuração padrão
const api = axios.create({
  baseURL: API_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Interceptor de requisição
api.interceptors.request.use(
  (config) => {
    // Adicionar token de autenticação se disponível
    const token = localStorage.getItem('authToken');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Interceptor de resposta
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Token expirado
      localStorage.removeItem('authToken');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

// ============================================
// API METHODS
// ============================================

export const apiService = {
  // Health & Status
  health: () => api.get('/health'),
  status: () => api.get('/status'),

  // Clientes
  getClientes: (skip = 0, limit = 50) => 
    api.get('/clientes', { params: { skip, limit } }),
  getCliente: (clienteId) => 
    api.get(`/clientes/${clienteId}`),
  createCliente: (data) => 
    api.post('/clientes', data),
  getClienteStatistics: (clienteId) => 
    api.get(`/clientes/${clienteId}/statistics`),

  // Documentos
  uploadDocument: (clienteId, file) => {
    const formData = new FormData();
    formData.append('file', file);
    return api.post(`/documentos/upload?cliente_id=${clienteId}`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
  },
  getDocumentStatus: (documentoId) => 
    api.get(`/documentos/${documentoId}/status`),
  getClienteDocuments: (clienteId) => 
    api.get(`/documentos/cliente/${clienteId}`),

  // Processamento de perguntas (RAG)
  processQuestion: (clienteId, pergunta, canalId = 1) => 
    api.post('/mensagens/processar', null, {
      params: { cliente_id: clienteId, pergunta, canal_id: canalId },
    }),

  // Fila de aprovação
  getApprovalQueue: (clienteId = null, skip = 0, limit = 50) => {
    const params = { skip, limit };
    if (clienteId) params.cliente_id = clienteId;
    return api.get('/fila-aprovacao', { params });
  },

  // Aprovação/Rejeição de mensagens
  approveMessage: (messageId, operadorId, editedResponse = null) => 
    api.post(`/mensagens/${messageId}/aprovar`, {
      resposta_editada: editedResponse,
      aprovada: true,
      operador_id: operadorId,
    }),

  rejectMessage: (messageId, operadorId, motivo) => 
    api.post(`/mensagens/${messageId}/aprovar`, {
      aprovada: false,
      motivo_rejeicao: motivo,
      operador_id: operadorId,
    }),

  // Envio de mensagens
  sendMessage: (messageId) => 
    api.post(`/mensagens/${messageId}/enviar`),

  // Feedback
  submitFeedback: (messageId, score, feedback = null) => 
    api.post(`/mensagens/${messageId}/feedback`, {
      score_satisfacao: score,
      feedback_usuario: feedback,
    }),

  // Relatórios
  getDailyReport: (clienteId = null, dias = 7) => {
    const params = { dias };
    if (clienteId) params.cliente_id = clienteId;
    return api.get('/relatorios/diario', { params });
  },
};

export default api;
