import { describe, it, expect, beforeEach, vi } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import MarketTicker from '@/components/MarketTicker';
import { useDashboardStore } from '@/lib/store';

describe('MarketTicker', () => {
  beforeEach(() => {
    // Reset the store before each test
    useDashboardStore.setState({
      marketData: {},
      connectionStatus: 'disconnected',
      agentPositions: [],
    });
  });

  it('renders loading state when no market data is available', () => {
    const { container } = render(<MarketTicker symbol="BTC-USD" />);

    const loadingDiv = container.querySelector('.animate-pulse');
    expect(loadingDiv).toBeInTheDocument();
    expect(loadingDiv).toHaveClass('bg-white', 'dark:bg-gray-800', 'rounded-lg');
  });

  it('renders market data when available', () => {
    const mockData = {
      symbol: 'BTC-USD',
      price: 45000,
      bid: 44995,
      ask: 45005,
      volume24h: 1000000000,
      change24h: 2.5,
      timestamp: Date.now(),
    };

    useDashboardStore.setState({
      marketData: { 'BTC-USD': mockData },
    });

    render(<MarketTicker symbol="BTC-USD" />);

    expect(screen.getByText('BTC-USD')).toBeInTheDocument();
    expect(screen.getByText('$45,000.00')).toBeInTheDocument();
    expect(screen.getByText('$44,995.00')).toBeInTheDocument();
    expect(screen.getByText('$45,005.00')).toBeInTheDocument();
    expect(screen.getByText('+2.50%')).toBeInTheDocument();
  });

  it('displays positive change in green', () => {
    const mockData = {
      symbol: 'ETH-USD',
      price: 2500,
      bid: 2498,
      ask: 2502,
      volume24h: 500000000,
      change24h: 3.2,
      timestamp: Date.now(),
    };

    useDashboardStore.setState({
      marketData: { 'ETH-USD': mockData },
    });

    render(<MarketTicker symbol="ETH-USD" />);

    const changeElement = screen.getByText('+3.20%');
    expect(changeElement).toHaveClass('bg-green-100');
  });

  it('displays negative change in red', () => {
    const mockData = {
      symbol: 'SOL-USD',
      price: 100,
      bid: 99.95,
      ask: 100.05,
      volume24h: 200000000,
      change24h: -1.5,
      timestamp: Date.now(),
    };

    useDashboardStore.setState({
      marketData: { 'SOL-USD': mockData },
    });

    render(<MarketTicker symbol="SOL-USD" />);

    const changeElement = screen.getByText('-1.50%');
    expect(changeElement).toHaveClass('bg-red-100');
  });

  it('updates when market data changes', async () => {
    const initialData = {
      symbol: 'BTC-USD',
      price: 45000,
      bid: 44995,
      ask: 45005,
      volume24h: 1000000000,
      change24h: 2.5,
      timestamp: Date.now(),
    };

    useDashboardStore.setState({
      marketData: { 'BTC-USD': initialData },
    });

    const { rerender } = render(<MarketTicker symbol="BTC-USD" />);
    expect(screen.getByText('$45,000.00')).toBeInTheDocument();

    // Update the market data
    const updatedData = {
      ...initialData,
      price: 46000,
      priceDirection: 'up' as const,
    };

    useDashboardStore.setState({
      marketData: { 'BTC-USD': updatedData },
    });

    rerender(<MarketTicker symbol="BTC-USD" />);

    await waitFor(() => {
      expect(screen.getByText('$46,000.00')).toBeInTheDocument();
    });
  });

  it('calculates and displays spread correctly', () => {
    const mockData = {
      symbol: 'BTC-USD',
      price: 45000,
      bid: 44990,
      ask: 45010,
      volume24h: 1000000000,
      change24h: 2.5,
      timestamp: Date.now(),
    };

    useDashboardStore.setState({
      marketData: { 'BTC-USD': mockData },
    });

    render(<MarketTicker symbol="BTC-USD" />);

    // Spread should be 45010 - 44990 = 20
    expect(screen.getByText(/\$20.00/)).toBeInTheDocument();
    // Spread percent should be (20 / 45000) * 100 = 0.044%
    expect(screen.getByText(/0.044%/)).toBeInTheDocument();
  });
});
