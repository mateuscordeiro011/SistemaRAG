import React from 'react';
import { AlertCircle, CircleCheck, CircleAlert, Terminal } from 'lucide-react';

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
      icon: CircleAlert,
      bgColor: 'bg-red-500/10',
      textColor: 'text-red-700',
      borderColor: 'border-red-200',
      label: 'ERRO',
    },
    success: {
      icon: CircleCheck,
      bgColor: 'bg-emerald-500/10',
      textColor: 'text-emerald-700',
      borderColor: 'border-emerald-200',
      label: 'SUCESSO',
    },
    warning: {
      icon: AlertCircle,
      bgColor: 'bg-amber-500/10',
      textColor: 'text-amber-700',
      borderColor: 'border-amber-200',
      label: 'AVISO',
    },
    info: {
      icon: Terminal,
      bgColor: 'bg-blue-500/10',
      textColor: 'text-blue-700',
      borderColor: 'border-blue-200',
      label: 'INFO',
    },
  };

  const config = badgeConfig[level] || badgeConfig.info;
  const Icon = config.icon;

  const sizeClasses = {
    sm: 'px-2 py-1 text-xs gap-1',
    md: 'px-2.5 py-1 text-sm gap-1.5',
    lg: 'px-3 py-1.5 text-base gap-2',
  };

  const iconSizes = {
    sm: 'w-3 h-3',
    md: 'w-3.5 h-3.5',
    lg: 'w-4 h-4',
  };

  return (
    <div
      className={`inline-flex items-center ${sizeClasses[size]} rounded-lg border ${config.bgColor} ${config.borderColor} ${config.textColor} font-semibold whitespace-nowrap`}
    >
      <Icon className={iconSizes[size]} />
      <span>{text || config.label}</span>
    </div>
  );
}