"""Pytest configuration and fixtures."""

import pytest
from pathlib import Path
from typing import Dict, Any, List
import pandas as pd


@pytest.fixture
def sample_swaps() -> List[Dict[str, Any]]:
    """Sample swap data for testing."""
    return [
        {
            "id": "0x123",
            "transaction": "0xabc",
            "timestamp": "1640000000",
            "blockNumber": "1000",
            "from": "0xfrom1",
            "to": "0xto1",
            "tokenIn": "0xtoken1",
            "tokenOut": "0xtoken2",
            "amountIn": "1000000",
            "amountOut": "2000000",
            "amountInUSD": "1000",
            "amountOutUSD": "2000",
        },
        {
            "id": "0x456",
            "transaction": "0xdef",
            "timestamp": "1640000100",
            "blockNumber": "1001",
            "from": "0xfrom2",
            "to": "0xto2",
            "tokenIn": "0xtoken1",
            "tokenOut": "0xtoken3",
            "amountIn": "500000",
            "amountOut": "1500000",
            "amountInUSD": "500",
            "amountOutUSD": "1500",
        },
    ]


@pytest.fixture
def sample_prices() -> Dict[str, Dict[str, float]]:
    """Sample price data for testing."""
    return {
        "bitcoin": {"usd": 50000.0, "usd_24h_change": 2.5},
        "ethereum": {"usd": 3000.0, "usd_24h_change": -1.2},
        "usd-coin": {"usd": 1.0, "usd_24h_change": 0.01},
    }


@pytest.fixture
def sample_dataframe(sample_swaps: List[Dict[str, Any]]) -> pd.DataFrame:
    """Sample DataFrame for testing."""
    df = pd.DataFrame(sample_swaps)

    # Convert types
    numeric_fields = ["amountIn", "amountOut", "amountInUSD", "amountOutUSD", "blockNumber"]
    for field in numeric_fields:
        df[field] = pd.to_numeric(df[field])

    df["timestamp"] = pd.to_datetime(df["timestamp"], unit="s")
    df["date"] = df["timestamp"].dt.date

    return df


@pytest.fixture
def temp_output_dir(tmp_path: Path) -> Path:
    """Temporary output directory for testing."""
    output_dir = tmp_path / "output"
    output_dir.mkdir(exist_ok=True)
    return output_dir


@pytest.fixture
def temp_state_file(tmp_path: Path) -> Path:
    """Temporary state file for testing."""
    return tmp_path / "state.json"
