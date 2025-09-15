"""Role exporter for SailPoint."""

from typing import Any, AsyncGenerator, Dict, Optional

from loguru import logger

from ..clients.sailpoint_client import SailPointClient
from ..models.sailpoint_entities import Role, parse_role
from .base_exporter import BaseExporter


class RoleExporter(BaseExporter):
    """Exporter for SailPoint Role entities."""

    async def export_all(
        self,
        filters: Optional[Dict[str, Any]] = None,
        limit: int = 250,
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Export all roles.

        Args:
            filters: Optional filters for the query
            limit: Number of items per page

        Yields:
            Role data dictionaries
        """
        entity_count = 0
        
        try:
            async for raw_role in self.client.get_roles(filters=filters, limit=limit):
                try:
                    role = parse_role(raw_role)
                    port_entity = self._map_role_to_port(role)
                    entity_count += 1
                    yield port_entity
                except Exception as e:
                    logger.error(f"Failed to parse role {raw_role.get('id', 'unknown')}: {e}")
                    continue

            await self._log_export_stats(entity_count, filters)
            
        except Exception as e:
            logger.error(f"Failed to export roles: {e}")
            raise

    async def export_single(self, role_id: str) -> Optional[Dict[str, Any]]:
        """Export a single role by ID.

        Args:
            role_id: Role identifier

        Returns:
            Role data dictionary or None if not found
        """
        try:
            raw_role = await self.client.get_single(f"/v3/roles/{role_id}")
            role = parse_role(raw_role)
            return self._map_role_to_port(role)
        except Exception as e:
            logger.error(f"Failed to export role {role_id}: {e}")
            return None

    def get_entity_kind(self) -> str:
        """Get the Port entity kind for roles.

        Returns:
            Entity kind string
        """
        return "role"

    def _map_role_to_port(self, role: Role) -> Dict[str, Any]:
        """Map a SailPoint role to Port format.

        Args:
            role: SailPoint role

        Returns:
            Mapped role data
        """
        return {
            "identifier": role.id,
            "title": role.name,
            "blueprint": self.get_entity_kind(),
            "properties": {
                "name": role.name,
                "description": role.description,
                "enabled": role.enabled,
                "owner": role.owner,
                "ownerId": role.owner_id,
                "requestable": role.requestable,
                "revocable": role.revocable,
                "created": role.created.isoformat() if role.created else None,
                "modified": role.modified.isoformat() if role.modified else None,
            },
            "relations": {
                "owner": role.owner_id,
            },
            "raw_data": role.raw_data,
        }
