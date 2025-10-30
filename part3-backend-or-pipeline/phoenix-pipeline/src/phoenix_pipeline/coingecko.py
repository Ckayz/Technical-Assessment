"""CoinGecko API client for price data."""

import logging
import random
import time
from collections import deque
from typing import Any, Dict, List, Optional, Union

import httpx
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential_jitter,
)

from phoenix_pipeline.config import settings

logger = logging.getLogger(__name__)


# Static mapping of common token addresses to CoinGecko IDs
# Ethereum mainnet addresses (lowercase)
TOKEN_ADDRESS_TO_COINGECKO_ID = {
    # Wrapped ETH
    "0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2": "weth",
    # USDC
    "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48": "usd-coin",
    # USDT
    "0xdac17f958d2ee523a2206206994597c13d831ec7": "tether",
    # WBTC
    "0x2260fac5e5542a773aa44fbcfedf7c193bc2c599": "wrapped-bitcoin",
    # DAI
    "0x6b175474e89094c44da98b954eedeac495271d0f": "dai",
    # UNI
    "0x1f9840a85d5af5bf1d1762f925bdaddc4201f984": "uniswap",
    # LINK
    "0x514910771af9ca656af840dff83e8264ecf986ca": "chainlink",
    # AAVE
    "0x7fc66500c84a76ad7e9c93437bfc5ac33e2ddae9": "aave",
    # CRV
    "0xd533a949740bb3306d119cc777fa900ba034cd52": "curve-dao-token",
    # MKR
    "0x9f8f72aa9304c8b593d555f12ef6589cc3a579a2": "maker",
}

# Symbol-based mapping for common tokens
TOKEN_SYMBOL_TO_COINGECKO_ID = {
    "eth": "ethereum",
    "weth": "weth",
    "btc": "bitcoin",
    "wbtc": "wrapped-bitcoin",
    "usdc": "usd-coin",
    "usdt": "tether",
    "dai": "dai",
    "uni": "uniswap",
    "link": "chainlink",
    "aave": "aave",
    "crv": "curve-dao-token",
    "mkr": "maker",
}


class RateLimiter:
    """In-memory rate limiter using sliding window."""

    def __init__(self, max_requests: int, window_seconds: float = 60.0):
        """
        Initialize rate limiter.

        Args:
            max_requests: Maximum number of requests allowed in the window
            window_seconds: Time window in seconds (default 60)
        """
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests: deque = deque()

    def acquire(self) -> None:
        """
        Acquire permission to make a request, blocking if necessary.

        This implements a sliding window rate limiter.
        """
        now = time.time()

        # Remove timestamps outside the current window
        while self.requests and self.requests[0] < now - self.window_seconds:
            self.requests.popleft()

        # If at limit, wait until oldest request expires
        if len(self.requests) >= self.max_requests:
            oldest = self.requests[0]
            wait_time = (oldest + self.window_seconds) - now
            if wait_time > 0:
                logger.debug(
                    f"Rate limit reached ({self.max_requests} req/{self.window_seconds}s). "
                    f"Waiting {wait_time:.2f}s"
                )
                time.sleep(wait_time)
                # Clean up again after sleeping
                now = time.time()
                while self.requests and self.requests[0] < now - self.window_seconds:
                    self.requests.popleft()

        # Record this request
        self.requests.append(now)

    def get_stats(self) -> Dict[str, Any]:
        """Get current rate limiter statistics."""
        now = time.time()
        # Clean up old requests
        while self.requests and self.requests[0] < now - self.window_seconds:
            self.requests.popleft()

        return {
            "requests_in_window": len(self.requests),
            "max_requests": self.max_requests,
            "window_seconds": self.window_seconds,
            "remaining": max(0, self.max_requests - len(self.requests)),
        }


