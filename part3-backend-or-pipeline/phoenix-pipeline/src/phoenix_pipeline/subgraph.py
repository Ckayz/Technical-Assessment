"""GraphQL client for Uniswap v3 subgraph."""

import logging
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import httpx
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from phoenix_pipeline.config import settings, SwapEvent

logger = logging.getLogger(__name__)


def compute_since_timestamp(window_minutes: int) -> int:
    """
    Calculate the 'since' timestamp for querying recent swaps.

    Args:
        window_minutes: Time window in minutes to look back from now

    Returns:
        Unix timestamp (epoch seconds) representing the start of the window

    Example:
        >>> # Get timestamp for 60 minutes ago
        >>> timestamp = compute_since_timestamp(60)
        >>> # timestamp will be current_time - 3600 seconds
    """
    now = datetime.utcnow()
    since = now - timedelta(minutes=window_minutes)
    timestamp = int(since.timestamp())

    logger.debug(
        f"Computed since timestamp: {timestamp} "
        f"({window_minutes} minutes ago from {now.isoformat()})"
    )

    return timestamp


def build_query(window_minutes: int) -> str:
    """
    Build a GraphQL query to fetch swap events from the last X minutes.

    This query fetches Uniswap v3 swap events with all necessary fields
    for enrichment and analysis. It uses timestamp filtering to get recent swaps.

    Args:
        window_minutes: Number of minutes to look back from current time

    Returns:
        GraphQL query string with embedded timestamp variable

    The query includes:
        - Transaction hash (id)
        - Timestamp
        - Token0 and Token1 with symbol and address
        - Swap amounts for both tokens
        - Block number
        - Pagination support (first, skip)

    Example:
        >>> query = build_query(60)
        >>> # Returns GraphQL query for swaps in last 60 minutes
    """
    since_timestamp = compute_since_timestamp(window_minutes)

    query = f"""
    query GetRecentSwaps($first: Int!, $skip: Int!) {{
        swaps(
            first: $first
            skip: $skip
            where: {{
                timestamp_gte: {since_timestamp}
            }}
            orderBy: timestamp
            orderDirection: asc
        ) {{
            id
            transaction {{
                id
            }}
            timestamp
            token0 {{
                symbol
                id
            }}
            token1 {{
                symbol
                id
            }}
            amount0
            amount1
            sqrtPriceX96
        }}
    }}
    """

    logger.debug(f"Built query for swaps since timestamp {since_timestamp}")
    return query


