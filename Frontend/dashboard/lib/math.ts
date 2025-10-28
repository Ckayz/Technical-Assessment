/**
 * Calculate the Profit and Loss for a position
 * @param entryPrice - The price at which the position was entered
 * @param currentPrice - The current market price
 * @param size - The position size (positive for long, negative for short)
 * @param leverage - The leverage multiplier
 * @returns The P&L value
 */
export function calculatePnL(
  entryPrice: number,
  currentPrice: number,
  size: number,
  leverage: number = 1
): number {
  const priceDiff = currentPrice - entryPrice;
  const pnl = (priceDiff / entryPrice) * size * leverage * 100;
  return parseFloat(pnl.toFixed(2));
}

/**
 * Calculate the percentage change
 * @param oldValue - The old value
 * @param newValue - The new value
 * @returns The percentage change
 */
export function calculatePercentageChange(
  oldValue: number,
  newValue: number
): number {
  if (oldValue === 0) return 0;
  const change = ((newValue - oldValue) / oldValue) * 100;
  return parseFloat(change.toFixed(2));
}

/**
 * Format a number as currency
 * @param value - The value to format
 * @param decimals - The number of decimal places
 * @returns The formatted currency string
 */
export function formatCurrency(value: number, decimals: number = 2): string {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  }).format(value);
}

/**
 * Format a number with commas
 * @param value - The value to format
 * @param decimals - The number of decimal places
 * @returns The formatted number string
 */
export function formatNumber(value: number, decimals: number = 2): string {
  return new Intl.NumberFormat('en-US', {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  }).format(value);
}
