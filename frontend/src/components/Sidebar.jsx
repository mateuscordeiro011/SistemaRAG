import React, { createContext, useContext, useState, useCallback } from 'react';

const LogsContext = createContext();

export function LogsProvider({ children }) {
  const [logs, setLogs] = useState([]);

  const addLog = useCallback((log) => {
    const newLog = {
      id: `log_${Date.now()}_${Math.random().toString(36).slice(2, 7)}`,
      timestamp: new Date(),
      read: false,
      ...log,
    };
    setLogs((prev) => [newLog, ...prev]);
  }, []);

  const markAllAsRead = useCallback(() => {
    setLogs((prev) => prev.map((log) => ({ ...log, read: true })));
  }, []);

  // Conta apenas logs não lidos com nível 'error' ou 'warning'
  const unreadCount = logs.filter((log) => !log.read && (log.level === 'error' || log.level === 'warning')).length;

  return (
    <LogsContext.Provider value={{ logs, addLog, markAllAsRead, unreadCount }}>
      {children}
    </LogsContext.Provider>
  );
}

export function useLogs() {
  return useContext(LogsContext);
}