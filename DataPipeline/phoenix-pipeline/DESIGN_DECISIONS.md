# Design Decisions

This document explains the technical choices made in building the Phoenix Pipeline, why they were made, and what alternatives were considered.

---

## Architecture Overview

The pipeline follows a **linear, orchestrated** architecture:

```
Config → Fetch → Filter → Enrich → Transform → Output
```

**Why linear?**
- Simple to understand and debug
- Easy to add steps or modify existing ones
- Predictable execution flow
- Sufficient for single-machine processing

**Alternatives considered:**
- **Event-driven** (Apache Kafka, RabbitMQ): Overkill for this scale, adds complexity
- **DAG-based** (Apache Airflow): Too heavy for a simple pipeline, harder to test locally
- **Streaming** (Apache Flink, Spark Streaming): Not needed, batch processing is sufficient

---

## Key Design Decisions

### 1. Idempotency via State Tracking

**Decision:** Track last processed block in `state.json` file

**Why:**
- **Safe reruns**: Can run pipeline multiple times without duplicating data
- **Crash recovery**: Automatically resumes from last checkpoint
- **Simple**: No database needed, just a JSON file
- **Testable**: Easy to simulate different states in tests

**How it works:**
```python
# First run
state = {"last_processed_block": 0}
swaps = fetch_swaps()  # blocks 1000-1100
enriched_swaps = process(swaps)
save_state({"last_processed_block": 1100})

# Second run (or after crash)
state = {"last_processed_block": 1100}
swaps = fetch_swaps()  # blocks 1000-1200 (includes old data)
new_swaps = filter_swaps(swaps, after_block=1100)  # Only 1101-1200
enriched_swaps = process(new_swaps)
save_state({"last_processed_block": 1200})
```

**Alternatives:**
- **Checksum-based**: Hash output files to detect changes → slower, more complex
- **Timestamp-based**: Filter by event timestamp → blockchain reorganizations can cause issues
- **Database tracking**: Overkill for a single-machine pipeline

**Trade-offs:**
- ✅ Simple, reliable, easy to implement
- ✅ Works well for append-only data (blockchain events)
- ❌ Not suitable for distributed systems (file locking issues)
- ❌ Manual intervention needed if state file corrupts (rare)

---

### 2. Rate Limiting with Sliding Window

**Decision:** Implement sliding window rate limiter for CoinGecko API

**Why:**
- **Respect API limits**: CoinGecko free tier allows ~10 requests/minute
- **Avoid bans**: Prevents account suspension
- **Smooth traffic**: Spreads requests evenly over time
- **More accurate**: Better than fixed delays between requests

**How it works:**
```python
class RateLimiter:
    def __init__(self, max_requests=10, window_seconds=60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests = deque()  # Track request timestamps

    def acquire(self):
        now = time.time()

        # Remove old requests outside window
        while self.requests and self.requests[0] < now - self.window_seconds:
            self.requests.popleft()

        # If at limit, wait until oldest request expires
        if len(self.requests) >= self.max_requests:
            wait_time = (self.requests[0] + self.window_seconds) - now
            time.sleep(wait_time)

        # Record this request
        self.requests.append(now)
```

**Example:**
```
Scenario: max_requests=10, window=60s

00:00 - Request 1-10 (fast, all go through)
00:05 - Request 11 (WAIT 55s until request 1 expires at 01:00)
01:00 - Request 11 goes through
```

**Alternatives:**
- **Fixed delay**: `time.sleep(6)` between requests → simpler but wastes time
- **Token bucket**: More complex, no significant benefit for this use case
- **No limiting**: Risk getting banned

**Trade-offs:**
- ✅ Accurate, efficient, respects API limits
- ✅ Handles burst patterns gracefully
- ❌ Blocks execution (but necessary for API compliance)
- ❌ Not distributed-system friendly (in-memory state)

---

### 3. Retry with Exponential Backoff

**Decision:** Retry failed API calls with exponential backoff (2s, 4s, 8s)

**Why:**
- **Handle transient failures**: Network hiccups, temporary server issues
- **Give services time to recover**: Don't hammer struggling servers
- **Standard practice**: Used by AWS, Google Cloud, most APIs

**Implementation:**
```python
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential_jitter,
    retry_if_exception_type,
)

@retry(
    stop=stop_after_attempt(3),  # Max 3 attempts
    wait=wait_exponential_jitter(initial=2, max=10),  # 2s, 4s, 8s (with jitter)
    retry=retry_if_exception_type((httpx.RequestError, httpx.HTTPStatusError)),
)
def fetch_swaps():
    response = client.post(url, json=query)
    response.raise_for_status()
    return response.json()
```

