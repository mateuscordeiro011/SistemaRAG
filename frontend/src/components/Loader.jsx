import React from 'react';

const Loader = ({ message = 'Carregando...' }) => {
  return (
    <div className="flex flex-col items-center justify-center py-8">
      <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      <p className="mt-3 text-gray-600 text-sm">{message}</p>
    </div>
  );
};

export default Loader;
