"""Generic exporter for configurable SailPoint resources."""

from typing import Any, AsyncGenerator, Dict, Optional

from loguru import logger

from ..clients.sailpoint_client import SailPointClient
from .base_exporter import BaseExporter


class GenericExporter(BaseExporter):
    """Generic exporter for any SailPoint resource type."""

    def __init__(
        self,
        client: SailPointClient,
        resource_kind: str,
        api_endpoint: str,
        port_blueprint: str,
    ) -> None:
        """Initialize the generic exporter.

        Args:
            client: SailPoint API client
            resource_kind: Port entity kind
            api_endpoint: SailPoint API endpoint path
            port_blueprint: Port blueprint identifier
        """
        super().__init__(client)
        self.resource_kind = resource_kind
        self.api_endpoint = api_endpoint
        self.port_blueprint = port_blueprint

    async def export_all(
        self,
        filters: Optional[Dict[str, Any]] = None,
        limit: int = 250,
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Export all entities of this resource type.

        Args:
            filters: Optional filters for the query
            limit: Number of items per page

        Yields:
            Entity data dictionaries
        """
        entity_count = 0
        
        try:
            async for raw_entity in self.client.get_paginated(
                self.api_endpoint,
                params=filters,
                limit=limit,
            ):
                try:
                    port_entity = self._map_generic_entity_to_port(raw_entity)
                    entity_count += 1
                    yield port_entity
                except Exception as e:
                    logger.error(f"Failed to parse {self.resource_kind} {raw_entity.get('id', 'unknown')}: {e}")
                    continue

            await self._log_export_stats(entity_count, filters)
            
        except Exception as e:
            logger.error(f"Failed to export {self.resource_kind}s: {e}")
            raise

    async def export_single(self, entity_id: str) -> Optional[Dict[str, Any]]:
        """Export a single entity by ID.

        Args:
            entity_id: Entity identifier

        Returns:
            Entity data dictionary or None if not found
        """
        try:
            raw_entity = await self.client.get_single(f"{self.api_endpoint}/{entity_id}")
            return self._map_generic_entity_to_port(raw_entity)
        except Exception as e:
            logger.error(f"Failed to export {self.resource_kind} {entity_id}: {e}")
            return None

    def get_entity_kind(self) -> str:
        """Get the Port entity kind for this exporter.

        Returns:
            Entity kind string
        """
        return self.resource_kind

    def _map_generic_entity_to_port(self, raw_entity: Dict[str, Any]) -> Dict[str, Any]:
        """Map a generic SailPoint entity to Port format.

        Args:
            raw_entity: Raw entity data from SailPoint API

        Returns:
            Mapped entity data
        """
        # Extract common fields
        entity_id = raw_entity.get("id", "")
        entity_name = raw_entity.get("name", "")
        
        # Create a generic title
        title = entity_name or entity_id
        
        # Extract common properties
        properties = {
            "name": entity_name,
            "id": entity_id,
        }
        
        # Add any additional properties from the raw data
        for key, value in raw_entity.items():
            if key not in ["id", "name", "raw_data"] and value is not None:
                # Convert camelCase to camelCase for Port
                properties[key] = value

        # Extract common relations
        relations = {}
        if "sourceId" in raw_entity:
            relations["source"] = raw_entity["sourceId"]
        if "ownerId" in raw_entity:
            relations["owner"] = raw_entity["ownerId"]
        if "identityId" in raw_entity:
            relations["identity"] = raw_entity["identityId"]

        return {
            "identifier": entity_id,
            "title": title,
            "blueprint": self.port_blueprint,
            "properties": properties,
            "relations": relations,
            "raw_data": raw_entity,
        }
