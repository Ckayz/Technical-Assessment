'use client';

import { useDashboardStore } from '@/lib/store';
import { formatCurrency } from '@/lib/math';
import { useEffect, useState } from 'react';

interface MarketTickerProps {
  symbol: string;
}

export default function MarketTicker({ symbol }: MarketTickerProps) {
  const marketData = useDashboardStore((state) => state.marketData[symbol]);
  const [flashClass, setFlashClass] = useState('');

  useEffect(() => {
    if (marketData?.priceDirection && marketData.priceDirection !== 'neutral') {
      setFlashClass(
        marketData.priceDirection === 'up'
          ? 'bg-green-500/20'
          : 'bg-red-500/20'
      );

      const timer = setTimeout(() => {
        setFlashClass('');
      }, 500);

      return () => clearTimeout(timer);
    }
  }, [marketData?.price, marketData?.priceDirection]);

  if (!marketData) {
    return (
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6 animate-pulse">
        <div className="h-6 bg-gray-200 dark:bg-gray-700 rounded w-24 mb-4"></div>
        <div className="h-8 bg-gray-200 dark:bg-gray-700 rounded w-32 mb-2"></div>
        <div className="space-y-2">
          <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-full"></div>
          <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-full"></div>
          <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-3/4"></div>
        </div>
      </div>
    );
  }

  const spread = marketData.ask - marketData.bid;
  const spreadPercent = (spread / marketData.price) * 100;

  return (
    <div
      className={`bg-white dark:bg-gray-800 rounded-lg shadow-md p-6 transition-all duration-500 ${flashClass}`}
    >
      {/* Symbol Header */}
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
          {symbol}
        </h3>
        <div
          className={`text-sm font-medium px-2 py-1 rounded ${
            marketData.change24h >= 0
              ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200'
              : 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200'
          }`}
        >
          {marketData.change24h >= 0 ? '+' : ''}
          {marketData.change24h.toFixed(2)}%
        </div>
      </div>

      {/* Current Price */}
      <div className="mb-4">
        <div className="text-3xl font-bold text-gray-900 dark:text-white">
          {formatCurrency(marketData.price)}
        </div>
        <div className="text-sm text-gray-500 dark:text-gray-400 mt-1">
          Last Price
        </div>
      </div>

      {/* Bid/Ask Spread */}
      <div className="grid grid-cols-2 gap-4 mb-4">
        <div>
          <div className="text-sm text-gray-500 dark:text-gray-400">Bid</div>
          <div className="text-lg font-semibold text-gray-900 dark:text-white">
            {formatCurrency(marketData.bid)}
          </div>
        </div>
        <div>
          <div className="text-sm text-gray-500 dark:text-gray-400">Ask</div>
          <div className="text-lg font-semibold text-gray-900 dark:text-white">
            {formatCurrency(marketData.ask)}
          </div>
        </div>
      </div>

      {/* Spread */}
      <div className="mb-4 pb-4 border-b border-gray-200 dark:border-gray-700">
        <div className="text-sm text-gray-500 dark:text-gray-400">Spread</div>
        <div className="text-base font-medium text-gray-900 dark:text-white">
          {formatCurrency(spread)} ({spreadPercent.toFixed(3)}%)
        </div>
      </div>

      {/* 24h Volume */}
      <div>
        <div className="text-sm text-gray-500 dark:text-gray-400">
          24h Volume
        </div>
        <div className="text-lg font-semibold text-gray-900 dark:text-white">
          {formatCurrency(marketData.volume24h, 0)}
        </div>
      </div>
    </div>
  );
}
