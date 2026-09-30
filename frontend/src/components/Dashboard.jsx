// ============================================
// DASHBOARD COMPONENT - Redesigned
// ============================================

import React, { useState, useEffect } from 'react';
import { formatDistanceToNow } from 'date-fns';
import { ptBR } from 'date-fns/locale';
import { mensagemService } from '../services/api';
import Loader from './Loader';
import Alert from './Alert';
import {
  CheckCircle2,
  XCircle,
  Send,
  RotateCcw,
  ChevronLeft,
  ChevronRight,
  MessageSquare,
  Building2,
  FileText,
  Zap,
  Brain,
  Clock,
  TrendingUp,
  Users,
} from 'lucide-react';

const Dashboard = ({ clienteId }) => {
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
  const [refreshInterval, setRefreshInterval] = useState(10000);
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);

  // ============================================
  // EFFECTS
  // ============================================

  useEffect(() => {
    if (clienteId) {
      fetchMessages();
    }
  }, [clienteId]);

  useEffect(() => {
    if (!autoRefresh || !clienteId) return;

    const interval = setInterval(() => {
      fetchMessages();
    }, refreshInterval);

    return () => clearInterval(interval);
  }, [autoRefresh, refreshInterval, clienteId]);

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
    if (!clienteId) return;

    try {
      setLoading(true);
      setError(null);

      const response = await mensagemService.getQueue(clienteId);
      setMessages(response.data.mensagens || response.data || []);
      setStats(response.data);

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

      await mensagemService.approve(selectedMessage.id, editedResponse);

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

      await mensagemService.reject(selectedMessage.id, rejectReason);

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

      await mensagemService.approve(selectedMessage.id, editedResponse || selectedMessage.resposta_ia);
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
    if (score >= 0.8) return 'text-emerald-600';
    if (score >= 0.5) return 'text-amber-600';
    return 'text-red-600';
  };

  const getScoreBadge = (score) => {
    if (score >= 0.8) return 'bg-emerald-100 text-emerald-700';
    if (score >= 0.5) return 'bg-amber-100 text-amber-700';
    return 'bg-red-100 text-red-700';
  };

  const getChannelConfig = (channel) => {
    const configs = {
      whatsapp: { label: 'WhatsApp', color: 'bg-emerald-100 text-emerald-700', icon: MessageSquare },
      outlook: { label: 'Outlook', color: 'bg-blue-100 text-blue-700', icon: Mail },
      web: { label: 'Web', color: 'bg-slate-100 text-slate-700', icon: MessageSquare },
      api: { label: 'API', color: 'bg-purple-100 text-purple-700', icon: Zap },
    };
    return configs[channel] || configs.web;
  };

  // ============================================
  // RENDER
  // ============================================

  if (!clienteId) {
    return (
      <div className="min-h-screen bg-green-50 flex items-center justify-center animate-fade-in">
        <div className="card max-w-md w-full mx-4 bg-gradient-to-br from-green-50 to-emerald-50 border-green-200">
          <div className="text-center">
            <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-green-500 to-green-600 flex items-center justify-center mx-auto mb-4 shadow-lg shadow-green-500/25">
              <Users className="w-8 h-8 text-white" />
            </div>
            <h2 className="text-lg font-bold text-slate-800 mb-2">Selecione um cliente</h2>
            <p className="text-slate-500 text-sm">Use o seletor no topo para escolher um cliente e ver sua fila de aprovação.</p>
          </div>
        </div>
      </div>
    );
  }

  const pendingCount = messages.length;
  const approvedCount = stats?.aprovadas || 0;
  const rejectedCount = stats?.rejeitadas || 0;
  const avgRelevance = messages.length > 0
    ? messages.reduce((acc, m) => acc + (m.score_relevancia || 0), 0) / messages.length
    : 0;

  return (
    <div className="min-h-screen bg-green-50 animate-fade-in">
      {/* HEADER */}
      <div className="card bg-white border-green-100 shadow-card sticky top-0 z-10 mb-6">
        <div className="flex flex-col lg:flex-row lg:items-start lg:justify-between gap-6">
          <div>
            <h1 className="text-2xl lg:text-3xl font-bold text-gradient">Fila de Aprovação</h1>
            <p className="text-slate-500 text-sm mt-1">Gerencie respostas geradas pela IA antes do envio</p>
          </div>

          {/* Stats Summary */}
          <div className="flex flex-wrap items-center gap-3 w-full lg:w-auto">
            <div className="card stat-card-primary p-4 min-w-[140px] text-center">
              <div className="text-3xl font-bold text-white">{pendingCount}</div>
              <div className="text-green-200 text-xs mt-1 font-medium">Pendentes</div>
            </div>
            <div className="card stat-card-primary p-4 min-w-[140px] text-center">
              <div className="text-3xl font-bold text-white">{approvedCount + rejectedCount}</div>
              <div className="text-green-200 text-xs mt-1 font-medium">Processadas</div>
            </div>
            <div className="card stat-card-primary p-4 min-w-[140px] text-center">
              <div className="text-3xl font-bold text-white">{(avgRelevance * 100).toFixed(0)}%</div>
              <div className="text-green-200 text-xs mt-1 font-medium">Relevância Média</div>
            </div>
          </div>
        </div>

        {/* Controls */}
        <div className="flex flex-wrap items-center gap-3 mt-4 pt-4 border-t border-green-100">
          <label className="flex items-center gap-2 cursor-pointer btn btn-secondary btn-sm">
            <input
              type="checkbox"
              checked={autoRefresh}
              onChange={(e) => setAutoRefresh(e.target.checked)}
              className="w-4 h-4 text-green-600 border-green-300 rounded focus:ring-green-500 accent-green-600"
            />
            <span className="text-sm text-slate-700">Auto-atualizar</span>
          </label>

          <select
            value={refreshInterval}
            onChange={(e) => setRefreshInterval(Number(e.target.value))}
            className="px-3 py-2 bg-white border border-green-200 rounded-xl text-sm focus:border-green-400 focus:ring-2 focus:ring-green-500/20 cursor-pointer"
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
            className="btn btn-secondary flex items-center gap-2"
          >
            <RotateCcw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
            Atualizar
          </button>
        </div>
      </div>

      {/* CONTENT */}
      <div className="space-y-6">
        {/* ALERTS */}
        {error && <Alert type="error" message={error} onClose={() => setError(null)} />}
        {success && <Alert type="success" message={success} onClose={() => setSuccess(null)} />}

        {/* LAYOUT: Lista + Detalhes */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          {/* LISTA DE MENSAGENS */}
          <div className="lg:col-span-4">
            <div className="card h-full flex flex-col">
              <div className="flex items-center justify-between p-4 border-b border-green-100 bg-green-50/30 rounded-t-xl">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-green-500 to-green-600 flex items-center justify-center">
                    <MessageSquare className="w-5 h-5 text-white" />
                  </div>
                  <div>
                    <h2 className="font-bold text-slate-800 text-lg">Mensagens Pendentes</h2>
                    <p className="text-xs text-slate-500">{messages.length} mensagem{messages.length !== 1 ? 's' : ''}</p>
                  </div>
                </div>
                <button
                  onClick={fetchMessages}
                  disabled={loading}
                  className="btn btn-secondary btn-sm flex items-center gap-1.5"
                >
                  <RotateCcw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
                  Atualizar
                </button>
              </div>

              {loading && messages.length === 0 ? (
                <div className="flex-1 flex items-center justify-center">
                  <Loader />
                </div>
              ) : messages.length === 0 ? (
                <div className="flex-1 flex flex-col items-center justify-center text-center p-8">
                  <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-emerald-100 to-green-100 flex items-center justify-center mb-4">
                    <CheckCircle2 className="w-8 h-8 text-emerald-600" />
                  </div>
                  <h3 className="text-lg font-bold text-slate-800 mb-1">Tudo limpo por aqui!</h3>
                  <p className="text-slate-500 text-sm">Nenhuma mensagem pendente de aprovação no momento.</p>
                </div>
              ) : (
                <div className="flex-1 overflow-y-auto divide-y divide-green-100/50">
                  {messages.map((message) => {
                    const channelConfig = getChannelConfig(message.canal);
                    const ChannelIcon = channelConfig.icon;
                    const isSelected = selectedMessage?.id === message.id;

                    return (
                      <button
                        key={message.id}
                        onClick={() => setSelectedMessage(message)}
                        className={`w-full text-left p-4 transition-all duration-200 flex flex-col gap-2 ${
                          isSelected
                            ? 'bg-gradient-to-r from-green-50 to-emerald-50 border-l-4 border-green-500'
                            : 'hover:bg-green-50/50'
                        }`}
                        aria-pressed={isSelected}
                      >
                        <div className="flex justify-between items-start gap-2">
                          <div className="flex-1 min-w-0">
                            <div className="flex items-center gap-2 flex-wrap">
                              <p className="font-semibold text-sm text-slate-900 truncate">{message.cliente}</p>
                              <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider ${channelConfig.color}`}>
                                <ChannelIcon className="w-3 h-3" />
                                {channelConfig.label}
                              </span>
                            </div>
                            <p className="text-xs text-slate-500 mt-1 line-clamp-2">{message.pergunta}</p>
                            <div className="flex items-center gap-3 mt-2 text-xs text-slate-400">
                              <span className="flex items-center gap-1">
                                <Clock className="w-3 h-3" />
                                {formatDistanceToNow(new Date(message.data_recebimento), { locale: ptBR, addSuffix: true })}
                              </span>
                              <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full font-mono ${getScoreBadge(message.score_relevancia)}`}>
                                {(message.score_relevancia * 100).toFixed(0)}%
                              </span>
                            </div>
                          </div>
                          {isSelected && (
                            <div className="flex-shrink-0 w-6 h-6 rounded-full bg-green-500 flex items-center justify-center">
                              <CheckCircle2 className="w-3.5 h-3.5 text-white" />
                            </div>
                          )}
                        </div>
                      </button>
                    );
                  })}
                </div>
              )}
            </div>
          </div>

          {/* DETALHES DA MENSAGEM SELECIONADA */}
          <div className="lg:col-span-8">
            {selectedMessage ? (
              <div className="card h-full flex flex-col animate-slide-in-right">
                {/* HEADER DO DETALHE */}
                <div className="flex items-start justify-between p-4 border-b border-green-100 bg-green-50/30 rounded-t-xl">
                  <div className="flex items-center gap-4">
                    <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-green-500 to-green-600 flex items-center justify-center flex-shrink-0">
                      <MessageSquare className="w-6 h-6 text-white" />
                    </div>
                    <div className="min-w-0">
                      <h3 className="text-lg font-bold text-slate-900 truncate">{selectedMessage.cliente}</h3>
                      <div className="flex items-center gap-3 mt-1 text-sm text-slate-500">
                        <span className="flex items-center gap-1">
                          <Building2 className="w-3.5 h-3.5" />
                          {selectedMessage.empresa}
                        </span>
                        <span className="flex items-center gap-1">
                          <MessageSquare className="w-3.5 h-3.5" />
                          {selectedMessage.canal}
                        </span>
                      </div>
                    </div>
                  </div>
                  <button
                    onClick={() => setSelectedMessage(null)}
                    className="p-2 text-slate-400 hover:text-slate-600 hover:bg-slate-100 rounded-xl transition-colors flex-shrink-0"
                  >
                    <XCircle className="w-5 h-5" />
                  </button>
                </div>

                {/* CONTENT */}
                <div className="flex-1 overflow-y-auto p-6 space-y-6">
                  {/* PERGUNTA */}
                  <div className="animate-fade-in">
                    <label className="block text-sm font-semibold text-slate-900 mb-2 flex items-center gap-2">
                      <MessageSquare className="w-4 h-4 text-green-600" />
                      Pergunta do Cliente
                    </label>
                    <div className="bg-slate-50 border border-slate-200 rounded-xl p-4 text-sm text-slate-700">
                      {selectedMessage.pergunta}
                    </div>
                  </div>

                  {/* CONTEXTO RECUPERADO */}
                  <div className="animate-slide-up">
                    <label className="block text-sm font-semibold text-slate-900 mb-3 flex items-center gap-2">
                      <Brain className="w-4 h-4 text-green-600" />
                      Contexto Recuperado (RAG)
                    </label>
                    <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                      <div className="card bg-gradient-to-br from-blue-50 to-blue-100 border-blue-200">
                        <div className="text-xs text-slate-500 font-medium uppercase tracking-wider">Chunks Recuperados</div>
                        <div className="text-3xl font-bold text-blue-600 mt-1">{selectedMessage.chunks_recuperados}</div>
                      </div>
                      <div className="card bg-gradient-to-br from-purple-50 to-purple-100 border-purple-200">
                        <div className="text-xs text-slate-500 font-medium uppercase tracking-wider">Score de Relevância</div>
                        <div className={`text-3xl font-bold mt-1 ${getScoreColor(selectedMessage.score_relevancia)}`}>
                          {(selectedMessage.score_relevancia * 100).toFixed(0)}%
                        </div>
                      </div>
                      <div className="card bg-gradient-to-br from-amber-50 to-amber-100 border-amber-200">
                        <div className="text-xs text-slate-500 font-medium uppercase tracking-wider">Tempo de Resposta</div>
                        <div className="text-3xl font-bold text-amber-600 mt-1">{selectedMessage.tempo_resposta || 'N/A'}ms</div>
                      </div>
                    </div>
                  </div>

                  {/* RESPOSTA IA (ORIGINAL) */}
                  <div className="animate-slide-up">
                    <label className="block text-sm font-semibold text-slate-900 mb-2 flex items-center gap-2">
                      <Zap className="w-4 h-4 text-green-600" />
                      Resposta Gerada pela IA
                    </label>
                    <div className="bg-green-50 border-l-4 border-green-500 rounded-xl p-4 text-sm text-slate-700">
                      {selectedMessage.resposta_ia}
                    </div>
                  </div>

                  {/* RESPOSTA EDITADA */}
                  <div className="animate-slide-up">
                    <label className="block text-sm font-semibold text-slate-900 mb-2 flex items-center gap-2">
                      <FileText className="w-4 h-4 text-green-600" />
                      Resposta (Editar se necessário)
                    </label>
                    <textarea
                      value={editedResponse}
                      onChange={(e) => setEditedResponse(e.target.value)}
                      className="w-full h-40 p-4 border border-green-200 rounded-xl focus:ring-2 focus:ring-green-500/20 focus:border-green-400 text-sm transition-all resize-none"
                      placeholder="Edite a resposta se necessário antes de aprovar..."
                    />
                    <p className="text-xs text-slate-500 mt-2 text-right">{editedResponse.length} caracteres</p>
                  </div>

                  {/* MOTIVO REJEIÇÃO */}
                  <div className="animate-slide-up">
                    <label className="block text-sm font-semibold text-slate-900 mb-2 flex items-center gap-2">
                      <XCircle className="w-4 h-4 text-red-500" />
                      Motivo de Rejeição (se aplicável)
                    </label>
                    <textarea
                      value={rejectReason}
                      onChange={(e) => setRejectReason(e.target.value)}
                      className="w-full h-24 p-4 border border-red-200 rounded-xl focus:ring-2 focus:ring-red-500/20 focus:border-red-400 text-sm transition-all resize-none"
                      placeholder="Descreva por que a resposta não é adequada..."
                    />
                  </div>
                </div>

                {/* ACTIONS */}
                <div className="p-4 border-t border-green-100 bg-green-50/30 rounded-b-xl flex flex-wrap gap-3">
                  <button
                    onClick={handleReject}
                    disabled={actionInProgress !== null || !rejectReason.trim()}
                    className="btn btn-danger flex-1 sm:flex-none flex items-center justify-center gap-2"
                  >
                    <XCircle className="w-4 h-4" />
                    {actionInProgress === 'reject' ? 'Rejeitando...' : 'Rejeitar'}
                  </button>
                  <button
                    onClick={handleApprove}
                    disabled={actionInProgress !== null}
                    className="btn btn-primary flex-1 sm:flex-none flex items-center justify-center gap-2"
                  >
                    <CheckCircle2 className="w-4 h-4" />
                    {actionInProgress === 'approve' ? 'Aprovando...' : 'Aprovar'}
                  </button>
                  <button
                    onClick={handleSend}
                    disabled={actionInProgress !== null}
                    className="btn btn-secondary flex-1 sm:flex-none flex items-center justify-center gap-2"
                  >
                    <Send className="w-4 h-4" />
                    {actionInProgress === 'send' ? 'Enviando...' : 'Aprovar e Enviar'}
                  </button>
                </div>
              </div>
            ) : (
              <div className="card h-[500px] flex items-center justify-center animate-fade-in">
                <div className="text-center">
                  <div className="w-20 h-20 rounded-2xl bg-gradient-to-br from-green-100 to-emerald-100 flex items-center justify-center mx-auto mb-4">
                    <MessageSquare className="w-10 h-10 text-green-500" />
                  </div>
                  <h3 className="text-lg font-bold text-slate-800 mb-1">Selecione uma mensagem</h3>
                  <p className="text-slate-500">Clique em uma mensagem na lista ao lado para visualizar detalhes e tomar ação.</p>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;