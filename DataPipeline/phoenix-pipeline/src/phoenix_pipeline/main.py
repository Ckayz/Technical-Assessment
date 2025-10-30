"""Main orchestrator for the Phoenix pipeline."""

import logging
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

import pandas as pd

from phoenix_pipeline.coingecko import CoinGeckoClient
from phoenix_pipeline.config import settings
from phoenix_pipeline.io import filter_swaps_by_block, read_state, write_csv, write_json, write_state
from phoenix_pipeline.subgraph import SubgraphClient, build_query
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
        self.transformer = DataTransformer()
        self.stats: Dict[str, Any] = {}
        logger.info("Phoenix pipeline initialized")

    def run(self) -> int:
        """
        Run the complete pipeline.

        Returns:
            Exit code (0 for success, 1 for failure)

        Workflow:
            1. Load config and state
            2. Compute time window and build GraphQL query
            3. Fetch swaps from subgraph
            4. Exit gracefully if no swaps
            5. Determine latest block and filter by state
            6. Collect unique tokens and fetch prices
            7. Enrich swaps and create summary
            8. Write outputs (swaps.json, summary.csv)
            9. Update state with latest block
            10. Print run statistics
        """
        start_time = time.time()

        logger.info("=" * 80)
        logger.info("Starting Phoenix Pipeline")
        logger.info("=" * 80)

        try:
            # 1. Load config and state
            logger.info("\n[1/10] Loading configuration and state...")
            state = read_state()
            last_processed_block = state.get("last_processed_block", 0)
            logger.info(f"  Config: window={settings.window_minutes}min, batch_size={settings.batch_size}")
            logger.info(f"  State: last_processed_block={last_processed_block}")

            # 2. Compute window and build query
            logger.info("\n[2/10] Building GraphQL query...")
            query = build_query(settings.window_minutes)
            logger.info(f"  Query: Fetching swaps from last {settings.window_minutes} minutes")

            # 3. Fetch swaps
            logger.info("\n[3/10] Fetching swaps from subgraph...")
            swaps = self._fetch_swaps()

            if not swaps:
                logger.info("\n✓ No swaps found in time window - exiting gracefully")
                self._print_stats(time.time() - start_time, swaps_fetched=0, swaps_processed=0)
                return 0

            logger.info(f"  Fetched: {len(swaps)} swaps")
            self.stats["swaps_fetched"] = len(swaps)

            # 4. Determine latest block and filter by state
            logger.info("\n[4/10] Filtering swaps by state...")
            swaps_dicts = [swap.model_dump() for swap in swaps]

            # Find latest block
            blocks = [s.get("blockNumber", 0) for s in swaps_dicts if "blockNumber" in s]
            latest_block = max(blocks) if blocks else 0
            logger.info(f"  Latest block in results: {latest_block}")

            # Filter by last processed block
            filtered_swaps = filter_swaps_by_block(swaps_dicts, last_processed_block)
            self.stats["swaps_filtered"] = len(swaps_dicts) - len(filtered_swaps)
            self.stats["swaps_new"] = len(filtered_swaps)

            if not filtered_swaps:
                logger.info("\n✓ No new swaps to process (all already processed) - exiting gracefully")
                self._print_stats(time.time() - start_time, swaps_fetched=len(swaps), swaps_processed=0)
                return 0

            logger.info(f"  New swaps to process: {len(filtered_swaps)}")

            # 5. Collect token addresses
            logger.info("\n[5/10] Collecting unique tokens...")
            tokens = self._collect_tokens(filtered_swaps)
            logger.info(f"  Unique tokens: {len(tokens)}")
            self.stats["unique_tokens"] = len(tokens)

            # 6. Fetch prices
            logger.info("\n[6/10] Fetching prices from CoinGecko...")
            prices = self._fetch_prices(tokens)
            logger.info(f"  Prices fetched: {len(prices)}/{len(tokens)} tokens")
            self.stats["prices_fetched"] = len(prices)
            self.stats["prices_missing"] = len(tokens) - len(prices)

            # 7. Enrich and summarize
            logger.info("\n[7/10] Enriching swaps with price data...")
            enriched = self.transformer.enrich_swaps(filtered_swaps, prices)
            logger.info(f"  Enriched: {len(enriched)} swaps")
            self.stats["swaps_enriched"] = len(enriched)
            self.stats["swaps_skipped"] = len(filtered_swaps) - len(enriched)

            logger.info("\n[8/10] Creating summary...")
            summary_df = self.transformer.summarize(enriched, top_n=None)
            logger.info(f"  Summary: {len(summary_df)} trading pairs")
            self.stats["pairs_summarized"] = len(summary_df)

            # 8. Write outputs
            logger.info("\n[9/10] Writing output files...")
            self._write_outputs(enriched, summary_df)

            # 9. Update state
            logger.info("\n[10/10] Updating state...")
            if latest_block > 0:
                write_state(block=latest_block)
                logger.info(f"  State updated: last_processed_block={latest_block}")
            else:
                logger.warning("  No valid block number found, state not updated")

            # 10. Print stats
            elapsed_time = time.time() - start_time
            logger.info("\n" + "=" * 80)
            logger.info("Pipeline Completed Successfully!")
            logger.info("=" * 80)
            self._print_stats(elapsed_time, swaps_fetched=len(swaps), swaps_processed=len(enriched))

            return 0

        except KeyboardInterrupt:
            logger.warning("\n\nPipeline interrupted by user")
            return 130
        except Exception as e:
            logger.error(f"\n\nPipeline failed with error: {e}", exc_info=True)
            return 1

    def _fetch_swaps(self) -> List[Any]:
        """
        Fetch swaps from the subgraph.

        Returns:
            List of SwapEvent objects
        """
        with SubgraphClient() as client:
            swaps = client.get_recent_swaps(
                window_minutes=settings.window_minutes,
                batch_size=settings.batch_size,
            )
        return swaps

    def _collect_tokens(self, swaps: List[Dict[str, Any]]) -> Set[str]:
        """
        Collect unique token addresses from swaps.

        Args:
            swaps: List of swap dictionaries

        Returns:
            Set of unique token addresses
        """
        tokens: Set[str] = set()
        for swap in swaps:
            token0 = swap.get("token0")
            token1 = swap.get("token1")
            if token0:
                tokens.add(token0)
            if token1:
                tokens.add(token1)
        return tokens

    def _fetch_prices(self, tokens: Set[str]) -> Dict[str, float]:
        """
        Fetch USD prices for all tokens.

        Args:
            tokens: Set of token addresses

        Returns:
            Dictionary mapping token address -> USD price
        """
        if not tokens:
            logger.warning("No tokens to fetch prices for")
            return {}

        with CoinGeckoClient() as client:
            prices = client.fetch_prices(list(tokens))

            # Log cache stats
            stats = client.get_cache_stats()
            logger.info(f"  CoinGecko stats: {stats}")
            self.stats["coingecko_cached"] = stats["cached_tokens"]
            self.stats["coingecko_requests"] = stats["rate_limiter"]["requests_in_window"]

        return prices

    def _write_outputs(self, enriched: List[Any], summary_df: pd.DataFrame) -> None:
        """
        Write output files.

        Args:
            enriched: List of EnrichedSwap objects
            summary_df: Summary DataFrame
        """
        # Ensure output directory exists
        output_dir = settings.output_dir
        output_dir.mkdir(parents=True, exist_ok=True)

        # Write swaps as JSON
        swaps_path = output_dir / "swaps.json"
        swaps_data = [swap.model_dump() for swap in enriched]
        write_json(swaps_path, swaps_data)
        logger.info(f"  ✓ Wrote {len(swaps_data)} swaps to: {swaps_path}")

        # Write summary as CSV
        summary_path = output_dir / "summary.csv"
        write_csv(summary_path, summary_df)
        logger.info(f"  ✓ Wrote {len(summary_df)} pairs to: {summary_path}")

        self.stats["output_swaps_file"] = str(swaps_path)
        self.stats["output_summary_file"] = str(summary_path)

    def _print_stats(self, elapsed_time: float, swaps_fetched: int, swaps_processed: int) -> None:
        """
        Print run statistics.

        Args:
            elapsed_time: Total elapsed time in seconds
            swaps_fetched: Number of swaps fetched
            swaps_processed: Number of swaps processed
        """
        logger.info("")
        logger.info("Run Statistics:")
        logger.info("-" * 80)
        logger.info(f"  Execution Time:        {elapsed_time:.2f} seconds")
        logger.info(f"  Swaps Fetched:         {swaps_fetched}")
        logger.info(f"  Swaps Filtered (old):  {self.stats.get('swaps_filtered', 0)}")
        logger.info(f"  Swaps New:             {self.stats.get('swaps_new', 0)}")
        logger.info(f"  Swaps Enriched:        {swaps_processed}")
        logger.info(f"  Swaps Skipped:         {self.stats.get('swaps_skipped', 0)} (missing prices)")
        logger.info(f"  Unique Tokens:         {self.stats.get('unique_tokens', 0)}")
        logger.info(f"  Prices Fetched:        {self.stats.get('prices_fetched', 0)}")
        logger.info(f"  Prices Missing:        {self.stats.get('prices_missing', 0)}")
        logger.info(f"  Trading Pairs:         {self.stats.get('pairs_summarized', 0)}")
        logger.info(f"  CoinGecko Cached:      {self.stats.get('coingecko_cached', 0)}")
        logger.info(f"  CoinGecko API Calls:   {self.stats.get('coingecko_requests', 0)}")

        if swaps_processed > 0:
            logger.info("")
            logger.info("Output Files:")
            logger.info(f"  Swaps:   {self.stats.get('output_swaps_file', 'N/A')}")
            logger.info(f"  Summary: {self.stats.get('output_summary_file', 'N/A')}")

        logger.info("-" * 80)


def main() -> int:
    """
    Main entry point for the pipeline.

    Returns:
        Exit code (0 for success, 1 for failure)
    """
    try:
        pipeline = PhoenixPipeline()
        return pipeline.run()
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
