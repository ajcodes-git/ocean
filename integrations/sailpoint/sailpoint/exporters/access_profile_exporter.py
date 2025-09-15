"""Access Profile exporter for SailPoint."""

from typing import Any, AsyncGenerator, Dict, Optional

from loguru import logger

from ..clients.sailpoint_client import SailPointClient
from ..models.sailpoint_entities import AccessProfile, parse_access_profile
from .base_exporter import BaseExporter


class AccessProfileExporter(BaseExporter):
    """Exporter for SailPoint Access Profile entities."""

    async def export_all(
        self,
        filters: Optional[Dict[str, Any]] = None,
        limit: int = 250,
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Export all access profiles.

        Args:
            filters: Optional filters for the query
            limit: Number of items per page

        Yields:
            Access Profile data dictionaries
        """
        entity_count = 0
        
        try:
            async for raw_profile in self.client.get_access_profiles(filters=filters, limit=limit):
                try:
                    profile = parse_access_profile(raw_profile)
                    port_entity = self._map_access_profile_to_port(profile)
                    entity_count += 1
                    yield port_entity
                except Exception as e:
                    logger.error(f"Failed to parse access profile {raw_profile.get('id', 'unknown')}: {e}")
                    continue

            await self._log_export_stats(entity_count, filters)
            
        except Exception as e:
            logger.error(f"Failed to export access profiles: {e}")
            raise

    async def export_single(self, profile_id: str) -> Optional[Dict[str, Any]]:
        """Export a single access profile by ID.

        Args:
            profile_id: Access Profile identifier

        Returns:
            Access Profile data dictionary or None if not found
        """
        try:
            raw_profile = await self.client.get_single(f"/v3/access-profiles/{profile_id}")
            profile = parse_access_profile(raw_profile)
            return self._map_access_profile_to_port(profile)
        except Exception as e:
            logger.error(f"Failed to export access profile {profile_id}: {e}")
            return None

    def get_entity_kind(self) -> str:
        """Get the Port entity kind for access profiles.

        Returns:
            Entity kind string
        """
        return "access-profile"

    def _map_access_profile_to_port(self, profile: AccessProfile) -> Dict[str, Any]:
        """Map a SailPoint access profile to Port format.

        Args:
            profile: SailPoint access profile

        Returns:
            Mapped access profile data
        """
        return {
            "identifier": profile.id,
            "title": profile.name,
            "blueprint": self.get_entity_kind(),
            "properties": {
                "name": profile.name,
                "description": profile.description,
                "sourceId": profile.source_id,
                "enabled": profile.enabled,
                "owner": profile.owner,
                "ownerId": profile.owner_id,
                "requestable": profile.requestable,
                "revocable": profile.revocable,
                "created": profile.created.isoformat() if profile.created else None,
                "modified": profile.modified.isoformat() if profile.modified else None,
            },
            "relations": {
                "source": profile.source_id,
                "owner": profile.owner_id,
            },
            "raw_data": profile.raw_data,
        }