@retry(
    retry=retry_if_exception_type((httpx.HTTPError, httpx.TimeoutException)),
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    reraise=True,
)
def _execute_graphql_request(
    client: httpx.Client,
    url: str,
    query: str,
    variables: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Execute a single GraphQL request with retry logic.

    Args:
        client: httpx Client instance
        url: GraphQL endpoint URL
        query: GraphQL query string
        variables: Query variables

    Returns:
        GraphQL response data dictionary

    Raises:
        httpx.HTTPError: On HTTP-level errors
        httpx.TimeoutException: On request timeout
        ValueError: On GraphQL errors or invalid response shape
    """
    payload = {
        "query": query,
        "variables": variables,
    }

    logger.debug(f"Executing GraphQL request with variables: {variables}")

    response = client.post(
        url,
        json=payload,
        headers={"Content-Type": "application/json"},
    )
    response.raise_for_status()

    # Parse response
    try:
        data = response.json()
    except Exception as e:
        raise ValueError(f"Failed to parse JSON response: {e}") from e

    # Validate response shape
    if not isinstance(data, dict):
        raise ValueError(
            f"Invalid response shape: expected dict, got {type(data).__name__}"
        )

    # Check for GraphQL errors
    if "errors" in data:
        errors = data["errors"]
        if not isinstance(errors, list) or not errors:
            raise ValueError(f"Invalid GraphQL errors format: {errors}")

        error_messages = [err.get("message", str(err)) for err in errors]
        error_msg = "; ".join(error_messages)
        logger.error(f"GraphQL errors: {error_msg}")
        raise ValueError(f"GraphQL query failed with errors: {error_msg}")

    # Validate data field exists
    if "data" not in data:
        raise ValueError(
            "Invalid GraphQL response: missing 'data' field. "
            f"Response keys: {list(data.keys())}"
        )

    return data["data"]


def fetch_swaps(
    client: httpx.Client,
    url: str,
    query: str,
    batch_size: int = 100,
    max_results: Optional[int] = None,
) -> List[SwapEvent]:
    """
    Fetch swap events from the subgraph with automatic pagination.

    This function handles pagination automatically, fetching all available
    swaps until no more results are returned. It validates each swap
    and converts it to a SwapEvent model.

    Args:
        client: httpx Client instance with configured timeout
        url: GraphQL endpoint URL
        query: GraphQL query string (should support $first and $skip variables)
        batch_size: Number of records to fetch per request (default: 100)
        max_results: Optional maximum number of results to fetch (None for unlimited)

    Returns:
        List of SwapEvent objects

    Raises:
        httpx.HTTPError: On HTTP-level errors (retried automatically)
        httpx.TimeoutException: On request timeout (retried automatically)
        ValueError: On GraphQL errors or validation failures

    Example:
        >>> with httpx.Client(timeout=30) as client:
        ...     query = build_query(60)
        ...     swaps = fetch_swaps(client, "https://...", query)
        ...     print(f"Fetched {len(swaps)} swaps")
    """
    all_swaps: List[SwapEvent] = []
    skip = 0
    fetched_count = 0

    logger.info(f"Starting swap fetch with batch_size={batch_size}")

    while True:
        # Check if we've reached max_results
        if max_results is not None and fetched_count >= max_results:
            logger.info(f"Reached max_results limit of {max_results}")
            break

        # Adjust batch size if approaching max_results
        current_batch_size = batch_size
        if max_results is not None:
            remaining = max_results - fetched_count
            current_batch_size = min(batch_size, remaining)

        # Execute query with pagination
        variables = {
            "first": current_batch_size,
            "skip": skip,
        }

        try:
            data = _execute_graphql_request(client, url, query, variables)
        except Exception as e:
            logger.error(f"Failed to fetch swaps at skip={skip}: {e}")
            raise

        # Validate response contains swaps
        if not isinstance(data, dict):
            raise ValueError(
                f"Invalid data shape: expected dict, got {type(data).__name__}"
            )

        if "swaps" not in data:
            raise ValueError(
                f"Response missing 'swaps' field. Available fields: {list(data.keys())}"
            )

        swaps_data = data["swaps"]

        if not isinstance(swaps_data, list):
            raise ValueError(
                f"Invalid swaps shape: expected list, got {type(swaps_data).__name__}"
            )

        # Break if no more results
        if not swaps_data:
            logger.info(f"No more swaps found. Total fetched: {len(all_swaps)}")
            break

        # Parse and validate each swap
        batch_swaps: List[SwapEvent] = []
        for idx, swap_raw in enumerate(swaps_data):
            try:
                # Validate required fields
                if not isinstance(swap_raw, dict):
                    raise ValueError(
                        f"Swap at index {idx} is not a dict: {type(swap_raw).__name__}"
                    )

                # Extract transaction hash
                tx_hash = swap_raw.get("id")
                if swap_raw.get("transaction"):
                    if isinstance(swap_raw["transaction"], dict):
                        tx_hash = swap_raw["transaction"].get("id", tx_hash)

                # Extract token addresses and symbols
                token0_data = swap_raw.get("token0", {})
                token1_data = swap_raw.get("token1", {})

                if not isinstance(token0_data, dict) or not isinstance(token1_data, dict):
                    raise ValueError(
                        f"Invalid token data at index {idx}: "
                        f"token0={type(token0_data).__name__}, "
                        f"token1={type(token1_data).__name__}"
                    )

                # Create SwapEvent
                swap_event = SwapEvent(
                    txHash=tx_hash or swap_raw.get("id", ""),
                    blockNumber=int(swap_raw.get("blockNumber", 0)) if swap_raw.get("blockNumber") else 0,
                    timestamp=int(swap_raw.get("timestamp", 0)),
                    token0=token0_data.get("id", ""),
                    token1=token1_data.get("id", ""),
                    amount0=str(swap_raw.get("amount0", "0")),
                    amount1=str(swap_raw.get("amount1", "0")),
                    sqrtPriceX96=str(swap_raw.get("sqrtPriceX96", "0")),
                )

                batch_swaps.append(swap_event)

            except Exception as e:
                logger.warning(
                    f"Failed to parse swap at index {idx} (skip={skip}): {e}. "
                    f"Raw data: {swap_raw}"
                )
                # Continue processing other swaps
                continue

        # Add to results
        all_swaps.extend(batch_swaps)
        fetched_count += len(batch_swaps)

        logger.info(
            f"Fetched batch: {len(batch_swaps)} swaps "
            f"(skip={skip}, total so far: {len(all_swaps)})"
        )

        # If we got fewer results than requested, we've reached the end
        if len(swaps_data) < current_batch_size:
            logger.info(
                f"Received fewer results than batch size "
                f"({len(swaps_data)} < {current_batch_size}). "
                f"Pagination complete."
            )
            break

        # Move to next page
        skip += current_batch_size

    logger.info(f"Fetch complete. Total swaps: {len(all_swaps)}")
    return all_swaps


class SubgraphClient:
    """
    Client for querying Uniswap v3 subgraph.

    This class provides a higher-level interface for fetching swap data
    with built-in retry logic, pagination, and error handling.

    Example:
        >>> with SubgraphClient() as client:
        ...     swaps = client.get_recent_swaps(window_minutes=60)
        ...     print(f"Found {len(swaps)} swaps")
    """

    def __init__(
        self,
        url: Optional[str] = None,
        timeout: Optional[int] = None,
        max_retries: Optional[int] = None,
    ) -> None:
        """
        Initialize the subgraph client.

        Args:
            url: GraphQL endpoint URL (defaults to settings)
            timeout: Request timeout in seconds (defaults to settings)
            max_retries: Maximum retry attempts (defaults to settings)
        """
        self.url = str(url or settings.subgraph_url)
        self.timeout = timeout or settings.subgraph_timeout
        self.max_retries = max_retries or settings.subgraph_max_retries
        self.client = httpx.Client(timeout=self.timeout)

    def __enter__(self) -> "SubgraphClient":
        """Context manager entry."""
        return self

    def __exit__(self, *args: object) -> None:
        """Context manager exit."""
        self.close()

    def close(self) -> None:
        """Close the HTTP client."""
        self.client.close()

    def get_recent_swaps(
        self,
        window_minutes: Optional[int] = None,
        batch_size: Optional[int] = None,
        max_results: Optional[int] = None,
    ) -> List[SwapEvent]:
        """
        Fetch recent swap events from the subgraph.

        Args:
            window_minutes: Time window in minutes (defaults to settings.window_minutes)
            batch_size: Records per request (defaults to settings.batch_size)
            max_results: Maximum total results to fetch (None for unlimited)

        Returns:
            List of SwapEvent objects

        Raises:
            httpx.HTTPError: On HTTP errors
            ValueError: On GraphQL errors or validation failures
        """
        window = window_minutes or settings.window_minutes
        batch = batch_size or settings.batch_size

        query = build_query(window)
        swaps = fetch_swaps(
            client=self.client,
            url=self.url,
            query=query,
            batch_size=batch,
            max_results=max_results,
        )

        logger.info(
            f"Fetched {len(swaps)} swaps from last {window} minutes "
            f"using batch_size={batch}"
        )
        return swaps
