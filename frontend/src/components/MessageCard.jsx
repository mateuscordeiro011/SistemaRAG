import React from 'react';
import { formatDistanceToNow } from 'date-fns';
import { ptBR } from 'date-fns/locale';

const MessageCard = ({ message, isSelected, onClick }) => {
  const getScoreBadgeColor = (score) => {
    if (score >= 0.8) return 'bg-green-100 text-green-800';
    if (score >= 0.5) return 'bg-yellow-100 text-yellow-800';
    return 'bg-red-100 text-red-800';
  };

  return (
    <div
      onClick={onClick}
      className={`p-4 border-b cursor-pointer hover:bg-gray-50 transition ${
        isSelected ? 'bg-blue-50 border-blue-300' : 'border-gray-200'
      }`}
    >
      <div className="flex justify-between items-start gap-3">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <h3 className="font-semibold text-gray-900 truncate">
              {message.cliente}
            </h3>
            <span className="text-xs text-gray-500">
              {message.empresa}
            </span>
          </div>
          <p className="text-xs text-gray-500 mt-1">
            Canal: {message.canal}
          </p>
          <p className="text-sm text-gray-700 mt-2 line-clamp-2">
            {message.pergunta}
          </p>
          <p className="text-xs text-gray-400 mt-2">
            {formatDistanceToNow(
              new Date(message.data_recebimento),
              { locale: ptBR, addSuffix: true }
            )}
          </p>
        </div>
        
        <div className="flex-shrink-0 flex flex-col gap-2 items-end">
          <span className={`inline-block px-2 py-1 text-xs font-semibold rounded ${
            getScoreBadgeColor(message.score_relevancia)
          }`}>
            {(message.score_relevancia * 100).toFixed(0)}%
          </span>
          <span className="text-xs bg-gray-100 text-gray-700 px-2 py-1 rounded">
            {message.chunks_recuperados} chunks
          </span>
        </div>
      </div>
    </div>
  );
};

export default MessageCard;
