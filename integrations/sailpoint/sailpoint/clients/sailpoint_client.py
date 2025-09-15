"""SailPoint API client with rate limiting, retries, and pagination."""

import asyncio
import time
from typing import Any, AsyncGenerator, Dict, List, Optional

from loguru import logger
import httpx

from ..clients.token_manager import TokenManager


class SailPointClient:
    """SailPoint API client with built-in rate limiting and retry logic."""

    def __init__(
        self,
        http_client: httpx.AsyncClient,
        token_manager: TokenManager,
        max_retries: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 60.0,
        backoff_factor: float = 2.0,
        max_concurrent_requests: int = 10,
    ) -> None:
        """Initialize the SailPoint client.

        Args:
            http_client: HTTP client for making requests
            token_manager: Token manager for authentication
            max_retries: Maximum number of retry attempts
            base_delay: Base delay for exponential backoff
            max_delay: Maximum delay between retries
            backoff_factor: Multiplier for exponential backoff
            max_concurrent_requests: Maximum concurrent requests
        """
        self.http_client = http_client
        self.token_manager = token_manager
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.backoff_factor = backoff_factor
        self.max_concurrent_requests = max_concurrent_requests
        self._semaphore = asyncio.Semaphore(max_concurrent_requests)

    async def _make_request(
        self,
        method: str,
        url: str,
        headers: Optional[Dict[str, str]] = None,
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Any] = None,
        json: Optional[Dict[str, Any]] = None,
    ) -> Any:
        """Make an HTTP request with retry logic and rate limiting.

        Args:
            method: HTTP method
            url: Request URL
            headers: Request headers
            params: Query parameters
            data: Request data
            json: JSON data

        Returns:
            Response object

        Raises:
            Exception: If all retry attempts fail
        """
        async with self._semaphore:
            for attempt in range(self.max_retries + 1):
                try:
                    # Get fresh token for each request
                    access_token = await self.token_manager.get_access_token()
                    
                    request_headers = {
                        "Authorization": f"Bearer {access_token}",
                        "Accept": "application/json",
                        "Content-Type": "application/json",
                        **(headers or {}),
                    }

                    logger.debug(f"Making {method} request to {url} (attempt {attempt + 1})")
                    
                    response = await self.http_client.request(
                        method=method,
                        url=url,
                        headers=request_headers,
                        params=params,
                        data=data,
                        json=json,
                    )

                    # Check if we need to refresh token
                    if await self.token_manager.refresh_token_if_needed(response.status_code):
                        if attempt < self.max_retries:
                            logger.info("Token refreshed, retrying request")
                            continue

                    # Handle rate limiting
                    if response.status_code == 429:
                        retry_after = self._get_retry_after(response)
                        if attempt < self.max_retries:
                            logger.warning(f"Rate limited, waiting {retry_after} seconds")
                            await asyncio.sleep(retry_after)
                            continue

                    response.raise_for_status()
                    return response

                except Exception as e:
                    if attempt < self.max_retries:
                        delay = min(
                            self.base_delay * (self.backoff_factor ** attempt),
                            self.max_delay,
                        )
                        logger.warning(f"Request failed (attempt {attempt + 1}): {e}, retrying in {delay}s")
                        await asyncio.sleep(delay)
                    else:
                        logger.error(f"Request failed after {self.max_retries + 1} attempts: {e}")
                        raise

    def _get_retry_after(self, response: Any) -> float:
        """Extract retry-after header value.

        Args:
            response: HTTP response

        Returns:
            Retry delay in seconds
        """
        retry_after = response.headers.get("Retry-After")
        if retry_after:
            try:
                return float(retry_after)
            except ValueError:
                pass
        return self.base_delay

    async def get_paginated(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        limit: int = 250,
        offset: int = 0,
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Get paginated data from a SailPoint endpoint.

        Args:
            endpoint: API endpoint path
            params: Query parameters
            limit: Number of items per page
            offset: Starting offset

        Yields:
            Individual items from the paginated response
        """
        current_offset = offset
        params = params or {}

        while True:
            page_params = {
                **params,
                "limit": limit,
                "offset": current_offset,
            }

            response = await self._make_request(
                "GET",
                f"{self.token_manager.tenant_url}{endpoint}",
                params=page_params,
            )

            data = response.json()
            items = data.get("items", [])

            if not items:
                logger.debug(f"No more items found at offset {current_offset}")
                break

            logger.debug(f"Retrieved {len(items)} items at offset {current_offset}")
            
            for item in items:
                yield item

            # Check if we've reached the end
            if len(items) < limit:
                logger.debug("Reached end of pagination")
                break

            current_offset += limit

    async def get_single(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Get a single item from a SailPoint endpoint.

        Args:
            endpoint: API endpoint path
            params: Query parameters

        Returns:
            Response data
        """
        response = await self._make_request(
            "GET",
            f"{self.token_manager.tenant_url}{endpoint}",
            params=params,
        )
        return response.json()

    async def get_identities(
        self,
        filters: Optional[Dict[str, Any]] = None,
        limit: int = 250,
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Get identities from SailPoint.

        Args:
            filters: Optional filters for the query
            limit: Number of items per page

        Yields:
            Identity objects
        """
        async for identity in self.get_paginated(
            "/v3/identities",
            params=filters,
            limit=limit,
        ):
            yield identity

    async def get_accounts(
        self,
        filters: Optional[Dict[str, Any]] = None,
        limit: int = 250,
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Get accounts from SailPoint.

        Args:
            filters: Optional filters for the query
            limit: Number of items per page

        Yields:
            Account objects
        """
        async for account in self.get_paginated(
            "/v3/accounts",
            params=filters,
            limit=limit,
        ):
            yield account

    async def get_entitlements(
        self,
        filters: Optional[Dict[str, Any]] = None,
        limit: int = 250,
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Get entitlements from SailPoint.

        Args:
            filters: Optional filters for the query
            limit: Number of items per page

        Yields:
            Entitlement objects
        """
        async for entitlement in self.get_paginated(
            "/v3/entitlements",
            params=filters,
            limit=limit,
        ):
            yield entitlement

    async def get_access_profiles(
        self,
        filters: Optional[Dict[str, Any]] = None,
        limit: int = 250,
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Get access profiles from SailPoint.

        Args:
            filters: Optional filters for the query
            limit: Number of items per page

        Yields:
            Access profile objects
        """
        async for profile in self.get_paginated(
            "/v3/access-profiles",
            params=filters,
            limit=limit,
        ):
            yield profile

    async def get_roles(
        self,
        filters: Optional[Dict[str, Any]] = None,
        limit: int = 250,
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Get roles from SailPoint.

        Args:
            filters: Optional filters for the query
            limit: Number of items per page

        Yields:
            Role objects
        """
        async for role in self.get_paginated(
            "/v3/roles",
            params=filters,
            limit=limit,
        ):
            yield role

    async def get_sources(
        self,
        filters: Optional[Dict[str, Any]] = None,
        limit: int = 250,
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Get sources from SailPoint.

        Args:
            filters: Optional filters for the query
            limit: Number of items per page

        Yields:
            Source objects
        """
        async for source in self.get_paginated(
            "/v3/sources",
            params=filters,
            limit=limit,
        ):
            yield source
