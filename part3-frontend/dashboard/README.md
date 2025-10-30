
## Features

- **Real-time Market Data**: Live price updates from Hyperliquid WebSocket API for BTC-USD, ETH-USD, and SOL-USD
- **Long/Short Position Support**: Full support for both long and short positions with accurate P&L calculations
- **Live P&L Tracking**: Monitor multiple trading positions with real-time profit/loss in both absolute ($) and percentage (%)
- **Smooth Animations**: Visual feedback with green/red flash animations on price movements and P&L flip animations
- **Connection Status**: Real-time WebSocket connection indicator with automatic reconnection and fallback to mock data
- **Responsive Design**: Mobile-first approach with optimized layouts for all screen sizes
- **Error Handling**: Top-level error boundary with graceful error recovery
- **Type Safety**: Full TypeScript implementation for better developer experience
- **Testing**: Comprehensive test coverage with 56 tests using Vitest and React Testing Library

## Getting Started

### Prerequisites

- Node.js 18.x or higher
- npm, yarn, or pnpm

### Installation

1. Clone the repository or navigate to the project directory:

```bash
cd dashboard
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
dashboard/
├── app/
│   ├── layout.tsx          # Root layout with error boundary
│   ├── page.tsx            # Main dashboard with ConnectionManager
│   └── globals.css         # Global styles
├── components/
│   ├── MarketTicker.tsx    # Real-time price display with animations
│   ├── AgentTable.tsx      # Position table with P&L and side badges
│   ├── ConnectionBadge.tsx # WebSocket status indicator
│   └── ErrorBoundary.tsx   # Error boundary component
├── lib/
│   ├── hyperliquid.ts      # Real Hyperliquid WebSocket client
│   ├── connectionManager.ts # Connection orchestration with fallback
│   ├── websocket.ts        # Mock WebSocket client (fallback)
│   ├── math.ts             # P&L calculations with long/short support
│   └── store.ts            # Zustand state management store
├── tests/
│   ├── MarketTicker.test.tsx  # MarketTicker component tests (6 tests)
│   ├── math.test.ts           # Math utilities tests (50 tests)
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

**Three-layer approach for resilience:**

1. **Real Client** (`lib/hyperliquid.ts`): Connects to Hyperliquid WebSocket API
   - URL: `wss://api.hyperliquid.xyz/ws`
   - Subscribes to `allMids` for real-time mid prices
   - Subscribes to `trades` for detailed trade data (BTC, ETH, SOL)
   - Implements jittered exponential backoff for reconnection (1s → 2s → 4s → 30s max)
   - Heartbeat mechanism to detect stale connections (60s timeout)

2. **Mock Client** (`lib/websocket.ts`): Fallback for when real API is unavailable
   - Simulates realistic market data with ~0.1% volatility
   - Same interface as real client for seamless switching

3. **Connection Manager** (`lib/connectionManager.ts`): Orchestration layer
   - Attempts real Hyperliquid connection first
   - Falls back to mock data after 10 seconds if no data received
   - Displays "FAKE DATA MODE" badge when using mock
   - Continues trying real API in background
   - Automatically switches back when real connection restored

**Why this approach?**
- Resilient to API outages or network issues
- Enables development without network dependency
- Clear user feedback about data source
- No interruption to user experience during connection issues

### 3. P&L Calculation Strategy

**Problem:** Need accurate P&L for both long and short positions with leverage, while handling edge cases.

**Solution:** Separate calculation functions in `lib/math.ts`

```typescript
// Modern approach with long/short awareness
calculatePnLWithSide(entryPrice, currentPrice, size, 'long' | 'short', leverage)
// Returns: { absolute, percentage, entryValue, currentValue }

// Legacy approach (backward compatible)
calculatePnL(entryPrice, currentPrice, size, leverage)
```

**Key features:**
- **Long positions**: Profit when price increases
- **Short positions**: Profit when price decreases
- **Edge case handling**: NaN, Infinity, negative values → returns safe default (0)
- **Leverage support**: Accurate P&L amplification
- **Dual output**: Both absolute ($) and percentage (%) values

**Critical decision: useMemo vs useEffect**

```typescript
// ❌ WRONG - Causes infinite re-renders
useEffect(() => {
  const newPositions = positions.map(p => ({ ...p, pnl: calculatePnL(...) }));
  setPositions(newPositions); // Triggers another render!
}, [positions]);

// ✅ CORRECT - Pure computation without side effects
const positionsWithPnL = useMemo(() => {
  return positions.map(p => ({ ...p, pnl: calculatePnL(...) }));
}, [positions, marketData]);
```

This was a critical fix early in development to prevent "Maximum update depth exceeded" errors.

### 4. Component Architecture

**MarketTicker Component:**
- Displays real-time market data for a single trading pair
- Implements price change animations (green flash for up, red for down)
- Shows bid/ask spread and calculates spread percentage
- Loading state with skeleton animation
- Fully responsive with Tailwind CSS

**AgentTable Component:**
- Desktop: Full table layout with Side, Size, Entry Price, Leverage, P&L ($), P&L (%)
- Mobile: Responsive card layout for better mobile UX
- Side badges: Blue for LONG, Purple for SHORT
- Live P&L calculation using `useMemo` (not `useEffect` to avoid infinite loops!)
- Flip animations: Pulse effect when P&L crosses from profit to loss or vice versa
- Color-coded P&L: Green for profit, red for loss

