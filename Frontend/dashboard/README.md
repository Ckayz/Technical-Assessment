# Phoenix Dashboard

A real-time cryptocurrency trading dashboard built with Next.js 14, TypeScript, and Tailwind CSS. This dashboard displays live market data for BTC-USD, ETH-USD, and SOL-USD, along with agent positions and their live P&L calculations.

![Next.js](https://img.shields.io/badge/Next.js-14-black?style=flat-square&logo=next.js)
![TypeScript](https://img.shields.io/badge/TypeScript-5-blue?style=flat-square&logo=typescript)
![Tailwind CSS](https://img.shields.io/badge/Tailwind-3-38bdf8?style=flat-square&logo=tailwind-css)
![Vitest](https://img.shields.io/badge/Vitest-Latest-6E9F18?style=flat-square&logo=vitest)

## Features

- **Real-time Market Data**: Live price updates for BTC-USD, ETH-USD, and SOL-USD with bid/ask spreads, 24h volume, and percentage changes
- **Agent Position Tracking**: Monitor multiple trading positions with live P&L calculations based on current market prices
- **Smooth Animations**: Visual feedback with green/red flash animations on price movements
- **Connection Status**: Real-time WebSocket connection status indicator with automatic reconnection
- **Responsive Design**: Mobile-first approach with optimized layouts for all screen sizes
- **Error Handling**: Top-level error boundary with graceful error recovery
- **Type Safety**: Full TypeScript implementation for better developer experience
- **Testing**: Comprehensive test coverage with Vitest and React Testing Library

## Getting Started

### Prerequisites

- Node.js 18.x or higher
- npm, yarn, or pnpm

### Installation

1. Clone the repository or navigate to the project directory:

```bash
cd phoenix-dashboard
```

2. Install dependencies:

```bash
npm install
# or
yarn install
# or
pnpm install
```

### Running the Development Server

```bash
npm run dev
# or
yarn dev
# or
pnpm dev
```

Open [http://localhost:3000](http://localhost:3000) with your browser to see the dashboard.

### Building for Production

```bash
npm run build
npm run start
```

### Running Tests

```bash
# Run tests once
npm test -- --run

# Run tests in watch mode
npm test

# Run tests with UI
npm run test:ui

# Run tests with coverage
npm run test:coverage
```

## Project Structure

```
phoenix-dashboard/
├── app/
│   ├── layout.tsx          # Root layout with error boundary
│   ├── page.tsx            # Main dashboard page with ConnectionManager
│   └── globals.css         # Global styles
├── components/
│   ├── MarketTicker.tsx    # Market data display component
│   ├── AgentTable.tsx      # Agent positions table component
│   ├── ConnectionBadge.tsx # WebSocket connection status indicator
│   └── ErrorBoundary.tsx   # Error boundary component
├── lib/
│   ├── hyperliquid.ts      # Real Hyperliquid WebSocket client
│   ├── connectionManager.ts # Connection manager with fallback logic
│   ├── websocket.ts        # Mock WebSocket client (fallback)
│   ├── math.ts             # Math utilities (P&L calculations)
│   └── store.ts            # Zustand state management store
├── tests/
│   ├── MarketTicker.test.tsx  # MarketTicker component tests
│   ├── math.test.ts           # Math utilities tests
│   └── setup.ts               # Test setup configuration
├── vitest.config.ts        # Vitest configuration
└── README.md
```

## Architecture Decisions

### 1. State Management: Zustand

**Why Zustand?**
- **Simplicity**: Minimal boilerplate compared to Redux or Context API
- **Performance**: Efficient re-renders with selector-based subscriptions
- **TypeScript Support**: Excellent type inference and type safety
- **Bundle Size**: Small footprint (~1KB gzipped)
- **DevTools**: Compatible with Redux DevTools for debugging

Zustand was chosen over alternatives because:
- **vs Redux**: Less boilerplate, no need for actions/reducers/middleware
- **vs Context API**: Better performance, no unnecessary re-renders
- **vs Jotai/Recoil**: Simpler API, more straightforward for this use case

### 2. WebSocket Architecture

**Design Decisions:**
- **Abstraction Layer**: Created a WebSocket client wrapper to handle connection lifecycle
- **Exponential Backoff**: Implements reconnection with increasing delays (1s → 2s → 4s → max 30s)
- **Mock Client**: Separate mock implementation for development/testing without real WebSocket server
- **Connection Status**: Centralized status management for UI feedback
- **Type Safety**: Strongly typed message handlers and configuration

**Reconnection Strategy:**
- Initial delay: 1 second
- Backoff multiplier: 2x
- Maximum delay: 30 seconds
- Maximum attempts: Configurable (default: Infinity)

### 3. Component Architecture

**MarketTicker Component:**
- Displays real-time market data for a single trading pair
- Implements price change animations (green flash for up, red for down)
- Shows bid/ask spread and calculates spread percentage
- Loading state with skeleton animation
- Fully responsive with Tailwind CSS

**AgentTable Component:**
- Desktop: Full table layout with all columns
- Mobile: Responsive card layout for better mobile UX
- Live P&L calculation triggered by market data updates
- Color-coded P&L (green for profit, red for loss)

**ConnectionBadge Component:**
- Visual indicator of WebSocket connection status
- Animated dot (pulse for connecting, ping for connected)
- Color-coded: green (connected), yellow (connecting), red (disconnected)

### 4. Testing Strategy

**Vitest + React Testing Library:**
- **Fast**: Vitest is significantly faster than Jest
- **Native ESM**: Better compatibility with modern JavaScript modules
- **Watch Mode**: Instant feedback during development
- **Component Tests**: MarketTicker component with various states
- **Utility Tests**: Math functions for P&L and formatting
- **Coverage**: Core functionality covered with 25+ tests

### 5. Styling: Tailwind CSS

**Benefits:**
- **Utility-First**: Rapid UI development with utility classes
- **Responsive**: Mobile-first approach with responsive modifiers
- **Dark Mode**: Built-in dark mode support (though not activated in current design)
- **Consistency**: Design system enforced through utility classes
- **Performance**: Purged unused CSS in production builds

### 6. TypeScript

**Type Safety Benefits:**
- **Interfaces**: Strongly typed market data, positions, and WebSocket messages
- **Type Inference**: Zustand store automatically infers state types
- **Compile-Time Errors**: Catch errors before runtime
- **Better DX**: IDE autocomplete and inline documentation
- **Refactoring Safety**: Confident refactoring with type checking

### 7. Next.js 14 App Router

**Modern Features:**
- **Server Components**: Default server rendering for better performance
- **Client Components**: 'use client' directive for interactive components
- **File-based Routing**: Intuitive routing structure
- **Built-in Optimization**: Image optimization, font optimization, etc.
- **Fast Refresh**: Instant feedback during development

### 8. Error Handling

**Error Boundary:**
- Top-level error boundary wraps the entire application
- Catches runtime errors in component tree
- Provides user-friendly error message
- Shows error details in development for debugging
- Refresh button to recover from errors

### 9. Performance Optimizations

- **Selective Re-renders**: Zustand selectors prevent unnecessary re-renders
- **Memoization**: Price animations use useEffect with proper dependencies
- **Efficient Updates**: Only affected components re-render on state changes
- **Lazy Loading**: Components load only when needed
- **Optimized Bundle**: Next.js automatically optimizes production bundles

## Hyperliquid WebSocket Integration

The dashboard automatically connects to the **Hyperliquid WebSocket API** for real-time market data. If the connection fails or the WebSocket schema differs, it automatically falls back to mock data after 10 seconds.

### WebSocket URL

```
wss://api.hyperliquid.xyz/ws
```

### Connection Architecture

The dashboard uses a **ConnectionManager** that implements a robust fallback strategy:

1. **Primary Connection**: Attempts to connect to Hyperliquid WebSocket API
2. **10-Second Timeout**: If no successful connection after 10 seconds, automatically switches to mock data
3. **Fake Data Indicator**: Displays an orange "FAKE DATA MODE" badge when using mock data
4. **Background Reconnection**: Continues attempting to connect to real API in the background
5. **Automatic Switchover**: Switches back to real data when connection is restored

### Subscriptions

The client subscribes to the following Hyperliquid channels on connection:

#### 1. All Mids (allMids)
```typescript
{
  method: 'subscribe',
  subscription: { type: 'allMids' }
}
```
Provides aggregated mid-prices for all trading pairs in real-time.

#### 2. Individual Coin Trades
```typescript
{
  method: 'subscribe',
  subscription: { type: 'trades', coin: 'BTC' }
}
{
  method: 'subscribe',
  subscription: { type: 'trades', coin: 'ETH' }
}
{
  method: 'subscribe',
  subscription: { type: 'trades', coin: 'SOL' }
}
```
Provides detailed trade data for each coin including price, size, side, and timestamp.

### Message Normalization

Hyperliquid uses coin symbols like "BTC", "ETH", "SOL" while the dashboard uses "BTC-USD", "ETH-USD", "SOL-USD". The `normalizeSymbol()` function in `lib/hyperliquid.ts` automatically converts between formats.

**Example Message Flow:**
```typescript
// Incoming from Hyperliquid
{
  channel: 'allMids',
  data: {
    'BTC': '45000.5',
    'ETH': '2500.25',
    'SOL': '100.75'
  }
}

// Normalized to Dashboard Format
{
  symbol: 'BTC-USD',
  price: 45000.5,
  bid: 44978.25,  // Estimated
  ask: 45022.75,  // Estimated
  volume24h: 0,
  change24h: 0,
  timestamp: 1640000000000
}
```

### Auto-Reconnection Strategy

The Hyperliquid client implements **jittered exponential backoff** for reconnection:

- **Initial Delay**: 1 second
- **Backoff Multiplier**: 2x (1s → 2s → 4s → 8s → 16s → 30s)
- **Maximum Delay**: 30 seconds
- **Jitter**: Random 0-25% added to prevent thundering herd
- **Maximum Attempts**: Unlimited (keeps retrying)

**Example Reconnection Timeline:**
```
Attempt 1: 1.12s delay (1s + 12% jitter)
Attempt 2: 2.43s delay (2s + 21% jitter)
Attempt 3: 4.67s delay (4s + 17% jitter)
Attempt 4: 8.92s delay (8s + 12% jitter)
Attempt 5: 17.34s delay (16s + 8% jitter)
Attempt 6: 27.56s delay (30s max + 8% jitter)
```

The reconnection count is displayed in the ConnectionBadge: "Reconnecting (3)"

### Heartbeat Mechanism

To detect stale connections, the client implements a heartbeat system:

- **Interval**: 30 seconds
- **Stale Threshold**: 60 seconds without messages
- **Action**: Automatically closes and reconnects if no messages received for 60 seconds

### Connection Status Badge

The `ConnectionBadge` component displays real-time connection status:

| Status | Color | Indicator |
|--------|-------|-----------|
| **Connected (Real)** | Green | Animated ping + "Connected" |
| **Connected (Fake)** | Orange | Solid dot + "FAKE DATA MODE" |
| **Connecting** | Yellow | Pulsing dot + "Connecting" |
| **Reconnecting** | Yellow | Pulsing dot + "Reconnecting (n)" |
| **Disconnected** | Red | Solid dot + "Disconnected" |
| **Error** | Red | Solid dot + "Error" + error message |

### Important Note

**⚠️ If the WebSocket schema differs from the expected format, the dashboard will automatically switch to mock mode.**

The connection manager will:
1. Attempt to parse incoming messages from Hyperliquid
2. If parsing fails or message format is unexpected, log warnings
3. Continue attempting reconnection in the background
4. Fall back to mock data if no successful messages after 10 seconds
5. Display "FAKE DATA MODE" badge to indicate mock data is being used

### File Structure

The Hyperliquid integration is split across three files:

**`lib/hyperliquid.ts`** - Real Hyperliquid WebSocket client
- Connection management
- Subscription handling
- Message parsing and normalization
- Reconnection with jittered exponential backoff
- Heartbeat mechanism

**`lib/connectionManager.ts`** - Fallback orchestration
- Manages real vs mock client switching
- Implements 10-second timeout
- Handles automatic fallback to mock
- Switches back to real when available

**`lib/websocket.ts`** - Mock WebSocket client (fallback)
- Simulates realistic market data
- Used when real API unavailable
- Same interface as real client

### Testing the Connection

**1. View Real Connection:**
```bash
npm run dev
```
Open http://localhost:3000 and look for a green "Connected" badge.

**2. Simulate Connection Failure:**
- Disconnect from internet
- Observe yellow "Reconnecting (n)" badge
- After 10 seconds, see orange "FAKE DATA MODE" badge
- Reconnect to internet
- Connection automatically switches back to green "Connected"

**3. Monitor Console Logs:**
```bash
# Connection logs
[Hyperliquid] Connected
[Hyperliquid] Subscribed to allMids
[Hyperliquid] Subscribed to trades for BTC
[Hyperliquid] Subscribed to trades for ETH
[Hyperliquid] Subscribed to trades for SOL

# Fallback logs (if connection fails)
[ConnectionManager] Real API failed for >10s, falling back to mock data
[Dashboard] Switched to mock data mode

# Reconnection logs
[Hyperliquid] Reconnecting in 2431ms (attempt 2)
[Hyperliquid] Connection closed: 1006
```

## Mock Data Fallback

When the dashboard cannot connect to Hyperliquid (or after 10 seconds of failed attempts), it automatically uses mock data:

- **Base Prices**: BTC-USD ($45,000), ETH-USD ($2,500), SOL-USD ($100)
- **Volatility**: ~0.1% price fluctuation
- **Update Frequency**: 1-2 seconds
- **Spread**: ~0.05% of price
- **Volume**: Random values between 500M and 1.5B
- **Visual Indicator**: Orange "FAKE DATA MODE" badge

## Future Enhancements

- [ ] Add historical price charts
- [ ] Implement order placement functionality
- [ ] Add position management (open/close positions)
- [ ] Persist user preferences in localStorage
- [ ] Add dark mode toggle
- [ ] Implement multi-language support
- [ ] Add notification system for price alerts
- [ ] Enhance test coverage to 90%+
- [ ] Add E2E tests with Playwright

## Technologies Used

- **Framework**: Next.js 14 (App Router)
- **Language**: TypeScript 5
- **Styling**: Tailwind CSS 3
- **State Management**: Zustand
- **Testing**: Vitest + React Testing Library
- **Linting**: ESLint

## License

This project is created for demonstration purposes.

## Author

Built as a technical assessment showcasing modern React/Next.js development practices.
