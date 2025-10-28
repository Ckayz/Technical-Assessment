import { describe, it, expect } from 'vitest';
import {
  calculatePnL,
  calculatePercentageChange,
  formatCurrency,
  formatNumber,
} from '@/lib/math';

describe('Math Utilities', () => {
  describe('calculatePnL', () => {
    it('calculates profit for a long position', () => {
      const pnl = calculatePnL(45000, 46000, 1, 10);
      // (46000 - 45000) / 45000 * 1 * 10 * 100 = 22.22
      expect(pnl).toBeCloseTo(22.22, 2);
    });

    it('calculates loss for a long position', () => {
      const pnl = calculatePnL(45000, 44000, 1, 10);
      // (44000 - 45000) / 45000 * 1 * 10 * 100 = -22.22
      expect(pnl).toBeCloseTo(-22.22, 2);
    });

    it('handles different leverage multipliers', () => {
      const pnl1x = calculatePnL(100, 110, 1, 1);
      const pnl5x = calculatePnL(100, 110, 1, 5);
      const pnl10x = calculatePnL(100, 110, 1, 10);

      expect(pnl5x).toBe(pnl1x * 5);
      expect(pnl10x).toBe(pnl1x * 10);
    });

    it('handles different position sizes', () => {
      const pnlSize1 = calculatePnL(100, 110, 1, 1);
      const pnlSize2 = calculatePnL(100, 110, 2, 1);

      expect(pnlSize2).toBe(pnlSize1 * 2);
    });

    it('returns 0 when entry price equals current price', () => {
      const pnl = calculatePnL(45000, 45000, 1, 10);
      expect(pnl).toBe(0);
    });
  });

  describe('calculatePercentageChange', () => {
    it('calculates positive percentage change', () => {
      const change = calculatePercentageChange(100, 110);
      expect(change).toBe(10);
    });

    it('calculates negative percentage change', () => {
      const change = calculatePercentageChange(100, 90);
      expect(change).toBe(-10);
    });

    it('returns 0 when values are equal', () => {
      const change = calculatePercentageChange(100, 100);
      expect(change).toBe(0);
    });

    it('returns 0 when old value is 0', () => {
      const change = calculatePercentageChange(0, 100);
      expect(change).toBe(0);
    });

    it('rounds to 2 decimal places', () => {
      const change = calculatePercentageChange(100, 103.333);
      expect(change).toBe(3.33);
    });
  });

  describe('formatCurrency', () => {
    it('formats currency with default 2 decimals', () => {
      expect(formatCurrency(1234.56)).toBe('$1,234.56');
    });

    it('formats currency with custom decimals', () => {
      expect(formatCurrency(1234.567, 3)).toBe('$1,234.567');
    });

    it('formats large numbers with commas', () => {
      expect(formatCurrency(1234567.89)).toBe('$1,234,567.89');
    });

    it('formats negative numbers', () => {
      expect(formatCurrency(-1234.56)).toBe('-$1,234.56');
    });

    it('formats zero correctly', () => {
      expect(formatCurrency(0)).toBe('$0.00');
    });
  });

  describe('formatNumber', () => {
    it('formats numbers with default 2 decimals', () => {
      expect(formatNumber(1234.56)).toBe('1,234.56');
    });

    it('formats numbers with custom decimals', () => {
      expect(formatNumber(1234.567, 3)).toBe('1,234.567');
    });

    it('formats large numbers with commas', () => {
      expect(formatNumber(1234567.89)).toBe('1,234,567.89');
    });

    it('formats negative numbers', () => {
      expect(formatNumber(-1234.56)).toBe('-1,234.56');
    });
  });
});
