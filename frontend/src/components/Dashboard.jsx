// ============================================
// DASHBOARD COMPONENT
// ============================================
// Componente principal que exibe a fila de aprovação de mensagens.
// Permite visualizar, editar, aprovar, rejeitar e enviar respostas.

import React, { useState, useEffect } from 'react';
import { formatDistanceToNow } from 'date-fns';
import { ptBR } from 'date-fns/locale';
import { apiService } from '../services/api';
import MessageCard from './MessageCard';
import Loader from './Loader';
import Alert from './Alert';

const Dashboard = () => {
  // ============================================
  // STATE
  // ============================================

  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);
  const [selectedMessage, setSelectedMessage] = useState(null);
  const [editedResponse, setEditedResponse] = useState('');
  const [rejectReason, setRejectReason] = useState('');
  const [actionInProgress, setActionInProgress] = useState(null);
  const [stats, setStats] = useState(null);
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [refreshInterval, setRefreshInterval] = useState(10000); // 10 segundos

  // ============================================
  // EFFECTS
  // ============================================

  // Fetch fila de aprovação
  useEffect(() => {
    fetchMessages();
  }, []);

  // Auto-refresh
  useEffect(() => {
    if (!autoRefresh) return;

    const interval = setInterval(() => {
      fetchMessages();
    }, refreshInterval);

    return () => clearInterval(interval);
  }, [autoRefresh, refreshInterval]);

  // Atualizar resposta editada quando mudar mensagem selecionada
  useEffect(() => {
    if (selectedMessage) {
      setEditedResponse(selectedMessage.resposta_ia);
      setRejectReason('');
    }
  }, [selectedMessage]);

  // ============================================
  // FUNCTIONS
  // ============================================

  const fetchMessages = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const response = await apiService.getApprovalQueue();
      setMessages(response.data.mensagens);
      setStats(response.data);

      // Esconder sucesso após 3 segundos
      if (success) {
        setTimeout(() => setSuccess(null), 3000);
      }
    } catch (err) {
      setError('Erro ao carregar fila de aprovação: ' + err.message);
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleApprove = async () => {
    if (!selectedMessage) return;

    try {
      setActionInProgress('approve');
      setError(null);

      const response = await apiService.approveMessage(
        selectedMessage.id,
        1, // TODO: Usar ID do usuário autenticado
        editedResponse
      );

      setSuccess('Mensagem aprovada com sucesso!');
      setSelectedMessage(null);
      await fetchMessages();
    } catch (err) {
      setError('Erro ao aprovar mensagem: ' + err.message);
      console.error(err);
    } finally {
      setActionInProgress(null);
    }
  };

  const handleReject = async () => {
    if (!selectedMessage || !rejectReason.trim()) {
      setError('Por favor, forneça um motivo para rejeição');
      return;
    }

    try {
      setActionInProgress('reject');
      setError(null);

      await apiService.rejectMessage(
        selectedMessage.id,
        1, // TODO: Usar ID do usuário autenticado
        rejectReason
      );

      setSuccess('Mensagem rejeitada');
      setSelectedMessage(null);
      await fetchMessages();
    } catch (err) {
      setError('Erro ao rejeitar mensagem: ' + err.message);
      console.error(err);
    } finally {
      setActionInProgress(null);
    }
  };

  const handleSend = async () => {
    if (!selectedMessage) return;

    try {
      setActionInProgress('send');
      setError(null);

      await apiService.sendMessage(selectedMessage.id);
      setSuccess('Mensagem enviada com sucesso!');
      setSelectedMessage(null);
      await fetchMessages();
    } catch (err) {
      setError('Erro ao enviar mensagem: ' + err.message);
      console.error(err);
    } finally {
      setActionInProgress(null);
    }
  };

  const getScoreColor = (score) => {
    if (score >= 0.8) return 'text-green-600';
    if (score >= 0.5) return 'text-yellow-600';
    return 'text-red-600';
  };

  // ============================================
  // RENDER
  // ============================================

  return (
    <div className="min-h-screen bg-gray-50">
      {/* HEADER */}
      <div className="bg-white border-b border-gray-200 shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex justify-between items-start">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">
                Fila de Aprovação
              </h1>
              <p className="mt-1 text-sm text-gray-500">
                Gerenciar respostas geradas pela IA antes do envio
              </p>
            </div>
            
            {/* STATS */}
            {stats && (
              <div className="bg-blue-50 rounded-lg px-4 py-3">
                <div className="text-center">
                  <div className="text-3xl font-bold text-blue-600">
                    {stats.total}
                  </div>
                  <div className="text-sm text-blue-700 mt-1">
                    Mensagens pendentes
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* CONTROLES */}
          <div className="mt-4 flex gap-3 items-center">
            <label className="flex items-center gap-2 cursor-pointer">
              <input
                type="checkbox"
                checked={autoRefresh}
                onChange={(e) => setAutoRefresh(e.target.checked)}
                className="rounded"
              />
              <span className="text-sm text-gray-700">
                Auto-atualizar
              </span>
            </label>
            
            <select
              value={refreshInterval}
              onChange={(e) => setRefreshInterval(Number(e.target.value))}
              className="text-sm px-2 py-1 border border-gray-300 rounded"
              disabled={!autoRefresh}
            >
              <option value={5000}>5 segundos</option>
              <option value={10000}>10 segundos</option>
              <option value={30000}>30 segundos</option>
              <option value={60000}>1 minuto</option>
            </select>

            <button
              onClick={fetchMessages}
              disabled={loading}
              className="px-3 py-1 bg-blue-600 text-white text-sm rounded hover:bg-blue-700 disabled:opacity-50"
            >
              {loading ? 'Carregando...' : 'Atualizar'}
            </button>
          </div>
        </div>
      </div>

      {/* CONTENT */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* ALERTS */}
        {error && <Alert type="error" message={error} onClose={() => setError(null)} />}
        {success && <Alert type="success" message={success} onClose={() => setSuccess(null)} />}

        {/* LAYOUT: Lista + Detalhes */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* LISTA DE MENSAGENS */}
          <div className="lg:col-span-1 bg-white rounded-lg shadow">
            <div className="px-6 py-4 border-b border-gray-200">
              <h2 className="text-lg font-semibold text-gray-900">
                Mensagens Pendentes
              </h2>
              <p className="text-sm text-gray-500 mt-1">
                {messages.length} mensagem{messages.length !== 1 ? 's' : ''}
              </p>
            </div>

            {loading && messages.length === 0 ? (
              <div className="p-6 text-center">
                <Loader />
              </div>
            ) : messages.length === 0 ? (
              <div className="p-6 text-center text-gray-500">
                Nenhuma mensagem pendente
              </div>
            ) : (
              <div className="divide-y divide-gray-200 max-h-96 overflow-y-auto">
                {messages.map((message) => (
                  <div
                    key={message.id}
                    onClick={() => setSelectedMessage(message)}
                    className={`p-4 cursor-pointer hover:bg-gray-50 transition ${
                      selectedMessage?.id === message.id ? 'bg-blue-50' : ''
                    }`}
                  >
                    <div className="flex justify-between items-start gap-2">
                      <div className="flex-1 min-w-0">
                        <p className="font-semibold text-sm text-gray-900 truncate">
                          {message.cliente}
                        </p>
                        <p className="text-xs text-gray-500 mt-1 line-clamp-2">
                          {message.pergunta}
                        </p>
                        <p className="text-xs text-gray-400 mt-2">
                          {formatDistanceToNow(
                            new Date(message.data_recebimento),
                            { locale: ptBR, addSuffix: true }
                          )}
                        </p>
                      </div>
                      <div className="flex-shrink-0">
                        <span className={`inline-block px-2 py-1 text-xs font-semibold rounded ${
                          message.score_relevancia >= 0.7
                            ? 'bg-green-100 text-green-800'
                            : message.score_relevancia >= 0.4
                            ? 'bg-yellow-100 text-yellow-800'
                            : 'bg-red-100 text-red-800'
                        }`}>
                          {(message.score_relevancia * 100).toFixed(0)}%
                        </span>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* DETALHES DA MENSAGEM SELECIONADA */}
          <div className="lg:col-span-2 bg-white rounded-lg shadow">
            {selectedMessage ? (
              <div className="h-full flex flex-col">
                {/* HEADER DO DETALHE */}
                <div className="px-6 py-4 border-b border-gray-200">
                  <div className="flex justify-between items-start">
                    <div>
                      <h3 className="text-lg font-semibold text-gray-900">
                        {selectedMessage.cliente}
                      </h3>
                      <p className="text-sm text-gray-500 mt-1">
                        {selectedMessage.empresa} • {selectedMessage.canal}
                      </p>
                    </div>
                    <button
                      onClick={() => setSelectedMessage(null)}
                      className="text-gray-400 hover:text-gray-600"
                    >
                      ✕
                    </button>
                  </div>
                </div>

                {/* CONTENT */}
                <div className="flex-1 overflow-y-auto px-6 py-4 space-y-6">
                  {/* PERGUNTA */}
                  <div>
                    <label className="block text-sm font-semibold text-gray-900 mb-2">
                      Pergunta do Cliente
                    </label>
                    <div className="bg-gray-50 rounded p-3 text-sm text-gray-700">
                      {selectedMessage.pergunta}
                    </div>
                  </div>

                  {/* CONTEXTO RECUPERADO */}
                  <div>
                    <label className="block text-sm font-semibold text-gray-900 mb-2">
                      Contexto Recuperado
                    </label>
                    <div className="grid grid-cols-2 gap-2">
                      <div className="bg-blue-50 rounded p-2">
                        <div className="text-xs text-gray-500">Chunks</div>
                        <div className="text-lg font-bold text-blue-600">
                          {selectedMessage.chunks_recuperados}
                        </div>
                      </div>
                      <div className="bg-purple-50 rounded p-2">
                        <div className="text-xs text-gray-500">Relevância</div>
                        <div className={`text-lg font-bold ${getScoreColor(selectedMessage.score_relevancia)}`}>
                          {(selectedMessage.score_relevancia * 100).toFixed(0)}%
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* RESPOSTA IA (ORIGINAL) */}
                  <div>
                    <label className="block text-sm font-semibold text-gray-900 mb-2">
                      Resposta Gerada pela IA
                    </label>
                    <div className="bg-gray-50 rounded p-3 text-sm text-gray-700 border-l-4 border-blue-500">
                      {selectedMessage.resposta_ia}
                    </div>
                  </div>

                  {/* RESPOSTA EDITADA */}
                  <div>
                    <label className="block text-sm font-semibold text-gray-900 mb-2">
                      Resposta (Editar se necessário)
                    </label>
                    <textarea
                      value={editedResponse}
                      onChange={(e) => setEditedResponse(e.target.value)}
                      className="w-full h-32 p-3 border border-gray-300 rounded focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm"
                      placeholder="Edite a resposta se necessário antes de aprovar..."
                    />
                    <p className="text-xs text-gray-500 mt-2">
                      {editedResponse.length} caracteres
                    </p>
                  </div>

                  {/* MOTIVO REJEIÇÃO */}
                  <div>
                    <label className="block text-sm font-semibold text-gray-900 mb-2">
                      Motivo de Rejeição (se aplicável)
                    </label>
                    <textarea
                      value={rejectReason}
                      onChange={(e) => setRejectReason(e.target.value)}
                      className="w-full h-20 p-3 border border-gray-300 rounded focus:ring-2 focus:ring-red-500 focus:border-transparent text-sm"
                      placeholder="Descreva por que a resposta não é adequada..."
                    />
                  </div>
                </div>

                {/* ACTIONS */}
                <div className="px-6 py-4 border-t border-gray-200 flex gap-3">
                  <button
                    onClick={handleApprove}
                    disabled={actionInProgress !== null}
                    className="flex-1 px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700 disabled:opacity-50 font-medium transition"
                  >
                    {actionInProgress === 'approve' ? 'Aprovando...' : '✓ Aprovar'}
                  </button>
                  <button
                    onClick={handleReject}
                    disabled={actionInProgress !== null || !rejectReason.trim()}
                    className="flex-1 px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700 disabled:opacity-50 font-medium transition"
                  >
                    {actionInProgress === 'reject' ? 'Rejeitando...' : '✕ Rejeitar'}
                  </button>
                  <button
                    onClick={handleSend}
                    disabled={actionInProgress !== null}
                    className="flex-1 px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50 font-medium transition"
                  >
                    {actionInProgress === 'send' ? 'Enviando...' : '📤 Enviar'}
                  </button>
                </div>
              </div>
            ) : (
              <div className="h-full flex items-center justify-center text-gray-500">
                Selecione uma mensagem para visualizar detalhes
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
