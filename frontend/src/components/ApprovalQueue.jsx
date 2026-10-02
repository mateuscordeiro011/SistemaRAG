import React, { useState, useEffect } from 'react';
import { 
  Send, 
  XCircle, 
  Edit3, 
  MessageSquare, 
  Building2, 
  FileText, 
  CheckCircle2, 
  Loader2, 
  AlertCircle,
  Brain,
  Zap,
  Clock,
  ChevronDown,
  ChevronUp,
  Mail,
} from 'lucide-react';
import { mensagemService } from '../services/api';
import LogBadge from './LogBadge';

export default function ApprovalQueue({ clienteId }) {
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedId, setSelectedId] = useState(null);
  const [editedResponse, setEditedResponse] = useState('');
  const [actionInProgress, setActionInProgress] = useState(null);

  const fetchMessages = async () => {
    if (!clienteId) {
      setMessages([]);
      setLoading(false);
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const data = await mensagemService.getQueue(clienteId);
      const msgs = data.mensagens || data || [];
      setMessages(msgs.map(m => ({
        id: m.id,
        client_name: m.cliente?.nome || m.cliente_nome || 'Cliente',
        company: m.cliente?.empresa || m.empresa || 'Empresa',
        channel: m.canal || 'web',
        question: m.pergunta,
        suggested_response: m.resposta_ia || m.resposta || '',
        sources: m.chunks_recuperados ? [`${m.chunks_recuperados} chunks (score: ${(m.score_relevancia * 100).toFixed(0)}%)`] : [],
        time: m.data_recebimento ? new Date(m.data_recebimento).toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' }) : 'Recente',
        score: m.score_relevancia || 0,
        chunks: m.chunks_recuperados || 0,
      })));
      
      if (msgs.length > 0 && !selectedId) {
        setSelectedId(msgs[0].id);
      }
    } catch (err) {
      setError('Erro ao carregar fila: ' + err.message);
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchMessages();
  }, [clienteId]);

  useEffect(() => {
    const activeMsg = messages.find((m) => m.id === selectedId);
    if (activeMsg) {
      setEditedResponse(activeMsg.suggested_response || '');
    } else {
      setEditedResponse('');
    }
  }, [selectedId, messages]);

  const handleApprove = async () => {
    const activeMsg = messages.find((m) => m.id === selectedId);
    if (!activeMsg || !editedResponse.trim()) return;

    setActionInProgress('approve');
    setError(null);
    try {
      await mensagemService.approve(activeMsg.id, editedResponse);
      setSelectedId(null);
      fetchMessages();
    } catch (err) {
      setError('Erro ao aprovar: ' + err.message);
      console.error(err);
    } finally {
      setActionInProgress(null);
    }
  };

  const handleReject = async () => {
    const activeMsg = messages.find((m) => m.id === selectedId);
    if (!activeMsg) return;

    const motivo = prompt('Motivo da rejeição:');
    if (!motivo) return;

    setActionInProgress('reject');
    setError(null);
    try {
      await mensagemService.reject(activeMsg.id, motivo);
      setSelectedId(null);
      fetchMessages();
    } catch (err) {
      setError('Erro ao rejeitar: ' + err.message);
      console.error(err);
    } finally {
      setActionInProgress(null);
    }
  };

  const handleSend = async () => {
    const activeMsg = messages.find((m) => m.id === selectedId);
    if (!activeMsg || !editedResponse.trim()) return;

    setActionInProgress('send');
    setError(null);
    try {
      await mensagemService.approve(activeMsg.id, editedResponse);
      setSelectedId(null);
      fetchMessages();
    } catch (err) {
      setError('Erro ao enviar: ' + err.message);
      console.error(err);
    } finally {
      setActionInProgress(null);
    }
  };

  if (!clienteId) {
    return (
      <div className="col-span-12 card bg-gradient-to-br from-green-50 to-emerald-50 border-green-200 animate-fade-in">
        <div className="flex items-center justify-center flex-col p-8 text-center">
          <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-green-500 to-green-600 flex items-center justify-center mb-4 shadow-lg shadow-green-500/25">
            <MessageSquare className="w-7 h-7 text-white" />
          </div>
          <h3 className="text-lg font-bold text-slate-800 mb-1">Selecione um cliente</h3>
          <p className="text-slate-500 text-sm">Use o seletor no topo para escolher um cliente e ver sua fila de aprovação.</p>
        </div>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="col-span-12 card animate-fade-in">
        <div className="flex flex-col items-center justify-center p-12">
          <Loader2 className="w-10 h-10 text-green-600 animate-spin" />
          <p className="text-slate-500 text-sm mt-3">Carregando fila de aprovação...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="col-span-12 card border-red-200 bg-red-50 animate-slide-down">
        <div className="flex items-center gap-3 p-4">
          <div className="w-10 h-10 rounded-xl bg-red-100 flex items-center justify-center flex-shrink-0">
            <AlertCircle className="w-5 h-5 text-red-600" />
          </div>
          <span className="text-sm text-red-700 flex-1">{error}</span>
          <button onClick={fetchMessages} className="btn btn-danger btn-sm">Tentar novamente</button>
        </div>
      </div>
    );
  }

  const activeMsg = messages.find((m) => m.id === selectedId);

  if (!messages.length) {
    return (
      <div className="col-span-12 card animate-fade-in">
        <div className="flex flex-col items-center justify-center p-12 text-center">
          <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-emerald-100 to-green-100 flex items-center justify-center mb-4">
            <CheckCircle2 className="w-7 h-7 text-emerald-600" />
          </div>
          <h3 className="text-lg font-bold text-slate-800 mb-1">Tudo limpo por aqui!</h3>
          <p className="text-slate-500 text-sm">Nenhuma mensagem pendente de aprovação no momento.</p>
        </div>
      </div>
    );
  }

  const getChannelConfig = (channel) => {
    const configs = {
      whatsapp: { label: 'WhatsApp', color: 'bg-emerald-100 text-emerald-700', icon: MessageSquare },
      outlook: { label: 'Outlook', color: 'bg-blue-100 text-blue-700', icon: Mail },
      web: { label: 'Web', color: 'bg-slate-100 text-slate-700', icon: MessageSquare },
      api: { label: 'API', color: 'bg-purple-100 text-purple-700', icon: Zap },
    };
    return configs[channel] || configs.web;
  };

  return (
    <div className="grid grid-cols-12 gap-6 h-[calc(100vh-200px)] min-h-[600px]">
      {/* Lista Lateral de Mensagens Pendentes */}
      <div className="col-span-12 lg:col-span-5 card flex flex-col overflow-hidden animate-slide-up">
        <div className="p-4 border-b border-green-100 bg-green-50/30 flex justify-between items-center">
          <h2 className="font-bold text-slate-800 text-sm flex items-center gap-2">
            <MessageSquare className="w-4 h-4 text-green-600" />
            Pendentes ({messages.length})
          </h2>
          <button
            onClick={fetchMessages}
            disabled={loading}
            className="btn btn-secondary btn-sm flex items-center gap-1.5"
          >
            <Loader2 className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
            Atualizar
          </button>
        </div>
        <div className="flex-1 overflow-y-auto divide-y divide-green-100/50">
          {messages.map((item) => {
            const channelConfig = getChannelConfig(item.channel);
            const ChannelIcon = channelConfig.icon;
            const isSelected = selectedId === item.id;

            return (
              <button
                key={item.id}
                onClick={() => setSelectedId(item.id)}
                className={`w-full text-left p-4 transition-all duration-200 flex flex-col gap-2 ${
                  isSelected
                    ? 'bg-gradient-to-r from-green-50 to-emerald-50 border-l-4 border-green-500'
                    : 'hover:bg-green-50/50'
                }`}
                aria-pressed={isSelected}
              >
                <div className="flex justify-between items-center w-full">
                  <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider ${channelConfig.color}`}>
                    <ChannelIcon className="w-3 h-3" />
                    {channelConfig.label}
                  </span>
                  <span className="text-xs text-slate-400">{item.time}</span>
                </div>
                <p className="font-semibold text-slate-800 text-sm line-clamp-1">{item.client_name}</p>
                <p className="text-xs text-slate-500 line-clamp-2">{item.question}</p>
                <div className="flex items-center justify-between pt-1">
                  <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full font-mono text-[10px] font-bold ${
                    item.score >= 0.8 ? 'bg-emerald-100 text-emerald-700' :
                    item.score >= 0.5 ? 'bg-amber-100 text-amber-700' :
                    'bg-red-100 text-red-700'
                  }`}>
                    {(item.score * 100).toFixed(0)}%
                  </span>
                  <span className="text-xs text-slate-400 font-mono">{item.chunks} chunks</span>
                </div>
              </button>
            );
          })}
        </div>
      </div>

      {/* Painel Detalhado de Edição e Aprovação */}
      {activeMsg && (
        <div className="col-span-12 lg:col-span-7 card flex flex-col animate-slide-in-right">
          <div className="flex-1 overflow-y-auto p-6 space-y-6">
            {/* Cabeçalho do Cliente */}
            <div className="flex items-center justify-between pb-4 border-b border-green-100">
              <div>
                <h3 className="text-lg font-bold text-slate-800">{activeMsg.client_name}</h3>
                <div className="flex items-center gap-2 text-xs text-slate-500 mt-1">
                  <Building2 className="w-3.5 h-3.5" />
                  <span>{activeMsg.company || 'Empresa não identificada'}</span>
                </div>
              </div>
            </div>

            {/* Pergunta Original */}
            <div className="card bg-slate-50 border-slate-200">
              <span className="text-xs font-bold text-slate-400 uppercase tracking-wider flex items-center gap-1.5 mb-2">
                <MessageSquare className="w-3.5 h-3.5 text-green-600" />
                Pergunta Recebida
              </span>
              <p className="text-slate-700 text-sm">{activeMsg.question}</p>
            </div>

            {/* Fontes Consultadas (RAG) */}
            {activeMsg.sources && activeMsg.sources.length > 0 && (
              <div className="card bg-amber-50/50 border-amber-100">
                <span className="text-xs font-bold text-amber-700 uppercase tracking-wider flex items-center gap-1.5 mb-2">
                  <Brain className="w-3.5 h-3.5" />
                  Fontes Consultadas na Base
                </span>
                <ul className="text-xs text-amber-900 space-y-1 list-disc list-inside">
                  {activeMsg.sources.map((src, idx) => (
                    <li key={idx}>{src}</li>
                  ))}
                </ul>
              </div>
            )}

            {/* Campo Editável da Resposta */}
            <div>
              <span className="text-xs font-bold text-slate-400 uppercase tracking-wider flex items-center gap-1.5 mb-2">
                <Edit3 className="w-3.5 h-3.5 text-green-600" />
                Resposta da IA (Editável)
              </span>
              <textarea
                value={editedResponse}
                onChange={(e) => setEditedResponse(e.target.value)}
                rows={6}
                className="w-full p-4 text-sm text-slate-700 bg-white border border-green-200 rounded-xl focus:ring-2 focus:ring-green-500/20 focus:border-green-400 outline-none resize-none shadow-sm"
                placeholder="Edite a resposta gerada pela IA antes de aprovar..."
              />
              <p className="text-xs text-slate-500 mt-2 text-right">{editedResponse.length} caracteres</p>
            </div>
          </div>

          {/* Botões de Ação */}
          <div className="flex items-center justify-end gap-3 p-6 border-t border-green-100 bg-green-50/30 rounded-b-xl">
            <button
              onClick={handleReject}
              disabled={actionInProgress !== null}
              className="btn btn-danger flex items-center gap-2"
            >
              <XCircle className="w-4 h-4" /> Rejeitar
            </button>
            <button
              onClick={handleApprove}
              disabled={actionInProgress !== null || !editedResponse.trim()}
              className="btn btn-primary flex items-center gap-2"
            >
              <CheckCircle2 className="w-4 h-4" /> {actionInProgress === 'approve' ? 'Aprovando...' : 'Aprovar'}
            </button>
            <button
              onClick={handleSend}
              disabled={actionInProgress !== null || !editedResponse.trim()}
              className="btn btn-secondary flex items-center gap-2"
            >
              <Send className="w-4 h-4" /> {actionInProgress === 'send' ? 'Enviando...' : 'Aprovar e Enviar'}
            </button>
          </div>
        </div>
      )}
    </div>
  );
}