"""Source exporter for SailPoint."""

from typing import Any, AsyncGenerator, Dict, Optional

from loguru import logger

from ..clients.sailpoint_client import SailPointClient
from ..models.sailpoint_entities import Source, parse_source
from .base_exporter import BaseExporter


class SourceExporter(BaseExporter):
    """Exporter for SailPoint Source entities."""

    async def export_all(
        self,
        filters: Optional[Dict[str, Any]] = None,
        limit: int = 250,
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Export all sources.

        Args:
            filters: Optional filters for the query
            limit: Number of items per page

        Yields:
            Source data dictionaries
        """
        entity_count = 0
        
        try:
            async for raw_source in self.client.get_sources(filters=filters, limit=limit):
                try:
                    source = parse_source(raw_source)
                    port_entity = self._map_source_to_port(source)
                    entity_count += 1
                    yield port_entity
                except Exception as e:
                    logger.error(f"Failed to parse source {raw_source.get('id', 'unknown')}: {e}")
                    continue

            await self._log_export_stats(entity_count, filters)
            
        except Exception as e:
            logger.error(f"Failed to export sources: {e}")
            raise

    async def export_single(self, source_id: str) -> Optional[Dict[str, Any]]:
        """Export a single source by ID.

        Args:
            source_id: Source identifier

        Returns:
            Source data dictionary or None if not found
        """
        try:
            raw_source = await self.client.get_single(f"/v3/sources/{source_id}")
            source = parse_source(raw_source)
            return self._map_source_to_port(source)
        except Exception as e:
            logger.error(f"Failed to export source {source_id}: {e}")
            return None

    def get_entity_kind(self) -> str:
        """Get the Port entity kind for sources.

        Returns:
            Entity kind string
        """
        return "source"

    def _map_source_to_port(self, source: Source) -> Dict[str, Any]:
        """Map a SailPoint source to Port format.

        Args:
            source: SailPoint source

        Returns:
            Mapped source data
        """
        return {
            "identifier": source.id,
            "title": source.name,
            "blueprint": self.get_entity_kind(),
            "properties": {
                "name": source.name,
                "description": source.description,
                "connector": source.connector,
                "connectorClass": source.connector_class,
                "connectorName": source.connector_name,
                "type": source.type,
                "category": source.category,
                "owner": source.owner,
                "ownerId": source.owner_id,
                "clusterId": source.cluster_id,
                "managementWorkgroup": source.management_workgroup,
                "healthy": source.healthy,
                "status": source.status,
                "since": source.since.isoformat() if source.since else None,
                "created": source.created.isoformat() if source.created else None,
                "modified": source.modified.isoformat() if source.modified else None,
            },
            "relations": {
                "owner": source.owner_id,
                "cluster": source.cluster_id,
            },
            "raw_data": source.raw_data,
        }
