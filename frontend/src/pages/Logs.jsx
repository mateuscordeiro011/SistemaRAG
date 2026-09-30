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
  Loader2,
  X,
  FileText,
  Database,
  MessageSquare,
  Smartphone,
  Mail,
  Zap,
} from 'lucide-react';
import { logService } from '../services/api';

export default function Logs({ clienteId }) {
  const [logs, setLogs] = useState([]);
  const [filteredLogs, setFilteredLogs] = useState([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedLevel, setSelectedLevel] = useState('todos');
  const [selectedChannel, setSelectedChannel] = useState('general');
  const [expandedLogId, setExpandedLogId] = useState(null);
  const [autoScroll, setAutoScroll] = useState(true);
  const [copiedId, setCopiedId] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const logsContainerRef = useRef(null);

  const levels = [
    { value: 'todos', label: 'Todos', color: 'slate' },
    { value: 'success', label: 'Sucesso', color: 'emerald' },
    { value: 'error', label: 'Erro', color: 'red' },
    { value: 'warning', label: 'Aviso', color: 'amber' },
    { value: 'info', label: 'Info', color: 'blue' },
  ];

  const channels = [
    { value: 'general', label: 'Geral', icon: Terminal },
    { value: 'rag', label: 'RAG/IA', icon: Brain },
    { value: 'mysql', label: 'MySQL', icon: Database },
    { value: 'whatsapp', label: 'WhatsApp', icon: MessageSquare },
    { value: 'outlook', label: 'Outlook', icon: Mail },
    { value: 'api', label: 'API Externa', icon: Zap },
  ];

  const fetchLogs = async () => {
    if (!clienteId) {
      setLogs([]);
      setLoading(false);
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const data = await logService.list(clienteId);
      const logArray = Array.isArray(data) ? data : (data.logs || data || []);
      setLogs(logArray);
    } catch (err) {
      setError('Erro ao carregar logs: ' + err.message);
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchLogs();
  }, [clienteId]);

  useEffect(() => {
    let result = logs;

    if (selectedLevel !== 'todos') {
      result = result.filter((log) => log.level === selectedLevel);
    }

    if (selectedChannel !== 'general') {
      result = result.filter((log) => log.channel === selectedChannel);
    } else if (selectedChannel === 'general') {
      result = result.filter((log) => log.channel === 'general');
    }

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

  const getLevelConfig = (level) => {
    const configs = {
      error: { label: 'ERRO', color: 'red', bg: 'bg-red-500/10', text: 'text-red-700', border: 'border-red-200', icon: CircleAlert, emoji: '🔴' },
      success: { label: 'SUCESSO', color: 'emerald', bg: 'bg-emerald-500/10', text: 'text-emerald-700', border: 'border-emerald-200', icon: CircleCheck, emoji: '✅' },
      warning: { label: 'AVISO', color: 'amber', bg: 'bg-amber-500/10', text: 'text-amber-700', border: 'border-amber-200', icon: AlertCircle, emoji: '🟡' },
      info: { label: 'INFO', color: 'blue', bg: 'bg-blue-500/10', text: 'text-blue-700', border: 'border-blue-200', icon: Terminal, emoji: '🔵' },
    };
    return configs[level] || configs.info;
  };

  const getChannelIcon = (channel) => {
    const ch = channels.find(c => c.value === channel);
    return ch ? ch.icon : Terminal;
  };

  const getChannelLabel = (channel) => {
    const ch = channels.find(c => c.value === channel);
    return ch ? ch.label : channel;
  };

  const renderDetails = (details) => {
    if (!details || Object.keys(details).length === 0) {
      return <div className="text-slate-500 text-sm italic">Nenhum detalhe adicional</div>;
    }

    const formatValue = (key, value) => {
      if (value === null) return <span className="text-slate-400 italic">null</span>;
      if (value === undefined) return <span className="text-slate-400 italic">undefined</span>;
      if (typeof value === 'object') {
        return (
          <details className="group">
            <summary className="cursor-pointer text-green-600 hover:text-green-700 font-mono text-sm select-none">
              {key}: {Array.isArray(value) ? `[Array ${value.length}]` : '{Objeto}'}
              <ChevronDown className="w-3.5 h-3.5 inline-block transition-transform group-open:rotate-180 ml-1" />
            </summary>
            <div className="ml-4 mt-1 space-y-1 border-l border-green-200 pl-3">
              {Array.isArray(value) ? (
                value.map((v, i) => <div key={i} className="font-mono text-xs text-slate-600">[{i}]: {formatValue('', v)}</div>)
              ) : (
                Object.entries(value).map(([k, v]) => <div key={k} className="font-mono text-xs text-slate-600">{k}: {formatValue('', v)}</div>)
              )}
            </div>
          </details>
        );
      }
      if (typeof value === 'string' && value.length > 200) {
        return (
          <details className="group">
            <summary className="cursor-pointer text-slate-600 hover:text-slate-700 font-mono text-sm select-none">
              {key}: "{value.substring(0, 100)}..." ({value.length} chars)
              <ChevronDown className="w-3.5 h-3.5 inline-block transition-transform group-open:rotate-180 ml-1" />
            </summary>
            <div className="ml-4 mt-1 p-2 bg-slate-50 rounded font-mono text-xs text-slate-700 whitespace-pre-wrap break-words max-h-40 overflow-auto">
              {value}
            </div>
          </details>
        );
      }
      return <span className="font-mono text-sm text-slate-700">{String(value)}</span>;
    };

    return (
      <div className="space-y-2">
        {Object.entries(details).map(([key, value]) => (
          <div key={key} className="flex flex-col gap-1">
            <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">{key}</span>
            <div className="ml-2">{formatValue(key, value)}</div>
          </div>
        ))}
      </div>
    );
  };

  if (!clienteId) {
    return (
      <div className="space-y-6 animate-fade-in">
        <div className="card bg-gradient-to-br from-amber-50 to-amber-100 border-amber-200">
          <div className="flex items-center gap-4">
            <div className="w-12 h-12 rounded-xl bg-amber-100 flex items-center justify-center flex-shrink-0">
              <AlertCircle className="w-6 h-6 text-amber-600" />
            </div>
            <div>
              <h3 className="text-base font-bold text-slate-800">Selecione um cliente</h3>
              <p className="text-xs text-slate-500 mt-0.5">Use o seletor no topo para escolher um cliente e ver seus logs.</p>
            </div>
          </div>
        </div>
      </div>
    );
  }

  const stats = {
    total: logs.length,
    errors: logs.filter((l) => l.level === 'error').length,
    warnings: logs.filter((l) => l.level === 'warning').length,
    successes: logs.filter((l) => l.level === 'success').length,
    info: logs.filter((l) => l.level === 'info').length,
  };

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Quick Stats */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
        <div className="stat-card">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-slate-500 font-medium">Total de Logs</p>
              <p className="text-3xl font-bold text-slate-900 mt-1">{stats.total}</p>
            </div>
            <div className="stat-icon bg-gradient-to-br from-slate-500 to-slate-600 text-white">
              <Terminal className="w-6 h-6" />
            </div>
          </div>
        </div>
        <div className="stat-card">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-slate-500 font-medium">Erros</p>
              <p className="text-3xl font-bold text-red-600 mt-1">{stats.errors}</p>
            </div>
            <div className="stat-icon bg-gradient-to-br from-red-500 to-red-600 text-white">
              <CircleAlert className="w-6 h-6" />
            </div>
          </div>
        </div>
        <div className="stat-card">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-slate-500 font-medium">Avisos</p>
              <p className="text-3xl font-bold text-amber-600 mt-1">{stats.warnings}</p>
            </div>
            <div className="stat-icon bg-gradient-to-br from-amber-500 to-amber-600 text-white">
              <AlertCircle className="w-6 h-6" />
            </div>
          </div>
        </div>
        <div className="stat-card">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-slate-500 font-medium">Sucessos</p>
              <p className="text-3xl font-bold text-emerald-600 mt-1">{stats.successes}</p>
            </div>
            <div className="stat-icon bg-gradient-to-br from-emerald-500 to-emerald-600 text-white">
              <CircleCheck className="w-6 h-6" />
            </div>
          </div>
        </div>
        <div className="stat-card">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-slate-500 font-medium">Info</p>
              <p className="text-3xl font-bold text-blue-600 mt-1">{stats.info}</p>
            </div>
            <div className="stat-icon bg-gradient-to-br from-blue-500 to-blue-600 text-white">
              <FileText className="w-6 h-6" />
            </div>
          </div>
        </div>
      </div>

      {/* Control Bar */}
      <div className="card animate-slide-up">
        <div className="space-y-4">
          {/* Search */}
          <div className="relative">
            <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400" />
            <input
              type="text"
              placeholder="Buscar por palavra-chave (ex: MySQL, OpenAI, WhatsApp, timeout, erro...)..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-12 pr-4 py-3 bg-white border border-green-200 rounded-xl text-slate-900 placeholder-slate-400 focus:border-green-400 focus:ring-2 focus:ring-green-500/20 transition-all"
            />
            {searchTerm && (
              <button
                onClick={() => setSearchTerm('')}
                className="absolute right-4 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600 p-1 rounded-lg hover:bg-slate-100 transition-colors"
              >
                <X className="w-5 h-5" />
              </button>
            )}
          </div>

          {/* Filters */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            {/* Level Filter */}
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-2 flex items-center gap-1.5">
                <Filter className="w-4 h-4" /> Nível
              </label>
              <select
                value={selectedLevel}
                onChange={(e) => setSelectedLevel(e.target.value)}
                className="w-full px-4 py-2.5 bg-white border border-green-200 rounded-xl text-slate-900 focus:border-green-400 focus:ring-2 focus:ring-green-500/20 cursor-pointer appearance-none bg-[url('data:image/svg+xml,%3Csvg xmlns=%27http://www.w3.org/2000/svg%27 fill=%27none%27 viewBox=%270 0 20 20%27%3E%3Cpath stroke=%27%236b8e72%27 stroke-linecap=%27round%27 stroke-linejoin=%27round%27 stroke-width=%271.5%27 d=%27M6 8l4 4 4-4%27/%3E%3C/svg%3E')] bg-[right_12px_center] bg-no-repeat bg-[length:16px] pr-10"
              >
                {levels.map((level) => (
                  <option key={level.value} value={level.value}>{level.label}</option>
                ))}
              </select>
            </div>

            {/* Channel Filter */}
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-2 flex items-center gap-1.5">
                <Filter className="w-4 h-4" /> Canal
              </label>
              <select
                value={selectedChannel}
                onChange={(e) => setSelectedChannel(e.target.value)}
                className="w-full px-4 py-2.5 bg-white border border-green-200 rounded-xl text-slate-900 focus:border-green-400 focus:ring-2 focus:ring-green-500/20 cursor-pointer appearance-none bg-[url('data:image/svg+xml,%3Csvg xmlns=%27http://www.w3.org/2000/svg%27 fill=%27none%27 viewBox=%270 0 20 20%27%3E%3Cpath stroke=%27%276b8e72%27 stroke-linecap=%27round%27 stroke-linejoin=%27round%27 stroke-width=%271.5%27 d=%27M6 8l4 4 4-4%27/%3E%3C/svg%3E')] bg-[right_12px_center] bg-no-repeat bg-[length:16px] pr-10"
              >
                {channels.map((channel) => (
                  <option key={channel.value} value={channel.value}>{channel.label}</option>
                ))}
              </select>
            </div>

            {/* Auto-scroll */}
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-2">Ações</label>
              <button
                onClick={() => setAutoScroll(!autoScroll)}
                className={`w-full flex items-center justify-center gap-2 px-4 py-2.5 rounded-xl font-medium text-sm transition-all ${
                  autoScroll
                    ? 'bg-gradient-to-r from-green-600 to-green-700 text-white shadow-[0_4px_14px_-2px_rgba(34,197,94,0.35)]'
                    : 'bg-white border border-green-200 text-slate-700 hover:bg-green-50 hover:border-green-300'
                }`}
              >
                <RotateCcw className={`w-4 h-4 ${autoScroll ? 'animate-spin' : ''}`} />
                Auto-scroll: {autoScroll ? 'ON' : 'OFF'}
              </button>
            </div>

            {/* Refresh */}
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-2">Atualizar</label>
              <button
                onClick={fetchLogs}
                disabled={loading}
                className="w-full btn btn-secondary flex items-center justify-center gap-2"
              >
                <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
                Recarregar
              </button>
            </div>
          </div>

          {/* Action Buttons */}
          <div className="flex flex-wrap gap-3 pt-2 border-t border-green-100">
            <button
              onClick={handleExportJSON}
              className="btn btn-secondary flex items-center gap-2"
            >
              <Download className="w-4 h-4" />
              Exportar JSON
            </button>
            <button
              onClick={handleExportCSV}
              className="btn btn-secondary flex items-center gap-2"
            >
              <FileText className="w-4 h-4" />
              Exportar CSV
            </button>
            <button
              onClick={handleClearLogs}
              className="btn btn-danger flex items-center gap-2 ml-auto"
            >
              <Trash2 className="w-4 h-4" />
              Limpar Logs
            </button>
          </div>
        </div>
      </div>

      {/* Log Terminal */}
      <div className="log-terminal animate-slide-up">
        {/* Terminal Header */}
        <div className="log-terminal-header">
          <div className="flex items-center gap-3">
            <div className="flex gap-1.5">
              <div className="w-3 h-3 rounded-full bg-red-500" />
              <div className="w-3 h-3 rounded-full bg-amber-500" />
              <div className="w-3 h-3 rounded-full bg-green-500" />
            </div>
            <span className="text-slate-300 font-mono text-sm">
              system-logs • {filteredLogs.length} resultado{filteredLogs.length !== 1 ? 's' : ''} • {clienteId}
            </span>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-xs text-slate-400 font-mono">
              {autoScroll ? '🟢 LIVE' : '🔴 PAUSADO'}
            </span>
          </div>
        </div>

        {/* Log Body */}
        <div
          ref={logsContainerRef}
          className="log-terminal-body"
          role="log"
          aria-live="polite"
          aria-label="Logs do sistema"
        >
          {loading ? (
            <div className="flex items-center justify-center h-64 text-slate-400">
              <div className="flex flex-col items-center gap-3">
                <Loader2 className="w-10 h-10 text-green-500 animate-spin" />
                <p>Carregando logs...</p>
              </div>
            </div>
          ) : error ? (
            <div className="flex items-center justify-center h-64 text-red-400">
              <div className="text-center">
                <AlertCircle className="w-10 h-10 mx-auto mb-3 opacity-50" />
                <p>{error}</p>
                <button onClick={fetchLogs} className="mt-3 btn btn-secondary btn-sm">
                  <RefreshCw className="w-4 h-4" /> Tentar Novamente
                </button>
              </div>
            </div>
          ) : filteredLogs.length === 0 ? (
            <div className="flex items-center justify-center h-64 text-slate-400">
              <div className="text-center">
                <Terminal className="w-16 h-16 mx-auto mb-4 opacity-30" />
                <p className="text-slate-400">Nenhum log encontrado com os filtros selecionados</p>
                <p className="text-xs text-slate-500 mt-1">Tente ajustar os filtros ou buscar por outros termos</p>
              </div>
            </div>
          ) : (
            filteredLogs.map((log) => {
              const isExpanded = expandedLogId === log.id;
              const levelConfig = getLevelConfig(log.level);
              const LevelIcon = levelConfig.icon;
              const ChannelIcon = getChannelIcon(log.channel);

              return (
                <div
                  key={log.id}
                  className={`log-entry ${isExpanded ? 'expanded' : ''} animate-fade-in`}
                >
                  {/* Main Log Line */}
                  <button
                    onClick={() => setExpandedLogId(isExpanded ? null : log.id)}
                    className="w-full px-4 py-3 text-left flex items-center gap-3 group"
                    aria-expanded={isExpanded}
                    aria-label={`Log de ${getLevelConfig(log.level).label} - ${log.message.substring(0, 50)}...`}
                  >
                    {/* Expand Icon */}
                    <div className="w-6 h-6 flex items-center justify-center text-slate-500 group-hover:text-slate-300 transition-colors">
                      {isExpanded ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
                    </div>

                    {/* Timestamp */}
                    <span className="log-timestamp w-36 flex-shrink-0 font-mono text-[11px]">
                      {formatTimestamp(log.timestamp)}
                    </span>

                    {/* Level Badge */}
                    <span className={`log-level ${levelConfig.color}`}>
                      <LevelIcon className="w-3.5 h-3.5" />
                      {levelConfig.label}
                    </span>

                    {/* Channel */}
                    <span className="flex items-center gap-1.5 text-slate-400 text-xs font-medium w-28 flex-shrink-0">
                      <ChannelIcon className="w-3.5 h-3.5" />
                      {getChannelLabel(log.channel)}
                    </span>

                    {/* Module */}
                    <span className="log-module w-32 flex-shrink-0 text-[11px] font-semibold">
                      [{log.module.toUpperCase()}]
                    </span>

                    {/* Message */}
                    <span className="log-message flex-1 truncate">{log.message}</span>

                    {/* Duration */}
                    {log.duration_ms > 0 && (
                      <span className={`log-duration font-mono text-[11px] flex-shrink-0 ${
                        log.duration_ms > 3000 ? 'text-red-400' : log.duration_ms > 1000 ? 'text-amber-400' : 'text-emerald-400'
                      }`}>
                        {log.duration_ms}ms
                      </span>
                    )}
                  </button>

                  {/* Expanded Details */}
                  {isExpanded && (
                    <div className="log-details animate-slide-down">
                      <div className="flex items-center justify-between mb-3">
                        <h4 className="text-green-400 font-semibold text-sm flex items-center gap-2">
                          <FileText className="w-4 h-4" />
                          Detalhes Completos do Log
                        </h4>
                        <button
                          onClick={() => handleCopyJSON(log.id)}
                          className={`flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
                            copiedId === log.id
                              ? 'bg-emerald-500/20 text-emerald-400'
                              : 'bg-slate-800 hover:bg-slate-700 text-slate-300'
                          }`}
                        >
                          {copiedId === log.id ? (
                            <>
                              <Check className="w-3.5 h-3.5" />
                              Copiado!
                            </>
                          ) : (
                            <>
                              <Copy className="w-3.5 h-3.5" />
                              Copiar JSON
                            </>
                          )}
                        </button>
                      </div>

                      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 mb-4">
                        <div className="space-y-3">
                          <div>
                            <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">ID</span>
                            <div className="font-mono text-sm text-slate-300 break-all bg-slate-900/50 px-3 py-2 rounded">{log.id}</div>
                          </div>
                          <div>
                            <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Timestamp ISO</span>
                            <div className="font-mono text-sm text-slate-300 bg-slate-900/50 px-3 py-2 rounded">{new Date(log.timestamp).toISOString()}</div>
                          </div>
                          <div>
                            <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Duração</span>
                            <div className="font-mono text-sm text-slate-300 bg-slate-900/50 px-3 py-2 rounded">{log.duration_ms} ms</div>
                          </div>
                        </div>
                        <div className="space-y-3">
                          <div>
                            <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Nível</span>
                            <div className="inline-flex items-center gap-2">
                              <span className={`log-level ${levelConfig.color}`}>
                                <LevelIcon className="w-3.5 h-3.5" />
                                {levelConfig.label}
                              </span>
                            </div>
                          </div>
                          <div>
                            <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Canal</span>
                            <div className="flex items-center gap-2 text-slate-300">
                              <ChannelIcon className="w-4 h-4 text-green-400" />
                              <span className="font-medium capitalize">{log.channel}</span>
                            </div>
                          </div>
                          <div>
                            <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Módulo</span>
                            <div className="font-mono text-sm text-slate-300 bg-slate-900/50 px-3 py-2 rounded">{log.module}</div>
                          </div>
                        </div>
                      </div>

                      <div className="border-t border-slate-800 pt-4">
                        {renderDetails(log.details)}
                      </div>
                    </div>
                  )}
                </div>
              );
            })
          )}
        </div>
      </div>

      {/* Severity Legend */}
      <div className="card animate-fade-in">
        <h3 className="font-semibold text-slate-900 mb-4 flex items-center gap-2">
          <Terminal className="w-5 h-5 text-green-600" />
          Legenda de Severidade
        </h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {levels.slice(1).map((level) => {
            const config = getLevelConfig(level.value);
            const Icon = config.icon;
            return (
              <div key={level.value} className="flex items-center gap-3 p-3 rounded-xl bg-white border border-green-100 hover:border-green-200 transition-colors">
                <div className={`inline-flex items-center gap-1.5 ${config.bg} ${config.border} ${config.text} px-3 py-1.5 rounded-lg`}>
                  <Icon className="w-4 h-4" />
                  <span className="font-semibold text-sm">{config.label}</span>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}