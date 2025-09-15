"""Data models for SailPoint entities."""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class SailPointEntity(BaseModel):
    """Base class for SailPoint entities."""

    id: str
    name: str
    created: Optional[datetime] = None
    modified: Optional[datetime] = None
    raw_data: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        """Pydantic configuration."""

        extra = "allow"
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None,
        }


class Identity(SailPointEntity):
    """SailPoint Identity entity."""

    display_name: Optional[str] = None
    email: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    status: Optional[str] = None
    lifecycle_state: Optional[str] = None
    manager: Optional[str] = None
    department: Optional[str] = None
    job_title: Optional[str] = None
    employee_number: Optional[str] = None
    phone_number: Optional[str] = None
    is_manager: Optional[bool] = None
    is_processing: Optional[bool] = None
    attributes: Dict[str, Any] = Field(default_factory=dict)


class Account(SailPointEntity):
    """SailPoint Account entity."""

    source_id: str
    identity_id: Optional[str] = None
    native_identity: str
    uuid: Optional[str] = None
    disabled: Optional[bool] = None
    locked: Optional[bool] = None
    privileged: Optional[bool] = None
    system_account: Optional[bool] = None
    uncorrelated: Optional[bool] = None
    attributes: Dict[str, Any] = Field(default_factory=dict)


class Entitlement(SailPointEntity):
    """SailPoint Entitlement entity."""

    source_id: str
    attribute: str
    value: str
    schema_name: Optional[str] = Field(alias="schema", default=None)
    privileged: Optional[bool] = None
    cloud_governed: Optional[bool] = None
    attributes: Dict[str, Any] = Field(default_factory=dict)


class AccessProfile(SailPointEntity):
    """SailPoint Access Profile entity."""

    source_id: str
    description: Optional[str] = None
    enabled: Optional[bool] = None
    owner: Optional[str] = None
    owner_id: Optional[str] = None
    requestable: Optional[bool] = None
    revocable: Optional[bool] = None
    attributes: Dict[str, Any] = Field(default_factory=dict)


class Role(SailPointEntity):
    """SailPoint Role entity."""

    description: Optional[str] = None
    enabled: Optional[bool] = None
    owner: Optional[str] = None
    owner_id: Optional[str] = None
    requestable: Optional[bool] = None
    revocable: Optional[bool] = None
    attributes: Dict[str, Any] = Field(default_factory=dict)


class Source(SailPointEntity):
    """SailPoint Source entity."""

    description: Optional[str] = None
    connector: str
    connector_class: Optional[str] = None
    connector_name: Optional[str] = None
    type: Optional[str] = None
    category: Optional[str] = None
    owner: Optional[str] = None
    owner_id: Optional[str] = None
    cluster_id: Optional[str] = None
    management_workgroup: Optional[str] = None
    healthy: Optional[bool] = None
    status: Optional[str] = None
    since: Optional[datetime] = None
    connector_metadata: Dict[str, Any] = Field(default_factory=dict)
    attributes: Dict[str, Any] = Field(default_factory=dict)


def parse_identity(raw_data: Dict[str, Any]) -> Identity:
    """Parse raw identity data into Identity model.

    Args:
        raw_data: Raw data from SailPoint API

    Returns:
        Parsed Identity object
    """
    return Identity(
        id=raw_data.get("id", ""),
        name=raw_data.get("name", ""),
        display_name=raw_data.get("displayName"),
        email=raw_data.get("email"),
        first_name=raw_data.get("firstName"),
        last_name=raw_data.get("lastName"),
        status=raw_data.get("status"),
        lifecycle_state=raw_data.get("lifecycleState"),
        manager=raw_data.get("manager"),
        department=raw_data.get("department"),
        job_title=raw_data.get("jobTitle"),
        employee_number=raw_data.get("employeeNumber"),
        phone_number=raw_data.get("phoneNumber"),
        is_manager=raw_data.get("isManager"),
        is_processing=raw_data.get("isProcessing"),
        created=raw_data.get("created"),
        modified=raw_data.get("modified"),
        attributes=raw_data.get("attributes", {}),
        raw_data=raw_data,
    )


