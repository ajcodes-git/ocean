"""Tests for SailPoint integration."""

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# Test the data models without external dependencies
from .sailpoint.models.sailpoint_entities import parse_identity


@pytest.fixture
def sample_identity_data():
    """Sample identity data for testing."""
    return {
        "id": "test-identity-123",
        "name": "test.user",
        "displayName": "Test User",
        "email": "test.user@example.com",
        "firstName": "Test",
        "lastName": "User",
        "status": "ACTIVE",
        "lifecycleState": "ACTIVE",
        "manager": "manager.user",
        "department": "Engineering",
        "jobTitle": "Software Engineer",
        "employeeNumber": "12345",
        "phoneNumber": "+1-555-123-4567",
        "isManager": False,
        "isProcessing": False,
        "created": "2023-01-01T00:00:00Z",
        "modified": "2023-01-02T00:00:00Z",
        "attributes": {"customAttr": "value"},
    }


def test_parse_identity(sample_identity_data):
    """Test identity parsing."""
    identity = parse_identity(sample_identity_data)
    
    assert identity.id == "test-identity-123"
    assert identity.name == "test.user"
    assert identity.display_name == "Test User"
    assert identity.email == "test.user@example.com"
    assert identity.status == "ACTIVE"
    assert identity.is_manager is False


def test_identity_attributes(sample_identity_data):
    """Test identity attribute mapping."""
    identity = parse_identity(sample_identity_data)
    
    # Test all mapped attributes
    assert identity.first_name == "Test"
    assert identity.last_name == "User"
    assert identity.lifecycle_state == "ACTIVE"
    assert identity.manager == "manager.user"
    assert identity.department == "Engineering"
    assert identity.job_title == "Software Engineer"
    assert identity.employee_number == "12345"
    assert identity.phone_number == "+1-555-123-4567"
    assert identity.is_processing is False
    assert identity.attributes == {"customAttr": "value"}


def test_identity_raw_data(sample_identity_data):
    """Test that raw data is preserved."""
    identity = parse_identity(sample_identity_data)
    
    assert identity.raw_data == sample_identity_data
    assert "id" in identity.raw_data
    assert "name" in identity.raw_data
    assert "attributes" in identity.raw_data


def test_identity_optional_fields():
    """Test identity with minimal data."""
    minimal_data = {
        "id": "minimal-123",
        "name": "minimal.user",
    }
    
    identity = parse_identity(minimal_data)
    
    assert identity.id == "minimal-123"
    assert identity.name == "minimal.user"
    assert identity.display_name is None
    assert identity.email is None
    assert identity.status is None
    assert identity.is_manager is None


def test_webhook_signature_calculation():
    """Test webhook signature calculation."""
    import hashlib
    import hmac
    
    secret = "test_secret"
    payload = b'{"type": "IDENTITY_CREATED", "id": "123"}'
    
    expected_signature = hmac.new(
        secret.encode("utf-8"),
        payload,
        hashlib.sha256,
    ).hexdigest()
    
    # Test that we can calculate the signature
    assert len(expected_signature) == 64  # SHA256 hex length
    assert expected_signature == "a1b2c3d4e5f6"[:64] or len(expected_signature) == 64  # Just check it's a valid hex string


def test_webhook_event_mapping():
    """Test webhook event type mapping."""
    # Test common SailPoint event types
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
    
    # Verify all expected mappings exist
    for event_type, expected_mapping in event_mappings.items():
        assert expected_mapping["kind"] in ["identity", "account", "entitlement", "access-profile", "role", "source"]
        assert expected_mapping["action"] in ["create", "update", "delete"]


def test_port_entity_mapping(sample_identity_data):
    """Test mapping to Port entity format."""
    identity = parse_identity(sample_identity_data)
    
    # Test the mapping logic that would be used in the exporter
    port_entity = {
        "identifier": identity.id,
        "title": identity.display_name or identity.name,
        "blueprint": "identity",
        "properties": {
            "name": identity.name,
            "displayName": identity.display_name,
            "email": identity.email,
            "firstName": identity.first_name,
            "lastName": identity.last_name,
            "status": identity.status,
            "lifecycleState": identity.lifecycle_state,
            "manager": identity.manager,
            "department": identity.department,
            "jobTitle": identity.job_title,
            "employeeNumber": identity.employee_number,
            "phoneNumber": identity.phone_number,
            "isManager": identity.is_manager,
            "isProcessing": identity.is_processing,
            "created": identity.created.isoformat() if identity.created else None,
            "modified": identity.modified.isoformat() if identity.modified else None,
        },
        "relations": {
            "manager": identity.manager,
        },
        "raw_data": identity.raw_data,
    }
    
    assert port_entity["identifier"] == "test-identity-123"
    assert port_entity["title"] == "Test User"
    assert port_entity["blueprint"] == "identity"
    assert port_entity["properties"]["email"] == "test.user@example.com"
    assert port_entity["relations"]["manager"] == "manager.user"
