"""Entitlement exporter for SailPoint."""

from typing import Any, AsyncGenerator, Dict, Optional

from loguru import logger

from ..clients.sailpoint_client import SailPointClient
from ..models.sailpoint_entities import Entitlement, parse_entitlement
from .base_exporter import BaseExporter


class EntitlementExporter(BaseExporter):
    """Exporter for SailPoint Entitlement entities."""

    async def export_all(
        self,
        filters: Optional[Dict[str, Any]] = None,
        limit: int = 250,
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Export all entitlements.

        Args:
            filters: Optional filters for the query
            limit: Number of items per page

        Yields:
            Entitlement data dictionaries
        """
        entity_count = 0
        
        try:
            async for raw_entitlement in self.client.get_entitlements(filters=filters, limit=limit):
                try:
                    entitlement = parse_entitlement(raw_entitlement)
                    port_entity = self._map_entitlement_to_port(entitlement)
                    entity_count += 1
                    yield port_entity
                except Exception as e:
                    logger.error(f"Failed to parse entitlement {raw_entitlement.get('id', 'unknown')}: {e}")
                    continue

            await self._log_export_stats(entity_count, filters)
            
        except Exception as e:
            logger.error(f"Failed to export entitlements: {e}")
            raise

    async def export_single(self, entitlement_id: str) -> Optional[Dict[str, Any]]:
        """Export a single entitlement by ID.

        Args:
            entitlement_id: Entitlement identifier

        Returns:
            Entitlement data dictionary or None if not found
        """
        try:
            raw_entitlement = await self.client.get_single(f"/v3/entitlements/{entitlement_id}")
            entitlement = parse_entitlement(raw_entitlement)
            return self._map_entitlement_to_port(entitlement)
        except Exception as e:
            logger.error(f"Failed to export entitlement {entitlement_id}: {e}")
            return None

    def get_entity_kind(self) -> str:
        """Get the Port entity kind for entitlements.

        Returns:
            Entity kind string
        """
        return "entitlement"

    def _map_entitlement_to_port(self, entitlement: Entitlement) -> Dict[str, Any]:
        """Map a SailPoint entitlement to Port format.

        Args:
            entitlement: SailPoint entitlement

        Returns:
            Mapped entitlement data
        """
        return {
            "identifier": entitlement.id,
            "title": f"{entitlement.name} ({entitlement.attribute}={entitlement.value})",
            "blueprint": self.get_entity_kind(),
            "properties": {
                "name": entitlement.name,
                "attribute": entitlement.attribute,
                "value": entitlement.value,
                "schema": entitlement.schema_name,
                "sourceId": entitlement.source_id,
                "privileged": entitlement.privileged,
                "cloudGoverned": entitlement.cloud_governed,
                "created": entitlement.created.isoformat() if entitlement.created else None,
                "modified": entitlement.modified.isoformat() if entitlement.modified else None,
            },
            "relations": {
                "source": entitlement.source_id,
            },
            "raw_data": entitlement.raw_data,
        }
