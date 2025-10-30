"""Demo script with mock data - No API key needed!"""

import logging
from datetime import datetime
from phoenix_pipeline.config import SwapEvent, EnrichedSwap, SummaryRow
from phoenix_pipeline.transform import DataTransformer
from phoenix_pipeline.io import DataWriter
import pandas as pd

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

def create_mock_swaps():
    """Create mock swap data for testing."""
    now = int(datetime.now().timestamp())

    mock_swaps = [
        SwapEvent(
            txHash=f"0x{'a' * 63}{i}",
            blockNumber=18000000 + i,
            timestamp=now - (3600 - i * 60),  # Last hour
            token0="0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2",  # WETH
            token1="0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",  # USDC
            amount0=str(1000000000000000000 * (i + 1)),  # 1-60 ETH
            amount1=str(-2000000000 * (i + 1)),  # Negative for swap out
            sqrtPriceX96="79228162514264337593543950336",
        )
        for i in range(60)
    ]

    return mock_swaps

def main():
    """Run pipeline with mock data."""
    logger.info("=" * 80)
    logger.info("Phoenix Pipeline Demo - Using Mock Data")
    logger.info("=" * 80)

    # Create mock swaps
    logger.info("Creating mock swap data...")
    swaps = create_mock_swaps()
    logger.info(f"Created {len(swaps)} mock swaps")

    # Convert to dicts
    swaps_dicts = [swap.model_dump() for swap in swaps]

    # Transform data
    logger.info("Transforming data...")
    transformer = DataTransformer()
    df = transformer.normalize_swaps(swaps_dicts)
    logger.info(f"Normalized {len(df)} swaps")

    # Validate
    df = transformer.validate_data(df)
    df = transformer.deduplicate_swaps(df)
    logger.info(f"After validation: {len(df)} swaps")

    # Show sample
    logger.info("\nSample data:")
    logger.info(f"Columns: {list(df.columns)}")
    logger.info(f"\nFirst swap:")
    logger.info(f"  TX: {df.iloc[0]['transaction']}")
    logger.info(f"  Block: {df.iloc[0]['blockNumber']}")
    logger.info(f"  Token0: {df.iloc[0]['token0']}")
    logger.info(f"  Token1: {df.iloc[0]['token1']}")
    logger.info(f"  Amount0: {df.iloc[0]['amount0']}")

    # Calculate aggregations
    logger.info("\nCalculating aggregations...")
    agg_df = transformer.calculate_aggregations(df)
    logger.info(f"Aggregated to {len(agg_df)} rows")

    # Write output
    logger.info("\nWriting output files...")
    writer = DataWriter()
    timestamp = pd.Timestamp.now().strftime("%Y%m%d_%H%M%S")

    swaps_file = writer.write(df, f"demo_swaps_{timestamp}")
    logger.info(f"✓ Wrote swaps to: {swaps_file}")

    if not agg_df.empty:
        agg_file = writer.write(agg_df, f"demo_aggregations_{timestamp}")
        logger.info(f"✓ Wrote aggregations to: {agg_file}")

    logger.info("\n" + "=" * 80)
    logger.info("Demo completed successfully!")
    logger.info("=" * 80)
    logger.info("\nNext steps:")
    logger.info("1. Check the output/ directory for the generated files")
    logger.info("2. Get a real API key to fetch live Uniswap data:")
    logger.info("   - See API_KEY_REQUIRED.md")
    logger.info("   - See SUBGRAPH_SETUP.md")
    logger.info("3. Update .env with your API key")
    logger.info("4. Run: python -m phoenix_pipeline.main")

if __name__ == "__main__":
    main()
