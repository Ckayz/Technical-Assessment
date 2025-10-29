import { ConnectionStatus, WebSocketClient, WebSocketMessage } from './websocket';
import { MarketData } from './store';

/**
 * Hyperliquid WebSocket API types
 */
interface HyperliquidSubscription {
  method: 'subscribe' | 'unsubscribe';
  subscription: {
    type: string;
    coin?: string;
  };
}

interface HyperliquidMessage {
  channel: string;
  data: unknown;
}

interface HyperliquidAllMids {
  [symbol: string]: string;  // Price as string
}

interface HyperliquidTrade {
  coin: string;
  side: string;
  px: string;  // Price
  sz: string;  // Size
  time: number;
  hash: string;
  tid: number;
}

interface HyperliquidL2Book {
  coin: string;
  levels: [[string, string, number][], [string, string, number][]];  // [bids, asks]
  time: number;
}

/**
 * Normalize Hyperliquid symbol to our format
 */
function normalizeSymbol(hlSymbol: string): string {
  // Hyperliquid uses symbols like "BTC", "ETH", "SOL"
  // We use "BTC-USD", "ETH-USD", "SOL-USD"
  const majorCoins = ['BTC', 'ETH', 'SOL'];
  if (majorCoins.includes(hlSymbol)) {
    return `${hlSymbol}-USD`;
  }
  return hlSymbol;
}

/**
 * Normalize Hyperliquid data to our MarketData format
 */
export function normalizeHyperliquidData(
  symbol: string,
  price: number,
  existingData?: Partial<MarketData>
): MarketData {
  return {
    symbol: normalizeSymbol(symbol),
    price,
    bid: existingData?.bid || price * 0.9995,  // Estimate if not available
    ask: existingData?.ask || price * 1.0005,  // Estimate if not available
    volume24h: existingData?.volume24h || 0,
    change24h: existingData?.change24h || 0,
    timestamp: Date.now(),
  };
}

/**
 * Create a real Hyperliquid WebSocket client
 */