**Backoff sequence:**
```
Attempt 1: Immediate
Attempt 2: Wait ~2s (1.5-2.5s with jitter)
Attempt 3: Wait ~4s (3-5s with jitter)
Attempt 4: Wait ~8s (6-10s with jitter, capped at max=10)
```

**Why jitter?**
- Prevents "thundering herd" problem (many clients retrying simultaneously)
- Spreads out retries over time

**Alternatives:**
- **Linear backoff**: 2s, 4s, 6s → less effective for overload scenarios
- **No retry**: Fragile, fails on temporary issues
- **Infinite retry**: Can hang forever, needs circuit breaker

**Trade-offs:**
- ✅ Robust, handles most failure scenarios
- ✅ Standard library (`tenacity`) is battle-tested
- ❌ Can slow down pipeline if API is consistently failing
- ❌ Doesn't help with permanent failures (bad API key, etc.)

---

### 4. Pydantic for Configuration

**Decision:** Use Pydantic `BaseSettings` for configuration management

**Why:**
- **Type safety**: Catches configuration errors at startup
- **Auto-validation**: Checks types, ranges, formats automatically
- **Environment variables**: Loads from `.env` automatically
- **Self-documenting**: Settings have types, defaults, descriptions

**Example:**
```python
from pydantic import Field
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    batch_size: int = Field(default=100, gt=0, description="Batch size for pagination")
    window_minutes: int = Field(default=60, gt=0, le=10080)  # Max 1 week
    subgraph_url: str = Field(..., description="GraphQL endpoint URL")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
```

**What it does:**
```python
# Bad config in .env
BATCH_SIZE=-10

# Pydantic raises clear error at startup:
# ValidationError: batch_size: ensure this value is greater than 0

# vs. Manual validation (easy to miss)
batch_size = int(os.getenv("BATCH_SIZE", "100"))
# Runs with -10, crashes later with cryptic error
```

**Alternatives:**
- **Manual `os.getenv()`**: Tedious, error-prone, no type checking
- **Config files (YAML, TOML)**: Extra dependency, environment variables are simpler
- **argparse**: Good for CLI, but env vars are more flexible for prod

**Trade-offs:**
- ✅ Catches errors early (fail fast)
- ✅ Clear error messages
- ✅ Less boilerplate
- ❌ Extra dependency (`pydantic`)
- ❌ Learning curve for Pydantic syntax

---

### 5. Stablecoin-Aware Volume Calculation

**Decision:** Use one side for stablecoin pairs, sum for others

**Why:**
- **Accurate metrics**: Avoids double-counting for stable-stable swaps
- **Industry standard**: Most DEX analytics use this approach

**Logic:**
```python
if token0_is_stable and token1_is_stable:
    # USDC-USDT: both ~$1, use one side
    volume = abs(amount0 * price0)
elif token0_is_stable:
    # WETH-USDC: use stable side (more accurate)
    volume = abs(amount0 * price0)
elif token1_is_stable:
    # USDT-WBTC: use stable side
    volume = abs(amount1 * price1)
else:
    # WETH-UNI: sum both sides (standard)
    volume = abs(amount0 * price0) + abs(amount1 * price1)
```

**Examples:**
```
Swap 1: 1000 USDC → 999 USDT
- Bad: 1000 * $1 + 999 * $1 = $1999 (inflated 2x)
- Good: 1000 * $1 = $1000

Swap 2: 1 WETH → 2000 USDC
- Bad: 2000 * $1 = $2000 (uses only one side)
- Good: 1 * $2000 = $2000 (same result, but USDC is more reliable)

Swap 3: 1 WETH → 5 UNI
- Volume: |1 * $2000| + |5 * $10| = $2050
```

**Alternatives:**
- **Always use one side**: Inconsistent, harder to explain
- **Always sum both**: Inflates stablecoin pair volumes
- **Use mid-price**: Complex, requires price oracle

**Trade-offs:**
- ✅ Accurate, matches industry standards
- ✅ Handles edge cases (stable-stable, stable-volatile)
- ❌ Requires maintaining stablecoin list
- ❌ Slight complexity in code

---

### 6. Token Decimal Handling

**Decision:** Static mapping of common tokens, default to 18 decimals

**Why:**
- **ERC-20 variation**: Tokens use different decimal places (6, 8, 18)
- **Accurate calculations**: Raw amounts need normalization
- **Performance**: No on-chain calls needed

