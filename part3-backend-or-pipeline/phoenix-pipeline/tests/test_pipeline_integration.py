"""Integration tests for the Phoenix pipeline.

Tests cover:
- Transform basic functionality with fixture swaps and mock prices
- Idempotency with state-based filtering
- Rate limiting in CoinGecko client
"""

import time
from pathlib import Path
from typing import Any, Dict, List
from unittest.mock import patch

import pytest

from phoenix_pipeline.coingecko import CoinGeckoClient, RateLimiter
from phoenix_pipeline.io import filter_swaps_by_block, read_state, write_state
from phoenix_pipeline.transform import DataTransformer


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def mock_swap_events() -> List[Dict[str, Any]]:
    """
    Create fixture swap events for testing.

    Returns swaps with different pairs and blocks for comprehensive testing.
    """
    return [
        {
            "txHash": "0xabc123",
            "blockNumber": 1000,
            "timestamp": 1640000000,
            "token0": "0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2",  # WETH
            "token1": "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48",  # USDC
            "amount0": "1000000000000000000",  # 1.0 WETH (18 decimals)
            "amount1": "-2000000000",  # -2000 USDC (6 decimals)
            "sqrtPriceX96": "1234567890",
        },
        {
            "txHash": "0xdef456",
            "blockNumber": 1001,
            "timestamp": 1640000100,
            "token0": "0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2",  # WETH
            "token1": "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48",  # USDC
            "amount0": "2000000000000000000",  # 2.0 WETH
            "amount1": "-4000000000",  # -4000 USDC
            "sqrtPriceX96": "1234567890",
        },
        {
            "txHash": "0xghi789",
            "blockNumber": 1002,
            "timestamp": 1640000200,
            "token0": "0x2260fac5e5542a773aa44fbcfedf7c193bc2c599",  # WBTC
            "token1": "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48",  # USDC
            "amount0": "50000000",  # 0.5 WBTC (8 decimals)
            "amount1": "-20000000000",  # -20000 USDC
            "sqrtPriceX96": "9876543210",
        },
    ]


@pytest.fixture
def mock_prices() -> Dict[str, float]:
    """
    Create mock price data (token address -> USD price).

    Prices are per whole token (not raw units).
    """
    return {
        "0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2": 2000.0,  # WETH = $2000
        "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48": 1.0,  # USDC = $1
        "0x2260fac5e5542a773aa44fbcfedf7c193bc2c599": 40000.0,  # WBTC = $40000
    }


# =============================================================================
# Test 1: Transform Basic Functionality
# =============================================================================


def test_transform_basic(
    mock_swap_events: List[Dict[str, Any]],
    mock_prices: Dict[str, float],
) -> None:
    """
    Test basic transform functionality with fixture swaps and mock prices.

    Validates:
    - Swaps are enriched with correct USD prices
    - USD volume is calculated correctly
    - Pairs are grouped and summarized correctly
    - Aggregations (count, totalUSD, avgUSD) are accurate
    """
    # Step 1: Enrich swaps with price data
    transformer = DataTransformer()
    enriched_swaps = transformer.enrich_swaps(mock_swap_events, mock_prices)

    # Verify all swaps were enriched (no missing prices)
    assert len(enriched_swaps) == 3, "All 3 swaps should be enriched"

    # Step 2: Verify USD calculations for first swap (WETH-USDC)
    swap0 = enriched_swaps[0]
    assert swap0.priceUSD0 == 2000.0, "WETH price should be $2000"
    assert swap0.priceUSD1 == 1.0, "USDC price should be $1"

    # Volume calculation: USDC is stablecoin, so use USDC side only
    # |amount1| = |-2000000000| / 10^6 = 2000 USDC = $2000
    expected_volume_0 = 2000.0
    assert abs(swap0.usdVolume - expected_volume_0) < 0.01, \
        f"Swap 0 volume should be ~${expected_volume_0} (got ${swap0.usdVolume})"

    # Step 3: Verify second swap (WETH-USDC)
    swap1 = enriched_swaps[1]
    # |amount1| = |-4000000000| / 10^6 = 4000 USDC = $4000
    expected_volume_1 = 4000.0
    assert abs(swap1.usdVolume - expected_volume_1) < 0.01, \
        f"Swap 1 volume should be ~${expected_volume_1}"

    # Step 4: Verify third swap (WBTC-USDC)
    swap2 = enriched_swaps[2]
    assert swap2.priceUSD0 == 40000.0, "WBTC price should be $40000"
    # |amount1| = |-20000000000| / 10^6 = 20000 USDC = $20000
    expected_volume_2 = 20000.0
    assert abs(swap2.usdVolume - expected_volume_2) < 0.01, \
        f"Swap 2 volume should be ~${expected_volume_2}"

    # Step 5: Summarize by pair
    summary_df = transformer.summarize(enriched_swaps, top_n=None)

    # Verify summary structure
    assert len(summary_df) == 2, "Should have 2 unique pairs (WETH-USDC and WBTC-USDC)"
    assert list(summary_df.columns) == ["pair", "count", "totalUSD", "avgUSD"]

    # Verify WETH-USDC pair (2 swaps)
    weth_usdc_pair = "0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2-0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48"
    weth_usdc_row = summary_df[summary_df["pair"] == weth_usdc_pair]
    assert len(weth_usdc_row) == 1, "WETH-USDC pair should exist"
    assert weth_usdc_row["count"].iloc[0] == 2, "WETH-USDC should have 2 swaps"
    assert abs(weth_usdc_row["totalUSD"].iloc[0] - 6000.0) < 0.01, \
        "WETH-USDC total should be $6000 (2000 + 4000)"
    assert abs(weth_usdc_row["avgUSD"].iloc[0] - 3000.0) < 0.01, \
        "WETH-USDC average should be $3000"

    # Verify WBTC-USDC pair (1 swap)
    wbtc_usdc_pair = "0x2260fac5e5542a773aa44fbcfedf7c193bc2c599-0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48"
    wbtc_usdc_row = summary_df[summary_df["pair"] == wbtc_usdc_pair]
    assert len(wbtc_usdc_row) == 1, "WBTC-USDC pair should exist"
    assert wbtc_usdc_row["count"].iloc[0] == 1, "WBTC-USDC should have 1 swap"
    assert abs(wbtc_usdc_row["totalUSD"].iloc[0] - 20000.0) < 0.01, \
        "WBTC-USDC total should be $20000"
    assert abs(wbtc_usdc_row["avgUSD"].iloc[0] - 20000.0) < 0.01, \
        "WBTC-USDC average should be $20000"

    # Verify sorting (by totalUSD descending)
    assert summary_df["pair"].iloc[0] == wbtc_usdc_pair, \
        "WBTC-USDC should be first (highest volume: $20000)"
    assert summary_df["pair"].iloc[1] == weth_usdc_pair, \
        "WETH-USDC should be second (lower volume: $6000)"


