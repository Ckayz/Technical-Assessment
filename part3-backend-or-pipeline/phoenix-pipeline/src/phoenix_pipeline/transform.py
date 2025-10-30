"""Data transformation and enrichment logic."""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

import pandas as pd

from phoenix_pipeline.config import EnrichedSwap, SummaryRow

logger = logging.getLogger(__name__)


class DataTransformer:
    """Transform and enrich swap data with price information."""

    @staticmethod
    def enrich_swaps(
        swaps: List[Dict[str, Any]],
        prices: Dict[str, float],
    ) -> List[EnrichedSwap]:
        """
        Enrich swap events with USD price data and volume calculations.

        Args:
            swaps: List of swap dictionaries (from SwapEvent.model_dump())
            prices: Dictionary mapping token addresses to USD prices

        Returns:
            List of EnrichedSwap objects with price and volume data

        Notes:
            - Skips swaps with missing prices (logs warning)
            - Rounds decimals to 6 places for USD values
            - Computes usdVolume = abs(amount0*price0) + abs(amount1*price1)
            - For stablecoins, uses one side if both are stable
            - Creates pair identifier as "TOKEN0-TOKEN1"
            - Amounts are assumed to be in raw token units (not normalized)
        """
        enriched_swaps: List[EnrichedSwap] = []
        skipped_count = 0

        # Stablecoin addresses (lowercase) for detection
        STABLECOINS = {
            "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48",  # USDC
            "0xdac17f958d2ee523a2206206994597c13d831ec7",  # USDT
            "0x6b175474e89094c44da98b954eedeac495271d0f",  # DAI
            "0x0000000000085d4780b73119b644ae5ecd22b376",  # TUSD
            "0x8e870d67f660d95d5be530380d0ec0bd388289e1",  # USDP
        }

        # Token decimals mapping (lowercase addresses)
        TOKEN_DECIMALS = {
            "0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2": 18,  # WETH
            "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48": 6,   # USDC
            "0xdac17f958d2ee523a2206206994597c13d831ec7": 6,   # USDT
            "0x6b175474e89094c44da98b954eedeac495271d0f": 18,  # DAI
            "0x2260fac5e5542a773aa44fbcfedf7c193bc2c599": 8,   # WBTC
            "0x1f9840a85d5af5bf1d1762f925bdaddc4201f984": 18,  # UNI
            "0x514910771af9ca656af840dff83e8264ecf986ca": 18,  # LINK
            "0x7fc66500c84a76ad7e9c93437bfc5ac33e2ddae9": 18,  # AAVE
            "0xd533a949740bb3306d119cc777fa900ba034cd52": 18,  # CRV
            "0x9f8f72aa9304c8b593d555f12ef6589cc3a579a2": 18,  # MKR
        }

        for swap in swaps:
            token0 = swap.get("token0", "").lower()
            token1 = swap.get("token1", "").lower()

            # Get prices (case-insensitive lookup)
            price0 = None
            price1 = None
            for addr, price in prices.items():
                addr_lower = addr.lower()
                if addr_lower == token0:
                    price0 = price
                if addr_lower == token1:
                    price1 = price

            # Skip if missing prices
            if price0 is None or price1 is None:
                logger.warning(
                    f"Skipping swap {swap.get('txHash', 'unknown')[:10]}...: "
                    f"missing prices (token0={token0[:10]}..., token1={token1[:10]}...)"
                )
                skipped_count += 1
                continue

            # Convert amounts to float
            try:
                amount0_raw = float(swap.get("amount0", 0))
                amount1_raw = float(swap.get("amount1", 0))
            except (ValueError, TypeError) as e:
                logger.warning(
                    f"Skipping swap {swap.get('txHash', 'unknown')[:10]}...: "
                    f"invalid amounts ({e})"
                )
                skipped_count += 1
                continue

            # Get decimals (default to 18 if unknown)
            decimals0 = TOKEN_DECIMALS.get(token0, 18)
            decimals1 = TOKEN_DECIMALS.get(token1, 18)

            # Normalize amounts (convert from raw units to decimal)
            amount0 = amount0_raw / (10 ** decimals0)
            amount1 = amount1_raw / (10 ** decimals1)

            # Calculate USD volume
            # For stablecoin pairs, use one side to avoid double-counting
            token0_is_stable = token0 in STABLECOINS
            token1_is_stable = token1 in STABLECOINS

            if token0_is_stable and token1_is_stable:
                # Both stable: use token0 side only (should be ~equal anyway)
                usd_volume = abs(amount0 * price0)
            elif token0_is_stable:
                # Token0 is stable: use token0 side (more accurate)
                usd_volume = abs(amount0 * price0)
            elif token1_is_stable:
                # Token1 is stable: use token1 side (more accurate)
                usd_volume = abs(amount1 * price1)
            else:
                # Neither stable: sum both sides
                usd_volume = abs(amount0 * price0) + abs(amount1 * price1)

            # Round to 6 decimal places
            usd_volume = round(usd_volume, 6)
            price0_rounded = round(price0, 6)
            price1_rounded = round(price1, 6)

            # Create pair identifier (token addresses)
            pair = f"{token0}-{token1}"

            # Create enriched swap
            enriched_swap = EnrichedSwap(
                txHash=swap["txHash"],
                blockNumber=swap["blockNumber"],
                timestamp=swap["timestamp"],
                token0=swap["token0"],
                token1=swap["token1"],
                amount0=swap["amount0"],
                amount1=swap["amount1"],
                sqrtPriceX96=swap["sqrtPriceX96"],
                priceUSD0=price0_rounded,
                priceUSD1=price1_rounded,
                usdVolume=usd_volume,
                pair=pair,
            )

            enriched_swaps.append(enriched_swap)

        if skipped_count > 0:
            logger.warning(f"Skipped {skipped_count} swaps due to missing prices or invalid data")

        logger.info(f"Enriched {len(enriched_swaps)} swaps with price data")
        return enriched_swaps

    @staticmethod
    def summarize(enriched: List[EnrichedSwap], top_n: Optional[int] = None) -> pd.DataFrame:
        """
        Summarize enriched swaps by trading pair.

        Args:
            enriched: List of EnrichedSwap objects
            top_n: Optional number of top pairs by USD volume to return

        Returns:
            DataFrame with columns: pair, count, totalUSD, avgUSD
            Sorted by totalUSD descending (deterministic ordering)

        Notes:
            - Groups by pair (token0-token1)
            - Computes count, totalUSD (sum), avgUSD (mean)
            - Rounds avgUSD and totalUSD to 2 decimal places
            - Sorts by totalUSD descending, then by pair ascending (for determinism)
        """
        if not enriched:
            logger.warning("No enriched swaps to summarize")
            return pd.DataFrame(columns=["pair", "count", "totalUSD", "avgUSD"])

        # Convert to DataFrame for easier aggregation
        df = pd.DataFrame([swap.model_dump() for swap in enriched])

        # Group by pair and aggregate
        summary = df.groupby("pair", as_index=False).agg(
            count=("usdVolume", "count"),
            totalUSD=("usdVolume", "sum"),
            avgUSD=("usdVolume", "mean"),
        )

        # Round to 2 decimal places
        summary["totalUSD"] = summary["totalUSD"].round(2)
        summary["avgUSD"] = summary["avgUSD"].round(2)

        # Sort by totalUSD descending, then by pair ascending (deterministic)
        summary = summary.sort_values(
            by=["totalUSD", "pair"],
            ascending=[False, True],
        ).reset_index(drop=True)

        # Optionally filter to top N pairs
        if top_n is not None and top_n > 0:
            summary = summary.head(top_n)
            logger.info(f"Summarized to top {top_n} pairs by USD volume")

        logger.info(f"Created summary with {len(summary)} pairs")
        return summary

    @staticmethod
    def normalize_swaps(swaps: List[Dict[str, Any]]) -> pd.DataFrame:
        """
        Normalize swap data into a pandas DataFrame.

        Args:
            swaps: List of swap dictionaries from subgraph (SwapEvent.model_dump())

        Returns:
            DataFrame with normalized swap data
        """
        if not swaps:
            logger.warning("No swaps to normalize")
            return pd.DataFrame()

        df = pd.DataFrame(swaps)

        # Handle both old field names and new SwapEvent field names
        # New: amount0, amount1, token0, token1, txHash
        # Old: amountIn, amountOut, tokenIn, tokenOut, transaction

        # Rename SwapEvent fields to match expected format if needed
        if "amount0" in df.columns and "amountIn" not in df.columns:
            df["amountIn"] = df["amount0"]
        if "amount1" in df.columns and "amountOut" not in df.columns:
            df["amountOut"] = df["amount1"]
        if "token0" in df.columns and "tokenIn" not in df.columns:
            df["tokenIn"] = df["token0"]
        if "token1" in df.columns and "tokenOut" not in df.columns:
            df["tokenOut"] = df["token1"]
        if "txHash" in df.columns and "transaction" not in df.columns:
            df["transaction"] = df["txHash"]

        # Convert numeric fields
        numeric_fields = ["amount0", "amount1", "amountIn", "amountOut", "amountInUSD", "amountOutUSD", "blockNumber"]
        for field in numeric_fields:
            if field in df.columns:
                df[field] = pd.to_numeric(df[field], errors="coerce")

        # Convert timestamp to datetime
        if "timestamp" in df.columns:
            df["timestamp"] = pd.to_datetime(df["timestamp"], unit="s")
            df["date"] = df["timestamp"].dt.date

        logger.info(f"Normalized {len(df)} swaps")
        return df

    @staticmethod
    def enrich_with_prices(
        df: pd.DataFrame,
        prices: Dict[str, Dict[str, float]],
    ) -> pd.DataFrame:
        """
        Enrich swap data with current price information.

        Args:
            df: DataFrame with swap data
            prices: Dictionary mapping token IDs to price data

        Returns:
            DataFrame with price data added
        """
        if df.empty:
            logger.warning("Empty DataFrame, skipping price enrichment")
            return df

        # Add price columns (example - adjust based on your token mapping)
        df = df.copy()
        df["current_price_usd"] = None
        df["price_change_24h"] = None

        # This is a simplified example - you'd need proper token address -> coingecko ID mapping
        for token_id, price_data in prices.items():
            df.loc[df["tokenIn"] == token_id, "current_price_usd"] = price_data.get("usd")
            df.loc[df["tokenIn"] == token_id, "price_change_24h"] = price_data.get("usd_24h_change")

        logger.info("Enriched swaps with current price data")
        return df

    @staticmethod
    def calculate_aggregations(df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate aggregated metrics from swap data.

        Args:
            df: DataFrame with swap data

        Returns:
            DataFrame with aggregated metrics
        """
        if df.empty:
            logger.warning("Empty DataFrame, skipping aggregations")
            return pd.DataFrame()

        # Aggregate by date and token
        agg_df = df.groupby(["date", "tokenIn"]).agg(
            {
                "amountIn": ["sum", "mean", "count"],
                "amountInUSD": ["sum", "mean"],
                "amountOut": ["sum", "mean"],
                "amountOutUSD": ["sum", "mean"],
            }
        ).reset_index()

        # Flatten column names
        agg_df.columns = ["_".join(col).strip("_") for col in agg_df.columns.values]

        logger.info(f"Calculated aggregations: {len(agg_df)} rows")
        return agg_df

    @staticmethod
    def calculate_volume_metrics(df: pd.DataFrame, window_hours: int = 24) -> pd.DataFrame:
        """
        Calculate rolling volume metrics.

        Args:
            df: DataFrame with swap data
            window_hours: Rolling window size in hours

        Returns:
            DataFrame with volume metrics
        """
        if df.empty or "timestamp" not in df.columns:
            logger.warning("Empty DataFrame or missing timestamp, skipping volume metrics")
            return df

        df = df.copy()
        df = df.sort_values("timestamp")

        # Calculate rolling volume
        window = f"{window_hours}h"
        df["rolling_volume_usd"] = (
            df.set_index("timestamp")["amountInUSD"]
            .rolling(window)
            .sum()
            .reset_index(drop=True)
        )

        logger.info(f"Calculated {window_hours}h rolling volume metrics")
        return df

    @staticmethod
    def detect_outliers(
        df: pd.DataFrame,
        column: str = "amountInUSD",
        threshold: float = 3.0,
    ) -> pd.DataFrame:
        """
        Detect outliers using z-score method.

        Args:
            df: DataFrame with swap data
            column: Column to check for outliers
            threshold: Z-score threshold for outlier detection

        Returns:
            DataFrame with outlier flag added
        """
        if df.empty or column not in df.columns:
            logger.warning(f"Cannot detect outliers: empty DataFrame or missing column '{column}'")
            return df

        df = df.copy()

        # Calculate z-score
        mean = df[column].mean()
        std = df[column].std()

        if std == 0:
            df["is_outlier"] = False
        else:
            df["z_score"] = (df[column] - mean) / std
            df["is_outlier"] = df["z_score"].abs() > threshold

        outlier_count = df["is_outlier"].sum()
        logger.info(f"Detected {outlier_count} outliers in {column}")

        return df

    @staticmethod
    def deduplicate_swaps(df: pd.DataFrame) -> pd.DataFrame:
        """
        Remove duplicate swap records based on transaction ID.

        Args:
            df: DataFrame with swap data

        Returns:
            DataFrame with duplicates removed
        """
        if df.empty or "id" not in df.columns:
            logger.warning("Cannot deduplicate: empty DataFrame or missing 'id' column")
            return df

        initial_count = len(df)
        df = df.drop_duplicates(subset=["id"], keep="first")
        removed_count = initial_count - len(df)

        if removed_count > 0:
            logger.warning(f"Removed {removed_count} duplicate swaps")
        else:
            logger.info("No duplicate swaps found")

        return df

    @staticmethod
    def validate_data(df: pd.DataFrame) -> pd.DataFrame:
        """
        Validate and clean swap data.

        Args:
            df: DataFrame with swap data

        Returns:
            DataFrame with invalid records filtered out
        """
        if df.empty:
            return df

        initial_count = len(df)

        # Remove rows with null critical fields
        critical_fields = ["id", "transaction", "tokenIn", "tokenOut", "blockNumber"]
        df = df.dropna(subset=[f for f in critical_fields if f in df.columns])

        # Remove rows with negative amounts
        amount_fields = ["amountIn", "amountOut", "amountInUSD", "amountOutUSD"]
        for field in amount_fields:
            if field in df.columns:
                df = df[df[field] >= 0]

        removed_count = initial_count - len(df)
        if removed_count > 0:
            logger.warning(f"Removed {removed_count} invalid records during validation")
        else:
            logger.info("All records passed validation")

        return df
