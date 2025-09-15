from typing import Any, Dict, List, Optional

from fastapi import Request
from loguru import logger
from port_ocean.context.ocean import ocean
import httpx

from .sailpoint.clients.sailpoint_client import SailPointClient
from .sailpoint.clients.token_manager import TokenManager
from .sailpoint.exporters.access_profile_exporter import AccessProfileExporter
from .sailpoint.exporters.account_exporter import AccountExporter
from .sailpoint.exporters.entitlement_exporter import EntitlementExporter
from .sailpoint.exporters.generic_exporter import GenericExporter
from .sailpoint.exporters.identity_exporter import IdentityExporter
from .sailpoint.exporters.role_exporter import RoleExporter
from .sailpoint.exporters.source_exporter import SourceExporter
from .sailpoint.webhooks.webhook_handler import WebhookHandler

# Global client instance
sailpoint_client: Optional[SailPointClient] = None
webhook_handler: Optional[WebhookHandler] = None


@ocean.on_start()
async def on_start() -> None:
    """Initialize the SailPoint integration."""
    global sailpoint_client, webhook_handler
    
    logger.info("Starting SailPoint integration")
    
    # Get configuration from Ocean
    config = ocean.integration_config
    
    # Extract SailPoint configuration
    tenant_url = config.get("tenantUrl")
    client_id = config.get("clientId")
    client_secret = config.get("clientSecret")
    
    if not all([tenant_url, client_id, client_secret]):
        raise ValueError("Missing required SailPoint configuration: tenantUrl, clientId, clientSecret")
    
    # Initialize HTTP client and token manager
    http_client = httpx.AsyncClient()
    token_manager = TokenManager(
        http_client=http_client,
        tenant_url=tenant_url,
        client_id=client_id,
        client_secret=client_secret,
    )
    
    # Initialize SailPoint client
    sailpoint_client = SailPointClient(
        http_client=http_client,
        token_manager=token_manager,
        max_retries=config.get("maxRetries", 3),
        base_delay=config.get("baseDelay", 1.0),
        max_delay=config.get("maxDelay", 60.0),
        backoff_factor=config.get("backoffFactor", 2.0),
        max_concurrent_requests=config.get("maxConcurrentRequests", 10),
    )
    
    # Initialize webhook handler
    webhook_secret = config.get("webhookSecret")
    webhook_handler = WebhookHandler(sailpoint_client, webhook_secret)
    
    logger.info("SailPoint integration initialized successfully")


@ocean.on_resync()
async def on_resync(kind: str) -> List[Dict[Any, Any]]:
    """Handle resync events for all SailPoint entity kinds.

    Args:
        kind: The entity kind to resync

    Returns:
        List of entity data dictionaries
    """
    if not sailpoint_client:
        logger.error("SailPoint client not initialized")
        return []

    logger.info(f"Starting resync for kind: {kind}")
    
    # Get configuration
    config = ocean.integration_config
    filters = config.get("filters", {}).get(kind, {})
    limit = config.get("limit", 250)
    
    try:
        # Route to appropriate exporter based on kind
        exporter = _get_exporter_for_kind(kind)
        if not exporter:
            logger.warning(f"No exporter found for kind: {kind}")
            return []

        # Export all entities
        entities = []
        async for entity in exporter.export_all(filters=filters, limit=limit):
            entities.append(entity)

        logger.info(f"Successfully exported {len(entities)} {kind} entities")
        return entities

    except Exception as e:
        logger.error(f"Failed to resync {kind}: {e}")
        return []


def _get_exporter_for_kind(kind: str) -> Optional[Any]:
    """Get the appropriate exporter for a given entity kind.

    Args:
        kind: Entity kind

    Returns:
        Exporter instance or None
    """
    if not sailpoint_client:
        return None

    exporters = {
        "identity": IdentityExporter(sailpoint_client),
        "account": AccountExporter(sailpoint_client),
        "entitlement": EntitlementExporter(sailpoint_client),
        "access-profile": AccessProfileExporter(sailpoint_client),
        "role": RoleExporter(sailpoint_client),
        "source": SourceExporter(sailpoint_client),
    }
    
    # Check for generic exporters configured in the spec
    config = ocean.integration_config
    generic_resources = config.get("genericResources", [])
    
    for resource in generic_resources:
        if resource.get("kind") == kind:
            return GenericExporter(
                client=sailpoint_client,
                resource_kind=kind,
                api_endpoint=resource.get("apiEndpoint", f"/v3/{kind}s"),
                port_blueprint=resource.get("portBlueprint", kind),
            )
    
    return exporters.get(kind)


@ocean.app.post("/webhook")
async def webhook_endpoint(request: Request) -> Dict[str, Any]:
    """Handle SailPoint webhook events.

    Args:
        request: FastAPI request object

    Returns:
        Webhook response
    """
    if not webhook_handler:
        logger.error("Webhook handler not initialized")
        return {"status": "error", "message": "Webhook handler not initialized"}

    return await webhook_handler.handle_webhook(request)
