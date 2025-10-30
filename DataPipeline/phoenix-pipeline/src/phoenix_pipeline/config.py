"""Configuration management using Pydantic settings."""

from pathlib import Path
from typing import Optional, List

from pydantic import BaseModel, Field, HttpUrl
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Subgraph Configuration
    subgraph_url: HttpUrl = Field(
        default="https://api.thegraph.com/subgraphs/name/uniswap/uniswap-v3",
        description="Uniswap v3 mainnet subgraph GraphQL endpoint",
    )

    # Time Window Configuration
    window_minutes: int = Field(
        default=60,
        description="Time window in minutes for aggregating data",
        ge=1,
    )

    # CoinGecko API Configuration
    coingecko_api: HttpUrl = Field(
        default="https://api.coingecko.com/api/v3",
        description="CoinGecko API base URL",
    )
    coingecko_api_key: Optional[str] = Field(
        default=None,
        description="CoinGecko API key (optional, for higher rate limits)",
    )

    # Output Configuration
    output_dir: Path = Field(
        default=Path("./output"),
        description="Directory for output files",
    )
    state_path: Path = Field(
        default=Path("./state.json"),
        description="Path to state file for tracking last processed block",
    )

    # Rate Limiting
    max_requests_per_min: int = Field(
        default=50,
        description="Maximum number of API requests per minute",
        ge=1,
    )

    # Additional Configuration
    batch_size: int = Field(
        default=100,
        description="Number of records to process in each batch",
        ge=1,
    )
    start_block: int = Field(
        default=0,
        description="Starting block number for processing",
        ge=0,
    )
    end_block: Optional[int] = Field(
        default=None,
        description="Ending block number for processing (None for latest)",
    )
    output_format: str = Field(
        default="csv",
        description="Output format: csv, json, or parquet",
        pattern="^(csv|json|parquet)$",
    )
    log_level: str = Field(
        default="INFO",
        description="Logging level",
        pattern="^(DEBUG|INFO|WARNING|ERROR|CRITICAL)$",
    )
    subgraph_timeout: int = Field(
        default=30,
        description="Timeout for subgraph requests in seconds",
        ge=1,
    )
    subgraph_max_retries: int = Field(
        default=3,
        description="Maximum number of retry attempts for subgraph requests",
        ge=0,
    )

    def __init__(self, **kwargs: object) -> None:
        """Initialize settings and create output directory if it doesn't exist."""
        super().__init__(**kwargs)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.state_path.parent.mkdir(parents=True, exist_ok=True)


class SwapEvent(BaseModel):
    """Raw swap event from subgraph."""

    txHash: str = Field(description="Transaction hash")
    blockNumber: int = Field(description="Block number when swap occurred")
    timestamp: int = Field(description="Unix timestamp of the swap")
    token0: str = Field(description="Address of token0 in the pair")
    token1: str = Field(description="Address of token1 in the pair")
    amount0: str = Field(description="Amount of token0 swapped (can be negative)")
    amount1: str = Field(description="Amount of token1 swapped (can be negative)")
    sqrtPriceX96: str = Field(description="Square root price ratio encoded as Q64.96")

    class Config:
        """Pydantic model configuration."""
        frozen = False
        extra = "allow"


class EnrichedSwap(BaseModel):
    """Swap event enriched with USD price data."""

    # Original swap event fields
    txHash: str = Field(description="Transaction hash")
    blockNumber: int = Field(description="Block number when swap occurred")
    timestamp: int = Field(description="Unix timestamp of the swap")
    token0: str = Field(description="Address of token0 in the pair")
    token1: str = Field(description="Address of token1 in the pair")
    amount0: str = Field(description="Amount of token0 swapped")
    amount1: str = Field(description="Amount of token1 swapped")
    sqrtPriceX96: str = Field(description="Square root price ratio encoded as Q64.96")

    # Enriched fields
    priceUSD0: Optional[float] = Field(default=None, description="USD price of token0")
    priceUSD1: Optional[float] = Field(default=None, description="USD price of token1")
    usdVolume: Optional[float] = Field(default=None, description="Total USD volume of the swap")
    pair: str = Field(description="Trading pair identifier (e.g., 'ETH/USDC')")

    class Config:
        """Pydantic model configuration."""
        frozen = False
        extra = "allow"


class SummaryRow(BaseModel):
    """Aggregated summary statistics for a trading pair."""

    pair: str = Field(description="Trading pair identifier (e.g., 'ETH/USDC')")
    count: int = Field(description="Number of swaps in the time window")
    totalUSD: float = Field(description="Total USD volume traded")
    avgUSD: float = Field(description="Average USD volume per swap")
    tradersTopN: Optional[List[str]] = Field(
        default=None,
        description="Optional list of top N trader addresses by volume",
    )

    class Config:
        """Pydantic model configuration."""
        frozen = False
        extra = "allow"


# Global settings instance
settings = Settings()
