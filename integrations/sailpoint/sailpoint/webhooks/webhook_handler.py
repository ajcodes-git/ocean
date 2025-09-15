"""Webhook handler for SailPoint real-time events."""

import hashlib
import hmac
import json
from typing import Any, Dict, List, Optional

from fastapi import HTTPException, Request
from loguru import logger
from port_ocean.core.handlers.webhook.abstract_webhook_processor import AbstractWebhookProcessor
from port_ocean.core.handlers.webhook.webhook_event import WebhookEvent, EventPayload

from ..clients.sailpoint_client import SailPointClient
from ..exporters.access_profile_exporter import AccessProfileExporter
from ..exporters.account_exporter import AccountExporter
from ..exporters.entitlement_exporter import EntitlementExporter
from ..exporters.identity_exporter import IdentityExporter
from ..exporters.role_exporter import RoleExporter
from ..exporters.source_exporter import SourceExporter


class WebhookHandler(AbstractWebhookProcessor):
    """Handles SailPoint webhook events with HMAC signature verification."""

    def __init__(self, client: SailPointClient, webhook_secret: Optional[str] = None) -> None:
        """Initialize the webhook handler.

        Args:
            client: SailPoint API client
            webhook_secret: Secret for HMAC signature verification
        """
        self.client = client
        self.webhook_secret = webhook_secret
        
        # Initialize exporters
        self.exporters = {
            "identity": IdentityExporter(client),
            "account": AccountExporter(client),
            "entitlement": EntitlementExporter(client),
            "access-profile": AccessProfileExporter(client),
            "role": RoleExporter(client),
            "source": SourceExporter(client),
        }

    def verify_signature(self, payload: bytes, signature: str) -> bool:
        """Verify HMAC signature of the webhook payload.

        Args:
            payload: Raw webhook payload
            signature: HMAC signature from headers

        Returns:
            True if signature is valid, False otherwise
        """
        if not self.webhook_secret:
            logger.warning("No webhook secret configured, skipping signature verification")
            return True

        try:
            # Remove 'sha256=' prefix if present
            if signature.startswith("sha256="):
                signature = signature[7:]

            # Calculate expected signature
            expected_signature = hmac.new(
                self.webhook_secret.encode("utf-8"),
                payload,
                hashlib.sha256,
            ).hexdigest()

            # Compare signatures using constant-time comparison
            return hmac.compare_digest(signature, expected_signature)

        except Exception as e:
            logger.error(f"Error verifying webhook signature: {e}")
            return False

    async def handle_webhook(self, request: Request) -> Dict[str, Any]:
        """Handle incoming webhook request.

        Args:
            request: FastAPI request object

        Returns:
            Response dictionary

        Raises:
            HTTPException: If webhook processing fails
        """
        try:
            # Get raw payload
            payload = await request.body()
            
            # Verify signature if secret is configured
            signature = request.headers.get("X-SailPoint-Signature", "")
            if not self.verify_signature(payload, signature):
                logger.warning("Invalid webhook signature")
                raise HTTPException(status_code=401, detail="Invalid signature")

            # Parse webhook data
            webhook_data = json.loads(payload.decode("utf-8"))
            logger.info(f"Received webhook: {webhook_data.get('type', 'unknown')}")

            # Process webhook event
            result = await self._process_webhook_event(webhook_data)
            
            return {
                "status": "success",
                "processed_entities": result.get("processed_entities", 0),
                "message": f"Processed {webhook_data.get('type', 'unknown')} event",
            }

        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in webhook payload: {e}")
            raise HTTPException(status_code=400, detail="Invalid JSON payload")
        except Exception as e:
            logger.error(f"Error processing webhook: {e}")
            raise HTTPException(status_code=500, detail="Internal server error")

    async def _process_webhook_event(self, webhook_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process a webhook event and fetch impacted resources.

        Args:
            webhook_data: Parsed webhook data

        Returns:
            Processing result
        """
        event_type = webhook_data.get("type", "")
        processed_entities = 0

        try:
            # Map event types to entity kinds and actions
            entity_mapping = self._get_entity_mapping_for_event(event_type)
            
            if not entity_mapping:
                logger.warning(f"No entity mapping found for event type: {event_type}")
                return {"processed_entities": 0}

            entity_kind = entity_mapping["kind"]
            entity_id = webhook_data.get("entityId") or webhook_data.get("id")
            
            if not entity_id:
                logger.warning(f"No entity ID found in webhook data for event: {event_type}")
                return {"processed_entities": 0}

            # Get the appropriate exporter
            exporter = self.exporters.get(entity_kind)
            if not exporter:
                logger.warning(f"No exporter found for entity kind: {entity_kind}")
                return {"processed_entities": 0}

            # Fetch and process the specific entity
            entity_data = await exporter.export_single(entity_id)
            if entity_data:
                # Here you would typically send the entity to Port
                # For now, we'll just log the success
                logger.info(f"Successfully processed {entity_kind} entity: {entity_id}")
                processed_entities = 1
            else:
                logger.warning(f"Failed to fetch {entity_kind} entity: {entity_id}")

        except Exception as e:
            logger.error(f"Error processing webhook event: {e}")

        return {"processed_entities": processed_entities}

    def _get_entity_mapping_for_event(self, event_type: str) -> Optional[Dict[str, str]]:
        """Get entity mapping for a given event type.

        Args:
            event_type: SailPoint event type

        Returns:
            Entity mapping or None if not found
        """
        # Map common SailPoint event types to entity kinds
        event_mappings = {
            "IDENTITY_CREATED": {"kind": "identity", "action": "create"},
            "IDENTITY_UPDATED": {"kind": "identity", "action": "update"},
            "IDENTITY_DELETED": {"kind": "identity", "action": "delete"},
            "ACCOUNT_CREATED": {"kind": "account", "action": "create"},
            "ACCOUNT_UPDATED": {"kind": "account", "action": "update"},
            "ACCOUNT_DELETED": {"kind": "account", "action": "delete"},
            "ENTITLEMENT_CREATED": {"kind": "entitlement", "action": "create"},
            "ENTITLEMENT_UPDATED": {"kind": "entitlement", "action": "update"},
            "ENTITLEMENT_DELETED": {"kind": "entitlement", "action": "delete"},
            "ACCESS_PROFILE_CREATED": {"kind": "access-profile", "action": "create"},
            "ACCESS_PROFILE_UPDATED": {"kind": "access-profile", "action": "update"},
            "ACCESS_PROFILE_DELETED": {"kind": "access-profile", "action": "delete"},
            "ROLE_CREATED": {"kind": "role", "action": "create"},
            "ROLE_UPDATED": {"kind": "role", "action": "update"},
            "ROLE_DELETED": {"kind": "role", "action": "delete"},
            "SOURCE_CREATED": {"kind": "source", "action": "create"},
            "SOURCE_UPDATED": {"kind": "source", "action": "update"},
            "SOURCE_DELETED": {"kind": "source", "action": "delete"},
        }

        return event_mappings.get(event_type)

    async def _validate_payload(self, payload: EventPayload) -> bool:
        """Validate the webhook payload.
        
        Args:
            payload: The webhook event payload
            
        Returns:
            True if payload is valid, False otherwise
        """
        try:
            # Check if payload has required fields
            if not isinstance(payload, dict):
                return False
                
            # Check for SailPoint event structure
            event_type = payload.get("eventType")
            if not event_type:
                return False
                
            # Check if we support this event type
            event_mapping = self._get_event_mapping(event_type)
            if not event_mapping:
                logger.warning(f"Unsupported event type: {event_type}")
                return False
                
            return True
        except Exception as e:
            logger.error(f"Payload validation failed: {e}")
            return False

    async def _process_webhook_event(self, event: WebhookEvent) -> None:
        """Process the webhook event.
        
        Args:
            event: The webhook event to process
        """
        try:
            payload = event.payload
            event_type = payload.get("eventType")
            
            logger.info(f"Processing SailPoint webhook event: {event_type}")
            
            # Get event mapping
            event_mapping = self._get_event_mapping(event_type)
            if not event_mapping:
                logger.warning(f"No mapping found for event type: {event_type}")
                return
                
            kind = event_mapping["kind"]
            action = event_mapping["action"]
            
            # Get the appropriate exporter
            exporter = self._get_exporter_for_kind(kind)
            if not exporter:
                logger.warning(f"No exporter found for kind: {kind}")
                return
                
            # Process the event based on action
            if action == "delete":
                # For delete events, we need to identify the entity
                entity_id = payload.get("id") or payload.get("entityId")
                if entity_id:
                    logger.info(f"Processing {action} event for {kind} with ID: {entity_id}")
                    # Note: In a real implementation, you would handle the delete operation
                    # For now, we'll just log it
                else:
                    logger.warning(f"No entity ID found for {action} event")
            else:
                # For create/update events, fetch the full entity
                entity_id = payload.get("id") or payload.get("entityId")
                if entity_id:
                    logger.info(f"Processing {action} event for {kind} with ID: {entity_id}")
                    # Note: In a real implementation, you would fetch and process the entity
                    # For now, we'll just log it
                else:
                    logger.warning(f"No entity ID found for {action} event")
                    
        except Exception as e:
            logger.error(f"Error processing webhook event: {e}")
            raise