def parse_account(raw_data: Dict[str, Any]) -> Account:
    """Parse raw account data into Account model.

    Args:
        raw_data: Raw data from SailPoint API

    Returns:
        Parsed Account object
    """
    return Account(
        id=raw_data.get("id", ""),
        name=raw_data.get("name", ""),
        source_id=raw_data.get("sourceId", ""),
        identity_id=raw_data.get("identityId"),
        native_identity=raw_data.get("nativeIdentity", ""),
        uuid=raw_data.get("uuid"),
        disabled=raw_data.get("disabled"),
        locked=raw_data.get("locked"),
        privileged=raw_data.get("privileged"),
        system_account=raw_data.get("systemAccount"),
        uncorrelated=raw_data.get("uncorrelated"),
        created=raw_data.get("created"),
        modified=raw_data.get("modified"),
        attributes=raw_data.get("attributes", {}),
        raw_data=raw_data,
    )


def parse_entitlement(raw_data: Dict[str, Any]) -> Entitlement:
    """Parse raw entitlement data into Entitlement model.

    Args:
        raw_data: Raw data from SailPoint API

    Returns:
        Parsed Entitlement object
    """
    return Entitlement(
        id=raw_data.get("id", ""),
        name=raw_data.get("name", ""),
        source_id=raw_data.get("sourceId", ""),
        attribute=raw_data.get("attribute", ""),
        value=raw_data.get("value", ""),
        schema_name=raw_data.get("schema"),
        privileged=raw_data.get("privileged"),
        cloud_governed=raw_data.get("cloudGoverned"),
        created=raw_data.get("created"),
        modified=raw_data.get("modified"),
        attributes=raw_data.get("attributes", {}),
        raw_data=raw_data,
    )


def parse_access_profile(raw_data: Dict[str, Any]) -> AccessProfile:
    """Parse raw access profile data into AccessProfile model.

    Args:
        raw_data: Raw data from SailPoint API

    Returns:
        Parsed AccessProfile object
    """
    return AccessProfile(
        id=raw_data.get("id", ""),
        name=raw_data.get("name", ""),
        source_id=raw_data.get("sourceId", ""),
        description=raw_data.get("description"),
        enabled=raw_data.get("enabled"),
        owner=raw_data.get("owner"),
        owner_id=raw_data.get("ownerId"),
        requestable=raw_data.get("requestable"),
        revocable=raw_data.get("revocable"),
        created=raw_data.get("created"),
        modified=raw_data.get("modified"),
        attributes=raw_data.get("attributes", {}),
        raw_data=raw_data,
    )


def parse_role(raw_data: Dict[str, Any]) -> Role:
    """Parse raw role data into Role model.

    Args:
        raw_data: Raw data from SailPoint API

    Returns:
        Parsed Role object
    """
    return Role(
        id=raw_data.get("id", ""),
        name=raw_data.get("name", ""),
        description=raw_data.get("description"),
        enabled=raw_data.get("enabled"),
        owner=raw_data.get("owner"),
        owner_id=raw_data.get("ownerId"),
        requestable=raw_data.get("requestable"),
        revocable=raw_data.get("revocable"),
        created=raw_data.get("created"),
        modified=raw_data.get("modified"),
        attributes=raw_data.get("attributes", {}),
        raw_data=raw_data,
    )


def parse_source(raw_data: Dict[str, Any]) -> Source:
    """Parse raw source data into Source model.

    Args:
        raw_data: Raw data from SailPoint API

    Returns:
        Parsed Source object
    """
    return Source(
        id=raw_data.get("id", ""),
        name=raw_data.get("name", ""),
        description=raw_data.get("description"),
        connector=raw_data.get("connector", ""),
        connector_class=raw_data.get("connectorClass"),
        connector_name=raw_data.get("connectorName"),
        type=raw_data.get("type"),
        category=raw_data.get("category"),
        owner=raw_data.get("owner"),
        owner_id=raw_data.get("ownerId"),
        cluster_id=raw_data.get("clusterId"),
        management_workgroup=raw_data.get("managementWorkgroup"),
        healthy=raw_data.get("healthy"),
        status=raw_data.get("status"),
        since=raw_data.get("since"),
        created=raw_data.get("created"),
        modified=raw_data.get("modified"),
        connector_metadata=raw_data.get("connectorMetadata", {}),
        attributes=raw_data.get("attributes", {}),
        raw_data=raw_data,
    )
