import React, { useState, useEffect } from 'react';
import Sidebar from './components/Sidebar';
import Dashboard from './components/Dashboard';
import ApprovalQueue from './components/ApprovalQueue';
import KnowledgeBase from './components/KnowledgeBase';
import Logs from './pages/Logs';
import { mensagemService } from './services/api';
import './index.css';

export default function App() {
  const [activeTab, setActiveTab] = useState('queue');
  const [clienteId, setClienteId] = useState(null);
  const [clientes, setClientes] = useState([]);

  useEffect(() => {
    fetchClientes();
  }, []);

  const fetchClientes = async () => {
    try {
      const response = await fetch(`${process.env.REACT_APP_API_URL || 'http://localhost:8000'}/clientes`);
      const data = await response.json();
      if (data.clientes && data.clientes.length > 0) {
        setClientes(data.clientes);
        if (!clienteId) {
          setClienteId(data.clientes[0].id);
        }
      }
    } catch (err) {
      console.error('Erro ao carregar clientes:', err);
    }
  };

  const handleApprove = async (id, newText) => {
    try {
      await mensagemService.approve(id, newText);
    } catch (err) {
      console.error('Erro ao aprovar:', err);
    }
  };

  const handleReject = async (id) => {
    const motivo = prompt('Motivo da rejeição:');
    if (!motivo) return;
    try {
      await mensagemService.reject(id, motivo);
    } catch (err) {
      console.error('Erro ao rejeitar:', err);
    }
  };

  if (!clienteId && clientes.length === 0) {
    return (
      <div className="flex min-h-screen bg-green-50 font-sans text-slate-900 items-center justify-center">
        <div className="card max-w-md w-full mx-4 bg-gradient-to-br from-green-50 to-emerald-50 border-green-200">
          <div className="text-center">
            <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-green-500 to-green-600 flex items-center justify-center mx-auto mb-4 shadow-lg shadow-green-500/25">
              <svg className="w-8 h-8 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6V4m0 2a2 2 0 100 4m0-4a2 2 0 110 4m-6 8a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4m6 6v10m6-2a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4" />
              </svg>
            </div>
            <h2 className="text-lg font-bold text-slate-800 mb-4">Nenhum cliente cadastrado</h2>
            <p className="text-slate-500 text-sm mb-6">Crie um cliente via API primeiro:</p>
            <pre className="bg-slate-900 text-green-300 p-4 rounded-xl text-xs text-left overflow-auto font-mono">
{`curl -X POST http://localhost:8000/clientes \\
  -H "Content-Type: application/json" \\
  -d '{
    "nome": "Minha Empresa",
    "empresa": "Empresa Ltda",
    "descricao": "Cliente de teste"
  }'`}
            </pre>
          </div>
        </div>
      </div>
    );
  }

  const tabConfig = {
    queue: { label: 'Fila de Aprovação', icon: '📋' },
    dashboard: { label: 'Dashboard', icon: '📊' },
    knowledge: { label: 'Base de Conhecimento', icon: '📚' },
    logs: { label: 'Logs & Diagnóstico', icon: '📋' },
    clients: { label: 'Clientes', icon: '👥' },
  };

  const currentTab = tabConfig[activeTab] || { label: activeTab, icon: '📄' };

  return (
    <div className="flex min-h-screen bg-green-50 font-sans text-slate-900">
      <Sidebar activeTab={activeTab} setActiveTab={setActiveTab} />

      <main className="flex-1 p-6 lg:p-8 overflow-y-auto">
        <header className="mb-8 flex flex-col lg:flex-row lg:justify-between lg:items-center gap-4">
          <div>
            <h1 className="text-2xl lg:text-3xl font-bold text-gradient">
              {currentTab.label}
            </h1>
            <p className="text-slate-500 text-sm mt-1">
              {activeTab === 'logs'
                ? 'Monitore em tempo real a saúde do sistema, banco de dados e APIs de IA.'
                : 'Gerencie o atendimento inteligente da sua empresa.'}
            </p>
          </div>
          <select
            value={clienteId || ''}
            onChange={(e) => setClienteId(e.target.value ? Number(e.target.value) : null)}
            className="w-full lg:w-64 px-4 py-3 bg-white border border-green-200 rounded-xl text-sm focus:ring-2 focus:ring-green-500/20 focus:border-green-400 cursor-pointer appearance-none bg-[url('data:image/svg+xml,%3Csvg xmlns=%27http://www.w3.org/2000/svg%27 fill=%27none%27 viewBox=%270 0 20 20%27%3E%3Cpath stroke=%27%236b8e72%27 stroke-linecap=%27round%27 stroke-linejoin=%27round%27 stroke-width=%271.5%27 d=%27M6 8l4 4 4-4%27/%3E%3C/svg%3E')] bg-[right_12px_center] bg-no-repeat bg-[length:16px] pr-10"
          >
            <option value="">Selecione o cliente...</option>
            {clientes.map((c) => (
              <option key={c.id} value={c.id}>
                {c.nome} ({c.empresa})
              </option>
            ))}
          </select>
        </header>

        {activeTab === 'dashboard' && <Dashboard clienteId={clienteId} />}
        {activeTab === 'queue' && <ApprovalQueue clienteId={clienteId} />}
        {activeTab === 'knowledge' && <KnowledgeBase clienteId={clienteId} />}
        {activeTab === 'logs' && <Logs clienteId={clienteId} />}
        {activeTab === 'clients' && (
          <div className="card bg-white border-green-100 text-center py-12">
            <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-green-100 to-emerald-100 flex items-center justify-center mx-auto mb-4">
              <svg className="w-8 h-8 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
              </svg>
            </div>
            <h3 className="text-lg font-bold text-slate-800 mb-2">Módulo de Clientes</h3>
            <p className="text-slate-500 text-sm">Módulo de mapeamento de clientes em desenvolvimento.</p>
          </div>
        )}
      </main>
    </div>
  );
}