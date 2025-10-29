"""CoinGecko API client for price data."""

import logging
import time
from typing import Any, Dict, List, Optional

import httpx
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from phoenix_pipeline.config import settings

logger = logging.getLogger(__name__)


class CoinGeckoClient:
    """Client for fetching cryptocurrency prices from CoinGecko."""

    def __init__(
        self,
        api_url: Optional[str] = None,
        api_key: Optional[str] = None,
        timeout: Optional[int] = None,
        max_retries: Optional[int] = None,
        rate_limit_delay: Optional[float] = None,
    ) -> None:
        """
        Initialize the CoinGecko client.

        Args:
            api_url: API base URL (defaults to settings)
            api_key: API key for authentication (defaults to settings)
            timeout: Request timeout in seconds (defaults to settings)
            max_retries: Maximum retry attempts (defaults to settings)
            rate_limit_delay: Delay between requests in seconds (defaults to settings)
        """
        self.api_url = str(api_url or settings.coingecko_api_url).rstrip("/")
        self.api_key = api_key or settings.coingecko_api_key
        self.timeout = timeout or settings.coingecko_timeout
        self.max_retries = max_retries or settings.coingecko_max_retries
        self.rate_limit_delay = rate_limit_delay or settings.coingecko_rate_limit_delay
        self.last_request_time = 0.0

        headers = {}
        if self.api_key:
            headers["x-cg-pro-api-key"] = self.api_key

        self.client = httpx.Client(timeout=self.timeout, headers=headers)

    def __enter__(self) -> "CoinGeckoClient":
        """Context manager entry."""
        return self

    def __exit__(self, *args: object) -> None:
        """Context manager exit."""
        self.close()

    def close(self) -> None:
        """Close the HTTP client."""
        self.client.close()

    def _rate_limit(self) -> None:
        """Apply rate limiting between requests."""
        elapsed = time.time() - self.last_request_time
        if elapsed < self.rate_limit_delay:
            sleep_time = self.rate_limit_delay - elapsed
            logger.debug(f"Rate limiting: sleeping for {sleep_time:.2f}s")
            time.sleep(sleep_time)
        self.last_request_time = time.time()

    @retry(
        retry=retry_if_exception_type((httpx.HTTPError, httpx.TimeoutException)),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        reraise=True,
    )
    def _make_request(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Make an API request with retry logic.

        Args:
            endpoint: API endpoint path
            params: Query parameters

        Returns:
            JSON response data

        Raises:
            httpx.HTTPError: On HTTP errors
        """
        self._rate_limit()

        url = f"{self.api_url}/{endpoint}"
        logger.debug(f"Requesting: {url}")

        response = self.client.get(url, params=params)
        response.raise_for_status()

        return response.json()

    def get_price(
        self,
        token_ids: List[str],
        vs_currency: str = "usd",
        include_24h_change: bool = True,
    ) -> Dict[str, Dict[str, float]]:
        """
        Get current prices for tokens.

        Args:
            token_ids: List of CoinGecko token IDs
            vs_currency: Currency to price against (default: usd)
            include_24h_change: Include 24h price change percentage

        Returns:
            Dictionary mapping token IDs to price data
        """
        params: Dict[str, Any] = {
            "ids": ",".join(token_ids),
            "vs_currencies": vs_currency,
        }

        if include_24h_change:
            params["include_24hr_change"] = "true"

        data = self._make_request("simple/price", params)
        logger.info(f"Fetched prices for {len(data)} tokens")
        return data

    def get_historical_price(
        self,
        token_id: str,
        date: str,
        vs_currency: str = "usd",
    ) -> Optional[float]:
        """
        Get historical price for a token on a specific date.

        Args:
            token_id: CoinGecko token ID
            date: Date in DD-MM-YYYY format
            vs_currency: Currency to price against (default: usd)

        Returns:
            Price on the specified date, or None if not available
        """
        endpoint = f"coins/{token_id}/history"
        params = {
            "date": date,
            "localization": "false",
        }

        data = self._make_request(endpoint, params)
        market_data = data.get("market_data", {})
        current_price = market_data.get("current_price", {})
        price = current_price.get(vs_currency)

        if price:
            logger.info(f"Historical price for {token_id} on {date}: {price} {vs_currency}")
        else:
            logger.warning(f"No historical price data for {token_id} on {date}")

        return price

    def search_tokens(self, query: str) -> List[Dict[str, Any]]:
        """
        Search for tokens by name or symbol.

        Args:
            query: Search query

        Returns:
            List of matching token dictionaries
        """
        data = self._make_request("search", {"query": query})
        coins = data.get("coins", [])
        logger.info(f"Found {len(coins)} tokens matching '{query}'")
        return coins

    def get_token_info(self, token_id: str) -> Dict[str, Any]:
        """
        Get detailed information about a token.

        Args:
            token_id: CoinGecko token ID

        Returns:
            Token information dictionary
        """
        endpoint = f"coins/{token_id}"
        params = {
            "localization": "false",
            "tickers": "false",
            "market_data": "true",
            "community_data": "false",
            "developer_data": "false",
        }

        data = self._make_request(endpoint, params)
        logger.info(f"Fetched info for token: {token_id}")
        return data
