import React, { useState } from 'react';
import { UploadCloud, File, Trash2, RefreshCw } from 'lucide-react';

export default function KnowledgeBase() {
  const [files, setFiles] = useState([
    { id: 1, name: 'politica_de_precos.pdf', size: '2.4 MB', type: 'PDF', date: '28/08/2026' },
    { id: 2, name: 'faq_produtos_2026.xlsx', size: '1.1 MB', type: 'XLSX', date: '29/08/2026' },
  ]);

  const handleFileUpload = (e) => {
    const uploadedFiles = Array.from(e.target.files);
    const newItems = uploadedFiles.map((file, index) => ({
      id: Date.now() + index,
      name: file.name,
      size: `${(file.size / (1024 * 1024)).toFixed(1)} MB`,
      type: file.name.split('.').pop().toUpperCase(),
      date: new Date().toLocaleDateString('pt-BR'),
    }));
    setFiles((prev) => [...prev, ...newItems]);
  };

  return (
    <div className="space-y-6">
      {/* Área de Drag and Drop */}
      <div className="border-2 border-dashed border-indigo-200 rounded-2xl p-8 text-center bg-indigo-50/30 hover:bg-indigo-50/50 transition-colors cursor-pointer relative">
        <input
          type="file"
          multiple
          onChange={handleFileUpload}
          className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
        />
        <UploadCloud className="w-12 h-12 text-indigo-600 mx-auto mb-3" />
        <h3 className="text-base font-bold text-slate-800">Arraste seus arquivos de conhecimento aqui</h3>
        <p className="text-xs text-slate-500 mt-1">Suporta PDF, Word (.docx), Excel (.xlsx) e TXT</p>
      </div>

      {/* Tabela de Arquivos Processados */}
      <div className="bg-white rounded-2xl shadow-sm border border-slate-100 overflow-hidden">
        <div className="p-4 border-b border-slate-100 bg-slate-50/50 flex justify-between items-center">
          <h3 className="font-bold text-slate-800 text-sm">Documentos Indexados no Banco</h3>
          <button className="flex items-center gap-1.5 text-xs text-indigo-600 font-medium hover:underline">
            <RefreshCw className="w-3.5 h-3.5" /> Reindexar Todos
          </button>
        </div>
        <table className="w-full text-left border-collapse">
          <thead>
            <tr className="border-b border-slate-100 text-[11px] font-bold text-slate-400 uppercase tracking-wider bg-slate-50/30">
              <th className="p-4">Arquivo</th>
              <th className="p-4">Tipo</th>
              <th className="p-4">Tamanho</th>
              <th className="p-4">Data</th>
              <th className="p-4 text-right">Ações</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100 text-sm text-slate-700">
            {files.map((file) => (
              <tr key={file.id} className="hover:bg-slate-50/50 transition-colors">
                <td className="p-4 font-medium flex items-center gap-2">
                  <File className="w-4 h-4 text-indigo-500" />
                  {file.name}
                </td>
                <td className="p-4"><span className="text-xs bg-slate-100 px-2 py-1 rounded font-mono">{file.type}</span></td>
                <td className="p-4 text-xs text-slate-500">{file.size}</td>
                <td className="p-4 text-xs text-slate-500">{file.date}</td>
                <td className="p-4 text-right">
                  <button
                    onClick={() => setFiles(files.filter((f) => f.id !== file.id))}
                    className="p-1.5 text-slate-400 hover:text-rose-600 rounded-lg hover:bg-rose-50 transition-colors"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}