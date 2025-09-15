"""Base exporter for SailPoint entities."""

from abc import ABC, abstractmethod
from typing import Any, AsyncGenerator, Dict, List, Optional

from loguru import logger

from ..clients.sailpoint_client import SailPointClient
from ..models.sailpoint_entities import SailPointEntity


class BaseExporter(ABC):
    """Base class for SailPoint entity exporters."""

    def __init__(self, client: SailPointClient) -> None:
        """Initialize the exporter.

        Args:
            client: SailPoint API client
        """
        self.client = client

    @abstractmethod
    async def export_all(
        self,
        filters: Optional[Dict[str, Any]] = None,
        limit: int = 250,
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Export all entities of this type.

        Args:
            filters: Optional filters for the query
            limit: Number of items per page

        Yields:
            Entity data dictionaries
        """
        pass

    @abstractmethod
    async def export_single(self, entity_id: str) -> Optional[Dict[str, Any]]:
        """Export a single entity by ID.

        Args:
            entity_id: Entity identifier

        Returns:
            Entity data dictionary or None if not found
        """
        pass

    @abstractmethod
    def get_entity_kind(self) -> str:
        """Get the Port entity kind for this exporter.

        Returns:
            Entity kind string
        """
        pass

    def _map_entity_to_port(self, entity: SailPointEntity) -> Dict[str, Any]:
        """Map a SailPoint entity to Port format.

        Args:
            entity: SailPoint entity

        Returns:
            Mapped entity data
        """
        return {
            "identifier": entity.id,
            "title": entity.name,
            "blueprint": self.get_entity_kind(),
            "properties": self._get_entity_properties(entity),
            "relations": self._get_entity_relations(entity),
            "raw_data": entity.raw_data,
        }

    def _get_entity_properties(self, entity: SailPointEntity) -> Dict[str, Any]:
        """Get Port properties for an entity.

        Args:
            entity: SailPoint entity

        Returns:
            Properties dictionary
        """
        return {
            "name": entity.name,
            "created": entity.created.isoformat() if entity.created else None,
            "modified": entity.modified.isoformat() if entity.modified else None,
        }

    def _get_entity_relations(self, entity: SailPointEntity) -> Dict[str, Any]:
        """Get Port relations for an entity.

        Args:
            entity: SailPoint entity

        Returns:
            Relations dictionary
        """
        return {}

    def _apply_filters(
        self,
        filters: Optional[Dict[str, Any]],
        default_filters: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Apply filters to query parameters.

        Args:
            filters: User-provided filters
            default_filters: Default filters to apply

        Returns:
            Combined filters
        """
        combined_filters = default_filters or {}
        if filters:
            combined_filters.update(filters)
        return combined_filters

    async def _log_export_stats(
        self,
        entity_count: int,
        filters: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Log export statistics.

        Args:
            entity_count: Number of entities exported
            filters: Applied filters
        """
        filter_str = f" with filters {filters}" if filters else ""
        logger.info(
            f"Exported {entity_count} {self.get_entity_kind()} entities{filter_str}"
        )