**ConnectionBadge Component:**
- Visual indicator of WebSocket connection status
- Animated dot (pulse for connecting, ping for connected)
- Color-coded status:
  - 🟢 Green "Connected" = Real Hyperliquid data
  - 🟠 Orange "FAKE DATA MODE" = Using mock data
  - 🟡 Yellow "Reconnecting (n)" = Attempting reconnection
  - 🔴 Red "Disconnected" = No connection

### 5. Testing Strategy

**Vitest + React Testing Library:**
- **Fast**: Vitest is significantly faster than Jest
- **Native ESM**: Better compatibility with modern JavaScript modules
- **Watch Mode**: Instant feedback during development
- **Component Tests**: MarketTicker component with various states (6 tests)
- **Unit Tests**: P&L calculations with comprehensive edge cases (50 tests)
- **Coverage**: 56 total tests covering long/short positions, leverage, NaN/Infinity handling

**Test breakdown:**
- Long position profit/loss scenarios
- Short position profit/loss scenarios
- Leverage multiplier validation
- Edge cases: NaN, Infinity, zero, negative values
- Real-world trading scenarios (BTC, ETH, SOL with various leverage)
- Currency and number formatting

### 6. Styling: Tailwind CSS

**Benefits:**
- **Utility-First**: Rapid UI development with utility classes
- **Responsive**: Mobile-first approach with responsive modifiers (`md:`, `lg:`)
- **Dark Mode**: Built-in dark mode support (though not activated in current design)
- **Consistency**: Design system enforced through utility classes
- **Performance**: Purged unused CSS in production builds

### 7. TypeScript

**Type Safety Benefits:**
- **Interfaces**: Strongly typed market data, positions, WebSocket messages
- **Position Side**: Type-safe `'long' | 'short'` literal types
- **Type Inference**: Zustand store automatically infers state types
- **Compile-Time Errors**: Catch errors before runtime
- **Better DX**: IDE autocomplete and inline documentation
- **Refactoring Safety**: Confident refactoring with type checking

### 8. Next.js 14 App Router

**Modern Features:**
- **Server Components**: Default server rendering for better performance
- **Client Components**: `'use client'` directive for interactive components
- **File-based Routing**: Intuitive routing structure
- **Built-in Optimization**: Image optimization, font optimization, etc.
- **Fast Refresh**: Instant feedback during development

### 9. Error Handling

**Multi-level approach:**
- **Top-level Error Boundary**: Catches React component errors, shows friendly message
- **WebSocket Error Handling**: Logs errors, triggers reconnection, falls back to mock
- **Math Guards**: Edge case validation in P&L calculations (prevents NaN/Infinity bugs)
- **TypeScript**: Compile-time type checking prevents runtime errors

### 10. Performance Optimizations

- **Selective Re-renders**: Zustand selectors prevent unnecessary re-renders
- **Memoization**: `useMemo` for P&L calculations, only recomputes when dependencies change
- **Efficient Updates**: Only affected components re-render on state changes
- **Lazy Loading**: Components load only when needed
- **Optimized Bundle**: Next.js automatically optimizes production bundles

## Hyperliquid WebSocket Integration

### Connection Details

The dashboard connects to the **real Hyperliquid WebSocket API**:

- **URL**: `wss://api.hyperliquid.xyz/ws`
- **Subscriptions**:
  - `allMids` - Real-time mid prices for all trading pairs
  - `trades` - Individual trade data for BTC, ETH, SOL

### Connection Status

Check the **ConnectionBadge** in the top-right corner:
- 🟢 **Connected** - Successfully receiving real Hyperliquid data
- 🟠 **FAKE DATA MODE** - Using mock data (connection failed or took >10s)
- 🟡 **Reconnecting (n)** - Attempting to reconnect (shows attempt count)
- 🔴 **Disconnected** - No connection established

### Fallback Strategy

1. Attempt Hyperliquid WebSocket connection
2. If no data received after **10 seconds** → automatically switch to mock data
3. Continue attempting real API connection in background
4. Automatically switch back to real data when connection restored

### Mock Data (Fallback Only)

When using mock data (orange badge), the dashboard simulates:

- **Base Prices**: BTC-USD ($45,000), ETH-USD ($2,500), SOL-USD ($100)
- **Volatility**: ~0.1% price fluctuation
- **Update Frequency**: 1-2 seconds
- **Spread**: ~0.05% of price
- **Volume**: Random values between 500M and 1.5B

### Known Limitations

- **24h Volume & % Change**: Not provided by Hyperliquid WebSocket (displays 0)
  - These would require REST API calls or historical data storage
- **Bid/Ask Spread**: Estimated from mid price (~0.05% typical spread)
  - Hyperliquid provides mid prices, not full order book depth

## Future Enhancements

- [ ] Add historical price charts (using Chart.js or Recharts)
- [ ] Implement order placement functionality
- [ ] Add position management UI (open/close/modify positions)
- [ ] Fetch 24h volume and % change from Hyperliquid REST API
- [ ] Persist user preferences in localStorage
- [ ] Add dark mode toggle
- [ ] Implement multi-language support (i18n)
- [ ] Add notification system for price alerts
- [ ] Implement position history and trade logs
- [ ] Add WebSocket message compression
- [ ] Enhance test coverage to 90%+
- [ ] Add E2E tests with Playwright

## Technologies Used

- **Framework**: Next.js 14 (App Router)
- **Language**: TypeScript 5
- **Styling**: Tailwind CSS 3
- **State Management**: Zustand
- **Testing**: Vitest + React Testing Library
- **WebSocket**: Native WebSocket API
- **Linting**: ESLint

## License

This project is created for demonstration purposes.
