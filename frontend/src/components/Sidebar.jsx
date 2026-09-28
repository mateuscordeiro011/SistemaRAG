import React, { useState } from 'react';

export default function Sidebar({ activeTab, setActiveTab }) {
  const tabs = [
    { id: 'queue', label: 'Fila de Aprovação', icon: '📋' },
    { id: 'dashboard', label: 'Dashboard', icon: '📊' },
    { id: 'knowledge', label: 'Base de Conhecimento', icon: '📚' },
    { id: 'logs', label: 'Logs & Diagnóstico', icon: '📋' },
    { id: 'clients', label: 'Clientes', icon: '👥' },
  ];

  return (
    <aside className="w-64 bg-white border-r border-slate-200 flex flex-col">
      <div className="p-6 border-b border-slate-200">
        <h1 className="text-xl font-bold text-indigo-600">SistemaRAG</h1>
        <p className="text-xs text-slate-500 mt-1">Painel de Controle</p>
      </div>
      
      <nav className="flex-1 p-4 space-y-2">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`w-full text-left px-4 py-3 rounded-xl transition-all flex items-center gap-3 ${
              activeTab === tab.id
                ? 'bg-indigo-50 text-indigo-700 font-medium shadow-sm'
                : 'text-slate-600 hover:bg-slate-50 hover:text-slate-900'
            }`}
          >
            <span className="text-lg">{tab.icon}</span>
            <span>{tab.label}</span>
          </button>
        ))}
      </nav>
      
      <div className="p-4 border-t border-slate-200 text-xs text-slate-500">
        <p>v1.0.0</p>
      </div>
    </aside>
  );
}