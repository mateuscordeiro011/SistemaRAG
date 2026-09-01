import React, { useState } from 'react';
import { Send, XCircle, Edit3, MessageSquare, Building2, FileText, CheckCircle2 } from 'lucide-react';

export default function ApprovalQueue({ messages = [], onApprove, onReject }) {
  const [selectedId, setSelectedId] = useState(messages[0]?.id || null);
  const [editedResponse, setEditedResponse] = useState('');

  const activeMsg = messages.find((m) => m.id === selectedId) || messages[0];

  React.useEffect(() => {
    if (activeMsg) {
      setEditedResponse(activeMsg.suggested_response || '');
    }
  }, [selectedId, activeMsg]);

  if (!messages.length) {
    return (
      <div className="bg-white rounded-2xl p-12 text-center shadow-sm border border-slate-100">
        <CheckCircle2 className="w-12 h-12 text-emerald-500 mx-auto mb-4" />
        <h3 className="text-lg font-bold text-slate-800">Tudo limpo por aqui!</h3>
        <p className="text-slate-500 text-sm mt-1">Nenhuma mensagem pendente de aprovação no momento.</p>
      </div>
    );
  }

  return (
    <div className="grid grid-cols-12 gap-6 h-[calc(100vh-140px)]">
      {/* Lista Lateral de Mensagens Pendentes */}
      <div className="col-span-5 bg-white rounded-2xl shadow-sm border border-slate-100 flex flex-col overflow-hidden">
        <div className="p-4 border-b border-slate-100 bg-slate-50/50">
          <h2 className="font-bold text-slate-800 text-sm">Pendentes ({messages.length})</h2>
        </div>
        <div className="flex-1 overflow-y-auto divide-y divide-slate-100">
          {messages.map((item) => (
            <button
              key={item.id}
              onClick={() => setSelectedId(item.id)}
              className={`w-full text-left p-4 transition-colors flex flex-col gap-2 ${
                selectedId === item.id ? 'bg-indigo-50/50 border-l-4 border-indigo-600' : 'hover:bg-slate-50'
              }`}
            >
              <div className="flex justify-between items-center w-full">
                <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full uppercase tracking-wider ${
                  item.channel === 'whatsapp' ? 'bg-emerald-100 text-emerald-700' : 'bg-blue-100 text-blue-700'
                }`}>
                  {item.channel}
                </span>
                <span className="text-xs text-slate-400">{item.time || 'Recente'}</span>
              </div>
              <p className="font-semibold text-slate-800 text-sm line-clamp-1">{item.client_name}</p>
              <p className="text-xs text-slate-500 line-clamp-2">{item.question}</p>
            </button>
          ))}
        </div>
      </div>

      {/* Painel Detalhado de Edição e Aprovação */}
      {activeMsg && (
        <div className="col-span-7 bg-white rounded-2xl shadow-sm border border-slate-100 p-6 flex flex-col justify-between overflow-y-auto">
          <div className="space-y-6">
            {/* Cabeçalho do Cliente */}
            <div className="flex items-center justify-between pb-4 border-b border-slate-100">
              <div>
                <h3 className="text-lg font-bold text-slate-800">{activeMsg.client_name}</h3>
                <div className="flex items-center gap-2 text-xs text-slate-500 mt-1">
                  <Building2 className="w-3.5 h-3.5" />
                  <span>{activeMsg.company || 'Empresa não identificada'}</span>
                </div>
              </div>
            </div>

            {/* Pergunta Original */}
            <div className="bg-slate-50 p-4 rounded-xl border border-slate-100">
              <span className="text-xs font-bold text-slate-400 uppercase tracking-wider flex items-center gap-1.5 mb-2">
                <MessageSquare className="w-3.5 h-3.5" /> Pergunta Recebida
              </span>
              <p className="text-slate-700 text-sm">{activeMsg.question}</p>
            </div>

            {/* Trechos Consultados (RAG) */}
            {activeMsg.sources && (
              <div className="bg-amber-50/50 p-4 rounded-xl border border-amber-100">
                <span className="text-xs font-bold text-amber-700 uppercase tracking-wider flex items-center gap-1.5 mb-2">
                  <FileText className="w-3.5 h-3.5" /> Fontes Consultadas na Base
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
                <Edit3 className="w-3.5 h-3.5" /> Resposta da IA (Editável)
              </span>
              <textarea
                value={editedResponse}
                onChange={(e) => setEditedResponse(e.target.value)}
                rows={6}
                className="w-full p-4 text-sm text-slate-700 bg-white border border-slate-200 rounded-xl focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none resize-none shadow-sm"
              />
            </div>
          </div>

          {/* Botões de Ação */}
          <div className="flex items-center justify-end gap-3 pt-4 border-t border-slate-100 mt-6">
            <button
              onClick={() => onReject(activeMsg.id)}
              className="flex items-center gap-2 px-4 py-2.5 rounded-xl border border-rose-200 text-rose-600 font-medium text-sm hover:bg-rose-50 transition-colors"
            >
              <XCircle className="w-4 h-4" /> Rejeitar
            </button>
            <button
              onClick={() => onApprove(activeMsg.id, editedResponse)}
              className="flex items-center gap-2 px-6 py-2.5 rounded-xl bg-indigo-600 text-white font-medium text-sm hover:bg-indigo-700 shadow-lg shadow-indigo-600/20 transition-all"
            >
              <Send className="w-4 h-4" /> Aprovar e Enviar
            </button>
          </div>
        </div>
      )}
    </div>
  );
}