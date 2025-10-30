"""Test script for CoinGecko client implementation."""

import logging
from phoenix_pipeline.coingecko import CoinGeckoClient

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def main():
    """Test CoinGecko client features."""
    logger.info("=" * 80)
    logger.info("Testing CoinGecko Client Implementation")
    logger.info("=" * 80)

    with CoinGeckoClient() as client:
        # Test 1: Fetch prices by symbol
        logger.info("\n--- Test 1: Fetch by Symbol ---")
        symbols = ["eth", "wbtc", "usdc"]
        prices = client.fetch_prices(symbols)
        for symbol, price in prices.items():
            logger.info(f"  {symbol.upper()}: ${price:.2f}")

        # Test 2: Fetch prices by address
        logger.info("\n--- Test 2: Fetch by Address ---")
        addresses = [
            "0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2",  # WETH
            "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48",  # USDC
        ]
        prices = client.fetch_prices(addresses)
        for addr, price in prices.items():
            logger.info(f"  {addr[:10]}...: ${price:.2f}")

        # Test 3: Test caching
        logger.info("\n--- Test 3: Test Caching (2nd fetch should be instant) ---")
        prices = client.fetch_prices(["eth", "wbtc"])
        logger.info(f"  ETH: ${prices['eth']:.2f} (from cache)")
        logger.info(f"  WBTC: ${prices['wbtc']:.2f} (from cache)")

        # Test 4: Mixed addresses and symbols
        logger.info("\n--- Test 4: Mixed Addresses and Symbols ---")
        mixed = [
            "eth",
            "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48",  # USDC
            "wbtc",
        ]
        prices = client.fetch_prices(mixed)
        for identifier, price in prices.items():
            logger.info(f"  {identifier}: ${price:.2f}")

        # Show stats
        logger.info("\n--- Cache and Rate Limiter Stats ---")
        stats = client.get_cache_stats()
        logger.info(f"  Cached tokens: {stats['cached_tokens']}")
        logger.info(f"  Rate limiter: {stats['rate_limiter']}")

    logger.info("\n" + "=" * 80)
    logger.info("All tests completed successfully!")
    logger.info("=" * 80)


if __name__ == "__main__":
    main()
