"""Data transformation and enrichment logic."""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

import pandas as pd

logger = logging.getLogger(__name__)


class DataTransformer:
    """Transform and enrich swap data with price information."""

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
