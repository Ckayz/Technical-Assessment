'use client';

import { useDashboardStore } from '@/lib/store';
import { formatCurrency, calculatePnLWithSide, type PnLResult } from '@/lib/math';
import { useMemo, useState, useEffect } from 'react';

interface PositionWithPnL {
  id: string;
  symbol: string;
  size: number;
  entryPrice: number;
  leverage: number;
  side: 'long' | 'short';
  pnlResult: PnLResult;
  prevSign: number;
}

export default function AgentTable() {
  const agentPositions = useDashboardStore((state) => state.agentPositions);
  const marketData = useDashboardStore((state) => state.marketData);

  const [prevSigns, setPrevSigns] = useState<Record<string, number>>({});
  const [flippedPositions, setFlippedPositions] = useState<Record<string, boolean>>({});

  // Calculate P&L on the fly without updating store
  const positionsWithPnL = useMemo(() => {
    return agentPositions.map((position): PositionWithPnL => {
      const market = marketData[position.symbol];
      let pnlResult: PnLResult = {
        absolute: 0,
        percentage: 0,
        entryValue: 0,
        currentValue: 0,
      };

      if (market) {
        pnlResult = calculatePnLWithSide(
          position.entryPrice,
          market.price,
          position.size,
          position.side,
          position.leverage
        );
      }

      const prevSign = prevSigns[position.id] || 0;
      return { ...position, pnlResult, prevSign };
    });
  }, [agentPositions, marketData, prevSigns]);

  // Detect P&L sign flips and trigger animations
  useEffect(() => {
    const newSigns: Record<string, number> = {};
    const newFlipped: Record<string, boolean> = {};

    positionsWithPnL.forEach((position) => {
      const currentSign = position.pnlResult.absolute > 0 ? 1 : position.pnlResult.absolute < 0 ? -1 : 0;
      const prevSign = prevSigns[position.id] || 0;
      newSigns[position.id] = currentSign;

      // Flip detection: only trigger if previous was non-zero and current is different non-zero
      if (prevSign !== 0 && currentSign !== 0 && prevSign !== currentSign) {
        newFlipped[position.id] = true;
        // Remove flip animation after 1 second
        setTimeout(() => {
          setFlippedPositions((prev) => ({ ...prev, [position.id]: false }));
        }, 1000);
      }
    });

    setPrevSigns(newSigns);
    setFlippedPositions((prev) => ({ ...prev, ...newFlipped }));
  }, [positionsWithPnL, prevSigns]);

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
              <th className="text-center py-3 px-4 text-sm font-semibold text-gray-700 dark:text-gray-300">
                Side
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
              <th className="text-right py-3 px-4 text-sm font-semibold text-gray-700 dark:text-gray-300">
                P&L %
              </th>
            </tr>
          </thead>
          <tbody>
            {positionsWithPnL.map((position) => {
              const isFlipped = flippedPositions[position.id];
              const pnlColor = position.pnlResult.absolute >= 0
                ? 'text-green-600 dark:text-green-400'
                : 'text-red-600 dark:text-red-400';

              return (
                <tr
                  key={position.id}
                  className="border-b border-gray-100 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-700/50 transition-colors"
                >
                  <td className="py-3 px-4 font-medium text-gray-900 dark:text-white">
                    {position.symbol}
                  </td>
                  <td className="py-3 px-4 text-center">
                    <span
                      className={`inline-block px-2 py-1 rounded text-xs font-semibold ${
                        position.side === 'long'
                          ? 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200'
                          : 'bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-200'
                      }`}
                    >
                      {position.side.toUpperCase()}
                    </span>
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
                    className={`py-3 px-4 text-right font-semibold ${pnlColor} ${
                      isFlipped ? 'animate-pulse' : ''
                    }`}
                  >
                    {position.pnlResult.absolute >= 0 ? '+' : ''}
                    {formatCurrency(position.pnlResult.absolute)}
                  </td>
                  <td
                    className={`py-3 px-4 text-right font-semibold ${pnlColor} ${
                      isFlipped ? 'animate-pulse' : ''
                    }`}
                  >
                    {position.pnlResult.percentage >= 0 ? '+' : ''}
                    {position.pnlResult.percentage.toFixed(2)}%
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      {/* Mobile Card View */}
      <div className="md:hidden space-y-4">
        {positionsWithPnL.map((position) => {
          const isFlipped = flippedPositions[position.id];
          const pnlColor = position.pnlResult.absolute >= 0
            ? 'text-green-600 dark:text-green-400'
            : 'text-red-600 dark:text-red-400';

          return (
            <div
              key={position.id}
              className="bg-gray-50 dark:bg-gray-700/50 rounded-lg p-4 space-y-2"
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <span className="font-semibold text-gray-900 dark:text-white">
                    {position.symbol}
                  </span>
                  <span
                    className={`inline-block px-2 py-1 rounded text-xs font-semibold ${
                      position.side === 'long'
                        ? 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200'
                        : 'bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-200'
                    }`}
                  >
                    {position.side.toUpperCase()}
                  </span>
                </div>
                <div className="text-right">
                  <div className={`font-semibold ${pnlColor} ${isFlipped ? 'animate-pulse' : ''}`}>
                    {position.pnlResult.absolute >= 0 ? '+' : ''}
                    {formatCurrency(position.pnlResult.absolute)}
                  </div>
                  <div className={`text-sm ${pnlColor} ${isFlipped ? 'animate-pulse' : ''}`}>
                    {position.pnlResult.percentage >= 0 ? '+' : ''}
                    {position.pnlResult.percentage.toFixed(2)}%
                  </div>
                </div>
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
          );
        })}
      </div>
    </div>
  );
}
