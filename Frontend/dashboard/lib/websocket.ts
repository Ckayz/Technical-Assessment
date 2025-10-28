export type ConnectionStatus = 'connected' | 'disconnected' | 'connecting';

export interface WebSocketConfig {
  url: string;
  protocols?: string | string[];
  maxReconnectAttempts?: number;
  initialReconnectDelay?: number;
  maxReconnectDelay?: number;
  reconnectBackoffMultiplier?: number;
}

export interface WebSocketMessage {
  [key: string]: unknown;
}

export interface WebSocketClient {
  connect: () => void;
  disconnect: () => void;
  send: (data: string | object) => void;
  onMessage: (callback: (data: WebSocketMessage) => void) => void;
  onStatusChange: (callback: (status: ConnectionStatus) => void) => void;
  getStatus: () => ConnectionStatus;
}

/**
 * Create a WebSocket client with automatic reconnection and exponential backoff
 */
export function createWebSocketClient(config: WebSocketConfig): WebSocketClient {
  const {
    url,
    protocols,
    maxReconnectAttempts = Infinity,
    initialReconnectDelay = 1000,
    maxReconnectDelay = 30000,
    reconnectBackoffMultiplier = 2,
  } = config;

  let ws: WebSocket | null = null;
  let status: ConnectionStatus = 'disconnected';
  let reconnectAttempts = 0;
  let reconnectTimeout: NodeJS.Timeout | null = null;
  let intentionallyClosed = false;

  const messageCallbacks: Array<(data: WebSocketMessage) => void> = [];
  const statusCallbacks: Array<(status: ConnectionStatus) => void> = [];

  const notifyStatusChange = (newStatus: ConnectionStatus) => {
    status = newStatus;
    statusCallbacks.forEach((callback) => callback(newStatus));
  };

  const calculateReconnectDelay = (): number => {
    const delay = Math.min(
      initialReconnectDelay * Math.pow(reconnectBackoffMultiplier, reconnectAttempts),
      maxReconnectDelay
    );
    return delay;
  };

  const scheduleReconnect = () => {
    if (intentionallyClosed || reconnectAttempts >= maxReconnectAttempts) {
      notifyStatusChange('disconnected');
      return;
    }

    const delay = calculateReconnectDelay();
    console.log(`Reconnecting in ${delay}ms (attempt ${reconnectAttempts + 1}/${maxReconnectAttempts})`);

    reconnectTimeout = setTimeout(() => {
      reconnectAttempts++;
      connect();
    }, delay);
  };

  const connect = () => {
    if (ws?.readyState === WebSocket.OPEN || ws?.readyState === WebSocket.CONNECTING) {
      return;
    }

    try {
      notifyStatusChange('connecting');
      ws = new WebSocket(url, protocols);

      ws.onopen = () => {
        console.log('WebSocket connected');
        notifyStatusChange('connected');
        reconnectAttempts = 0;
        if (reconnectTimeout) {
          clearTimeout(reconnectTimeout);
          reconnectTimeout = null;
        }
      };

      ws.onmessage = (event) => {
        try {
          const data = typeof event.data === 'string' ? JSON.parse(event.data) : event.data;
          messageCallbacks.forEach((callback) => callback(data));
        } catch (error) {
          console.error('Error parsing WebSocket message:', error);
        }
      };

      ws.onerror = (error) => {
        console.error('WebSocket error:', error);
      };

      ws.onclose = () => {
        console.log('WebSocket closed');
        ws = null;

        if (!intentionallyClosed) {
          notifyStatusChange('disconnected');
          scheduleReconnect();
        }
      };
    } catch (error) {
      console.error('Error creating WebSocket:', error);
      notifyStatusChange('disconnected');
      scheduleReconnect();
    }
  };

  const disconnect = () => {
    intentionallyClosed = true;
    if (reconnectTimeout) {
      clearTimeout(reconnectTimeout);
      reconnectTimeout = null;
    }
    if (ws) {
      ws.close();
      ws = null;
    }
    notifyStatusChange('disconnected');
  };

  const send = (data: string | object) => {
    if (ws?.readyState === WebSocket.OPEN) {
      const message = typeof data === 'string' ? data : JSON.stringify(data);
      ws.send(message);
    } else {
      console.warn('WebSocket is not connected. Cannot send message.');
    }
  };

  const onMessage = (callback: (data: WebSocketMessage) => void) => {
    messageCallbacks.push(callback);
  };

  const onStatusChange = (callback: (status: ConnectionStatus) => void) => {
    statusCallbacks.push(callback);
  };

  const getStatus = (): ConnectionStatus => {
    return status;
  };

  return {
    connect,
    disconnect,
    send,
    onMessage,
    onStatusChange,
    getStatus,
  };
}

/**
 * Mock WebSocket client for development/testing
 * Simulates market data updates
 */
export function createMockWebSocketClient(): WebSocketClient {
  let status: ConnectionStatus = 'disconnected';
  let interval: NodeJS.Timeout | null = null;

  const messageCallbacks: Array<(data: WebSocketMessage) => void> = [];
  const statusCallbacks: Array<(status: ConnectionStatus) => void> = [];

  const symbols = ['BTC-USD', 'ETH-USD', 'SOL-USD'];
  const basePrices: Record<string, number> = {
    'BTC-USD': 45000,
    'ETH-USD': 2500,
    'SOL-USD': 100,
  };

  const notifyStatusChange = (newStatus: ConnectionStatus) => {
    status = newStatus;
    statusCallbacks.forEach((callback) => callback(newStatus));
  };

  const generateMockData = () => {
    symbols.forEach((symbol) => {
      const basePrice = basePrices[symbol];
      const volatility = basePrice * 0.001; // 0.1% volatility
      const price = basePrice + (Math.random() - 0.5) * volatility * 2;
      const spread = price * 0.0005; // 0.05% spread

      const mockData = {
        symbol,
        price: parseFloat(price.toFixed(2)),
        bid: parseFloat((price - spread / 2).toFixed(2)),
        ask: parseFloat((price + spread / 2).toFixed(2)),
        volume24h: Math.floor(Math.random() * 1000000000) + 500000000,
        change24h: parseFloat(((Math.random() - 0.5) * 10).toFixed(2)),
        timestamp: Date.now(),
      };

      messageCallbacks.forEach((callback) => callback(mockData));
    });
  };

  const connect = () => {
    notifyStatusChange('connecting');
    setTimeout(() => {
      notifyStatusChange('connected');
      // Send initial data
      generateMockData();
      // Update data every 1-2 seconds
      interval = setInterval(generateMockData, 1000 + Math.random() * 1000);
    }, 500);
  };

  const disconnect = () => {
    if (interval) {
      clearInterval(interval);
      interval = null;
    }
    notifyStatusChange('disconnected');
  };

  const send = (data: string | object) => {
    console.log('Mock WebSocket send:', data);
  };

  const onMessage = (callback: (data: WebSocketMessage) => void) => {
    messageCallbacks.push(callback);
  };

  const onStatusChange = (callback: (status: ConnectionStatus) => void) => {
    statusCallbacks.push(callback);
  };

  const getStatus = (): ConnectionStatus => {
    return status;
  };

  return {
    connect,
    disconnect,
    send,
    onMessage,
    onStatusChange,
    getStatus,
  };
}
