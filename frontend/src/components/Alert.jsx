import React, { useEffect } from 'react';
import { CheckCircle2, XCircle, AlertCircle, Info } from 'lucide-react';

const Alert = ({ type = 'info', message, onClose, autoClose = true, duration = 3000 }) => {
  useEffect(() => {
    if (autoClose) {
      const timer = setTimeout(onClose, duration);
      return () => clearTimeout(timer);
    }
  }, [autoClose, duration, onClose]);

  const configs = {
    success: {
      bg: 'bg-emerald-50',
      border: 'border-emerald-200',
      text: 'text-emerald-800',
      icon: CheckCircle2,
      iconBg: 'bg-emerald-100',
      iconColor: 'text-emerald-600',
    },
    error: {
      bg: 'bg-red-50',
      border: 'border-red-200',
      text: 'text-red-800',
      icon: XCircle,
      iconBg: 'bg-red-100',
      iconColor: 'text-red-600',
    },
    warning: {
      bg: 'bg-amber-50',
      border: 'border-amber-200',
      text: 'text-amber-800',
      icon: AlertCircle,
      iconBg: 'bg-amber-100',
      iconColor: 'text-amber-600',
    },
    info: {
      bg: 'bg-blue-50',
      border: 'border-blue-200',
      text: 'text-blue-800',
      icon: Info,
      iconBg: 'bg-blue-100',
      iconColor: 'text-blue-600',
    },
  };

  const config = configs[type] || configs.info;
  const Icon = config.icon;

  return (
    <div className={`mb-4 p-4 rounded-xl border-l-4 ${config.bg} ${config.border} ${config.text} animate-slide-down`}>
      <div className="flex items-start gap-3">
        <div className={`w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0 ${config.iconBg} ${config.iconColor}`}>
          <Icon className="w-5 h-5" />
        </div>
        <p className="text-sm flex-1 mt-0.5 leading-relaxed">{message}</p>
        <button
          onClick={onClose}
          className={`${config.text} ml-3 hover:opacity-70 p-1 rounded-lg hover:bg-black/5 transition-opacity flex-shrink-0`}
        >
          <XCircle className="w-5 h-5" />
        </button>
      </div>
    </div>
  );
};

export default Alert;