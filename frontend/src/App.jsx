import React, { useState } from 'react';
import Sidebar from './components/Sidebar';
import Dashboard from './components/Dashboard';
import ApprovalQueue from './components/ApprovalQueue';
import KnowledgeBase from './components/KnowledgeBase';
import Logs from './pages/Logs';
import './index.css';


export default function App() {
  const [activeTab, setActiveTab] = useState('queue');

  // Dados mockados de exemplo para teste imediato
  const [messages, setMessages] = useState([
    {
      id: 1,
      client_name: 'João Silva',
      company: 'Tech Solutions Ltd',
      channel: 'whatsapp',
      question: 'Qual o prazo de garantia para o contrato de manutenção?',
      suggested_response: 'Olá João! O prazo padrão de garantia para o contrato de manutenção é de 12 meses conforme a nossa política comercial vigente.',
      sources: ['politica_comercial_2026.pdf (pág. 3)'],
      time: '10:42',
    },
  ]);

  const handleApprove = (id, newText) => {
    console.log('Aprovado:', id, newText);
    setMessages((prev) => prev.filter((m) => m.id !== id));
  };

  const handleReject = (id) => {
    console.log('Rejeitado:', id);
    setMessages((prev) => prev.filter((m) => m.id !== id));
  };

  return (
    <div className="flex min-h-screen bg-slate-50 font-sans text-slate-900">
      <Sidebar activeTab={activeTab} setActiveTab={setActiveTab} />

      <main className="flex-1 p-8 overflow-y-auto">
        <header className="mb-8">
          <h1 className="text-2xl font-bold text-slate-900 capitalize">
            {activeTab === 'queue'
              ? 'Fila de Aprovação'
              : activeTab === 'knowledge'
                ? 'Base de Conhecimento'
                : activeTab === 'logs'
                  ? 'Logs & Diagnóstico do Sistema'
                  : activeTab}
          </h1>
          <p className="text-slate-500 text-sm">
            {activeTab === 'logs'
              ? 'Monitore em tempo real a saúde do sistema, banco de dados e APIs de IA.'
              : 'Gerencie o atendimento inteligente da sua empresa.'}
          </p>
        </header>

        {activeTab === 'dashboard' && <Dashboard />}
        {activeTab === 'queue' && <ApprovalQueue messages={messages} onApprove={handleApprove} onReject={handleReject} />}
        {activeTab === 'knowledge' && <KnowledgeBase />}
        {activeTab === 'logs' && <Logs />}
        {activeTab === 'clients' && (
          <div className="bg-white p-8 rounded-2xl border border-slate-100 text-slate-500 text-sm">
            Módulo de mapeamento de clientes em desenvolvimento.
          </div>
        )}
      </main>
    </div>
  );
}