**Mapping:**
```python
TOKEN_DECIMALS = {
    "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48": 6,   # USDC
    "0xdac17f958d2ee523a2206206994597c13d831ec7": 6,   # USDT
    "0x2260fac5e5542a773aa44fbcfedf7c193bc2c599": 8,   # WBTC
    "0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2": 18,  # WETH
    # ... more tokens
}

decimals = TOKEN_DECIMALS.get(token_address, 18)  # Default to 18
amount_normalized = amount_raw / (10 ** decimals)
```

**Example:**
```
USDC swap: amount_raw = 2000000000 (6 decimals)
Normalized: 2000000000 / 10^6 = 2000 USDC

WETH swap: amount_raw = 1000000000000000000 (18 decimals)
Normalized: 1000000000000000000 / 10^18 = 1 WETH
```

**Alternatives:**
- **On-chain lookup**: Call `token.decimals()` → slow, requires RPC node
- **Subgraph metadata**: Not always available, extra complexity
- **Assume 18**: Works for most tokens, but wrong for USDC, USDT, WBTC

**Trade-offs:**
- ✅ Fast, no network calls
- ✅ Covers most popular tokens
- ✅ Extensible (add more tokens easily)
- ❌ Limited to known tokens
- ❌ Defaults to 18 for unknown tokens (may be inaccurate)

---

### 7. Context Managers for Resource Management

**Decision:** Use `with` statements for all clients

**Why:**
- **Automatic cleanup**: Connections closed even if errors occur
- **No resource leaks**: HTTPX connections properly closed
- **Pythonic**: Standard practice in Python
- **Simpler error handling**: No need for try/finally everywhere

**Implementation:**
```python
class SubgraphClient:
    def __enter__(self):
        self.client = httpx.Client(timeout=30)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.client.close()

# Usage
with SubgraphClient() as client:
    swaps = client.get_swaps()
    # Automatic cleanup even if exception occurs
# client.client is now closed
```

**Alternatives:**
- **Manual cleanup**: `try/finally` everywhere → verbose, error-prone
- **Singletons**: Shared client instance → harder to test, state management issues
- **No cleanup**: Resource leaks, can exhaust file descriptors

**Trade-offs:**
- ✅ Clean, idiomatic Python
- ✅ Prevents resource leaks
- ✅ Works with testing frameworks
- ❌ Slightly more boilerplate in class definition
- ❌ Recreates clients on each use (acceptable for this scale)

---

### 8. File-Based State vs. Database

**Decision:** Use JSON file for state tracking

**Why:**
- **Simplicity**: No database setup, works out of the box
- **Portability**: Easy to copy, inspect, backup
- **Sufficient**: Single-machine pipeline, low concurrency
- **Debuggable**: Can manually edit if needed

**Alternatives:**
| Solution | Pros | Cons | When to Use |
|----------|------|------|-------------|
| **JSON file** | Simple, portable, no setup | Not distributed, file locking | Single machine, low frequency |
| **SQLite** | Queryable, atomic operations | File-based, not fully distributed | Single machine, more complex state |
| **PostgreSQL** | Distributed, transactional, scalable | Requires setup, overkill for simple state | Multi-machine, high concurrency |
| **Redis** | Fast, distributed, pub/sub | Requires Redis server, another service | Distributed systems, caching |

**When to upgrade:**
- Multiple machines running pipeline concurrently → Use PostgreSQL or Redis
- Need audit trail of all runs → Use database with history table
- State is complex (>100 fields) → Use SQLite or PostgreSQL
- Need transactions → Use database with ACID guarantees

**Trade-offs:**
- ✅ Zero setup, works immediately
- ✅ Human-readable, easy to debug
- ✅ Perfect for the current scale
- ❌ Not suitable for distributed systems
- ❌ No built-in locking (use file locks if needed)
- ❌ No query capabilities (but state is tiny, so not needed)

---

### 9. Static Token Mapping vs. Dynamic Lookup

**Decision:** Static mapping for common tokens, with CoinGecko fallback

**Why:**
- **Performance**: No API calls for known tokens
- **Reliability**: Works even if CoinGecko is down
- **Cost**: Free (no API calls consumed)
- **Coverage**: Top tokens account for 95%+ of volume

**Hybrid approach:**
```python
# 1. Check static mapping
TOKEN_MAP = {
    "0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2": "weth",
    "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48": "usd-coin",
    # ... top 50 tokens
}

coingecko_id = TOKEN_MAP.get(token_address)

if coingecko_id:
    # Fast path: use static mapping
    price = coingecko.get_price(coingecko_id)
else:
    # Slow path: query CoinGecko API for mapping
    coingecko_id = coingecko.search_token_by_address(token_address)
    price = coingecko.get_price(coingecko_id)
```

