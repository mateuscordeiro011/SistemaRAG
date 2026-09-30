import React from 'react';
import { Loader2 } from 'lucide-react';

const Loader = ({ size = 'md', message }) => {
  const sizes = {
    sm: 'w-6 h-6 border-2',
    md: 'w-10 h-10 border-3',
    lg: 'w-14 h-14 border-4',
  };

  return (
    <div className="flex flex-col items-center justify-center py-8 gap-3">
      <div className={`${sizes[size]} border-green-200 border-t-green-600 rounded-full animate-spin`} />
      {message && <p className="text-slate-500 text-sm">{message}</p>}
    </div>
  );
};

export default Loader;