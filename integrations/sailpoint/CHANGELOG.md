# Changelog - Ocean - sailpoint

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0-beta] - 2025-09-12

### Added
- Initial SailPoint Identity Security Cloud integration for Port Ocean
- OAuth 2.0 Client Credentials authentication with automatic token refresh
- Comprehensive HTTP client with rate limiting, retries, and exponential backoff
- Support for all core SailPoint entity types:
  - Identities (users, employees)
  - Accounts (system accounts, service accounts)
  - Entitlements (permissions, access rights)
  - Access Profiles (grouped permissions)
  - Roles (business roles)
  - Sources (identity sources, connectors)
- Pagination support for all API endpoints
- Real-time webhook support with HMAC signature verification
- Configurable filters for each entity type
- Generic exporter for extensible resource support
- Comprehensive test suite with mocked responses
- Port blueprints and configuration files
- Detailed logging and error handling
- Support for concurrent API requests with configurable limits

### Features
- **Authentication**: Secure OAuth 2.0 token management with automatic refresh
- **Rate Limiting**: Intelligent rate limit handling with Retry-After header support
- **Pagination**: Efficient data retrieval with configurable page sizes
- **Webhooks**: Real-time event processing for immediate data updates
- **Filtering**: Flexible filtering options for each resource type
- **Extensibility**: Generic exporter for easy addition of new resource types
- **Monitoring**: Comprehensive logging and metrics for operational visibility
- **Testing**: Full test coverage with mocked SailPoint API responses

### Configuration
- `tenantUrl`: SailPoint tenant URL (required)
- `clientId`: OAuth 2.0 Client ID (required, sensitive)
- `clientSecret`: OAuth 2.0 Client Secret (required, sensitive)
- `maxRetries`: Maximum retry attempts (default: 3)
- `baseDelay`: Base delay for exponential backoff (default: 1.0s)
- `maxDelay`: Maximum delay between retries (default: 60.0s)
- `backoffFactor`: Exponential backoff multiplier (default: 2.0)
- `maxConcurrentRequests`: Concurrent request limit (default: 10)
- `limit`: Items per page for pagination (default: 250)
- `filters`: Resource-specific filters
- `webhookSecret`: HMAC signature verification secret (optional)
- `genericResources`: Configuration for additional resource types

### Security
- OAuth 2.0 Client Credentials flow for secure API access
- HMAC signature verification for webhook authenticity
- Sensitive configuration values properly marked
- Rate limiting to prevent API abuse
- Comprehensive error handling and logging

<!-- towncrier release notes start -->
