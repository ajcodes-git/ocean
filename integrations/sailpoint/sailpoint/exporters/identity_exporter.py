"""Identity exporter for SailPoint."""

from typing import Any, AsyncGenerator, Dict, Optional

from loguru import logger

from ..clients.sailpoint_client import SailPointClient
from ..models.sailpoint_entities import Identity, parse_identity
from .base_exporter import BaseExporter


class IdentityExporter(BaseExporter):
    """Exporter for SailPoint Identity entities."""

    async def export_all(
        self,
        filters: Optional[Dict[str, Any]] = None,
        limit: int = 250,
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Export all identities.

        Args:
            filters: Optional filters for the query
            limit: Number of items per page

        Yields:
            Identity data dictionaries
        """
        entity_count = 0
        
        try:
            async for raw_identity in self.client.get_identities(filters=filters, limit=limit):
                try:
                    identity = parse_identity(raw_identity)
                    port_entity = self._map_identity_to_port(identity)
                    entity_count += 1
                    yield port_entity
                except Exception as e:
                    logger.error(f"Failed to parse identity {raw_identity.get('id', 'unknown')}: {e}")
                    continue

            await self._log_export_stats(entity_count, filters)
            
        except Exception as e:
            logger.error(f"Failed to export identities: {e}")
            raise

    async def export_single(self, identity_id: str) -> Optional[Dict[str, Any]]:
        """Export a single identity by ID.

        Args:
            identity_id: Identity identifier

        Returns:
            Identity data dictionary or None if not found
        """
        try:
            raw_identity = await self.client.get_single(f"/v3/identities/{identity_id}")
            identity = parse_identity(raw_identity)
            return self._map_identity_to_port(identity)
        except Exception as e:
            logger.error(f"Failed to export identity {identity_id}: {e}")
            return None

    def get_entity_kind(self) -> str:
        """Get the Port entity kind for identities.

        Returns:
            Entity kind string
        """
        return "identity"

    def _map_identity_to_port(self, identity: Identity) -> Dict[str, Any]:
        """Map a SailPoint identity to Port format.

        Args:
            identity: SailPoint identity

        Returns:
            Mapped identity data
        """
        return {
            "identifier": identity.id,
            "title": identity.display_name or identity.name,
            "blueprint": self.get_entity_kind(),
            "properties": {
                "name": identity.name,
                "displayName": identity.display_name,
                "email": identity.email,
                "firstName": identity.first_name,
                "lastName": identity.last_name,
                "status": identity.status,
                "lifecycleState": identity.lifecycle_state,
                "manager": identity.manager,
                "department": identity.department,
                "jobTitle": identity.job_title,
                "employeeNumber": identity.employee_number,
                "phoneNumber": identity.phone_number,
                "isManager": identity.is_manager,
                "isProcessing": identity.is_processing,
                "created": identity.created.isoformat() if identity.created else None,
                "modified": identity.modified.isoformat() if identity.modified else None,
            },
            "relations": {
                "manager": identity.manager,
            },
            "raw_data": identity.raw_data,
        }
