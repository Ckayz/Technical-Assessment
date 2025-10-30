import { describe, it, expect } from 'vitest';
import {
  calculatePnL,
  calculatePnLWithSide,
  calculatePercentageChange,
  formatCurrency,
  formatNumber,
  type PositionSide,
} from '@/lib/math';

describe('Math Utilities', () => {
  describe('calculatePnL (legacy)', () => {
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

  describe('calculatePnLWithSide', () => {
    describe('Long positions', () => {
      it('calculates profit when price increases', () => {
        const result = calculatePnLWithSide(100, 110, 1, 'long', 1);
        expect(result.absolute).toBe(10);
        expect(result.percentage).toBe(10);
        expect(result.entryValue).toBe(100);
        expect(result.currentValue).toBe(110);
      });

      it('calculates loss when price decreases', () => {
        const result = calculatePnLWithSide(100, 90, 1, 'long', 1);
        expect(result.absolute).toBe(-10);
        expect(result.percentage).toBe(-10);
      });

      it('handles leverage correctly', () => {
        const result = calculatePnLWithSide(100, 110, 1, 'long', 10);
        // P&L = (110 - 100) * 1 * 10 = 100
        // Percentage = (100 / 100) * 100 = 100%
        expect(result.absolute).toBe(100);
        expect(result.percentage).toBe(100);
      });

      it('handles fractional position sizes', () => {
        const result = calculatePnLWithSide(100, 110, 0.5, 'long', 1);
        // P&L = (110 - 100) * 0.5 * 1 = 5
        // Percentage = (5 / 50) * 100 = 10%
        expect(result.absolute).toBe(5);
        expect(result.percentage).toBe(10);
        expect(result.entryValue).toBe(50);
      });

      it('returns 0 when entry equals current price', () => {
        const result = calculatePnLWithSide(100, 100, 1, 'long', 1);
        expect(result.absolute).toBe(0);
        expect(result.percentage).toBe(0);
      });
    });

    describe('Short positions', () => {
      it('calculates profit when price decreases', () => {
        const result = calculatePnLWithSide(100, 90, 1, 'short', 1);
        expect(result.absolute).toBe(10);
        expect(result.percentage).toBe(10);
      });

      it('calculates loss when price increases', () => {
        const result = calculatePnLWithSide(100, 110, 1, 'short', 1);
        expect(result.absolute).toBe(-10);
        expect(result.percentage).toBe(-10);
      });

      it('handles leverage correctly', () => {
        const result = calculatePnLWithSide(100, 90, 1, 'short', 5);
        // P&L = (100 - 90) * 1 * 5 = 50
        // Percentage = (50 / 100) * 100 = 50%
        expect(result.absolute).toBe(50);
        expect(result.percentage).toBe(50);
      });

      it('handles fractional position sizes', () => {
        const result = calculatePnLWithSide(100, 90, 0.5, 'short', 1);
        // P&L = (100 - 90) * 0.5 * 1 = 5
        // Percentage = (5 / 50) * 100 = 10%
        expect(result.absolute).toBe(5);
        expect(result.percentage).toBe(10);
      });

      it('returns 0 when entry equals current price', () => {
        const result = calculatePnLWithSide(100, 100, 1, 'short', 1);
        expect(result.absolute).toBe(0);
        expect(result.percentage).toBe(0);
      });
    });

    describe('Edge cases - zero and negative values', () => {
      it('handles zero size', () => {
        const result = calculatePnLWithSide(100, 110, 0, 'long', 1);
        expect(result.absolute).toBe(0);
        expect(result.percentage).toBe(0);
      });

      it('handles negative size (converts to absolute)', () => {
        const result = calculatePnLWithSide(100, 110, -1, 'long', 1);
        expect(result.absolute).toBe(10);
        expect(result.percentage).toBe(10);
      });

      it('returns 0 for zero entry price', () => {
        const result = calculatePnLWithSide(0, 110, 1, 'long', 1);
        expect(result.absolute).toBe(0);
        expect(result.percentage).toBe(0);
      });

      it('returns 0 for negative entry price', () => {
        const result = calculatePnLWithSide(-100, 110, 1, 'long', 1);
        expect(result.absolute).toBe(0);
        expect(result.percentage).toBe(0);
      });

      it('returns 0 for zero current price', () => {
        const result = calculatePnLWithSide(100, 0, 1, 'long', 1);
        expect(result.absolute).toBe(0);
        expect(result.percentage).toBe(0);
      });

      it('returns 0 for negative current price', () => {
        const result = calculatePnLWithSide(100, -110, 1, 'long', 1);
        expect(result.absolute).toBe(0);
        expect(result.percentage).toBe(0);
      });

      it('returns 0 for zero leverage', () => {
        const result = calculatePnLWithSide(100, 110, 1, 'long', 0);
        expect(result.absolute).toBe(0);
        expect(result.percentage).toBe(0);
      });

      it('returns 0 for negative leverage', () => {
        const result = calculatePnLWithSide(100, 110, 1, 'long', -1);
        expect(result.absolute).toBe(0);
        expect(result.percentage).toBe(0);
      });
    });

    describe('Edge cases - NaN and Infinity', () => {
      it('handles NaN entry price', () => {
        const result = calculatePnLWithSide(NaN, 110, 1, 'long', 1);
        expect(result.absolute).toBe(0);
        expect(result.percentage).toBe(0);
      });

      it('handles NaN current price', () => {
        const result = calculatePnLWithSide(100, NaN, 1, 'long', 1);
        expect(result.absolute).toBe(0);
        expect(result.percentage).toBe(0);
      });

      it('handles NaN size', () => {
        const result = calculatePnLWithSide(100, 110, NaN, 'long', 1);
        expect(result.absolute).toBe(0);
        expect(result.percentage).toBe(0);
      });

      it('handles NaN leverage', () => {
        const result = calculatePnLWithSide(100, 110, 1, 'long', NaN);
        expect(result.absolute).toBe(0);
        expect(result.percentage).toBe(0);
      });

      it('handles Infinity entry price', () => {
        const result = calculatePnLWithSide(Infinity, 110, 1, 'long', 1);
        expect(result.absolute).toBe(0);
        expect(result.percentage).toBe(0);
      });

      it('handles Infinity current price', () => {
        const result = calculatePnLWithSide(100, Infinity, 1, 'long', 1);
        expect(result.absolute).toBe(0);
        expect(result.percentage).toBe(0);
      });

      it('handles Infinity size', () => {
        const result = calculatePnLWithSide(100, 110, Infinity, 'long', 1);
        expect(result.absolute).toBe(0);
        expect(result.percentage).toBe(0);
      });

      it('handles Infinity leverage', () => {
        const result = calculatePnLWithSide(100, 110, 1, 'long', Infinity);
        expect(result.absolute).toBe(0);
        expect(result.percentage).toBe(0);
      });
    });

    describe('Real-world scenarios', () => {
      it('BTC long position with 10x leverage', () => {
        const result = calculatePnLWithSide(45000, 46000, 0.5, 'long', 10);
        // P&L = (46000 - 45000) * 0.5 * 10 = 5000
        // Percentage = (5000 / 22500) * 100 = 22.22%
        expect(result.absolute).toBe(5000);
        expect(result.percentage).toBeCloseTo(22.22, 2);
        expect(result.entryValue).toBe(22500);
      });

      it('ETH short position with 5x leverage', () => {
        const result = calculatePnLWithSide(2500, 2450, 2, 'short', 5);
        // P&L = (2500 - 2450) * 2 * 5 = 500
        // Percentage = (500 / 5000) * 100 = 10%
        expect(result.absolute).toBe(500);
        expect(result.percentage).toBe(10);
        expect(result.entryValue).toBe(5000);
      });

      it('SOL long position with 3x leverage', () => {
        const result = calculatePnLWithSide(100, 102, 50, 'long', 3);
        // P&L = (102 - 100) * 50 * 3 = 300
        // Percentage = (300 / 5000) * 100 = 6%
        expect(result.absolute).toBe(300);
        expect(result.percentage).toBe(6);
      });

      it('Large position with high leverage - profit scenario', () => {
        const result = calculatePnLWithSide(1000, 1050, 10, 'long', 20);
        // P&L = (1050 - 1000) * 10 * 20 = 10000
        // Percentage = (10000 / 10000) * 100 = 100%
        expect(result.absolute).toBe(10000);
        expect(result.percentage).toBe(100);
      });

      it('Large position with high leverage - loss scenario', () => {
        const result = calculatePnLWithSide(1000, 1050, 10, 'short', 20);
        // Short position loses when price increases
        // P&L = (1000 - 1050) * 10 * 20 = -10000
        // Percentage = (-10000 / 10000) * 100 = -100%
        expect(result.absolute).toBe(-10000);
        expect(result.percentage).toBe(-100);
      });
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
