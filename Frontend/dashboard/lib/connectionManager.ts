import { createHyperliquidWebSocketClient } from './hyperliquid';
import { createMockWebSocketClient } from './websocket';
import { MarketData } from './store';
import { ConnectionStatus, WebSocketClient } from './websocket';

interface ConnectionManagerCallbacks {
  onMarketData: (data: MarketData) => void;
  onStatusChange: (status: ConnectionStatus) => void;
  onReconnectAttempt: (attempt: number) => void;
  onFallbackToMock: () => void;
  onError: (error: string) => void;
}

/**
 * Connection Manager
 * Manages the connection to Hyperliquid WebSocket with automatic fallback to mock data
 */
export class ConnectionManager {
  private realClient: WebSocketClient | null = null;
  private mockClient: WebSocketClient | null = null;
  private callbacks: ConnectionManagerCallbacks;
  private fallbackTimeout: NodeJS.Timeout | null = null;
  private isUsingMock = false;
  private lastSuccessfulConnection = 0;
  private connectionAttemptStart = 0;

  constructor(callbacks: ConnectionManagerCallbacks) {
    this.callbacks = callbacks;
  }

  /**
   * Start the connection manager
   * Tries to connect to Hyperliquid, falls back to mock after 10 seconds
   */
  connect() {
    this.connectionAttemptStart = Date.now();
    this.startFallbackTimer();
    this.connectToHyperliquid();
  }

  /**
   * Disconnect from all clients
   */
  disconnect() {
    this.clearFallbackTimer();

    if (this.realClient) {
      this.realClient.disconnect();
      this.realClient = null;
    }

    if (this.mockClient) {
      this.mockClient.disconnect();
      this.mockClient = null;
    }

    this.isUsingMock = false;
  }

  /**
   * Check if currently using mock data
   */
  isUsingMockData(): boolean {
    return this.isUsingMock;
  }

  /**
   * Start the 10-second fallback timer
   */
  private startFallbackTimer() {
    this.clearFallbackTimer();

    console.log('[ConnectionManager] Starting 10-second fallback timer...');

    this.fallbackTimeout = setTimeout(() => {
      const timeSinceStart = Date.now() - this.connectionAttemptStart;

      console.log(`[ConnectionManager] Fallback timer triggered. Time since start: ${timeSinceStart}ms, Last successful: ${this.lastSuccessfulConnection}, Using mock: ${this.isUsingMock}`);

      // If still not connected after 10 seconds, fall back to mock
      if (!this.lastSuccessfulConnection || timeSinceStart >= 10000) {
        console.warn('[ConnectionManager] Real API failed for >10s, falling back to mock data');
        this.fallbackToMock();
      } else {
        console.log('[ConnectionManager] Successfully connected within 10s, no fallback needed');
      }
    }, 10000);
  }

  /**
   * Clear the fallback timer
   */
  private clearFallbackTimer() {
    if (this.fallbackTimeout) {
      clearTimeout(this.fallbackTimeout);
      this.fallbackTimeout = null;
    }
  }

  /**
   * Connect to Hyperliquid WebSocket
   */
  private connectToHyperliquid() {
    if (this.isUsingMock) {
      // Already using mock, don't try to reconnect to real
      return;
    }

    console.log('[ConnectionManager] Attempting to connect to Hyperliquid...');

    this.realClient = createHyperliquidWebSocketClient(
      (data) => {
        // Successfully receiving data from real API
        console.log('[ConnectionManager] Received market data from Hyperliquid');
        this.lastSuccessfulConnection = Date.now();
        this.clearFallbackTimer();
        this.callbacks.onMarketData(data);

        // If we were using mock, switch back to real
        if (this.isUsingMock) {
          console.log('[ConnectionManager] Real API sending data, switching from mock');
          this.isUsingMock = false;
          if (this.mockClient) {
            this.mockClient.disconnect();
            this.mockClient = null;
          }
        }
      },
      (status, error) => {
        console.log(`[ConnectionManager] Hyperliquid status: ${status}`, error || '');

        // Don't clear fallback timer just because status is 'connected'
        // Only clear it when we actually receive data (in onMarketData callback)

        if (error) {
          this.callbacks.onError(error);
        }

        this.callbacks.onStatusChange(status);
      },
      (attempt) => {
        this.callbacks.onReconnectAttempt(attempt);
      }
    );

    this.realClient.connect();
  }

  /**
   * Fall back to mock WebSocket client
   */
  private fallbackToMock() {
    if (this.isUsingMock) {
      // Already using mock
      console.log('[ConnectionManager] Already using mock data, skipping fallback');
      return;
    }

    console.log('[ConnectionManager] Falling back to mock data');

    this.isUsingMock = true;
    this.callbacks.onFallbackToMock();
    console.log('[ConnectionManager] Called onFallbackToMock callback');

    // Disconnect from real client (but don't destroy it, keep trying in background)
    // Note: For simplicity, we'll just mark as using mock and let real client keep trying
    // If real client reconnects successfully, we'll switch back

    // Start mock client
    console.log('[ConnectionManager] Creating mock WebSocket client...');
    this.mockClient = createMockWebSocketClient();

    this.mockClient.onMessage((data) => {
      if (this.isUsingMock) {
        // Only use mock data if still in mock mode
        this.callbacks.onMarketData(data as unknown as MarketData);
      }
    });

    this.mockClient.onStatusChange((status) => {
      if (this.isUsingMock) {
        console.log(`[ConnectionManager] Mock client status: ${status}`);
        this.callbacks.onStatusChange(status);
      }
    });

    console.log('[ConnectionManager] Connecting mock client...');
    this.mockClient.connect();
  }

  /**
   * Get current connection status
   */
  getStatus(): 'real' | 'mock' | 'none' {
    if (this.isUsingMock && this.mockClient) {
      return 'mock';
    }
    if (this.realClient && this.realClient.getStatus() === 'connected') {
      return 'real';
    }
    return 'none';
  }
}

/**
 * Create a connection manager
 */
export function createConnectionManager(
  callbacks: ConnectionManagerCallbacks
): ConnectionManager {
  return new ConnectionManager(callbacks);
}
