# SailPoint Integration for Port Ocean

A comprehensive Ocean integration for SailPoint Identity Security Cloud that enables platform and security teams to visualize access, relationships, and governance posture inside their internal developer portal.

## Features

### Core Entity Support
- **Identities**: Users, employees, and their attributes
- **Accounts**: System accounts, service accounts, and their status
- **Entitlements**: Permissions, access rights, and privileges
- **Access Profiles**: Grouped permissions and access patterns
- **Roles**: Business roles and responsibilities
- **Sources**: Identity sources, connectors, and their health

### Advanced Capabilities
- **OAuth 2.0 Authentication**: Secure API access with automatic token refresh
- **Rate Limiting**: Intelligent handling of API rate limits with exponential backoff
- **Pagination**: Efficient data retrieval with configurable page sizes
- **Real-time Updates**: Webhook support for immediate data synchronization
- **Filtering**: Flexible filtering options for each resource type
- **Extensibility**: Generic exporter for easy addition of new resource types
- **Monitoring**: Comprehensive logging and error handling

## Configuration

### Required Settings
- `tenantUrl`: Your SailPoint tenant URL (e.g., `https://{tenant}.api.sailpoint.com`)
- `clientId`: OAuth 2.0 Client ID
- `clientSecret`: OAuth 2.0 Client Secret

### Optional Settings
- `maxRetries`: Maximum retry attempts (default: 3)
- `baseDelay`: Base delay for exponential backoff in seconds (default: 1.0)
- `maxDelay`: Maximum delay between retries in seconds (default: 60.0)
- `backoffFactor`: Exponential backoff multiplier (default: 2.0)
- `maxConcurrentRequests`: Concurrent request limit (default: 10)
- `limit`: Items per page for pagination (default: 250)
- `webhookSecret`: Secret for webhook HMAC signature verification
- `filters`: Resource-specific filters for data filtering

### Filter Examples
```yaml
filters:
  identity:
    status: "ACTIVE"
    lifecycleState: "ACTIVE"
  account:
    sourceId: "source-123"
    disabled: false
  entitlement:
    privileged: true
    sourceId: "source-456"
```

## Installation

1. Install the integration using Ocean CLI:
```bash
ocean new sailpoint
```

2. Configure your SailPoint credentials in the integration settings

3. Deploy the integration to your Port environment

## Usage

### Full Sync
The integration automatically performs full synchronization of all configured entity types when triggered by Port's resync mechanism.

### Real-time Updates
Configure webhooks in SailPoint to point to your integration's `/webhook` endpoint for real-time updates.

### Custom Resources
Use the generic exporter to add support for additional SailPoint resource types without code changes:

```yaml
genericResources:
  - kind: "custom-resource"
    apiEndpoint: "/v3/custom-resources"
    portBlueprint: "customResource"
```

## Development

### Running Tests
```bash
pytest tests/
```

### Code Quality
```bash
black sailpoint/
ruff check sailpoint/
mypy sailpoint/
```

## Security

- OAuth 2.0 Client Credentials flow for secure API access
- HMAC signature verification for webhook authenticity
- Sensitive configuration values properly marked
- Rate limiting to prevent API abuse
- Comprehensive error handling and logging

## Support

For issues and questions, please refer to the Port Ocean documentation or create an issue in the repository.

## License

This integration is part of the Port Ocean ecosystem and follows the same licensing terms.

#### Install & use the integration - [Integration documentation](https://docs.port.io/build-your-software-catalog/sync-data-to-catalog/)

#### Develop & improve the integration - [Ocean integration development documentation](https://ocean.getport.io/develop-an-integration/)