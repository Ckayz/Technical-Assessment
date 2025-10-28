'use client';

import { useDashboardStore } from '@/lib/store';
import { ConnectionStatus } from '@/lib/websocket';

export default function ConnectionBadge() {
  const connectionStatus = useDashboardStore((state) => state.connectionStatus);

  const getStatusStyles = (status: ConnectionStatus) => {
    switch (status) {
      case 'connected':
        return {
          bg: 'bg-green-100 dark:bg-green-900',
          text: 'text-green-800 dark:text-green-200',
          dot: 'bg-green-500',
        };
      case 'connecting':
        return {
          bg: 'bg-yellow-100 dark:bg-yellow-900',
          text: 'text-yellow-800 dark:text-yellow-200',
          dot: 'bg-yellow-500',
        };
      case 'disconnected':
        return {
          bg: 'bg-red-100 dark:bg-red-900',
          text: 'text-red-800 dark:text-red-200',
          dot: 'bg-red-500',
        };
    }
  };

  const styles = getStatusStyles(connectionStatus);

  return (
    <div
      className={`inline-flex items-center gap-2 px-3 py-1.5 rounded-full text-sm font-medium ${styles.bg} ${styles.text}`}
    >
      <div className="relative">
        <div
          className={`w-2 h-2 rounded-full ${styles.dot} ${
            connectionStatus === 'connecting' ? 'animate-pulse' : ''
          }`}
        />
        {connectionStatus === 'connected' && (
          <div
            className={`absolute inset-0 w-2 h-2 rounded-full ${styles.dot} animate-ping opacity-75`}
          />
        )}
      </div>
      <span className="capitalize">{connectionStatus}</span>
    </div>
  );
}
