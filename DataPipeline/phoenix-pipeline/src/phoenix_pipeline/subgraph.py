"""GraphQL client for Phoenix subgraph."""

import logging
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


class SubgraphClient:
    """Client for querying Phoenix DEX subgraph."""

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

    @retry(
        retry=retry_if_exception_type((httpx.HTTPError, httpx.TimeoutException)),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        reraise=True,
    )
    def _execute_query(self, query: str, variables: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Execute a GraphQL query with retry logic.

        Args:
            query: GraphQL query string
            variables: Query variables

        Returns:
            GraphQL response data

        Raises:
            httpx.HTTPError: On HTTP errors
            ValueError: On GraphQL errors
        """
        payload = {"query": query}
        if variables:
            payload["variables"] = variables

        logger.debug(f"Executing query: {query[:100]}...")
        response = self.client.post(self.url, json=payload)
        response.raise_for_status()

        data = response.json()
        if "errors" in data:
            error_msg = data["errors"][0].get("message", "Unknown GraphQL error")
            logger.error(f"GraphQL error: {error_msg}")
            raise ValueError(f"GraphQL error: {error_msg}")

        return data.get("data", {})

    def get_swaps(
        self,
        start_block: int = 0,
        end_block: Optional[int] = None,
        first: int = 100,
        skip: int = 0,
    ) -> List[Dict[str, Any]]:
        """
        Fetch swap events from the subgraph.

        Args:
            start_block: Starting block number
            end_block: Ending block number (None for no limit)
            first: Number of results to fetch
            skip: Number of results to skip

        Returns:
            List of swap event dictionaries
        """
        query = """
        query GetSwaps($startBlock: Int!, $endBlock: Int, $first: Int!, $skip: Int!) {
            swaps(
                first: $first
                skip: $skip
                where: {
                    blockNumber_gte: $startBlock
                    blockNumber_lte: $endBlock
                }
                orderBy: blockNumber
                orderDirection: asc
            ) {
                id
                transaction
                timestamp
                blockNumber
                from
                to
                tokenIn
                tokenOut
                amountIn
                amountOut
                amountInUSD
                amountOutUSD
            }
        }
        """

        variables = {
            "startBlock": start_block,
            "endBlock": end_block or 999999999,
            "first": first,
            "skip": skip,
        }

        data = self._execute_query(query, variables)
        swaps = data.get("swaps", [])
        logger.info(f"Fetched {len(swaps)} swaps from block {start_block}")
        return swaps

    def get_latest_block(self) -> int:
        """
        Get the latest block number from the subgraph.

        Returns:
            Latest block number
        """
        query = """
        query GetLatestBlock {
            _meta {
                block {
                    number
                }
            }
        }
        """

        data = self._execute_query(query)
        block_number = data.get("_meta", {}).get("block", {}).get("number", 0)
        logger.info(f"Latest subgraph block: {block_number}")
        return block_number

    def get_token_info(self, token_address: str) -> Dict[str, Any]:
        """
        Get token information from the subgraph.

        Args:
            token_address: Token contract address

        Returns:
            Token information dictionary
        """
        query = """
        query GetToken($address: ID!) {
            token(id: $address) {
                id
                symbol
                name
                decimals
                totalSupply
                tradeVolume
                tradeVolumeUSD
            }
        }
        """

        variables = {"address": token_address.lower()}
        data = self._execute_query(query, variables)
        token = data.get("token", {})
        logger.debug(f"Fetched token info for {token_address}: {token.get('symbol')}")
        return token