# =============================================================================
# Test 2: Idempotency
# =============================================================================


def test_idempotency(
    tmp_path: Path,
    mock_swap_events: List[Dict[str, Any]],
) -> None:
    """
    Test idempotency by ensuring swaps at or before last_processed_block are skipped.

    Validates:
    - State is read and written correctly
    - filter_swaps_by_block filters correctly based on state
    - Older swaps are excluded from processing
    - Only new swaps (blockNumber > last_processed_block) are returned
    """
    # Setup: Use temporary state file
    state_file = tmp_path / "state.json"

    # Step 1: Initialize state with last_processed_block = 1000
    write_state(path=state_file, block=1000)

    # Verify state was written
    state = read_state(path=state_file)
    assert state["last_processed_block"] == 1000, "State should have block 1000"

    # Step 2: Filter swaps (blocks: 1000, 1001, 1002)
    filtered_swaps = filter_swaps_by_block(mock_swap_events, last_processed_block=1000)

    # Verify only swaps with blockNumber > 1000 are included
    assert len(filtered_swaps) == 2, "Should have 2 swaps (blocks 1001, 1002)"
    assert filtered_swaps[0]["blockNumber"] == 1001, "First swap should be block 1001"
    assert filtered_swaps[1]["blockNumber"] == 1002, "Second swap should be block 1002"

    # Step 3: Verify block 1000 swap was excluded
    assert all(s["blockNumber"] > 1000 for s in filtered_swaps), \
        "All filtered swaps should have blockNumber > 1000"

    # Step 4: Test with higher last_processed_block (1001)
    write_state(path=state_file, block=1001)
    filtered_swaps_2 = filter_swaps_by_block(mock_swap_events, last_processed_block=1001)

    assert len(filtered_swaps_2) == 1, "Should have 1 swap (block 1002)"
    assert filtered_swaps_2[0]["blockNumber"] == 1002, "Only block 1002 should remain"

    # Step 5: Test with last_processed_block = 1002 (all swaps should be filtered)
    write_state(path=state_file, block=1002)
    filtered_swaps_3 = filter_swaps_by_block(mock_swap_events, last_processed_block=1002)

    assert len(filtered_swaps_3) == 0, "No swaps should remain (all at or before block 1002)"

    # Step 6: Verify state file metadata
    final_state = read_state(path=state_file)
    assert final_state["last_processed_block"] == 1002
    assert "last_updated" in final_state, "State should have last_updated timestamp"


# =============================================================================
# Test 3: Rate Limiting
# =============================================================================


