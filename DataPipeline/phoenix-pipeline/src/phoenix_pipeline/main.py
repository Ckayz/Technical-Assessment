"""Main orchestrator for the Phoenix pipeline."""

import logging
import sys
from typing import Optional

import pandas as pd

from phoenix_pipeline.coingecko import CoinGeckoClient
from phoenix_pipeline.config import settings
from phoenix_pipeline.io import DataWriter, StateManager
from phoenix_pipeline.subgraph import SubgraphClient
from phoenix_pipeline.transform import DataTransformer

# Configure logging
logging.basicConfig(
    level=settings.log_level,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


class PhoenixPipeline:
    """Main pipeline orchestrator."""

    def __init__(self) -> None:
        """Initialize pipeline components."""
        self.state_manager = StateManager()
        self.data_writer = DataWriter()
        self.transformer = DataTransformer()
        logger.info("Phoenix pipeline initialized")

    def run(
        self,
        start_block: Optional[int] = None,
        end_block: Optional[int] = None,
        resume: bool = True,
    ) -> None:
        """
        Run the complete pipeline.

        Args:
            start_block: Starting block number (None to use state/config)
            end_block: Ending block number (None for latest)
            resume: Whether to resume from last processed block
        """
        logger.info("=" * 80)
        logger.info("Starting Phoenix Pipeline")
        logger.info("=" * 80)

        try:
            # Determine starting block
            if resume and start_block is None:
                start_block = self.state_manager.get_last_processed_block()
                logger.info(f"Resuming from block {start_block}")
            elif start_block is None:
                start_block = settings.start_block
                logger.info(f"Starting from configured block {start_block}")

            # Fetch data from subgraph
            swaps_df = self._fetch_swaps(start_block, end_block)

            if swaps_df.empty:
                logger.info("No swaps to process")
                return

            # Transform and validate data
            swaps_df = self._transform_data(swaps_df)

            # Enrich with price data
            swaps_df = self._enrich_with_prices(swaps_df)

            # Calculate aggregations
            agg_df = self._calculate_aggregations(swaps_df)

            # Write output
            self._write_output(swaps_df, agg_df)

            # Update state
            max_block = int(swaps_df["blockNumber"].max())
            self.state_manager.update_last_processed_block(max_block)

            logger.info("=" * 80)
            logger.info(f"Pipeline completed successfully. Processed up to block {max_block}")
            logger.info("=" * 80)

        except Exception as e:
            logger.error(f"Pipeline failed with error: {e}", exc_info=True)
            raise

    def _fetch_swaps(
        self,
        start_block: int,
        end_block: Optional[int],
    ) -> pd.DataFrame:
        """
        Fetch swaps from the subgraph.

        Args:
            start_block: Starting block number
            end_block: Ending block number

        Returns:
            DataFrame with swap data
        """
        logger.info(f"Fetching swaps from block {start_block}")

        all_swaps = []
        skip = 0
        batch_size = settings.batch_size

        with SubgraphClient() as client:
            # Get latest block if end_block not specified
            if end_block is None:
                end_block = client.get_latest_block()
                logger.info(f"Using latest block: {end_block}")

            while True:
                swaps = client.get_swaps(
                    start_block=start_block,
                    end_block=end_block,
                    first=batch_size,
                    skip=skip,
                )

                if not swaps:
                    break

                all_swaps.extend(swaps)
                skip += batch_size

                logger.info(f"Fetched {len(all_swaps)} total swaps so far...")

                # Stop if we got fewer results than batch size
                if len(swaps) < batch_size:
                    break

        df = self.transformer.normalize_swaps(all_swaps)
        logger.info(f"Fetched total of {len(df)} swaps")
        return df

    def _transform_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Transform and validate swap data.

        Args:
            df: Raw swap data

        Returns:
            Transformed and validated DataFrame
        """
        logger.info("Transforming and validating data")

        # Deduplicate
        df = self.transformer.deduplicate_swaps(df)

        # Validate
        df = self.transformer.validate_data(df)

        # Detect outliers
        df = self.transformer.detect_outliers(df)

        return df

    def _enrich_with_prices(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Enrich swap data with current price information.

        Args:
            df: Swap data

        Returns:
            Enriched DataFrame
        """
        logger.info("Enriching data with price information")

        try:
            # Extract unique token addresses (simplified example)
            # In a real implementation, you'd need a mapping from contract addresses to CoinGecko IDs
            unique_tokens = df["tokenIn"].unique()[:10]  # Limit for demo

            # For demo purposes, using common token IDs
            # In production, you'd need proper address -> coingecko ID mapping
            demo_token_ids = ["bitcoin", "ethereum", "usd-coin"]

            with CoinGeckoClient() as client:
                prices = client.get_price(demo_token_ids)
                df = self.transformer.enrich_with_prices(df, prices)

        except Exception as e:
            logger.warning(f"Failed to enrich with prices: {e}")
            # Continue without price enrichment

        return df

    def _calculate_aggregations(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate aggregated metrics.

        Args:
            df: Swap data

        Returns:
            DataFrame with aggregated metrics
        """
        logger.info("Calculating aggregations")

        agg_df = self.transformer.calculate_aggregations(df)
        return agg_df

    def _write_output(
        self,
        swaps_df: pd.DataFrame,
        agg_df: pd.DataFrame,
    ) -> None:
        """
        Write output files.

        Args:
            swaps_df: Detailed swap data
            agg_df: Aggregated metrics
        """
        logger.info("Writing output files")

        timestamp = pd.Timestamp.now().strftime("%Y%m%d_%H%M%S")

        # Write detailed swaps
        swaps_file = self.data_writer.write(
            swaps_df,
            f"swaps_{timestamp}",
        )
        logger.info(f"Wrote swaps to {swaps_file}")

        # Write aggregations
        if not agg_df.empty:
            agg_file = self.data_writer.write(
                agg_df,
                f"aggregations_{timestamp}",
            )
            logger.info(f"Wrote aggregations to {agg_file}")


def main() -> int:
    """
    Main entry point for the pipeline.

    Returns:
        Exit code (0 for success, 1 for failure)
    """
    try:
        pipeline = PhoenixPipeline()
        pipeline.run()
        return 0
    except Exception as e:
        logger.error(f"Pipeline execution failed: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
