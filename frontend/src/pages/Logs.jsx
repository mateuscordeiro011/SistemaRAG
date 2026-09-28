import React, { useState, useEffect, useRef } from 'react';
import {
  Search,
  Filter,
  Download,
  Trash2,
  RotateCcw,
  ChevronDown,
  ChevronUp,
  Copy,
  Check,
  AlertCircle,
  CircleCheck,
  CircleAlert,
  Terminal,
} from 'lucide-react';
import LogBadge from '../components/LogBadge';

/**
 * Componente Logs.jsx - Sistema completo de visualização e filtragem de logs
 * 
 * Funcionalidades:
 * - Filtros por nível (erro, sucesso, aviso, info)
 * - Filtro por canal (RAG/IA, MySQL, WhatsApp, Outlook, etc)
 * - Busca textual por palavra-chave
 * - Auto-scroll para logs em tempo real
 * - Expansão de linha para ver detalhes JSON
 * - Exportação em JSON/CSV
 * - Limpeza de logs
*/

export default function Logs() {
  const [logs, setLogs] = useState([]);
  const [filteredLogs, setFilteredLogs] = useState([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedLevel, setSelectedLevel] = useState('todos');
  const [selectedChannel, setSelectedChannel] = useState('general');
  const [expandedLogId, setExpandedLogId] = useState(null);
  const [autoScroll, setAutoScroll] = useState(true);
  const [copiedId, setCopiedId] = useState(null);
  const logsContainerRef = useRef(null);

  // Níveis e canais disponíveis
  const levels = [
    { value: 'todos', label: 'Todos', color: 'slate' },
    { value: 'success', label: 'Sucesso', color: 'emerald' },
    { value: 'error', label: 'Erro', color: 'red' },
    { value: 'warning', label: 'Aviso', color: 'amber' },
    { value: 'info', label: 'Info', color: 'blue' },
  ];

  const channels = [
    { value: 'general', label: 'Geral' },
    { value: 'rag', label: 'RAG/IA' },
    { value: 'mysql', label: 'MySQL' },
    { value: 'whatsapp', label: 'WhatsApp' },
    { value: 'outlook', label: 'Outlook' },
  ];

  // Atualizar filtros quando search ou level mudarem
  useEffect(() => {
    let result = logs;

    // Filtro por nível
    if (selectedLevel !== 'todos') {
      result = result.filter((log) => log.level === selectedLevel);
    }

    // Filtro por canal
    if (selectedChannel !== 'general') {
      result = result.filter((log) => log.channel === selectedChannel);
    } else if (selectedChannel === 'general') {
      result = result.filter((log) => log.channel === 'general');
    }

    // Filtro por busca textual
    if (searchTerm.trim()) {
      const term = searchTerm.toLowerCase();
      result = result.filter(
        (log) =>
          log.message.toLowerCase().includes(term) ||
          log.module.toLowerCase().includes(term) ||
          JSON.stringify(log.details).toLowerCase().includes(term)
      );
    }

    setFilteredLogs(result);
    setExpandedLogId(null);
  }, [searchTerm, selectedLevel, selectedChannel, logs]);

  // Auto-scroll para o último log quando há novos
  useEffect(() => {
    if (autoScroll && logsContainerRef.current) {
      setTimeout(() => {
        logsContainerRef.current?.scrollTo({
          top: logsContainerRef.current.scrollHeight,
          behavior: 'smooth',
        });
      }, 100);
    }
  }, [filteredLogs, autoScroll]);

  // Simular recepção de novos logs (para demonstração)
  useEffect(() => {
    const interval = setInterval(() => {
      // Chance de 30% de novo log aparecer a cada 5 segundos
      if (Math.random() > 0.7) {
        const newLog = {
          id: `log_${Date.now()}`,
          timestamp: new Date(),
          level: ['success', 'info', 'warning', 'error'][Math.floor(Math.random() * 4)],
          channel: channels[Math.floor(Math.random() * channels.length)].value,
          module: 'Sistema',
          message: `Nova operação registrada em tempo real - ${new Date().toLocaleTimeString()}`,
          duration_ms: Math.floor(Math.random() * 5000),
          details: { timestamp: new Date().toISOString() },
        };
        setLogs((prev) => [newLog, ...prev]);
      }
    }, 5000);

    return () => clearInterval(interval);
  }, []);

  // Funções de ação
  const handleClearLogs = () => {
    if (window.confirm('Tem certeza que deseja limpar todos os logs?')) {
      setLogs([]);
      setFilteredLogs([]);
    }
  };

  const handleExportJSON = () => {
    const dataStr = JSON.stringify(filteredLogs, null, 2);
    downloadFile(dataStr, 'logs.json', 'application/json');
  };

  const handleExportCSV = () => {
    const headers = ['Timestamp', 'Nível', 'Canal', 'Módulo', 'Mensagem', 'Duração (ms)'];
    const rows = filteredLogs.map((log) => [
      new Date(log.timestamp).toLocaleString('pt-BR'),
      log.level.toUpperCase(),
      log.channel.toUpperCase(),
      log.module,
      `"${log.message}"`,
      log.duration_ms,
    ]);

    const csv = [headers, ...rows].map((row) => row.join(',')).join('\n');
    downloadFile(csv, 'logs.csv', 'text/csv');
  };

  const downloadFile = (content, filename, type) => {
    const element = document.createElement('a');
    element.setAttribute('href', `data:${type};charset=utf-8,${encodeURIComponent(content)}`);
    element.setAttribute('download', filename);
    element.style.display = 'none';
    document.body.appendChild(element);
    element.click();
    document.body.removeChild(element);
  };

  const handleCopyJSON = (logId) => {
    const log = logs.find((l) => l.id === logId);
    if (log) {
      navigator.clipboard.writeText(JSON.stringify(log, null, 2));
      setCopiedId(logId);
      setTimeout(() => setCopiedId(null), 2000);
    }
  };

  const formatTimestamp = (date) => {
    return new Date(date).toLocaleString('pt-BR', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
    });
  };

  const getLevelColor = (level) => {
    const colors = {
      error: 'red',
      success: 'emerald',
      warning: 'amber',
      info: 'blue',
    };
    return colors[level] || 'slate';
  };

  return (
    <div className="space-y-6">
      {/* Header com Estatísticas Rápidas */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        {[
          { label: 'Total de Logs', value: logs.length, icon: '📊', color: 'blue' },
          { label: 'Erros', value: logs.filter((l) => l.level === 'error').length, icon: '🔴', color: 'red' },
          { label: 'Avisos', value: logs.filter((l) => l.level === 'warning').length, icon: '🟡', color: 'amber' },
          { label: 'Sucessos', value: logs.filter((l) => l.level === 'success').length, icon: '✅', color: 'emerald' },
        ].map((stat, idx) => (
          <div
            key={idx}
            className={`bg-gradient-to-br from-${stat.color}-50 to-${stat.color}-100 dark:from-${stat.color}-900/20 dark:to-${stat.color}-800/20 border border-${stat.color}-200 dark:border-${stat.color}-700/50 rounded-lg p-4`}
          >
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-slate-600 dark:text-slate-400">{stat.label}</p>
                <p className="text-2xl font-bold text-slate-900 dark:text-white mt-1">{stat.value}</p>
              </div>
              <span className="text-3xl">{stat.icon}</span>
            </div>
          </div>
        ))}
      </div>

      {/* Barra de Controle e Filtros */}
      <div className="bg-white dark:bg-slate-800 rounded-xl shadow-sm border border-slate-200 dark:border-slate-700 p-6 space-y-4">
        {/* Busca */}
        <div className="flex items-center gap-2 px-4 py-3 bg-slate-50 dark:bg-slate-900/50 rounded-lg border border-slate-200 dark:border-slate-700">
          <Search className="w-5 h-5 text-slate-400" />
          <input
            type="text"
            placeholder="Buscar por palavra-chave (ex: MySQL, OpenAI, WhatsApp)..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="flex-1 bg-transparent outline-none text-slate-900 dark:text-white placeholder-slate-400"
          />
          {searchTerm && (
            <button
              onClick={() => setSearchTerm('')}
              className="text-slate-400 hover:text-slate-600 dark:hover:text-slate-300"
            >
              ✕
            </button>
          )}
        </div>

        {/* Filtros */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {/* Filtro por Nível */}
          <div>
            <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
              <Filter className="w-4 h-4 inline mr-1" /> Nível
            </label>
            <select
              value={selectedLevel}
              onChange={(e) => setSelectedLevel(e.target.value)}
              className="w-full px-3 py-2 bg-white dark:bg-slate-700 text-slate-900 dark:text-white border border-slate-300 dark:border-slate-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
            >
              {levels.map((level) => (
                <option key={level.value} value={level.value}>
                  {level.label}
                </option>
              ))}
            </select>
          </div>

          {/* Filtro por Canal */}
          <div>
            <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
              <Filter className="w-4 h-4 inline mr-1" /> Canal
            </label>
            <select
              value={selectedChannel}
              onChange={(e) => setSelectedChannel(e.target.value)}
              className="w-full px-3 py-2 bg-white dark:bg-slate-700 text-slate-900 dark:text-white border border-slate-300 dark:border-slate-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
            >
              {channels.map((channel) => (
                <option key={channel.value} value={channel.value}>
                  {channel.label}
                </option>
              ))}
            </select>
          </div>

          {/* Controles */}
          <div>
            <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
              Ações
            </label>
            <div className="flex gap-2">
              <button
                onClick={() => setAutoScroll(!autoScroll)}
                className={`flex-1 flex items-center justify-center gap-2 px-3 py-2 rounded-lg font-medium text-sm transition-colors ${
                  autoScroll
                    ? 'bg-indigo-600 text-white'
                    : 'bg-slate-200 dark:bg-slate-700 text-slate-700 dark:text-slate-300'
                }`}
              >
                <RotateCcw className="w-4 h-4" />
                Auto-scroll: {autoScroll ? 'ON' : 'OFF'}
              </button>
            </div>
          </div>
        </div>

        {/* Botões de Ação */}
        <div className="flex gap-2 flex-wrap">
          <button
            onClick={handleExportJSON}
            className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-medium text-sm transition-colors"
          >
            <Download className="w-4 h-4" />
            Exportar JSON
          </button>
          <button
            onClick={handleExportCSV}
            className="flex items-center gap-2 px-4 py-2 bg-green-600 hover:bg-green-700 text-white rounded-lg font-medium text-sm transition-colors"
          >
            <Download className="w-4 h-4" />
            Exportar CSV
          </button>
          <button
            onClick={handleClearLogs}
            className="flex items-center gap-2 px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg font-medium text-sm transition-colors ml-auto"
          >
            <Trash2 className="w-4 h-4" />
            Limpar Logs
          </button>
        </div>
      </div>

      {/* Feed de Logs estilo Terminal */}
      <div className="bg-slate-950 dark:bg-slate-900 rounded-xl shadow-lg border border-slate-800 overflow-hidden">
        {/* Header do Terminal */}
        <div className="bg-slate-900 dark:bg-slate-800 px-6 py-3 border-b border-slate-800 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Terminal className="w-5 h-5 text-indigo-400" />
            <span className="text-slate-400 font-mono text-sm">
              Logs do Sistema • {filteredLogs.length} resultado{filteredLogs.length !== 1 ? 's' : ''}
            </span>
          </div>
          <div className="flex gap-1">
            <div className="w-3 h-3 rounded-full bg-red-500"></div>
            <div className="w-3 h-3 rounded-full bg-amber-500"></div>
            <div className="w-3 h-3 rounded-full bg-green-500"></div>
          </div>
        </div>

        {/* Container de Logs com scroll */}
        <div
          ref={logsContainerRef}
          className="h-[600px] overflow-y-auto font-mono text-sm bg-slate-950 space-y-0"
        >
          {filteredLogs.length === 0 ? (
            <div className="flex items-center justify-center h-full text-slate-400">
              <div className="text-center">
                <AlertCircle className="w-12 h-12 mx-auto mb-4 opacity-50" />
                <p>Nenhum log encontrado com os filtros selecionados</p>
              </div>
            </div>
          ) : (
            filteredLogs.map((log) => {
              const isExpanded = expandedLogId === log.id;

              return (
                <div
                  key={log.id}
                  className="border-b border-slate-800 hover:bg-slate-900/50 transition-colors"
                >
                  {/* Linha Principal do Log */}
                  <button
                    onClick={() => setExpandedLogId(isExpanded ? null : log.id)}
                    className="w-full px-6 py-3 text-left hover:bg-slate-900/30 transition-colors flex items-center gap-3 group"
                  >
                    {/* Ícone de Expansão */}
                    <div className="w-5 h-5 text-slate-600 group-hover:text-slate-400">
                      {isExpanded ? <ChevronUp size={18} /> : <ChevronDown size={18} />}
                    </div>

                    {/* Timestamp */}
                    <span className="text-slate-500 w-32 flex-shrink-0 text-xs">
                      {formatTimestamp(log.timestamp)}
                    </span>

                    {/* Badge de Nível */}
                    <div className="w-24 flex-shrink-0">
                      <LogBadge level={log.level} size="sm" />
                    </div>

                    {/* Módulo */}
                    <span className="text-indigo-400 w-32 flex-shrink-0 text-xs font-semibold">
                      [{log.module.toUpperCase()}]
                    </span>

                    {/* Mensagem */}
                    <span className="text-slate-100 flex-1 truncate">{log.message}</span>

                    {/* Duração */}
                    {log.duration_ms > 0 && (
                      <span className={`text-xs font-mono flex-shrink-0 ${
                        log.duration_ms > 3000
                          ? 'text-red-400'
                          : log.duration_ms > 1000
                            ? 'text-amber-400'
                            : 'text-emerald-400'
                      }`}>
                        {log.duration_ms}ms
                      </span>
                    )}
                  </button>

                  {/* Seção Expandida - Detalhes JSON */}
                  {isExpanded && (
                    <div className="bg-slate-900/50 border-t border-slate-800 px-6 py-4 space-y-3">
                      {/* Informações de Detalhes */}
                      <div className="space-y-2">
                        <h4 className="text-indigo-400 font-semibold text-sm">Detalhes Completos:</h4>
                        <pre className="bg-slate-950 p-4 rounded border border-slate-800 text-slate-300 text-xs overflow-x-auto max-h-64 overflow-y-auto">
                          {JSON.stringify(log.details, null, 2)}
                        </pre>
                      </div>

                      {/* Botões de Ação para o Log */}
                      <div className="flex gap-2">
                        <button
                          onClick={() => handleCopyJSON(log.id)}
                          className={`flex items-center gap-2 px-3 py-2 rounded text-xs font-medium transition-colors ${
                            copiedId === log.id
                              ? 'bg-emerald-600/30 text-emerald-300'
                              : 'bg-slate-800 hover:bg-slate-700 text-slate-300'
                          }`}
                        >
                          {copiedId === log.id ? (
                            <>
                              <Check className="w-4 h-4" />
                              Copiado!
                            </>
                          ) : (
                            <>
                              <Copy className="w-4 h-4" />
                              Copiar JSON
                            </>
                          )}
                        </button>
                      </div>
                    </div>
                  )}
                </div>
              );
            })
          )}
        </div>
      </div>

      {/* Legenda de Cores */}
      <div className="bg-white dark:bg-slate-800 rounded-xl shadow-sm border border-slate-200 dark:border-slate-700 p-6">
        <h3 className="font-semibold text-slate-900 dark:text-white mb-4">Legenda de Severidade</h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {levels.slice(1).map((level) => (
            <div key={level.value} className="flex items-center gap-3">
              <LogBadge level={level.value} size="sm" />
              <span className="text-sm text-slate-600 dark:text-slate-400">{level.label}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