def test_rate_limit() -> None:
    """
    Test CoinGecko rate limiter with many price requests.

    Validates:
    - Rate limiter blocks/delays requests when limit is reached
    - Requests are tracked correctly within the sliding window
    - Stats (requests_in_window, remaining) are accurate
    - Limiter respects max_requests constraint
    """
    # Step 1: Create a rate limiter (max 5 requests per 2 seconds)
    limiter = RateLimiter(max_requests=5, window_seconds=2.0)

    # Step 2: Make 5 requests quickly (should all succeed without blocking)
    start_time = time.time()
    for i in range(5):
        limiter.acquire()

    elapsed = time.time() - start_time
    assert elapsed < 0.5, "First 5 requests should be fast (no blocking)"

    # Verify stats
    stats = limiter.get_stats()
    assert stats["requests_in_window"] == 5, "Should have 5 requests in window"
    assert stats["remaining"] == 0, "Should have 0 remaining slots"

    # Step 3: Make 6th request (should block until window clears)
    start_6th = time.time()
    limiter.acquire()
    elapsed_6th = time.time() - start_6th

    # Should have waited at least ~2 seconds (until oldest request expires)
    assert elapsed_6th >= 1.8, \
        f"6th request should block for ~2s (blocked for {elapsed_6th:.2f}s)"

    # Step 4: Verify window slides correctly
    # After blocking, we should have 5 requests again (oldest one expired)
    stats_after = limiter.get_stats()
    assert stats_after["requests_in_window"] <= 5, \
        "Should still respect max 5 requests in window"

    # Step 5: Test rapid fire requests (10 requests)
    limiter2 = RateLimiter(max_requests=3, window_seconds=1.0)

    rapid_start = time.time()
    for i in range(10):
        limiter2.acquire()
    rapid_elapsed = time.time() - rapid_start

    # 10 requests with max 3/second should take at least ~3 seconds
    # (First 3 are immediate, then wait 1s, next 3, wait 1s, next 3, wait 1s, last 1)
    assert rapid_elapsed >= 3.0, \
        f"10 requests at 3/sec should take >=3s (took {rapid_elapsed:.2f}s)"

    # Step 6: Verify stats are accurate
    final_stats = limiter2.get_stats()
    assert final_stats["max_requests"] == 3
    assert final_stats["window_seconds"] == 1.0
    assert final_stats["requests_in_window"] <= 3, "Should never exceed max requests"


def test_rate_limit_integration_with_coingecko() -> None:
    """
    Integration test: Verify CoinGeckoClient uses rate limiter correctly.

    This test uses mocks to avoid real API calls.
    """
    # Step 1: Create client with strict rate limit (2 requests per 1 second)
    client = CoinGeckoClient(max_requests_per_min=2)

    # Mock the HTTP client to avoid real API calls
    with patch.object(client.client, "get") as mock_get:
        # Mock successful responses
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {
            "0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2": {"usd": 2000.0},
        }

        # Step 2: Make 2 requests (should be fast)
        start = time.time()
        tokens = ["0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2"] * 2

        for token in tokens:
            client.fetch_prices([token])

        elapsed = time.time() - start
        assert elapsed < 1.0, "First 2 requests should be fast"

        # Step 3: Verify rate limiter stats
        stats = client.get_cache_stats()
        # Note: fetch_prices may cache, so check limiter directly
        limiter_stats = client.rate_limiter.get_stats()

        # Should have made at most 2 requests (or fewer if cached)
        assert limiter_stats["requests_in_window"] <= 2, \
            "Should respect rate limit of 2 requests"


# =============================================================================
# Additional Edge Case Tests
# =============================================================================


def test_transform_with_missing_prices(
    mock_swap_events: List[Dict[str, Any]],
) -> None:
    """
    Test transform behavior when some prices are missing.

    Swaps with missing prices should be skipped with warnings.
    """
    # Provide prices for only WETH (not USDC or WBTC)
    partial_prices = {
        "0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2": 2000.0,  # WETH only
    }

    transformer = DataTransformer()
    enriched = transformer.enrich_swaps(mock_swap_events, partial_prices)

    # All swaps need both token prices, so all should be skipped
    assert len(enriched) == 0, "All swaps should be skipped (missing USDC/WBTC prices)"


def test_idempotency_with_empty_swaps(tmp_path: Path) -> None:
    """
    Test filter_swaps_by_block with empty swap list.
    """
    filtered = filter_swaps_by_block([], last_processed_block=1000)
    assert len(filtered) == 0, "Empty list should return empty list"


def test_rate_limiter_stats_accuracy() -> None:
    """
    Test rate limiter stats are updated correctly.
    """
    limiter = RateLimiter(max_requests=10, window_seconds=5.0)

    # Make 3 requests
    for _ in range(3):
        limiter.acquire()

    stats = limiter.get_stats()
    assert stats["requests_in_window"] == 3
    assert stats["max_requests"] == 10
    assert stats["remaining"] == 7
    assert stats["window_seconds"] == 5.0

    # Wait for window to clear
    time.sleep(5.1)

    # Stats should show 0 requests (all expired)
    stats_after = limiter.get_stats()
    assert stats_after["requests_in_window"] == 0, \
        "All requests should have expired after window"
    assert stats_after["remaining"] == 10