**Alternatives:**
- **Fully static**: No fallback → limited to known tokens
- **Fully dynamic**: Always query CoinGecko → slow, expensive
- **On-chain lookup**: Query token contract for symbol → requires RPC node, slow

**Trade-offs:**
- ✅ Fast for common tokens (99% of swaps)
- ✅ Extensible (can add more mappings)
- ✅ Graceful degradation (falls back to API)
- ❌ Requires maintenance (add new popular tokens)
- ❌ May miss obscure tokens (acceptable for this use case)

---

### 10. Batch Processing vs. Streaming

**Decision:** Batch processing with pagination

**Why:**
- **Sufficient**: Hourly/daily runs are acceptable
- **Simple**: No streaming infrastructure needed
- **Testable**: Easy to reproduce runs
- **Cost**: No streaming service costs

**Batch approach:**
```python
# Run every hour
while True:
    swaps = fetch_swaps(last_60_minutes)
    process_and_save(swaps)
    time.sleep(3600)  # Sleep 1 hour
```

**vs. Streaming:**
```python
# Real-time processing
stream = kafka_consumer("swap_events")
for swap in stream:
    process_and_save(swap)
```

**When to use streaming:**
- **Real-time requirements**: Need sub-second latency
- **High volume**: Millions of events per hour
- **Complex event processing**: Time windows, joins, aggregations
- **Multiple consumers**: Different services need the same data

**Trade-offs:**
| Aspect | Batch | Streaming |
|--------|-------|-----------|
| **Latency** | Minutes to hours | Seconds |
| **Complexity** | Low | High |
| **Cost** | Low (run on schedule) | High (always running) |
| **Infrastructure** | None (just the script) | Kafka, Flink, etc. |
| **Debugging** | Easy (rerun batch) | Hard (replay stream) |
| **Scalability** | Vertical (bigger machine) | Horizontal (more workers) |

**Decision:** Batch is perfect for this use case (daily/hourly reports)

---

## Summary Table

| Decision | Why | Trade-off |
|----------|-----|-----------|
| State-based idempotency | Simple, reliable | Not distributed |
| Sliding window rate limiter | Respect API limits | Blocks execution |
| Exponential backoff retry | Handle transient failures | Can slow down |
| Pydantic config | Type safety, validation | Extra dependency |
| Stablecoin-aware volumes | Accurate metrics | Maintenance overhead |
| Static token decimals | Fast, no API calls | Limited to known tokens |
| Context managers | Automatic cleanup | Slight boilerplate |
| File-based state | Simple, portable | Not for distributed systems |
| Static + dynamic token mapping | Fast + extensible | Requires maintenance |
| Batch processing | Simple, sufficient | Not real-time |

---

## Future Improvements

### If Requirements Change

**More tokens needed:**
- Add on-chain decimal lookup using Web3.py
- Cache results in database

**Distributed pipeline:**
- Replace file state with PostgreSQL or Redis
- Add distributed locking (e.g., Redis locks)

**Real-time processing:**
- Switch to streaming (Kafka + Flink)
- Subscribe to blockchain events via WebSocket

**Higher CoinGecko limits:**
- Upgrade to Pro plan ($129/month for 500 req/min)
- Or implement price caching with TTL (e.g., cache for 5 minutes)

**More complex aggregations:**
- Use DuckDB or ClickHouse for analytics
- Add materialized views for common queries

**Production deployment:**
- Containerize with Docker
- Deploy on Kubernetes with CronJob
- Add monitoring (Prometheus, Grafana)
- Add alerting (PagerDuty, Slack)

---

## Lessons Learned

1. **Start simple**: File-based state works great for MVP
2. **Optimize for readability**: Junior devs can understand the code
3. **Test edge cases**: Missing prices, empty data, rate limits
4. **Document trade-offs**: Future you will thank current you
5. **Use standard libraries**: `tenacity`, `pydantic`, `pandas` are battle-tested

---

## References

- [Pydantic Documentation](https://docs.pydantic.dev/)
- [tenacity Retry Library](https://tenacity.readthedocs.io/)
- [CoinGecko API Docs](https://www.coingecko.com/en/api/documentation)
- [The Graph Query Best Practices](https://thegraph.com/docs/en/querying/querying-best-practices/)
- [Exponential Backoff Algorithm](https://aws.amazon.com/blogs/architecture/exponential-backoff-and-jitter/)
