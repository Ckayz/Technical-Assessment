/**
 * Position side type for P&L calculations
 */
export type PositionSide = 'long' | 'short';

/**
 * P&L calculation result with absolute and percentage values
 */
export interface PnLResult {
  absolute: number;
  percentage: number;
  entryValue: number;
  currentValue: number;
}

/**
 * Calculate the Profit and Loss for a position with side consideration
 * @param entryPrice - The price at which the position was entered
 * @param currentPrice - The current market price
 * @param size - The position size (always use positive number)
 * @param side - Position side ('long' or 'short')
 * @param leverage - The leverage multiplier
 * @returns The P&L result with absolute and percentage values
 */
export function calculatePnLWithSide(
  entryPrice: number,
  currentPrice: number,
  size: number,
  side: PositionSide,
  leverage: number = 1
): PnLResult {
  // Guard against invalid inputs - check for NaN and Infinity
  if (!isFinite(entryPrice) || !isFinite(currentPrice) || !isFinite(size) || !isFinite(leverage)) {
    return {
      absolute: 0,
      percentage: 0,
      entryValue: 0,
      currentValue: 0,
    };
  }

  // Guard against invalid values
  if (entryPrice <= 0 || currentPrice <= 0 || leverage <= 0) {
    return {
      absolute: 0,
      percentage: 0,
      entryValue: 0,
      currentValue: 0,
    };
  }

  // Handle zero size
  if (size === 0) {
    return {
      absolute: 0,
      percentage: 0,
      entryValue: 0,
      currentValue: 0,
    };
  }

  // Use absolute size for calculations
  const absSize = Math.abs(size);

  // Calculate entry and current values
  const entryValue = entryPrice * absSize;
  const currentValue = currentPrice * absSize;

  // Calculate P&L based on side
  let pnlAbsolute: number;
  if (side === 'long') {
    // Long: profit when price goes up
    pnlAbsolute = (currentPrice - entryPrice) * absSize * leverage;
  } else {
    // Short: profit when price goes down
    pnlAbsolute = (entryPrice - currentPrice) * absSize * leverage;
  }

  // Calculate percentage P&L relative to entry value
  const pnlPercentage = (pnlAbsolute / entryValue) * 100;

  return {
    absolute: parseFloat(pnlAbsolute.toFixed(2)),
    percentage: parseFloat(pnlPercentage.toFixed(2)),
    entryValue: parseFloat(entryValue.toFixed(2)),
    currentValue: parseFloat(currentValue.toFixed(2)),
  };
}

/**
 * Calculate simple P&L (backward compatible with old API)
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
