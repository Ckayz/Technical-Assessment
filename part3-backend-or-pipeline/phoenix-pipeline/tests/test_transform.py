"""Tests for data transformation module."""

import pandas as pd
import pytest
from typing import Dict, Any, List

from phoenix_pipeline.transform import DataTransformer


class TestDataTransformer:
    """Test suite for DataTransformer."""

    def test_normalize_swaps(self, sample_swaps: List[Dict[str, Any]]) -> None:
        """Test normalizing swap data into DataFrame."""
        df = DataTransformer.normalize_swaps(sample_swaps)

        assert not df.empty
        assert len(df) == 2
        assert "blockNumber" in df.columns
        assert "timestamp" in df.columns
        assert "date" in df.columns
        assert df["blockNumber"].dtype in [int, "int64"]
        assert pd.api.types.is_datetime64_any_dtype(df["timestamp"])

    def test_normalize_empty_swaps(self) -> None:
        """Test normalizing empty swap list."""
        df = DataTransformer.normalize_swaps([])
        assert df.empty

    def test_enrich_with_prices(
        self,
        sample_dataframe: pd.DataFrame,
        sample_prices: Dict[str, Dict[str, float]],
    ) -> None:
        """Test enriching data with price information."""
        df = DataTransformer.enrich_with_prices(sample_dataframe, sample_prices)

        assert "current_price_usd" in df.columns
        assert "price_change_24h" in df.columns

    def test_calculate_aggregations(self, sample_dataframe: pd.DataFrame) -> None:
        """Test calculating aggregations."""
        agg_df = DataTransformer.calculate_aggregations(sample_dataframe)

        assert not agg_df.empty
        assert "date" in agg_df.columns
        assert "tokenIn" in agg_df.columns

    def test_calculate_aggregations_empty(self) -> None:
        """Test aggregations with empty DataFrame."""
        df = pd.DataFrame()
        agg_df = DataTransformer.calculate_aggregations(df)
        assert agg_df.empty

    def test_deduplicate_swaps(self, sample_dataframe: pd.DataFrame) -> None:
        """Test deduplicating swap records."""
        # Add a duplicate row
        df_with_dup = pd.concat([sample_dataframe, sample_dataframe.iloc[[0]]], ignore_index=True)

        assert len(df_with_dup) == 3

        df_dedup = DataTransformer.deduplicate_swaps(df_with_dup)
        assert len(df_dedup) == 2

    def test_validate_data(self, sample_dataframe: pd.DataFrame) -> None:
        """Test data validation."""
        # Add invalid row with negative amount
        invalid_row = sample_dataframe.iloc[0].copy()
        invalid_row["amountIn"] = -1000
        df_with_invalid = pd.concat([sample_dataframe, invalid_row.to_frame().T], ignore_index=True)

        df_valid = DataTransformer.validate_data(df_with_invalid)
        assert len(df_valid) == 2  # Invalid row removed
        assert (df_valid["amountIn"] >= 0).all()

    def test_detect_outliers(self, sample_dataframe: pd.DataFrame) -> None:
        """Test outlier detection."""
        df = DataTransformer.detect_outliers(sample_dataframe, column="amountInUSD")

        assert "is_outlier" in df.columns
        assert "z_score" in df.columns

    def test_calculate_volume_metrics(self, sample_dataframe: pd.DataFrame) -> None:
        """Test rolling volume metrics calculation."""
        df = DataTransformer.calculate_volume_metrics(sample_dataframe, window_hours=24)

        assert "rolling_volume_usd" in df.columns
