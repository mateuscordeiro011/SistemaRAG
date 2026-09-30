import React, { useState } from 'react';
import {
  LayoutDashboard,
  ClipboardList,
  Database,
  Terminal,
  Users,
  ChevronLeft,
  ChevronRight,
} from 'lucide-react';

export default function Sidebar({ activeTab, setActiveTab }) {
  const [collapsed, setCollapsed] = useState(false);

  const tabs = [
    { id: 'queue', label: 'Fila de Aprovação', icon: ClipboardList },
    { id: 'dashboard', label: 'Dashboard', icon: LayoutDashboard },
    { id: 'knowledge', label: 'Base de Conhecimento', icon: Database },
    { id: 'logs', label: 'Logs & Diagnóstico', icon: Terminal },
    { id: 'clients', label: 'Clientes', icon: Users },
  ];

  return (
    <aside className={`flex flex-col transition-all duration-300 ease-out ${
      collapsed ? 'w-20' : 'w-72'
    } bg-gradient-to-b from-green-950 to-green-900 text-green-50 border-r border-green-800`}>
      {/* Header */}
      <div className="p-6 border-b border-green-800 flex items-center justify-between">
        {!collapsed && (
          <div className="flex-1 min-w-0">
            <h1 className="text-xl font-bold text-green-400 tracking-tight">SistemaRAG</h1>
            <p className="text-xs text-green-400/70 mt-1">Painel de Controle</p>
          </div>
        )}
        <button
          onClick={() => setCollapsed(!collapsed)}
          className="p-2 rounded-xl text-green-300 hover:text-green-100 hover:bg-green-800/50 transition-all duration-200 flex-shrink-0"
          aria-label={collapsed ? 'Expandir menu' : 'Colapsar menu'}
        >
          {collapsed ? <ChevronRight size={18} /> : <ChevronLeft size={18} />}
        </button>
      </div>

      {/* Navigation */}
      <nav className="flex-1 p-4 space-y-1.5 overflow-y-auto">
        {tabs.map((tab) => {
          const Icon = tab.icon;
          const isActive = activeTab === tab.id;
          
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`
                w-full relative overflow-hidden rounded-xl transition-all duration-200 ease-out
                flex items-center gap-3 px-4 py-3
                ${isActive 
                  ? 'bg-gradient-to-r from-green-600/20 to-green-500/10 text-white font-medium shadow-[0_4px_14px_-2px_rgba(34,197,94,0.35)] border border-green-600/30'
                  : 'text-green-300/80 hover:text-white hover:bg-green-800/30'
                }
                ${collapsed ? 'justify-center' : 'justify-start'}
              `}
              title={collapsed ? tab.label : undefined}
            >
              <span className="flex-shrink-0 w-5 h-5 flex items-center justify-center">
                <Icon size={18} strokeWidth={2.5} aria-hidden="true" />
              </span>
              {!collapsed && (
                <span className="truncate transition-opacity duration-200">{tab.label}</span>
              )}
              {isActive && !collapsed && (
                <span className="absolute left-0 top-1/2 -translate-y-1/2 w-1 h-6 bg-green-400 rounded-r-full" />
              )}
            </button>
          );
        })}
      </nav>

      {/* Footer */}
      <div className="p-4 border-t border-green-800">
        {!collapsed ? (
          <div className="flex items-center gap-3 p-3 rounded-xl bg-green-800/30">
            <div className="w-8 h-8 rounded-xl bg-gradient-to-br from-green-500 to-green-600 flex items-center justify-center flex-shrink-0">
              <Database size={14} className="text-green-950" />
            </div>
            <div className="min-w-0 flex-1">
              <p className="text-xs font-medium text-green-100 truncate">Base de Conhecimento</p>
              <p className="text-[10px] text-green-400/70">v2.0.0 • Produção</p>
            </div>
          </div>
        ) : (
          <div className="flex justify-center">
            <div className="w-8 h-8 rounded-xl bg-gradient-to-br from-green-500 to-green-600 flex items-center justify-center">
              <Database size={14} className="text-green-950" />
            </div>
          </div>
        )}
      </div>
    </aside>
  );
}