class CoinGeckoClient:
    """
    Client for fetching cryptocurrency prices from CoinGecko.

    Features:
    - In-memory rate limiting (configurable requests per minute)
    - Price caching within a run
    - Retry with exponential backoff and jitter
    - Static token mappings for robustness
    - Support for both addresses and symbols
    """

    def __init__(
        self,
        api_url: Optional[str] = None,
        api_key: Optional[str] = None,
        timeout: int = 30,
        max_requests_per_min: Optional[int] = None,
    ) -> None:
        """
        Initialize the CoinGecko client.

        Args:
            api_url: API base URL (defaults to settings)
            api_key: API key for authentication (defaults to settings)
            timeout: Request timeout in seconds
            max_requests_per_min: Max requests per minute (defaults to settings)
        """
        self.api_url = str(api_url or settings.coingecko_api).rstrip("/")
        self.api_key = api_key or settings.coingecko_api_key
        self.timeout = timeout

        # Initialize rate limiter
        max_rpm = max_requests_per_min or settings.max_requests_per_min
        self.rate_limiter = RateLimiter(max_requests=max_rpm, window_seconds=60.0)

        # Initialize price cache
        self.price_cache: Dict[str, Dict[str, float]] = {}

        # Setup HTTP client
        headers = {"Accept": "application/json"}
        if self.api_key:
            headers["x-cg-pro-api-key"] = self.api_key

        self.client = httpx.Client(timeout=self.timeout, headers=headers)

        logger.info(f"CoinGecko client initialized (rate limit: {max_rpm} req/min)")

    def __enter__(self) -> "CoinGeckoClient":
        """Context manager entry."""
        return self

    def __exit__(self, *args: object) -> None:
        """Context manager exit."""
        self.close()

    def close(self) -> None:
        """Close the HTTP client."""
        self.client.close()
        stats = self.rate_limiter.get_stats()
        logger.info(
            f"CoinGecko client closed. "
            f"Cache hits: {len(self.price_cache)}, "
            f"Requests used: {stats['requests_in_window']}/{stats['max_requests']}"
        )

    def _resolve_token_id(self, identifier: str) -> Optional[str]:
        """
        Resolve a token address or symbol to a CoinGecko ID.

        Args:
            identifier: Token address (0x...) or symbol (eth, wbtc, etc.)

        Returns:
            CoinGecko ID if found, None otherwise
        """
        identifier_lower = identifier.lower().strip()

        # Check if it's an address (starts with 0x)
        if identifier_lower.startswith("0x"):
            coingecko_id = TOKEN_ADDRESS_TO_COINGECKO_ID.get(identifier_lower)
            if coingecko_id:
                logger.debug(f"Resolved address {identifier_lower} -> {coingecko_id}")
                return coingecko_id
        else:
            # Try as symbol
            coingecko_id = TOKEN_SYMBOL_TO_COINGECKO_ID.get(identifier_lower)
            if coingecko_id:
                logger.debug(f"Resolved symbol {identifier_lower} -> {coingecko_id}")
                return coingecko_id

        # If not found, assume it's already a CoinGecko ID
        logger.debug(f"Using {identifier} as-is (assuming CoinGecko ID)")
        return identifier

    def _should_retry(self, retry_state) -> bool:
        """Check if request should be retried (only on 5xx errors)."""
        if retry_state.outcome.failed:
            exception = retry_state.outcome.exception()
            if isinstance(exception, httpx.HTTPStatusError):
                return exception.response.status_code >= 500
        return False

    @retry(
        retry=lambda retry_state: CoinGeckoClient._should_retry(None, retry_state),
        stop=stop_after_attempt(3),
        wait=wait_exponential_jitter(initial=1, max=10, jitter=2),
        reraise=True,
    )
    def _make_request(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Make an API request with retry logic and rate limiting.

        Retries only on HTTP >= 500 errors with exponential backoff + jitter.

        Args:
            endpoint: API endpoint path
            params: Query parameters

        Returns:
            JSON response data

        Raises:
            httpx.HTTPStatusError: On HTTP >= 500 errors (retried)
            httpx.HTTPError: On other HTTP errors
        """
        # Apply rate limiting
        self.rate_limiter.acquire()

        url = f"{self.api_url}/{endpoint}"
        logger.debug(f"CoinGecko API request: {url}")

        response = self.client.get(url, params=params)

        # Raise for any HTTP error
        if response.status_code >= 400:
            if response.status_code >= 500:
                # 5xx errors will be retried
                logger.warning(f"CoinGecko API error {response.status_code} (will retry): {response.text}")
            else:
                # 4xx errors will not be retried
                logger.warning(f"CoinGecko API error {response.status_code}: {response.text}")
            response.raise_for_status()

        return response.json()

    def fetch_prices(
        self,
        symbols_or_addresses: List[str],
        vs_currency: str = "usd",
        use_cache: bool = True,
    ) -> Dict[str, float]:
        """
        Fetch current USD prices for a list of token symbols or addresses.

        This is the main method to use for price fetching. It handles:
        - Address/symbol resolution
        - Caching
        - Batch requests
        - Rate limiting

        Args:
            symbols_or_addresses: List of token addresses (0x...) or symbols (eth, wbtc)
            vs_currency: Currency to price against (default: usd)
            use_cache: Whether to use cached prices (default: True)

        Returns:
            Dictionary mapping original input -> price in USD
            Example: {"0xc02aaa...": 2500.50, "eth": 2500.50}

        Example:
            >>> client = CoinGeckoClient()
            >>> prices = client.fetch_prices(["0xc02aaa...", "wbtc", "usdc"])
            >>> print(prices)
            {'0xc02aaa...': 2500.50, 'wbtc': 45000.0, 'usdc': 1.0}
        """
        result: Dict[str, float] = {}
        to_fetch: List[tuple[str, str]] = []  # (original_input, coingecko_id)

        # Step 1: Check cache and resolve IDs
        for identifier in symbols_or_addresses:
            cache_key = f"{identifier}_{vs_currency}"

            if use_cache and cache_key in self.price_cache:
                # Cache hit
                cached_data = self.price_cache[cache_key]
                result[identifier] = cached_data.get(vs_currency, 0.0)
                logger.debug(f"Cache hit: {identifier} = ${result[identifier]}")
            else:
                # Need to fetch
                coingecko_id = self._resolve_token_id(identifier)
                if coingecko_id:
                    to_fetch.append((identifier, coingecko_id))

        # Step 2: Fetch prices for uncached tokens
        if to_fetch:
            # Get unique CoinGecko IDs
            unique_ids = list(set([cg_id for _, cg_id in to_fetch]))

            logger.info(f"Fetching prices for {len(unique_ids)} tokens from CoinGecko...")

            try:
                # Make API request
                params = {
                    "ids": ",".join(unique_ids),
                    "vs_currencies": vs_currency,
                    "include_24hr_change": "false",
                }

                price_data = self._make_request("simple/price", params)

                # Process results
                for original_input, coingecko_id in to_fetch:
                    if coingecko_id in price_data:
                        price = price_data[coingecko_id].get(vs_currency, 0.0)
                        result[original_input] = price

                        # Cache the result
                        cache_key = f"{original_input}_{vs_currency}"
                        self.price_cache[cache_key] = {vs_currency: price}

                        logger.debug(f"Fetched: {original_input} ({coingecko_id}) = ${price}")
                    else:
                        logger.warning(f"No price data for {coingecko_id} (input: {original_input})")
                        result[original_input] = 0.0

                logger.info(f"Successfully fetched prices for {len(result)} tokens")

            except Exception as e:
                logger.error(f"Failed to fetch prices from CoinGecko: {e}")
                # Fill remaining with zeros
                for original_input, _ in to_fetch:
                    if original_input not in result:
                        result[original_input] = 0.0

        return result

    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache and rate limiter statistics."""
        return {
            "cached_tokens": len(self.price_cache),
            "rate_limiter": self.rate_limiter.get_stats(),
        }

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
