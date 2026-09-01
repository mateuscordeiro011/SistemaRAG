import React from 'react';
import { AlertCircle, CheckCircle, AlertTriangle, Info, Eye } from 'lucide-react';

/**
 * Componente LogBadge - Exibe status de severidade do log com visual profissional
 * 
 * Props:
 * - level: 'error' | 'success' | 'warning' | 'info'
 * - text: string opcional (exibe texto customizado)
 * - size: 'sm' | 'md' | 'lg' (tamanho do componente)
 */
export default function LogBadge({ level = 'info', text = '', size = 'md' }) {
  const badgeConfig = {
    error: {
      icon: AlertCircle,
      bgColor: 'bg-red-500/10 dark:bg-red-900/20',
      textColor: 'text-red-700 dark:text-red-400',
      borderColor: 'border-red-200 dark:border-red-800',
      label: 'ERRO',
      emoji: '🔴',
    },
    success: {
      icon: CheckCircle,
      bgColor: 'bg-emerald-500/10 dark:bg-emerald-900/20',
      textColor: 'text-emerald-700 dark:text-emerald-400',
      borderColor: 'border-emerald-200 dark:border-emerald-800',
      label: 'SUCESSO',
      emoji: '✅',
    },
    warning: {
      icon: AlertTriangle,
      bgColor: 'bg-amber-500/10 dark:bg-amber-900/20',
      textColor: 'text-amber-700 dark:text-amber-400',
      borderColor: 'border-amber-200 dark:border-amber-800',
      label: 'AVISO',
      emoji: '🟡',
    },
    info: {
      icon: Info,
      bgColor: 'bg-blue-500/10 dark:bg-blue-900/20',
      textColor: 'text-blue-700 dark:text-blue-400',
      borderColor: 'border-blue-200 dark:border-blue-800',
      label: 'INFO',
      emoji: '🔵',
    },
  };

  const config = badgeConfig[level] || badgeConfig.info;
  const Icon = config.icon;

  const sizeClasses = {
    sm: 'px-2 py-1 text-xs gap-1',
    md: 'px-3 py-1.5 text-sm gap-2',
    lg: 'px-4 py-2 text-base gap-2',
  };

  return (
    <div
      className={`inline-flex items-center ${sizeClasses[size]} rounded-lg border ${config.bgColor} ${config.borderColor} ${config.textColor} font-semibold whitespace-nowrap`}
    >
      <Icon className={size === 'sm' ? 'w-3 h-3' : size === 'md' ? 'w-4 h-4' : 'w-5 h-5'} />
      <span>{text || config.label}</span>
    </div>
  );
}
