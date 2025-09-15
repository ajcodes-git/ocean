"""Token management for SailPoint OAuth 2.0 authentication."""

import asyncio
import time
from typing import Optional

from loguru import logger
import httpx


class TokenManager:
    """Manages OAuth 2.0 tokens for SailPoint API authentication."""

    def __init__(
        self,
        http_client: httpx.AsyncClient,
        tenant_url: str,
        client_id: str,
        client_secret: str,
    ) -> None:
        """Initialize the token manager.

        Args:
            http_client: HTTP client for making requests
            tenant_url: SailPoint tenant URL (e.g., https://{tenant}.api.sailpoint.com)
            client_id: OAuth 2.0 client ID
            client_secret: OAuth 2.0 client secret
        """
        self.http_client = http_client
        self.tenant_url = tenant_url.rstrip("/")
        self.client_id = client_id
        self.client_secret = client_secret
        self._access_token: Optional[str] = None
        self._token_expires_at: Optional[float] = None
        self._lock = asyncio.Lock()

    async def get_access_token(self) -> str:
        """Get a valid access token, refreshing if necessary.

        Returns:
            Valid access token

        Raises:
            Exception: If token acquisition fails
        """
        async with self._lock:
            if self._is_token_valid():
                logger.debug("Using cached access token")
                return self._access_token

            logger.info("Acquiring new access token from SailPoint")
            await self._acquire_token()

            if not self._access_token:
                raise Exception("Failed to acquire access token")

            return self._access_token

    def _is_token_valid(self) -> bool:
        """Check if the current token is still valid.

        Returns:
            True if token is valid, False otherwise
        """
        if not self._access_token or not self._token_expires_at:
            return False

        # Add 60 second buffer to avoid edge cases
        return time.time() < (self._token_expires_at - 60)

    async def _acquire_token(self) -> None:
        """Acquire a new access token from SailPoint."""
        auth_url = f"{self.tenant_url}/oauth/token"
        
        data = {
            "grant_type": "client_credentials",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
        }

        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "application/json",
        }

        try:
            response = await self.http_client.post(
                auth_url,
                data=data,
                headers=headers,
            )
            response.raise_for_status()

            token_data = response.json()
            self._access_token = token_data["access_token"]
            
            # Calculate expiration time
            expires_in = token_data.get("expires_in", 3600)  # Default to 1 hour
            self._token_expires_at = time.time() + expires_in

            logger.info(
                f"Successfully acquired access token, expires in {expires_in} seconds"
            )

        except Exception as e:
            logger.error(f"Failed to acquire access token: {e}")
            raise

    async def refresh_token_if_needed(self, response_status: int) -> bool:
        """Refresh token if the response indicates authentication failure.

        Args:
            response_status: HTTP response status code

        Returns:
            True if token was refreshed, False otherwise
        """
        if response_status in (401, 403):
            logger.warning("Authentication failed, refreshing token")
            await self._acquire_token()
            return True
        return False
