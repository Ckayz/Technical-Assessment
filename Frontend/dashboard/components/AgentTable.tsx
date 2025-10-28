'use client';

import { useDashboardStore } from '@/lib/store';
import { formatCurrency } from '@/lib/math';
import { useEffect } from 'react';

export default function AgentTable() {
  const agentPositions = useDashboardStore((state) => state.agentPositions);
  const marketData = useDashboardStore((state) => state.marketData);
  const updateAgentPnL = useDashboardStore((state) => state.updateAgentPnL);

  // Update P&L when market data changes
  useEffect(() => {
    agentPositions.forEach((position) => {
      const market = marketData[position.symbol];
      if (market) {
        const priceDiff = market.price - position.entryPrice;
        const pnl = (priceDiff / position.entryPrice) * position.size * position.leverage * 100;
        updateAgentPnL(position.id, parseFloat(pnl.toFixed(2)));
      }
    });
  }, [marketData, agentPositions, updateAgentPnL]);

  if (agentPositions.length === 0) {
    return (
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
        <h2 className="text-xl font-bold text-gray-900 dark:text-white mb-4">
          Agent Positions
        </h2>
        <div className="text-center py-8 text-gray-500 dark:text-gray-400">
          No active positions
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
      <h2 className="text-xl font-bold text-gray-900 dark:text-white mb-4">
        Agent Positions
      </h2>

      {/* Desktop Table View */}
      <div className="hidden md:block overflow-x-auto">
        <table className="w-full">
          <thead>
            <tr className="border-b border-gray-200 dark:border-gray-700">
              <th className="text-left py-3 px-4 text-sm font-semibold text-gray-700 dark:text-gray-300">
                Symbol
              </th>
              <th className="text-right py-3 px-4 text-sm font-semibold text-gray-700 dark:text-gray-300">
                Size
              </th>
              <th className="text-right py-3 px-4 text-sm font-semibold text-gray-700 dark:text-gray-300">
                Entry Price
              </th>
              <th className="text-right py-3 px-4 text-sm font-semibold text-gray-700 dark:text-gray-300">
                Leverage
              </th>
              <th className="text-right py-3 px-4 text-sm font-semibold text-gray-700 dark:text-gray-300">
                P&L
              </th>
            </tr>
          </thead>
          <tbody>
            {agentPositions.map((position) => (
              <tr
                key={position.id}
                className="border-b border-gray-100 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-700/50 transition-colors"
              >
                <td className="py-3 px-4 font-medium text-gray-900 dark:text-white">
                  {position.symbol}
                </td>
                <td className="py-3 px-4 text-right text-gray-900 dark:text-white">
                  {position.size.toFixed(4)}
                </td>
                <td className="py-3 px-4 text-right text-gray-900 dark:text-white">
                  {formatCurrency(position.entryPrice)}
                </td>
                <td className="py-3 px-4 text-right text-gray-900 dark:text-white">
                  {position.leverage}x
                </td>
                <td
                  className={`py-3 px-4 text-right font-semibold ${
                    (position.pnl ?? 0) >= 0
                      ? 'text-green-600 dark:text-green-400'
                      : 'text-red-600 dark:text-red-400'
                  }`}
                >
                  {(position.pnl ?? 0) >= 0 ? '+' : ''}
                  {formatCurrency(position.pnl ?? 0)}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Mobile Card View */}
      <div className="md:hidden space-y-4">
        {agentPositions.map((position) => (
          <div
            key={position.id}
            className="bg-gray-50 dark:bg-gray-700/50 rounded-lg p-4 space-y-2"
          >
            <div className="flex items-center justify-between">
              <span className="font-semibold text-gray-900 dark:text-white">
                {position.symbol}
              </span>
              <span
                className={`font-semibold ${
                  (position.pnl ?? 0) >= 0
                    ? 'text-green-600 dark:text-green-400'
                    : 'text-red-600 dark:text-red-400'
                }`}
              >
                {(position.pnl ?? 0) >= 0 ? '+' : ''}
                {formatCurrency(position.pnl ?? 0)}
              </span>
            </div>
            <div className="grid grid-cols-3 gap-2 text-sm">
              <div>
                <div className="text-gray-500 dark:text-gray-400">Size</div>
                <div className="text-gray-900 dark:text-white font-medium">
                  {position.size.toFixed(4)}
                </div>
              </div>
              <div>
                <div className="text-gray-500 dark:text-gray-400">Entry</div>
                <div className="text-gray-900 dark:text-white font-medium">
                  {formatCurrency(position.entryPrice)}
                </div>
              </div>
              <div>
                <div className="text-gray-500 dark:text-gray-400">Leverage</div>
                <div className="text-gray-900 dark:text-white font-medium">
                  {position.leverage}x
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
