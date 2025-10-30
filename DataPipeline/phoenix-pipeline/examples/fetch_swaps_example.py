"""Example script demonstrating how to fetch swaps from Uniswap v3 subgraph."""

import logging
from phoenix_pipeline.subgraph import SubgraphClient, build_query, fetch_swaps, compute_since_timestamp
from phoenix_pipeline.config import settings
import httpx

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)


def example_basic_usage() -> None:
    """Example 1: Basic usage with SubgraphClient."""
    logger.info("=" * 60)
    logger.info("Example 1: Basic usage with SubgraphClient")
    logger.info("=" * 60)

    with SubgraphClient() as client:
        # Fetch swaps from the last 60 minutes
        swaps = client.get_recent_swaps(window_minutes=60)

        logger.info(f"Fetched {len(swaps)} swaps")

        # Display first few swaps
        for i, swap in enumerate(swaps[:3]):
            logger.info(f"\nSwap {i + 1}:")
            logger.info(f"  TX Hash: {swap.txHash}")
            logger.info(f"  Timestamp: {swap.timestamp}")
            logger.info(f"  Token0: {swap.token0}")
            logger.info(f"  Token1: {swap.token1}")
            logger.info(f"  Amount0: {swap.amount0}")
            logger.info(f"  Amount1: {swap.amount1}")


def example_custom_parameters() -> None:
    """Example 2: Using custom parameters."""
    logger.info("\n" + "=" * 60)
    logger.info("Example 2: Custom parameters (15 min window, max 50 results)")
    logger.info("=" * 60)

    with SubgraphClient() as client:
        swaps = client.get_recent_swaps(
            window_minutes=15,
            batch_size=50,
            max_results=50,
        )

        logger.info(f"Fetched {len(swaps)} swaps from last 15 minutes")


def example_direct_functions() -> None:
    """Example 3: Using the direct functions for more control."""
    logger.info("\n" + "=" * 60)
    logger.info("Example 3: Using direct functions")
    logger.info("=" * 60)

    # Build query
    query = build_query(window_minutes=30)
    logger.info(f"Built query for 30-minute window")

    # Compute timestamp
    since = compute_since_timestamp(30)
    logger.info(f"Since timestamp: {since}")

    # Fetch with custom client
    with httpx.Client(timeout=30) as http_client:
        swaps = fetch_swaps(
            client=http_client,
            url=str(settings.subgraph_url),
            query=query,
            batch_size=100,
            max_results=200,
        )

        logger.info(f"Fetched {len(swaps)} swaps")

        if swaps:
            logger.info(f"\nFirst swap:")
            logger.info(f"  TX: {swaps[0].txHash}")
            logger.info(f"  Tokens: {swaps[0].token0} / {swaps[0].token1}")


def example_error_handling() -> None:
    """Example 4: Error handling."""
    logger.info("\n" + "=" * 60)
    logger.info("Example 4: Error handling")
    logger.info("=" * 60)

    try:
        with SubgraphClient() as client:
            swaps = client.get_recent_swaps(window_minutes=5)
            logger.info(f"Successfully fetched {len(swaps)} swaps")

    except httpx.HTTPError as e:
        logger.error(f"HTTP error occurred: {e}")

    except ValueError as e:
        logger.error(f"Validation error: {e}")

    except Exception as e:
        logger.error(f"Unexpected error: {e}")


if __name__ == "__main__":
    logger.info("Starting Uniswap v3 Subgraph Examples")
    logger.info(f"Using subgraph URL: {settings.subgraph_url}")

    # Run examples
    try:
        example_basic_usage()
        example_custom_parameters()
        example_direct_functions()
        example_error_handling()

        logger.info("\n" + "=" * 60)
        logger.info("All examples completed successfully!")
        logger.info("=" * 60)

    except Exception as e:
        logger.error(f"Example failed: {e}", exc_info=True)
