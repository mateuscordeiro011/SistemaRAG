import React, { useState } from 'react';
import { LayoutDashboard, CheckSquare, Database, Users, Bot, Terminal, AlertCircle } from 'lucide-react';

export default function Sidebar({ activeTab, setActiveTab }) {
  // Contador de notificações de erro (mockado)
  const errorCount = 3;

  const menuItems = [
    { id: 'dashboard', label: 'Visão Geral', icon: LayoutDashboard },
    { id: 'queue', label: 'Fila de Aprovação', icon: CheckSquare },
    { id: 'knowledge', label: 'Base de Conhecimento', icon: Database },
    { id: 'logs', label: 'Logs & Diagnóstico', icon: Terminal, badge: errorCount > 0 ? errorCount : null },
    { id: 'clients', label: 'Clientes e Empresas', icon: Users },
  ];

  return (
    <aside className="w-64 bg-slate-900 text-slate-100 flex flex-col h-screen sticky top-0 border-r border-slate-800">
      <div className="p-6 flex items-center gap-3 border-b border-slate-800">
        <div className="bg-indigo-600 p-2 rounded-lg">
          <Bot className="w-6 h-6 text-white" />
        </div>
        <div>
          <h1 className="font-bold text-lg leading-tight">AI Assistant</h1>
          <span className="text-xs text-slate-400">Painel de Controle</span>
        </div>
      </div>

      <nav className="flex-1 p-4 space-y-1">
        {menuItems.map((item) => {
          const Icon = item.icon;
          const isActive = activeTab === item.id;
          return (
            <button
              key={item.id}
              onClick={() => setActiveTab(item.id)}
              className={`w-full flex items-center gap-3 px-4 py-3 rounded-xl font-medium text-sm transition-colors relative group ${
                isActive
                  ? 'bg-indigo-600 text-white shadow-lg shadow-indigo-600/30'
                  : 'text-slate-400 hover:bg-slate-800 hover:text-slate-200'
              }`}
            >
              <Icon className="w-5 h-5" />
              <span className="flex-1">{item.label}</span>
              {item.badge && (
                <div className="flex items-center justify-center w-6 h-6 bg-red-600 text-white text-xs font-bold rounded-full animate-pulse">
                  {item.badge}
                </div>
              )}
            </button>
          );
        })}
      </nav>

      <div className="p-4 border-t border-slate-800">
        <div className="bg-slate-800/50 p-3 rounded-xl flex items-center gap-3">
          <div className="w-3 h-3 rounded-full bg-emerald-500 animate-pulse"></div>
          <span className="text-xs text-slate-300 font-medium">Sistema Conectado</span>
        </div>
      </div>
    </aside>
  );
}