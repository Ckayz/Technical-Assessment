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
│   ├── page.tsx            # Main dashboard page
│   └── globals.css         # Global styles
├── components/
│   ├── MarketTicker.tsx    # Market data display component
│   ├── AgentTable.tsx      # Agent positions table component
│   ├── ConnectionBadge.tsx # WebSocket connection status indicator
│   └── ErrorBoundary.tsx   # Error boundary component
├── lib/
│   ├── websocket.ts        # WebSocket client with reconnection logic
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

## Mock Data

The dashboard currently uses a mock WebSocket client that simulates real-time market data:

- **Base Prices**: BTC-USD ($45,000), ETH-USD ($2,500), SOL-USD ($100)
- **Volatility**: ~0.1% price fluctuation
- **Update Frequency**: 1-2 seconds
- **Spread**: ~0.05% of price
- **Volume**: Random values between 500M and 1.5B

To connect to a real WebSocket server, replace `createMockWebSocketClient()` with `createWebSocketClient()` in `app/page.tsx` and provide the WebSocket URL.

## Future Enhancements

- [ ] Connect to real Hyperliquid WebSocket API
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
