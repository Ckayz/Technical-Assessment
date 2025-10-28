'use client';

import { useEffect } from 'react';
import { useDashboardStore, MarketData } from '@/lib/store';
import { createMockWebSocketClient } from '@/lib/websocket';
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
  },
  {
    id: '2',
    symbol: 'ETH-USD',
    size: 2.5,
    entryPrice: 2480,
    leverage: 5,
  },
  {
    id: '3',
    symbol: 'SOL-USD',
    size: 50,
    entryPrice: 99.5,
    leverage: 3,
  },
  {
    id: '4',
    symbol: 'BTC-USD',
    size: 0.25,
    entryPrice: 45200,
    leverage: 15,
  },
  {
    id: '5',
    symbol: 'ETH-USD',
    size: 5,
    entryPrice: 2510,
    leverage: 8,
  },
];

export default function Dashboard() {
  const updateMarketData = useDashboardStore((state) => state.updateMarketData);
  const setConnectionStatus = useDashboardStore((state) => state.setConnectionStatus);
  const setAgentPositions = useDashboardStore((state) => state.setAgentPositions);

  useEffect(() => {
    // Initialize agent positions
    setAgentPositions(mockPositions);

    // Create WebSocket client
    const wsClient = createMockWebSocketClient();

    // Set up message handler
    wsClient.onMessage((data) => {
      updateMarketData(data as unknown as MarketData);
    });

    // Set up status change handler
    wsClient.onStatusChange((status) => {
      setConnectionStatus(status);
    });

    // Connect
    wsClient.connect();

    // Cleanup
    return () => {
      wsClient.disconnect();
    };
  }, [updateMarketData, setConnectionStatus, setAgentPositions]);

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
              Real-time market data and agent positions
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
