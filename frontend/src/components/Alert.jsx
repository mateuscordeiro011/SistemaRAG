import React, { useEffect } from 'react';

const Alert = ({ type = 'info', message, onClose, autoClose = true, duration = 3000 }) => {
  useEffect(() => {
    if (autoClose) {
      const timer = setTimeout(onClose, duration);
      return () => clearTimeout(timer);
    }
  }, [autoClose, duration, onClose]);

  const bgColor = {
    success: 'bg-green-100 border-green-400',
    error: 'bg-red-100 border-red-400',
    warning: 'bg-yellow-100 border-yellow-400',
    info: 'bg-blue-100 border-blue-400',
  }[type] || 'bg-blue-100 border-blue-400';

  const textColor = {
    success: 'text-green-800',
    error: 'text-red-800',
    warning: 'text-yellow-800',
    info: 'text-blue-800',
  }[type] || 'text-blue-800';

  const icon = {
    success: '✓',
    error: '✕',
    warning: '!',
    info: 'ℹ',
  }[type] || 'ℹ';

  return (
    <div className={`mb-4 p-4 border-l-4 rounded ${bgColor}`}>
      <div className="flex items-center">
        <span className={`${textColor} text-xl font-bold mr-3 flex-shrink-0`}>
          {icon}
        </span>
        <p className={`${textColor} text-sm flex-1`}>
          {message}
        </p>
        <button
          onClick={onClose}
          className={`${textColor} ml-3 hover:opacity-70`}
        >
          ✕
        </button>
      </div>
    </div>
  );
};

export default Alert;
