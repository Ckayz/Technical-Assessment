"""Quick test script to verify main.py works."""

import logging
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)

try:
    logger.info("Testing imports...")
    from phoenix_pipeline.config import settings, SwapEvent
    from phoenix_pipeline.subgraph import SubgraphClient, build_query, compute_since_timestamp
    from phoenix_pipeline.io import StateManager
    from phoenix_pipeline.transform import DataTransformer

    logger.info("✓ All imports successful")

    # Test config
    logger.info(f"\nConfig loaded:")
    logger.info(f"  Subgraph URL: {settings.subgraph_url}")
    logger.info(f"  Window minutes: {settings.window_minutes}")
    logger.info(f"  State path: {settings.state_path}")
    logger.info(f"  Output dir: {settings.output_dir}")

    # Test timestamp helper
    logger.info("\nTesting compute_since_timestamp...")
    timestamp = compute_since_timestamp(60)
    logger.info(f"✓ Timestamp for 60 min ago: {timestamp}")

    # Test query builder
    logger.info("\nTesting build_query...")
    query = build_query(60)
    logger.info(f"✓ Query built ({len(query)} chars)")

    # Test SwapEvent model
    logger.info("\nTesting SwapEvent model...")
    swap = SwapEvent(
        txHash="0x123",
        blockNumber=12345,
        timestamp=1640000000,
        token0="0xabc",
        token1="0xdef",
        amount0="1000",
        amount1="2000",
        sqrtPriceX96="79228162514264337593543950336",
    )
    logger.info(f"✓ SwapEvent created: {swap.txHash}")

    # Test StateManager
    logger.info("\nTesting StateManager...")
    state_manager = StateManager()
    logger.info(f"✓ StateManager initialized with: {state_manager.state_file}")

    # Test DataTransformer
    logger.info("\nTesting DataTransformer...")
    transformer = DataTransformer()
    swaps_dicts = [swap.model_dump()]
    df = transformer.normalize_swaps(swaps_dicts)
    logger.info(f"✓ Normalized {len(df)} swaps")
    logger.info(f"  Columns: {list(df.columns)}")

    logger.info("\n" + "=" * 60)
    logger.info("✓ All basic tests passed!")
    logger.info("=" * 60)

    logger.info("\nNOTE: To test with real data, run:")
    logger.info("  python -m phoenix_pipeline.main")
    logger.info("\nThis will fetch real swaps from Uniswap v3 subgraph.")

except Exception as e:
    logger.error(f"\n✗ Test failed: {e}", exc_info=True)
    sys.exit(1)
