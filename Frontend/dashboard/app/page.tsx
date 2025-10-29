'use client';

import { useEffect, useRef } from 'react';
import { useDashboardStore } from '@/lib/store';
import { createConnectionManager, ConnectionManager } from '@/lib/connectionManager';
import MarketTicker from '@/components/MarketTicker';
import AgentTable from '@/components/AgentTable';
import ConnectionBadge from '@/components/ConnectionBadge';

// Mock agent positions
const mockPositions = [
  {
    id: '1',
    symbol: 'BTC-USD',
    size: 0.5,
    entryPrice: 44800,
    leverage: 10,
    side: 'long' as const,
  },
  {
    id: '2',
    symbol: 'ETH-USD',
    size: 2.5,
    entryPrice: 2480,
    leverage: 5,
    side: 'short' as const,
  },
  {
    id: '3',
    symbol: 'SOL-USD',
    size: 50,
    entryPrice: 99.5,
    leverage: 3,
    side: 'long' as const,
  },
  {
    id: '4',
    symbol: 'BTC-USD',
    size: 0.25,
    entryPrice: 45200,
    leverage: 15,
    side: 'short' as const,
  },
  {
    id: '5',
    symbol: 'ETH-USD',
    size: 5,
    entryPrice: 2510,
    leverage: 8,
    side: 'long' as const,
  },
];

export default function Dashboard() {
  const updateMarketData = useDashboardStore((state) => state.updateMarketData);
  const setConnectionStatus = useDashboardStore((state) => state.setConnectionStatus);
  const setAgentPositions = useDashboardStore((state) => state.setAgentPositions);
  const setReconnectAttempt = useDashboardStore((state) => state.setReconnectAttempt);
  const setIsFakeData = useDashboardStore((state) => state.setIsFakeData);
  const setConnectionError = useDashboardStore((state) => state.setConnectionError);

  const connectionManagerRef = useRef<ConnectionManager | null>(null);

  useEffect(() => {
    // Initialize agent positions
    setAgentPositions(mockPositions);

    // Create connection manager
    const manager = createConnectionManager({
      onMarketData: (data) => {
        updateMarketData(data);
      },
      onStatusChange: (status) => {
        setConnectionStatus(status);
      },
      onReconnectAttempt: (attempt) => {
        setReconnectAttempt(attempt);
      },
      onFallbackToMock: () => {
        console.log('[Dashboard] Switched to mock data mode');
        setIsFakeData(true);
      },
      onError: (error) => {
        console.error('[Dashboard] Connection error:', error);
        setConnectionError(error);
      },
    });

    connectionManagerRef.current = manager;

    // Connect (will try real API first, fall back to mock after 10s)
    manager.connect();

    // Cleanup
    return () => {
      if (connectionManagerRef.current) {
        connectionManagerRef.current.disconnect();
        connectionManagerRef.current = null;
      }
    };
  }, [
    updateMarketData,
    setConnectionStatus,
    setAgentPositions,
    setReconnectAttempt,
    setIsFakeData,
    setConnectionError,
  ]);

  return (
    <main className="min-h-screen bg-gray-50 dark:bg-gray-900 p-4 md:p-8">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between mb-8 gap-4">
          <div>
            <h1 className="text-3xl md:text-4xl font-bold text-gray-900 dark:text-white mb-2">
              Phoenix Dashboard
            </h1>
            <p className="text-gray-600 dark:text-gray-400">
              Real-time Hyperliquid market data and agent positions
            </p>
          </div>
          <ConnectionBadge />
        </div>

        {/* Market Tickers */}
        <div className="mb-8">
          <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">
            Market Data
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            <MarketTicker symbol="BTC-USD" />
            <MarketTicker symbol="ETH-USD" />
            <MarketTicker symbol="SOL-USD" />
          </div>
        </div>

        {/* Agent Positions Table */}
        <AgentTable />
      </div>
    </main>
  );
}
