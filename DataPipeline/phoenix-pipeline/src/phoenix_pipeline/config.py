"""Configuration management using Pydantic settings."""

from pathlib import Path
from typing import Optional

from pydantic import Field, HttpUrl
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Phoenix Subgraph
    subgraph_url: HttpUrl = Field(
        default="https://api.thegraph.com/subgraphs/name/phoenix/dex",
        description="Phoenix subgraph GraphQL endpoint",
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

    # CoinGecko API
    coingecko_api_url: HttpUrl = Field(
        default="https://api.coingecko.com/api/v3",
        description="CoinGecko API base URL",
    )
    coingecko_api_key: Optional[str] = Field(
        default=None,
        description="CoinGecko API key (optional, for higher rate limits)",
    )
    coingecko_timeout: int = Field(
        default=30,
        description="Timeout for CoinGecko requests in seconds",
        ge=1,
    )
    coingecko_max_retries: int = Field(
        default=3,
        description="Maximum number of retry attempts for CoinGecko requests",
        ge=0,
    )
    coingecko_rate_limit_delay: float = Field(
        default=1.2,
        description="Delay between CoinGecko requests in seconds",
        ge=0,
    )

    # Pipeline Configuration
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

    # Output Configuration
    output_dir: Path = Field(
        default=Path("output"),
        description="Directory for output files",
    )
    output_format: str = Field(
        default="csv",
        description="Output format: csv, json, or parquet",
        pattern="^(csv|json|parquet)$",
    )
    state_file: Path = Field(
        default=Path("output/state.json"),
        description="File to track last processed block",
    )

    # Logging
    log_level: str = Field(
        default="INFO",
        description="Logging level",
        pattern="^(DEBUG|INFO|WARNING|ERROR|CRITICAL)$",
    )

    def __init__(self, **kwargs: object) -> None:
        """Initialize settings and create output directory if it doesn't exist."""
        super().__init__(**kwargs)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.state_file.parent.mkdir(parents=True, exist_ok=True)


# Global settings instance
settings = Settings()
