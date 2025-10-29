'use client';

import { useDashboardStore } from '@/lib/store';
import { ConnectionStatus } from '@/lib/websocket';

export default function ConnectionBadge() {
  const connectionStatus = useDashboardStore((state) => state.connectionStatus);
  const reconnectAttempt = useDashboardStore((state) => state.reconnectAttempt);
  const isFakeData = useDashboardStore((state) => state.isFakeData);
  const connectionError = useDashboardStore((state) => state.connectionError);

  const getStatusStyles = (status: ConnectionStatus) => {
    switch (status) {
      case 'connected':
        return {
          bg: isFakeData ? 'bg-orange-100 dark:bg-orange-900' : 'bg-green-100 dark:bg-green-900',
          text: isFakeData ? 'text-orange-800 dark:text-orange-200' : 'text-green-800 dark:text-green-200',
          dot: isFakeData ? 'bg-orange-500' : 'bg-green-500',
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

  const getStatusText = () => {
    if (isFakeData && connectionStatus === 'connected') {
      return 'FAKE DATA MODE';
    }

    if (connectionStatus === 'connecting' && reconnectAttempt > 0) {
      return `Reconnecting (${reconnectAttempt})`;
    }

    if (connectionStatus === 'disconnected' && connectionError) {
      return 'Error';
    }

    return connectionStatus.charAt(0).toUpperCase() + connectionStatus.slice(1);
  };

  return (
    <div className="flex flex-col items-end gap-1">
      <div
        className={`inline-flex items-center gap-2 px-3 py-1.5 rounded-full text-sm font-medium ${styles.bg} ${styles.text}`}
      >
        <div className="relative">
          <div
            className={`w-2 h-2 rounded-full ${styles.dot} ${
              connectionStatus === 'connecting' ? 'animate-pulse' : ''
            }`}
          />
          {connectionStatus === 'connected' && !isFakeData && (
            <div
              className={`absolute inset-0 w-2 h-2 rounded-full ${styles.dot} animate-ping opacity-75`}
            />
          )}
        </div>
        <span className="font-semibold">{getStatusText()}</span>
      </div>

      {isFakeData && (
        <div className="text-xs text-orange-600 dark:text-orange-400 font-medium">
          Using mock data - Real API unavailable
        </div>
      )}

      {connectionError && connectionStatus === 'disconnected' && (
        <div className="text-xs text-red-600 dark:text-red-400 max-w-xs truncate">
          {connectionError}
        </div>
      )}
    </div>
  );
}