export function createHyperliquidWebSocketClient(
  onMarketData: (data: MarketData) => void,
  statusChangeCallback: (status: ConnectionStatus, error?: string) => void,
  onReconnectAttempt: (attempt: number) => void
): WebSocketClient {
  const HYPERLIQUID_WS_URL = 'wss://api.hyperliquid.xyz/ws';
  const SYMBOLS = ['BTC', 'ETH', 'SOL'];

  let ws: WebSocket | null = null;
  let status: ConnectionStatus = 'disconnected';
  let reconnectAttempts = 0;
  let reconnectTimeout: NodeJS.Timeout | null = null;
  let heartbeatInterval: NodeJS.Timeout | null = null;
  let intentionallyClosed = false;
  let lastMessageTime = Date.now();

  const messageCallbacks: Array<(data: WebSocketMessage) => void> = [];
  const statusCallbacks: Array<(status: ConnectionStatus) => void> = [];

  // Store last known prices for each symbol
  const lastPrices: Record<string, Partial<MarketData>> = {};

  const notifyStatusChange = (newStatus: ConnectionStatus, error?: string) => {
    status = newStatus;
    statusCallbacks.forEach((callback) => callback(newStatus));
    statusChangeCallback(newStatus, error);
  };

  const calculateReconnectDelay = (): number => {
    const baseDelay = 1000;
    const maxDelay = 30000;
    const backoffMultiplier = 2;

    // Exponential backoff with jitter
    const exponentialDelay = Math.min(
      baseDelay * Math.pow(backoffMultiplier, reconnectAttempts),
      maxDelay
    );

    // Add jitter: random value between 0% and 25% of the delay
    const jitter = Math.random() * 0.25 * exponentialDelay;

    return exponentialDelay + jitter;
  };

  const sendSubscriptions = () => {
    if (ws?.readyState !== WebSocket.OPEN) return;

    try {
      // Subscribe to allMids for all price updates
      const allMidsSubscription: HyperliquidSubscription = {
        method: 'subscribe',
        subscription: { type: 'allMids' },
      };
      ws.send(JSON.stringify(allMidsSubscription));
      console.log('[Hyperliquid] Subscribed to allMids');

      // Subscribe to individual coin trades for more detailed data
      SYMBOLS.forEach((symbol) => {
        const tradesSubscription: HyperliquidSubscription = {
          method: 'subscribe',
          subscription: { type: 'trades', coin: symbol },
        };
        ws.send(JSON.stringify(tradesSubscription));
        console.log(`[Hyperliquid] Subscribed to trades for ${symbol}`);
      });
    } catch (error) {
      console.error('[Hyperliquid] Error sending subscriptions:', error);
    }
  };

  const startHeartbeat = () => {
    if (heartbeatInterval) clearInterval(heartbeatInterval);

    // Send ping every 30 seconds and check for stale connection
    heartbeatInterval = setInterval(() => {
      if (ws?.readyState === WebSocket.OPEN) {
        try {
          // Hyperliquid doesn't require explicit ping, but we check for stale data
          const timeSinceLastMessage = Date.now() - lastMessageTime;

          if (timeSinceLastMessage > 60000) {
            // No message in 60 seconds, connection might be stale
            console.warn('[Hyperliquid] Connection appears stale, reconnecting...');
            ws.close();
          }
        } catch (error) {
          console.error('[Hyperliquid] Heartbeat error:', error);
        }
      }
    }, 30000);
  };

  const stopHeartbeat = () => {
    if (heartbeatInterval) {
      clearInterval(heartbeatInterval);
      heartbeatInterval = null;
    }
  };

  const handleMessage = (rawData: unknown) => {
    try {
      lastMessageTime = Date.now();

      const message = rawData as HyperliquidMessage;

      if (message.channel === 'allMids') {
        // Handle allMids data: { "BTC": "45000.5", "ETH": "2500.25", ... }
        const mids = message.data as HyperliquidAllMids;

        console.log('[Hyperliquid] Received allMids data:', Object.keys(mids).length, 'symbols');

        Object.entries(mids).forEach(([symbol, priceStr]) => {
          if (SYMBOLS.includes(symbol)) {
            const price = parseFloat(priceStr);
            if (!isNaN(price)) {
              const normalizedSymbol = normalizeSymbol(symbol);
              const marketData = normalizeHyperliquidData(
                symbol,
                price,
                lastPrices[normalizedSymbol]
              );

              // Update last known price
              lastPrices[normalizedSymbol] = marketData;

              console.log(`[Hyperliquid] Updated ${normalizedSymbol}: $${price.toFixed(2)}`);
              onMarketData(marketData);
            }
          }
        });
      } else if (message.channel === 'trades') {
        // Handle individual trade data - data is already an array of trades
        const trades = message.data as HyperliquidTrade[];

        if (trades && Array.isArray(trades) && trades.length > 0) {
          const latestTrade = trades[trades.length - 1];
          const price = parseFloat(latestTrade.px);
          const normalizedSymbol = normalizeSymbol(latestTrade.coin);

          console.log(`[Hyperliquid] Processing trade: ${latestTrade.coin} at $${price}`);

          if (!isNaN(price)) {
            const marketData = normalizeHyperliquidData(
              latestTrade.coin,
              price,
              lastPrices[normalizedSymbol]
            );

            lastPrices[normalizedSymbol] = marketData;
            console.log(`[Hyperliquid] Sending market data to callback:`, normalizedSymbol, price);
            onMarketData(marketData);
          }
        }
      } else if (message.channel === 'subscriptionResponse') {
        console.log('[Hyperliquid] Subscription confirmed:', message.data);
      }

      // Notify generic message callbacks
      messageCallbacks.forEach((callback) => callback(message as WebSocketMessage));
    } catch (error) {
      console.error('[Hyperliquid] Error parsing message:', error);
    }
  };

  const scheduleReconnect = () => {
    if (intentionallyClosed) {
      notifyStatusChange('disconnected');
      return;
    }

    const delay = calculateReconnectDelay();
    reconnectAttempts++;
    onReconnectAttempt(reconnectAttempts);

    console.log(
      `[Hyperliquid] Reconnecting in ${Math.round(delay)}ms (attempt ${reconnectAttempts})`
    );

    reconnectTimeout = setTimeout(() => {
      connect();
    }, delay);
  };

  const connect = () => {
    if (ws?.readyState === WebSocket.OPEN || ws?.readyState === WebSocket.CONNECTING) {
      return;
    }

    try {
      console.log(`[Hyperliquid] Connecting to ${HYPERLIQUID_WS_URL}...`);
      notifyStatusChange('connecting');
      ws = new WebSocket(HYPERLIQUID_WS_URL);

      ws.onopen = () => {
        console.log('[Hyperliquid] WebSocket connection opened successfully!');
        notifyStatusChange('connected');
        reconnectAttempts = 0;
        onReconnectAttempt(0);
        lastMessageTime = Date.now();

        if (reconnectTimeout) {
          clearTimeout(reconnectTimeout);
          reconnectTimeout = null;
        }

        sendSubscriptions();
        startHeartbeat();
      };

      ws.onmessage = (event) => {
        console.log('[Hyperliquid] RAW MESSAGE RECEIVED:', event.data);
        try {
          const data = JSON.parse(event.data);
          console.log('[Hyperliquid] Parsed message:', JSON.stringify(data, null, 2));
          console.log('[Hyperliquid] Message channel:', data.channel || 'unknown channel');
          handleMessage(data);
        } catch (error) {
          console.error('[Hyperliquid] Error parsing message:', error, 'Raw data:', event.data);
        }
      };

      ws.onerror = (error) => {
        console.error('[Hyperliquid] WebSocket error:', error);
        console.error('[Hyperliquid] WebSocket readyState:', ws?.readyState);
        console.error('[Hyperliquid] This may be due to CORS restrictions or the API blocking browser connections');
        notifyStatusChange('disconnected', 'Connection error');
      };

      ws.onclose = (event) => {
        console.log('[Hyperliquid] Connection closed. Code:', event.code, 'Reason:', event.reason || 'No reason provided');
        console.log('[Hyperliquid] Close event details:', {
          code: event.code,
          reason: event.reason,
          wasClean: event.wasClean
        });
        stopHeartbeat();
        ws = null;

        if (!intentionallyClosed) {
          notifyStatusChange('disconnected', event.reason || 'Connection closed');
          scheduleReconnect();
        }
      };
    } catch (error) {
      console.error('[Hyperliquid] Error creating WebSocket:', error);
      notifyStatusChange('disconnected', String(error));
      scheduleReconnect();
    }
  };

  const disconnect = () => {
    intentionallyClosed = true;

    if (reconnectTimeout) {
      clearTimeout(reconnectTimeout);
      reconnectTimeout = null;
    }

    stopHeartbeat();

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
      console.warn('[Hyperliquid] WebSocket not connected, cannot send message');
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
