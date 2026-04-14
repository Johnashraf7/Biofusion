"""
BioFusion AI — Base HTTP Client
Shared async HTTP client with retry logic, rate limiting, and error handling.
"""

import asyncio
import logging
import time
from typing import Any, Dict, List, Optional, Union

import httpx

from config import (
    HTTP_TIMEOUT,
    HTTP_MAX_CONNECTIONS,
    HTTP_MAX_RETRIES,
    HTTP_RETRY_BASE_DELAY,
    RATE_LIMITS,
)

logger = logging.getLogger("biofusion.http")


class RateLimiter:
    """
    Per-service rate limiter.
    Ensures minimum delay between consecutive requests to the same service.
    """

    def __init__(self):
        self._last_call: Dict[str, float] = {}
        self._locks: Dict[str, asyncio.Lock] = {}

    def _get_lock(self, service: str) -> asyncio.Lock:
        if service not in self._locks:
            self._locks[service] = asyncio.Lock()
        return self._locks[service]

    async def acquire(self, service: str) -> None:
        """Wait until the rate limit window has passed for this service."""
        lock = self._get_lock(service)
        async with lock:
            min_delay = RATE_LIMITS.get(service, RATE_LIMITS["default"])
            last = self._last_call.get(service, 0)
            elapsed = time.time() - last
            if elapsed < min_delay:
                wait_time = min_delay - elapsed
                logger.debug("Rate limit: waiting %.3fs for %s", wait_time, service)
                await asyncio.sleep(wait_time)
            self._last_call[service] = time.time()


class BaseClient:
    """
    Async HTTP client with retry, rate limiting, and connection pooling.

    Usage:
        client = BaseClient()
        await client.start()
        data = await client.fetch_json("uniprot", "https://rest.uniprot.org/...", params={})
        await client.stop()
    """

    def __init__(self):
        self._client: Optional[httpx.AsyncClient] = None
        self._rate_limiter = RateLimiter()

    async def start(self) -> None:
        """Start the HTTP client with connection pooling."""
        limits = httpx.Limits(
            max_connections=HTTP_MAX_CONNECTIONS,
            max_keepalive_connections=HTTP_MAX_CONNECTIONS,
        )
        self._client = httpx.AsyncClient(
            limits=limits,
            timeout=httpx.Timeout(HTTP_TIMEOUT),
            follow_redirects=True,
            headers={
                "User-Agent": "BioFusion-AI/1.0 (bioinformatics-platform)",
                "Accept": "application/json",
            },
        )
        logger.info("HTTP client started")

    async def stop(self) -> None:
        """Shutdown the HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None
            logger.info("HTTP client stopped")

    @property
    def client(self) -> httpx.AsyncClient:
        if self._client is None:
            raise RuntimeError("HTTP client not started. Call start() first.")
        return self._client

    async def fetch_json(
        self,
        service: str,
        url: str,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        max_retries: int = HTTP_MAX_RETRIES,
    ) -> Optional[Union[Dict, List]]:
        """
        Fetch JSON from a URL with rate limiting and retry logic.

        Args:
            service: Service name for rate limiting (e.g., "uniprot", "kegg")
            url: Full URL to fetch
            params: Optional query parameters
            headers: Optional additional headers
            max_retries: Max number of retries on failure

        Returns:
            Parsed JSON data, or None on complete failure
        """
        last_error: Optional[Exception] = None

        for attempt in range(max_retries + 1):
            try:
                # Enforce rate limit
                await self._rate_limiter.acquire(service)

                response = await self.client.get(url, params=params, headers=headers)

                if response.status_code == 429:
                    # Rate limited — back off
                    retry_after = int(response.headers.get("Retry-After", "5"))
                    logger.warning("Rate limited by %s, waiting %ds", service, retry_after)
                    await asyncio.sleep(retry_after)
                    continue

                response.raise_for_status()

                # Some APIs return empty bodies on success
                if not response.content:
                    return {}

                return response.json()

            except httpx.HTTPStatusError as e:
                last_error = e
                logger.warning(
                    "HTTP %d from %s (attempt %d/%d): %s",
                    e.response.status_code, service, attempt + 1, max_retries + 1, url,
                )
            except httpx.TimeoutException as e:
                last_error = e
                logger.warning(
                    "Timeout from %s (attempt %d/%d): %s",
                    service, attempt + 1, max_retries + 1, url,
                )
            except (httpx.RequestError, Exception) as e:
                last_error = e
                logger.warning(
                    "Request error from %s (attempt %d/%d): %s",
                    service, attempt + 1, max_retries + 1, e,
                )

            # Exponential backoff
            if attempt < max_retries:
                delay = HTTP_RETRY_BASE_DELAY * (2 ** attempt)
                logger.debug("Retrying %s in %ss...", service, delay)
                await asyncio.sleep(delay)

        logger.error("All retries exhausted for %s: %s — %s", service, url, last_error)
        return None

    async def fetch_text(
        self,
        service: str,
        url: str,
        params: Optional[Dict[str, Any]] = None,
        max_retries: int = HTTP_MAX_RETRIES,
    ) -> Optional[str]:
        """
        Fetch plain text from a URL (for APIs like KEGG that return text).

        Returns:
            Response text, or None on complete failure
        """
        last_error: Optional[Exception] = None

        for attempt in range(max_retries + 1):
            try:
                await self._rate_limiter.acquire(service)
                response = await self.client.get(url, params=params)
                response.raise_for_status()
                return response.text

            except (httpx.HTTPStatusError, httpx.TimeoutException, httpx.RequestError) as e:
                last_error = e
                logger.warning(
                    "Text fetch error from %s (attempt %d/%d): %s",
                    service, attempt + 1, max_retries + 1, e,
                )

            if attempt < max_retries:
                delay = HTTP_RETRY_BASE_DELAY * (2 ** attempt)
                await asyncio.sleep(delay)

        logger.error("All retries exhausted for text fetch %s: %s — %s", service, url, last_error)
        return None

    async def fetch_graphql(
        self,
        service: str,
        url: str,
        query: str,
        variables: Optional[Dict[str, Any]] = None,
        max_retries: int = HTTP_MAX_RETRIES,
    ) -> Optional[Dict]:
        """
        Execute a GraphQL query (for Open Targets).

        Args:
            service: Service name for rate limiting
            url: GraphQL endpoint URL
            query: GraphQL query string
            variables: Optional query variables

        Returns:
            The 'data' field from the GraphQL response, or None on failure
        """
        payload: Dict[str, Any] = {"query": query}
        if variables:
            payload["variables"] = variables

        last_error: Optional[Exception] = None

        for attempt in range(max_retries + 1):
            try:
                await self._rate_limiter.acquire(service)

                response = await self.client.post(
                    url,
                    json=payload,
                    headers={"Content-Type": "application/json"},
                )
                response.raise_for_status()
                result = response.json()

                if "errors" in result:
                    logger.warning("GraphQL errors from %s: %s", service, result["errors"])

                return result.get("data")

            except (httpx.HTTPStatusError, httpx.TimeoutException, httpx.RequestError) as e:
                last_error = e
                logger.warning(
                    "GraphQL error from %s (attempt %d/%d): %s",
                    service, attempt + 1, max_retries + 1, e,
                )

            if attempt < max_retries:
                delay = HTTP_RETRY_BASE_DELAY * (2 ** attempt)
                await asyncio.sleep(delay)

        logger.error("All retries exhausted for GraphQL %s: %s — %s", service, url, last_error)
        return None


# ─── Singleton ─────────────────────────────────────────────────────────────────

http_client = BaseClient()
