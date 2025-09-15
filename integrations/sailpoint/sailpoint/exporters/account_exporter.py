"""Account exporter for SailPoint."""

from typing import Any, AsyncGenerator, Dict, Optional

from loguru import logger

from ..clients.sailpoint_client import SailPointClient
from ..models.sailpoint_entities import Account, parse_account
from .base_exporter import BaseExporter


class AccountExporter(BaseExporter):
    """Exporter for SailPoint Account entities."""

    async def export_all(
        self,
        filters: Optional[Dict[str, Any]] = None,
        limit: int = 250,
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Export all accounts.

        Args:
            filters: Optional filters for the query
            limit: Number of items per page

        Yields:
            Account data dictionaries
        """
        entity_count = 0
        
        try:
            async for raw_account in self.client.get_accounts(filters=filters, limit=limit):
                try:
                    account = parse_account(raw_account)
                    port_entity = self._map_account_to_port(account)
                    entity_count += 1
                    yield port_entity
                except Exception as e:
                    logger.error(f"Failed to parse account {raw_account.get('id', 'unknown')}: {e}")
                    continue

            await self._log_export_stats(entity_count, filters)
            
        except Exception as e:
            logger.error(f"Failed to export accounts: {e}")
            raise

    async def export_single(self, account_id: str) -> Optional[Dict[str, Any]]:
        """Export a single account by ID.

        Args:
            account_id: Account identifier

        Returns:
            Account data dictionary or None if not found
        """
        try:
            raw_account = await self.client.get_single(f"/v3/accounts/{account_id}")
            account = parse_account(raw_account)
            return self._map_account_to_port(account)
        except Exception as e:
            logger.error(f"Failed to export account {account_id}: {e}")
            return None

    def get_entity_kind(self) -> str:
        """Get the Port entity kind for accounts.

        Returns:
            Entity kind string
        """
        return "account"

    def _map_account_to_port(self, account: Account) -> Dict[str, Any]:
        """Map a SailPoint account to Port format.

        Args:
            account: SailPoint account

        Returns:
            Mapped account data
        """
        return {
            "identifier": account.id,
            "title": f"{account.name} ({account.native_identity})",
            "blueprint": self.get_entity_kind(),
            "properties": {
                "name": account.name,
                "nativeIdentity": account.native_identity,
                "sourceId": account.source_id,
                "identityId": account.identity_id,
                "uuid": account.uuid,
                "disabled": account.disabled,
                "locked": account.locked,
                "privileged": account.privileged,
                "systemAccount": account.system_account,
                "uncorrelated": account.uncorrelated,
                "created": account.created.isoformat() if account.created else None,
                "modified": account.modified.isoformat() if account.modified else None,
            },
            "relations": {
                "identity": account.identity_id,
                "source": account.source_id,
            },
            "raw_data": account.raw_data,
        }
