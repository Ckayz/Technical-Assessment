# Phoenix Data Pipeline

**A production-ready data enrichment pipeline for blockchain swap data**

This project is a complete solution for the Data Pipeline Challenge, demonstrating real-world data engineering skills with clean, maintainable code.

---

## Table of Contents

- [What This Pipeline Does](#what-this-pipeline-does)
- [Quick Start](#quick-start)
- [Requirements Met](#requirements-met)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Configuration](#configuration)
- [How It Works](#how-it-works)
- [Design Decisions](#design-decisions)
- [Sample Output](#sample-output)
- [Testing](#testing)
- [Troubleshooting](#troubleshooting)

---

## What This Pipeline Does

Think of this as a **data assembly line** that:

1. **Fetches** raw swap data from Uniswap V3 (a decentralized exchange)
2. **Enriches** it with real-time crypto prices from CoinGecko
3. **Transforms** and aggregates the data into useful insights
4. **Exports** results to JSON and CSV files

### Real-World Example

```
Raw Data → [Pipeline] → Enriched Data

Input:
- Someone swapped 2 WETH for 4000 USDC

Pipeline:
- Fetches price: WETH = $2000, USDC = $1
- Calculates: Volume = $4000
- Groups: WETH-USDC pair

Output:
- CSV/JSON with USD values, pair stats, summaries
```

---

## Quick Start

### Prerequisites

- **Python 3.11+** ([Download](https://www.python.org/downloads/))
- **The Graph API Key** (free, takes 5 min - [Get here](https://thegraph.com/studio/))

### Installation

```bash
# 1. Clone the repository
git clone <your-repo-url>
cd phoenix-pipeline

# 2. Install uv (fast Python package manager)
curl -LsSf https://astral.sh/uv/install.sh | sh

# 3. Create virtual environment and install dependencies
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
uv pip install -e .
```

### Configuration

1. **Copy the example environment file:**
   ```bash
   cp .env.example .env
   ```

2. **Edit `.env` and add your API key:**
   ```bash
   # Get your free API key from: https://thegraph.com/studio/
   SUBGRAPH_URL=https://gateway.thegraph.com/api/YOUR_KEY_HERE/subgraphs/id/HUZDsRpEVP2AvzDCyzDHtdc64dyDxx8FQjzsmqSg4H3B

   # Optional: CoinGecko is free without a key (with rate limits)
   COINGECKO_API_KEY=
   ```

### Run the Pipeline

```bash
# Option 1: Using Python module
python -m phoenix_pipeline

# Option 2: Using Makefile
make run

# Option 3: Using the installed command
phoenix-pipeline
```

**First run?** See [Setup Guide](#setup-guide) below for getting your API key.

---

## Requirements Met

This pipeline fulfills all challenge requirements:

### ✅ 1. Data Ingestion
- Queries **Uniswap V3 subgraph** on The Graph
- Fetches recent swap events (configurable time window)
- Automatic pagination for large datasets
- Retry logic with exponential backoff

**Code:** `src/phoenix_pipeline/subgraph.py`

### ✅ 2. Data Enrichment
- Enriches swaps with **CoinGecko price data**
- Transforms raw token amounts to USD values
- Aggregates by trading pairs
- Handles multiple token standards (ERC-20 with different decimals)

**Code:** `src/phoenix_pipeline/coingecko.py`, `src/phoenix_pipeline/transform.py`

### ✅ 3. Data Output
- Exports to **JSON** (`output/swaps.json`)
- Exports to **CSV** (`output/summary.csv`)
- Summary statistics (count, total volume, average per pair)
- Timestamped output files

**Code:** `src/phoenix_pipeline/io.py`, `src/phoenix_pipeline/main.py`

### ✅ 4. Production-Ready Features

| Feature | Implementation | Why It Matters |
|---------|---------------|----------------|
| **Idempotent** | State tracking with `state.json` | Can re-run without duplicates |
| **Rate Limiting** | Sliding window rate limiter | Respects API limits, avoids bans |
| **Error Handling** | Try-catch with retries | Handles network failures gracefully |
| **Configuration** | Environment variables via `.env` | Easy to customize without code changes |
| **Logging** | Structured logging with levels | Easy debugging and monitoring |
| **Type Safety** | Pydantic models + mypy | Catches bugs before runtime |
| **Testing** | Comprehensive pytest suite | Ensures reliability |

**Code:** All modules include these features

---

## Tech Stack

### Core
- **Python 3.11+** - Modern Python with type hints
- **Pydantic** - Data validation and settings management
- **pandas** - Data transformation and aggregation
- **httpx** - Async-capable HTTP client

### APIs
- **The Graph** - Blockchain data indexing (Uniswap V3 subgraph)
- **CoinGecko** - Cryptocurrency price data

### Development
- **pytest** - Testing framework with fixtures
- **mypy** - Static type checking
- **uv** - Fast package management
- **GitHub Actions** - CI/CD automation

---

## Project Structure

```
phoenix-pipeline/
├── src/
│   └── phoenix_pipeline/
│       ├── __init__.py           # Package initialization
│       ├── __main__.py           # Entry point (python -m phoenix_pipeline)
│       ├── config.py             # Settings and data models (Pydantic)
│       ├── subgraph.py           # GraphQL client for Uniswap data
│       ├── coingecko.py          # Price API client with rate limiting
│       ├── transform.py          # Data transformation and enrichment
│       ├── io.py                 # File I/O and state management
│       └── main.py               # Pipeline orchestrator
│
├── tests/                        # Test suite
│   ├── conftest.py              # Pytest fixtures
│   ├── test_config.py           # Config tests
│   ├── test_transform.py        # Transform logic tests
│   ├── test_io.py               # I/O tests
│   └── test_pipeline_integration.py  # End-to-end tests
│
├── output/                       # Generated output (not in git)
│   ├── swaps.json               # Enriched swap data
│   ├── summary.csv              # Aggregated statistics
│   └── state.json               # Pipeline state (for idempotency)
│
├── .env.example                  # Example configuration
├── .env                          # Your configuration (not in git)
├── pyproject.toml               # Dependencies and package config
├── Makefile                     # Convenience commands
├── README.md                    # This file
└── DESIGN_DECISIONS.md          # Detailed design explanations
```

### Key Files Explained

- **config.py**: All settings in one place using Pydantic for validation
- **subgraph.py**: Handles GraphQL queries, pagination, retries
- **coingecko.py**: Fetches prices with caching and rate limiting
- **transform.py**: Converts raw swap data to enriched insights
- **io.py**: Reads/writes files, manages state for idempotency
- **main.py**: Orchestrates the entire pipeline workflow

---

## Configuration

All configuration is done via environment variables in `.env`:

### Required Settings

```bash
# The Graph API endpoint (REQUIRED - get free key at thegraph.com/studio)
SUBGRAPH_URL=https://gateway.thegraph.com/api/YOUR_KEY/subgraphs/id/HUZDsRpEVP2AvzDCyzDHtdc64dyDxx8FQjzsmqSg4H3B
```

### Optional Settings

```bash
# Time window for fetching swaps (default: 60 minutes)
WINDOW_MINUTES=60

# Number of records per batch (default: 100)
BATCH_SIZE=100

# Output directory (default: ./output)
OUTPUT_DIR=output

# State file location (default: output/state.json)
STATE_FILE=output/state.json

# Logging level: DEBUG, INFO, WARNING, ERROR (default: INFO)
LOG_LEVEL=INFO

# CoinGecko API key (optional - free tier works without key)
COINGECKO_API_KEY=

# CoinGecko rate limit (requests per minute, default: 10 for free tier)
COINGECKO_MAX_REQUESTS_PER_MIN=10
```

### Environment Variable Examples

```bash
# Fetch last 24 hours of swaps
WINDOW_MINUTES=1440 python -m phoenix_pipeline

# Enable debug logging
LOG_LEVEL=DEBUG python -m phoenix_pipeline

# Use larger batches (faster, more memory)
BATCH_SIZE=500 python -m phoenix_pipeline
```

---

## How It Works

### Pipeline Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                         PHOENIX PIPELINE                         │
└─────────────────────────────────────────────────────────────────┘

Step 1: Load Configuration & State
├── Read .env file (settings)
├── Read state.json (last processed block)
└── Initialize clients (Subgraph, CoinGecko)

Step 2: Fetch Swap Data
├── Compute time window (e.g., last 60 minutes)
├── Build GraphQL query
├── Fetch from Uniswap V3 subgraph (with pagination)
└── Exit if no swaps found

Step 3: Filter by State (Idempotency)
├── Extract latest block number from swaps
├── Filter out already-processed swaps (block <= last_processed_block)
└── Exit if no new swaps

Step 4: Collect Tokens & Fetch Prices
├── Extract unique token addresses from swaps
├── Fetch USD prices from CoinGecko (with rate limiting)
└── Cache prices for reuse within run

Step 5: Enrich & Transform
├── Match prices to swaps
├── Calculate USD volumes (handle stablecoins correctly)
├── Create pair identifiers (token0-token1)
└── Skip swaps with missing prices

Step 6: Summarize
├── Group by trading pair
├── Calculate: count, total volume, average volume
└── Sort by total volume (highest first)

Step 7: Write Outputs
├── Write enriched swaps to output/swaps.json
├── Write summary to output/summary.csv
└── Update state.json with latest block

Step 8: Print Statistics
└── Display run stats (counts, time, API calls, skipped swaps)
```

### Code Flow Example

```python
# Simplified version of what the pipeline does

# 1. Load state
state = read_state()  # {"last_processed_block": 18000000}

# 2. Fetch swaps
swaps = client.get_recent_swaps(window_minutes=60)
# Returns: [
#   {txHash: "0xabc", blockNumber: 18000100, token0: "WETH", token1: "USDC", ...},
#   {txHash: "0xdef", blockNumber: 18000200, token0: "WBTC", token1: "USDC", ...}
# ]

# 3. Filter by state (skip block 18000000 and earlier)
new_swaps = filter_swaps_by_block(swaps, last_processed_block=18000000)
# Returns: [both swaps, since they're > 18000000]

# 4. Get unique tokens
tokens = {"0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2", "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48", ...}

# 5. Fetch prices
prices = coingecko.fetch_prices(tokens)
# Returns: {"0xc02...": 2000.0, "0xa0b...": 1.0, ...}

# 6. Enrich
enriched = transformer.enrich_swaps(new_swaps, prices)
# Returns: [
#   {txHash: "0xabc", ..., priceUSD0: 2000.0, priceUSD1: 1.0, usdVolume: 4000.0, pair: "WETH-USDC"},
#   {txHash: "0xdef", ..., priceUSD0: 40000.0, priceUSD1: 1.0, usdVolume: 20000.0, pair: "WBTC-USDC"}
# ]

# 7. Summarize
summary = transformer.summarize(enriched)
# Returns:
#   pair         count  totalUSD  avgUSD
#   WBTC-USDC    1      20000.00  20000.00
#   WETH-USDC    1      4000.00   4000.00

# 8. Write outputs
write_json("output/swaps.json", enriched)
write_csv("output/summary.csv", summary)
write_state(block=18000200)  # Save latest block
```

---

## Design Decisions

### Why These Choices?

#### 1. **Pydantic for Configuration**

**What:** Type-safe settings management with automatic validation

**Why:**
- Catches configuration errors before the pipeline runs
- Clear error messages (e.g., "BATCH_SIZE must be > 0")
- Auto-loads from environment variables
- Self-documenting (settings have types and defaults)

**Example:**
```python
# Bad: Manual validation
batch_size = int(os.getenv("BATCH_SIZE", "100"))
if batch_size <= 0:
    raise ValueError("BATCH_SIZE must be positive")

# Good: Pydantic handles it
class Settings(BaseSettings):
    batch_size: int = Field(default=100, gt=0)
```

#### 2. **State-Based Idempotency**

**What:** Track last processed block in `state.json`

**Why:**
- Safe to re-run: won't process same swaps twice
- Resume after crashes: picks up where it left off
- No duplicates in output files

**Example:**
```python
# First run: processes blocks 1000-1100, saves state = 1100
# Second run: only processes blocks > 1100 (new data)
# Crash recovery: reads state, continues from block 1100
```

#### 3. **Sliding Window Rate Limiter**

**What:** Track API requests in a time window (e.g., 10 requests/minute)

**Why:**
- Respects CoinGecko's free tier limits
- Prevents API bans
- More accurate than fixed delays (adapts to burst patterns)

**Example:**
```python
# Without limiter: 100 requests in 10 seconds → BANNED
# With limiter: Spreads 100 requests over 10 minutes → OK
```

#### 4. **Retry with Exponential Backoff**

**What:** Retry failed requests with increasing delays (2s, 4s, 8s)

**Why:**
- Handles temporary network issues
- Gives servers time to recover
- Avoids hammering struggling services

**Example:**
```python
# Request fails → wait 2s → retry
# Fails again → wait 4s → retry
# Fails again → wait 8s → retry
# Still fails → give up, log error
```

#### 5. **Stablecoin-Aware Volume Calculation**

**What:** Use one side for stable-stable pairs, sum for others

**Why:**
- USDC-USDT swap: both sides ≈ same value (avoid double counting)
- WETH-USDC swap: sum both sides (standard approach)
- More accurate volume metrics

**Example:**
```python
# Swap: 1000 USDC → 999 USDT
# Bad: volume = 1000 + 999 = $1999 (inflated)
# Good: volume = 1000 (one side only, since both are ~$1)

# Swap: 1 WETH → 2000 USDC
# volume = |1 * $2000| + |2000 * $1| = $4000 (sum both)
```

#### 6. **Context Managers for Resources**

**What:** Use `with` statements for clients (auto-cleanup)

**Why:**
- HTTP connections closed properly
- No resource leaks
- Cleaner code

**Example:**
```python
# Bad: Manual cleanup
client = SubgraphClient()
try:
    swaps = client.get_swaps()
finally:
    client.close()

# Good: Context manager
with SubgraphClient() as client:
    swaps = client.get_swaps()
# Auto-closed here
```

### Trade-offs Made

| Decision | Pro | Con | Why Chosen |
|----------|-----|-----|------------|
| Use pandas | Fast aggregations, familiar | Memory-heavy for huge datasets | Swaps fit in memory, simplicity wins |
| Static token mapping | Fast, no API calls | Limited to known tokens | Common tokens covered, extensible |
| File-based state | Simple, no database | Not suitable for distributed systems | Single-machine pipeline is fine |
| Free CoinGecko tier | No cost | Rate limits (10 req/min) | Sufficient for demo, upgradeable |

---

## Sample Output

### Console Output (Abbreviated)

```bash
$ python -m phoenix_pipeline

2025-10-30 14:30:00 - INFO - ================================================================================
2025-10-30 14:30:00 - INFO - Starting Phoenix Pipeline
2025-10-30 14:30:00 - INFO - ================================================================================

2025-10-30 14:30:00 - INFO - [1/10] Loading configuration and state...
2025-10-30 14:30:00 - INFO -   Config: window=60min, batch_size=100
2025-10-30 14:30:00 - INFO -   State: last_processed_block=18500000

2025-10-30 14:30:01 - INFO - [3/10] Fetching swaps from subgraph...
2025-10-30 14:30:03 - INFO -   Fetched: 234 swaps

2025-10-30 14:30:03 - INFO - [4/10] Filtering swaps by state...
2025-10-30 14:30:03 - INFO -   Latest block in results: 18500150
2025-10-30 14:30:03 - INFO -   New swaps to process: 234

2025-10-30 14:30:03 - INFO - [5/10] Collecting unique tokens...
2025-10-30 14:30:03 - INFO -   Unique tokens: 48

2025-10-30 14:30:03 - INFO - [6/10] Fetching prices from CoinGecko...
2025-10-30 14:30:08 - INFO -   Prices fetched: 45/48 tokens

2025-10-30 14:30:08 - INFO - [7/10] Enriching swaps with price data...
2025-10-30 14:30:08 - INFO -   Enriched: 228 swaps

2025-10-30 14:30:08 - INFO - [8/10] Creating summary...
2025-10-30 14:30:08 - INFO -   Summary: 32 trading pairs

2025-10-30 14:30:08 - INFO - [9/10] Writing output files...
2025-10-30 14:30:08 - INFO -   ✓ Wrote 228 swaps to: output/swaps.json
2025-10-30 14:30:08 - INFO -   ✓ Wrote 32 pairs to: output/summary.csv

2025-10-30 14:30:08 - INFO - ================================================================================
2025-10-30 14:30:08 - INFO - Pipeline Completed Successfully!
2025-10-30 14:30:08 - INFO - ================================================================================

Run Statistics:
--------------------------------------------------------------------------------
  Execution Time:        8.45 seconds
  Swaps Fetched:         234
  Swaps Enriched:        228
  Swaps Skipped:         6 (missing prices)
  Unique Tokens:         48
  Prices Fetched:        45
  Trading Pairs:         32
  CoinGecko API Calls:   5
--------------------------------------------------------------------------------
```

### output/swaps.json (Sample)

```json
[
  {
    "txHash": "0x1a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0b1c2d3e4f5a6b7c8d9e0f1a2b",
    "blockNumber": 18500120,
    "timestamp": 1698765432,
    "token0": "0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2",
    "token1": "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48",
    "amount0": "1000000000000000000",
    "amount1": "-2000000000",
    "sqrtPriceX96": "1234567890123456789",
    "priceUSD0": 2000.5,
    "priceUSD1": 1.0,
    "usdVolume": 2000.5,
    "pair": "0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2-0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48"
  },
  ...
]
```

### output/summary.csv (Sample)

```csv
pair,count,totalUSD,avgUSD
0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2-0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48,145,2850000.50,19655.17
0x2260fac5e5542a773aa44fbcfedf7c193bc2c599-0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48,42,1680000.25,40000.01
0x1f9840a85d5af5bf1d1762f925bdaddc4201f984-0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2,28,168000.75,6000.03
...
```

### output/state.json

```json
{
  "last_processed_block": 18500150,
  "last_updated": "2025-10-30T14:30:08.123456"
}
```

---

## Testing

### Run All Tests

```bash
# Run full test suite
pytest

# With coverage report
pytest --cov=src/phoenix_pipeline --cov-report=html

# Run specific test file
pytest tests/test_pipeline_integration.py -v

# Run specific test
pytest tests/test_pipeline_integration.py::test_transform_basic -v
```

### Test Coverage

The project includes comprehensive tests:

- **Unit tests**: Individual functions (`test_transform.py`, `test_io.py`)
- **Integration tests**: Full pipeline scenarios (`test_pipeline_integration.py`)
- **Edge cases**: Missing prices, empty data, rate limiting

**Key tests:**
- `test_transform_basic`: Validates enrichment with fixtures
- `test_idempotency`: Ensures state-based filtering works
- `test_rate_limit`: Verifies rate limiter blocks correctly

### Type Checking

```bash
# Run mypy type checker
mypy src/phoenix_pipeline

# Expected output: Success: no issues found
```

### CI/CD

The project includes GitHub Actions workflow (`.github/workflows/ci.yml`):
- Runs on push/PR to `main` and `develop`
- Tests on Python 3.11 and 3.12
- Runs pytest with coverage
- Performs mypy type checking
- Uploads coverage to Codecov

---

## Troubleshooting

### Common Issues

#### 1. "malformed API key" or "Not found"

**Problem:** The Graph API key is missing or incorrect

**Solution:**
```bash
# 1. Get free API key: https://thegraph.com/studio/
# 2. Update .env file:
SUBGRAPH_URL=https://gateway.thegraph.com/api/YOUR_ACTUAL_KEY/subgraphs/id/HUZDsRpEVP2AvzDCyzDHtdc64dyDxx8FQjzsmqSg4H3B

# 3. Verify it's not still [api-key] placeholder
cat .env | grep SUBGRAPH_URL
```

#### 2. "No swaps found in time window"

**Problem:** The time window is too short or Uniswap has low activity

**Solution:**
```bash
# Increase time window to 24 hours
WINDOW_MINUTES=1440 python -m phoenix_pipeline
```

#### 3. Rate limit errors from CoinGecko

**Problem:** Too many price requests

**Solution:**
```bash
# Option 1: Reduce max requests per minute
COINGECKO_MAX_REQUESTS_PER_MIN=5 python -m phoenix_pipeline

# Option 2: Get CoinGecko Pro API key (higher limits)
# Sign up at https://www.coingecko.com/en/api/pricing
COINGECKO_API_KEY=your_key_here python -m phoenix_pipeline
```

#### 4. "No module named 'phoenix_pipeline'"

**Problem:** Package not installed or wrong virtual environment

**Solution:**
```bash
# Activate virtual environment
source .venv/bin/activate

# Install package
uv pip install -e .

# Verify installation
python -c "import phoenix_pipeline; print('OK')"
```

#### 5. Import errors or missing dependencies

**Problem:** Dependencies not installed

**Solution:**
```bash
# Reinstall all dependencies
uv pip install -e ".[dev]"

# Or with regular pip
pip install -e ".[dev]"
```

### Getting Help

1. **Check logs**: Set `LOG_LEVEL=DEBUG` for detailed output
2. **Test API key**: Use `curl` to test your Graph API endpoint
3. **Run basic tests**: `python test_main.py` (if available)
4. **Check GitHub Issues**: See if others had similar problems

---

## Setup Guide

### Getting The Graph API Key (5 minutes)

1. **Visit**: https://thegraph.com/studio/

2. **Connect Wallet**:
   - Click "Connect Wallet"
   - Use MetaMask, Coinbase Wallet, or any Web3 wallet
   - **Note**: No gas fees, no transactions—just for authentication
   - Don't have a wallet? Download [MetaMask](https://metamask.io/) (2 minutes)

3. **Create API Key**:
   - Once logged in, click "API Keys" in the sidebar
   - Click "Create API Key"
   - Name it (e.g., "phoenix-pipeline")
   - Copy the key (looks like: `abc123def456ghi789...`)

4. **Update `.env`**:
   ```bash
   # Open .env file
   nano .env

   # Find line 10:
   SUBGRAPH_URL=https://gateway.thegraph.com/api/[api-key]/subgraphs/id/HUZDsRpEVP2AvzDCyzDHtdc64dyDxx8FQjzsmqSg4H3B

   # Replace [api-key] with your actual key:
   SUBGRAPH_URL=https://gateway.thegraph.com/api/abc123def456ghi789/subgraphs/id/HUZDsRpEVP2AvzDCyzDHtdc64dyDxx8FQjzsmqSg4H3B

   # Save and exit
   ```

5. **Verify**:
   ```bash
   python -m phoenix_pipeline
   ```

### Why an API Key?

The Graph shut down their free hosted service on June 12, 2024, migrating to a decentralized network. Everyone now needs an API key, but it's still free:

- ✅ **100,000 queries/month** on free tier
- ✅ No credit card required
- ✅ More than enough for development

---

## Contributing

Want to improve the pipeline? Here's how:

1. **Fork** the repository
2. **Create** a feature branch (`git checkout -b feature/amazing-feature`)
3. **Add tests** for new functionality
4. **Ensure** all tests pass (`pytest`)
5. **Run** type checking (`mypy src/phoenix_pipeline`)
6. **Submit** a pull request

### Code Standards

- Use type hints for all functions
- Write docstrings for public APIs
- Add tests for new features
- Follow PEP 8 style guide
- Keep functions focused and testable

---

## License

MIT License - see LICENSE file for details

---

## Acknowledgments

- **Uniswap V3** for the decentralized exchange protocol
- **The Graph** for blockchain data indexing
- **CoinGecko** for cryptocurrency price data
- **pydantic**, **pandas**, **httpx** for excellent Python libraries

---

## Questions?

- **Found a bug?** Open an issue on GitHub
- **Need help?** Check the [Troubleshooting](#troubleshooting) section
- **Want to contribute?** See [Contributing](#contributing)

**Enjoy building with Phoenix Pipeline!** 🚀
