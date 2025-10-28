import { create } from 'zustand';
import { ConnectionStatus } from './websocket';

export interface MarketData {
  symbol: string;
  price: number;
  bid: number;
  ask: number;
  volume24h: number;
  change24h: number;
  timestamp: number;
  priceDirection?: 'up' | 'down' | 'neutral';
}

export interface AgentPosition {
  id: string;
  symbol: string;
  size: number;
  entryPrice: number;
  leverage: number;
  pnl?: number;
}

interface DashboardState {
  // Market data
  marketData: Record<string, MarketData>;
  updateMarketData: (data: MarketData) => void;

  // Agent positions
  agentPositions: AgentPosition[];
  setAgentPositions: (positions: AgentPosition[]) => void;
  updateAgentPnL: (id: string, pnl: number) => void;

  // Connection status
  connectionStatus: ConnectionStatus;
  setConnectionStatus: (status: ConnectionStatus) => void;
}

export const useDashboardStore = create<DashboardState>((set) => ({
  // Market data
  marketData: {},
  updateMarketData: (data: MarketData) =>
    set((state) => {
      const existing = state.marketData[data.symbol];
      let priceDirection: 'up' | 'down' | 'neutral' = 'neutral';

      if (existing) {
        if (data.price > existing.price) {
          priceDirection = 'up';
        } else if (data.price < existing.price) {
          priceDirection = 'down';
        }
      }

      return {
        marketData: {
          ...state.marketData,
          [data.symbol]: {
            ...data,
            priceDirection,
          },
        },
      };
    }),

  // Agent positions
  agentPositions: [],
  setAgentPositions: (positions: AgentPosition[]) =>
    set({ agentPositions: positions }),
  updateAgentPnL: (id: string, pnl: number) =>
    set((state) => ({
      agentPositions: state.agentPositions.map((position) =>
        position.id === id ? { ...position, pnl } : position
      ),
    })),

  // Connection status
  connectionStatus: 'disconnected',
  setConnectionStatus: (status: ConnectionStatus) =>
    set({ connectionStatus: status }),
}));
