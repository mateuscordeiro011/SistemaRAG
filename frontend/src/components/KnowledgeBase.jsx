import React, { useState, useEffect, useRef, useCallback } from 'react';
import {
  UploadCloud,
  File,
  Trash2,
  RefreshCw,
  Loader2,
  AlertCircle,
  CheckCircle2,
  XCircle,
  FileText,
  ArrowUpTray,
  Database,
  Brain,
  Sparkles,
} from 'lucide-react';
import { documentoService } from '../services/api';

export default function KnowledgeBase({ clienteId }) {
  const [files, setFiles] = useState([]);
  const [uploading, setUploading] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [dragActive, setDragActive] = useState(false);
  const [selectedFile, setSelectedFile] = useState(null);
  const [viewMode, setViewMode] = useState('table'); // 'table' | 'grid'
  const dropZoneRef = useRef(null);

  const fetchDocuments = useCallback(async () => {
    if (!clienteId) return;
    setLoading(true);
    setError(null);
    try {
      const data = await documentoService.list(clienteId);
      const docs = data.documentos || data || [];
      setFiles(docs.map((d) => ({
        id: d.id,
        name: d.nome_arquivo || d.nome,
        size: d.tamanho_bytes ? `${(d.tamanho_bytes / (1024 * 1024)).toFixed(1)} MB` : 'N/A',
        type: d.tipo_arquivo || d.tipo,
        date: d.data_upload ? new Date(d.data_upload).toLocaleDateString('pt-BR', {
          day: '2-digit',
          month: '2-digit',
          year: 'numeric',
          hour: '2-digit',
          minute: '2-digit',
        }) : 'N/A',
        status: d.status,
        chunks: d.chunks_recuperados || 0,
        relevance: d.score_relevancia || 0,
      })));
    } catch (err) {
      setError('Erro ao carregar documentos: ' + err.message);
      console.error(err);
    } finally {
      setLoading(false);
    }
  }, [clienteId]);

  useEffect(() => {
    if (clienteId) {
      fetchDocuments();
    } else {
      setFiles([]);
      setLoading(false);
    }
  }, [clienteId, fetchDocuments]);

  const handleDrag = useCallback((e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  }, []);

  const handleDrop = useCallback((e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      handleFiles(Array.from(e.dataTransfer.files));
    }
  }, []);

  const handleFileUpload = async (e) => {
    const uploadedFiles = Array.from(e.target.files);
    if (!clienteId || uploadedFiles.length === 0) return;
    handleFiles(uploadedFiles);
    e.target.value = '';
  };

  const handleFiles = async (filesToUpload) => {
    setUploading(true);
    setError(null);

    for (const file of filesToUpload) {
      try {
        await documentoService.upload(file, clienteId);
      } catch (err) {
        setError(`Erro ao enviar ${file.name}: ${err.message}`);
        console.error(err);
      }
    }

    setUploading(false);
    fetchDocuments();
  };

  const handleDelete = async (documentoId) => {
    if (!window.confirm('Tem certeza que deseja excluir este documento? Esta ação não pode ser desfeita.')) return;
    try {
      await documentoService.delete(documentoId);
      fetchDocuments();
    } catch (err) {
      setError('Erro ao excluir: ' + err.message);
      console.error(err);
    }
  };

  const handleReindex = async () => {
    // TODO: implementar reindexação em lote
    alert('Reindexação em lote será implementada em breve');
  };

  const getFileIcon = (type) => {
    const t = type?.toLowerCase() || '';
    if (t.includes('pdf')) return <FileText className="w-5 h-5 text-red-500" />;
    if (t.includes('word') || t.includes('docx')) return <FileText className="w-5 h-5 text-blue-500" />;
    if (t.includes('excel') || t.includes('xlsx')) return <FileText className="w-5 h-5 text-green-500" />;
    if (t.includes('text') || t.includes('txt') || t.includes('md')) return <FileText className="w-5 h-5 text-slate-500" />;
    return <File className="w-5 h-5 text-slate-400" />;
  };

  const getStatusConfig = (status) => {
    const s = status?.toUpperCase() || '';
    if (s === 'SUCESSO' || s === 'PROCESSADO' || s === 'INDEXADO') {
      return { label: 'Indexado', className: 'badge-success', icon: <CheckCircle2 className="w-3 h-3" /> };
    }
    if (s === 'PROCESSANDO' || s === 'PENDENTE') {
      return { label: 'Processando', className: 'badge-processing', icon: <Loader2 className="w-3 h-3 animate-spin" /> };
    }
    if (s === 'ERRO' || s === 'FALHA') {
      return { label: 'Erro', className: 'badge-error', icon: <XCircle className="w-3 h-3" /> };
    }
    return { label: status || 'Desconhecido', className: 'badge-info', icon: <File className="w-3 h-3" /> };
  };

  const formatFileSize = (bytes) => {
    if (!bytes || bytes === 'N/A') return 'N/A';
    const num = parseFloat(bytes);
    if (isNaN(num)) return bytes;
    if (num < 1024) return `${num} B`;
    if (num < 1024 * 1024) return `${(num / 1024).toFixed(1)} KB`;
    return `${(num / (1024 * 1024)).toFixed(1)} MB`;
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
              <p className="text-xs text-slate-500 mt-0.5">Use o seletor no topo para escolher um cliente e gerenciar seus documentos.</p>
            </div>
          </div>
        </div>
      </div>
    );
  }

  const totalSize = files.reduce((acc, f) => {
    const match = f.size.match(/([\d.]+)\s*(KB|MB|GB)/);
    if (match) {
      const val = parseFloat(match[1]);
      const unit = match[2];
      if (unit === 'KB') return acc + val * 1024;
      if (unit === 'MB') return acc + val * 1024 * 1024;
      if (unit === 'GB') return acc + val * 1024 * 1024 * 1024;
    }
    return acc;
  }, 0);

  const formatTotalSize = (bytes) => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    if (bytes < 1024 * 1024 * 1024) return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
    return `${(bytes / (1024 * 1024 * 1024)).toFixed(2)} GB`;
  };

  const indexedCount = files.filter(f => {
    const s = f.status?.toUpperCase() || '';
    return s === 'SUCESSO' || s === 'PROCESSADO' || s === 'INDEXADO';
  }).length;

  const processingCount = files.filter(f => {
    const s = f.status?.toUpperCase() || '';
    return s === 'PROCESSANDO' || s === 'PENDENTE';
  }).length;

  const errorCount = files.filter(f => {
    const s = f.status?.toUpperCase() || '';
    return s === 'ERRO' || s === 'FALHA';
  }).length;

  return (
    <div
      ref={dropZoneRef}
      onDragEnter={handleDrag}
      onDragLeave={handleDrag}
      onDragOver={handleDrag}
      onDrop={handleDrop}
      className="space-y-6 animate-fade-in"
    >
      {/* Upload Zone */}
      <div className="relative">
        <div 
          className={`drop-zone relative overflow-hidden ${dragActive || uploading ? 'active dragover' : ''}`}
          role="button"
          tabIndex={0}
          onKeyDown={(e) => (e.key === 'Enter' || e.key === ' ') && dropZoneRef.current?.querySelector('input')?.click()}
          aria-label="Área de upload de arquivos"
        >
          <input
            type="file"
            multiple
            accept=".pdf,.docx,.xlsx,.txt,.md"
            onChange={handleFileUpload}
            disabled={uploading}
            className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
            aria-label="Selecionar arquivos"
          />
          
          {uploading ? (
            <div className="flex flex-col items-center gap-4">
              <div className="relative">
                <Loader2 className="w-14 h-14 text-green-600 mx-auto animate-spin" />
                <div className="absolute inset-0 border-4 border-green-200 border-t-green-600 rounded-full animate-spin" />
              </div>
              <div className="text-center">
                <h3 className="text-lg font-bold text-slate-800">Enviando arquivos...</h3>
                <p className="text-sm text-slate-500 mt-1">Aguarde enquanto processamos seus documentos</p>
              </div>
            </div>
          ) : (
            <>
              <div className="flex flex-col items-center gap-4">
                <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-green-500 to-green-600 flex items-center justify-center shadow-lg shadow-green-500/25">
                  <UploadCloud className="w-8 h-8 text-white" />
                </div>
                <div className="text-center">
                  <h3 className="text-lg font-bold text-slate-800">Arraste seus arquivos de conhecimento aqui</h3>
                  <p className="text-sm text-slate-500 mt-1">Ou clique para selecionar — Suporta PDF, Word (.docx), Excel (.xlsx) e TXT</p>
                </div>
              </div>
              
              <div className="mt-6 pt-6 border-t border-green-200/50 flex flex-wrap items-center justify-center gap-4 text-sm text-slate-500">
                <span className="flex items-center gap-1.5">
                  <FileText className="w-4 h-4" /> PDF
                </span>
                <span className="flex items-center gap-1.5">
                  <FileText className="w-4 h-4" /> DOCX
                </span>
                <span className="flex items-center gap-1.5">
                  <FileText className="w-4 h-4" /> XLSX
                </span>
                <span className="flex items-center gap-1.5">
                  <FileText className="w-4 h-4" /> TXT/MD
                </span>
                <span className="flex items-center gap-1.5 text-green-600 font-medium">
                  <Sparkles className="w-4 h-4" /> Máx. 50MB por arquivo
                </span>
              </div>
            </>
          )}
        </div>

        {error && (
          <div className="mt-4 card border-red-200 bg-red-50 animate-slide-down">
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 rounded-lg bg-red-100 flex items-center justify-center flex-shrink-0">
                <AlertCircle className="w-4 h-4 text-red-600" />
              </div>
              <span className="text-sm text-red-700 flex-1">{error}</span>
              <button onClick={() => setError(null)} className="text-red-500 hover:text-red-700 p-1">
                <XCircle className="w-5 h-5" />
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 animate-slide-up">
        <div className="stat-card">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-slate-500 font-medium">Total de Documentos</p>
              <p className="text-3xl font-bold text-slate-900 mt-1">{files.length}</p>
            </div>
            <div className="stat-icon bg-gradient-to-br from-green-500 to-green-600 text-white">
              <Database className="w-6 h-6" />
            </div>
          </div>
        </div>
        <div className="stat-card">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-slate-500 font-medium">Indexados com Sucesso</p>
              <p className="text-3xl font-bold text-green-600 mt-1">{indexedCount}</p>
            </div>
            <div className="stat-icon bg-gradient-to-br from-emerald-500 to-emerald-600 text-white">
              <CheckCircle2 className="w-6 h-6" />
            </div>
          </div>
        </div>
        <div className="stat-card">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-slate-500 font-medium">Em Processamento</p>
              <p className="text-3xl font-bold text-amber-600 mt-1">{processingCount}</p>
            </div>
            <div className="stat-icon bg-gradient-to-br from-amber-500 to-amber-600 text-white">
              <Loader2 className="w-6 h-6" />
            </div>
          </div>
        </div>
        <div className="stat-card">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-slate-500 font-medium">Tamanho Total</p>
              <p className="text-3xl font-bold text-slate-900 mt-1">{formatTotalSize(totalSize)}</p>
            </div>
            <div className="stat-icon bg-gradient-to-br from-blue-500 to-blue-600 text-white">
              <FileText className="w-6 h-6" />
            </div>
          </div>
        </div>
      </div>

      {/* Documents Table/Grid */}
      <div className="card animate-slide-up">
        <div className="flex flex-wrap items-center justify-between gap-4 mb-6 pb-4 border-b border-green-100">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-green-500 to-green-600 flex items-center justify-center">
              <Database className="w-5 h-5 text-white" />
            </div>
            <div>
              <h3 className="font-bold text-slate-800 text-lg">Documentos Indexados no Banco</h3>
              <p className="text-xs text-slate-500">{files.length} documento{files.length !== 1 ? 's' : ''} encontrado{files.length !== 1 ? 's' : ''}</p>
            </div>
          </div>
          
          <div className="flex items-center gap-3">
            <div className="tab-nav" role="tablist">
              <button
                role="tab"
                aria-selected={viewMode === 'table'}
                onClick={() => setViewMode('table')}
                className={`tab-btn ${viewMode === 'table' ? 'active' : ''}`}
              >
                <FileText className="w-4 h-4 mr-1.5" /> Tabela
              </button>
              <button
                role="tab"
                aria-selected={viewMode === 'grid'}
                onClick={() => setViewMode('grid')}
                className={`tab-btn ${viewMode === 'grid' ? 'active' : ''}`}
              >
                <File className="w-4 h-4 mr-1.5" /> Grade
              </button>
            </div>

            <button
              onClick={handleReindex}
              disabled={uploading || loading}
              className="btn btn-secondary btn-sm flex items-center gap-2"
            >
              <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
              Atualizar
            </button>
          </div>
        </div>

        {loading ? (
          <div className="flex items-center justify-center py-12">
            <div className="flex flex-col items-center gap-3">
              <Loader2 className="w-10 h-10 text-green-600 animate-spin" />
              <p className="text-slate-500 text-sm">Carregando documentos...</p>
            </div>
          </div>
        ) : files.length === 0 ? (
          <div className="empty-state">
            <div className="empty-state-icon">
              <Brain className="w-10 h-10" />
            </div>
            <h4 className="empty-state-title">Nenhum documento indexado ainda</h4>
            <p className="empty-state-text">Faça upload de arquivos acima para começar a construir sua base de conhecimento. O sistema processará e indexará automaticamente para uso em consultas RAG.</p>
            <div className="mt-6 flex items-center justify-center gap-2 text-xs text-slate-400">
              <Sparkles className="w-3.5 h-3.5" />
              <span>Dica: PDFs com texto selecionável funcionam melhor</span>
            </div>
          </div>
        ) : viewMode === 'table' ? (
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse" role="table">
              <thead>
                <tr className="border-b border-green-100 text-[10px] font-bold text-slate-400 uppercase tracking-wider bg-green-50/30">
                  <th className="p-4">Documento</th>
                  <th className="p-4 hidden md:table-cell">Tipo</th>
                  <th className="p-4 hidden lg:table-cell">Tamanho</th>
                  <th className="p-4 hidden lg:table-cell">Data</th>
                  <th className="p-4">Status</th>
                  <th className="p-4 hidden xl:table-cell">Chunks</th>
                  <th className="p-4 hidden xl:table-cell">Relevância</th>
                  <th className="p-4 text-right">Ações</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-green-100/50 text-sm text-slate-700">
                {files.map((file) => {
                  const statusConfig = getStatusConfig(file.status);
                  return (
                    <tr key={file.id} className="hover:bg-green-50/30 transition-colors animate-fade-in">
                      <td className="p-4 font-medium flex items-center gap-3 min-w-[200px]">
                        <div className="w-10 h-10 rounded-lg bg-green-50 flex items-center justify-center flex-shrink-0">
                          {getFileIcon(file.type)}
                        </div>
                        <div className="min-w-0">
                          <p className="truncate text-slate-800">{file.name}</p>
                          <p className="text-xs text-slate-400 truncate">{file.type?.toUpperCase() || 'N/A'}</p>
                        </div>
                      </td>
                      <td className="p-4 hidden md:table-cell">
                        <span className="text-xs bg-green-50 px-2 py-1 rounded font-mono text-green-700">{file.type?.toUpperCase() || 'N/A'}</span>
                      </td>
                      <td className="p-4 hidden lg:table-cell text-xs text-slate-500">{file.size}</td>
                      <td className="p-4 hidden lg:table-cell text-xs text-slate-500">{file.date}</td>
                      <td className="p-4">
                        <span className={`inline-flex items-center gap-1.5 ${statusConfig.className}`}>
                          {statusConfig.icon}
                          {statusConfig.label}
                        </span>
                      </td>
                      <td className="p-4 hidden xl:table-cell text-xs text-slate-500 font-mono">{file.chunks}</td>
                      <td className="p-4 hidden xl:table-cell">
                        <div className="flex items-center gap-2">
                          <div className="w-24 h-1.5 bg-green-100 rounded-full overflow-hidden">
                            <div 
                              className="h-full bg-gradient-to-r from-green-500 to-green-600 rounded-full transition-all duration-500" 
                              style={{ width: `${Math.min(file.relevance * 100, 100)}%` }}
                            />
                          </div>
                          <span className="text-xs font-mono text-slate-500 w-10 text-right">{(file.relevance * 100).toFixed(0)}%</span>
                        </div>
                      </td>
                      <td className="p-4 text-right">
                        <button
                          onClick={() => handleDelete(file.id)}
                          disabled={uploading || loading}
                          className="p-2 text-slate-400 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors disabled:opacity-50 tooltip"
                          data-tooltip="Excluir documento"
                          aria-label={`Excluir ${file.name}`}
                        >
                          <Trash2 className="w-4.5 h-4.5" />
                        </button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
            {files.map((file) => {
              const statusConfig = getStatusConfig(file.status);
              return (
                <div 
                  key={file.id} 
                  className="group bg-white border border-green-100 rounded-xl p-4 hover:border-green-300 hover:shadow-soft transition-all duration-200 animate-fade-in"
                >
                  <div className="flex items-start justify-between gap-3 mb-3">
                    <div className="w-12 h-12 rounded-lg bg-green-50 flex items-center justify-center flex-shrink-0">
                      {getFileIcon(file.type)}
                    </div>
                    <button
                      onClick={() => handleDelete(file.id)}
                      disabled={uploading || loading}
                      className="p-1.5 text-slate-300 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors disabled:opacity-50 opacity-0 group-hover:opacity-100"
                      aria-label={`Excluir ${file.name}`}
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                  
                  <div className="space-y-2 text-sm">
                    <p className="font-medium text-slate-800 truncate" title={file.name}>{file.name}</p>
                    <div className="flex items-center gap-2 text-xs text-slate-500">
                      <span className="bg-green-50 px-2 py-0.5 rounded font-mono">{file.type?.toUpperCase() || 'N/A'}</span>
                      <span>•</span>
                      <span>{file.size}</span>
                    </div>
                    <div className="flex items-center gap-2 text-xs text-slate-500">
                      <span>{file.date}</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <span className={`inline-flex items-center gap-1 ${statusConfig.className}`}>
                        {statusConfig.icon}
                        {statusConfig.label}
                      </span>
                    </div>
                    <div className="pt-2 border-t border-green-100 flex items-center justify-between">
                      <div className="flex items-center gap-2 text-xs text-slate-500">
                        <span className="font-mono">{file.chunks} chunks</span>
                        <span>•</span>
                        <div className="w-20 h-1.5 bg-green-100 rounded-full overflow-hidden">
                          <div 
                            className="h-full bg-gradient-to-r from-green-500 to-green-600 rounded-full" 
                            style={{ width: `${Math.min(file.relevance * 100, 100)}%` }}
                          />
                        </div>
                      </div>
                      <span className="text-xs font-mono text-slate-400">{(file.relevance * 100).toFixed(0)}%</span>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}