from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.enums import AssetClass, TwinEventType, TwinLifecycleStatus
from app.domain.twin import (
    DigitalTwin,
    DigitalTwinCreate,
    DigitalTwinUpdate,
    LifecycleTransitionRequest,
    TwinEvent,
    TwinEventCreate,
)
from app.persistence.models import DigitalTwinRecord, SiteRecord, TwinEventRecord


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class TwinServiceError(ValueError):
    """Base exception for twin service errors."""


class TwinNotFoundError(TwinServiceError):
    """Raised when a requested digital twin cannot be found."""


class TwinAlreadyExistsError(TwinServiceError):
    """Raised when attempting to create a digital twin with an existing ID."""


class InvalidTransitionError(TwinServiceError):
    """Raised when an invalid lifecycle transition is requested."""


class InvalidHierarchyError(TwinServiceError):
    """Raised when a parent-child relationship violates hierarchy rules or forms a cycle."""


VALID_TRANSITIONS: dict[TwinLifecycleStatus, set[TwinLifecycleStatus]] = {
    TwinLifecycleStatus.DISCOVERED: {
        TwinLifecycleStatus.REGISTERED,
        TwinLifecycleStatus.DECOMMISSIONED,
    },
    TwinLifecycleStatus.REGISTERED: {
        TwinLifecycleStatus.COMMISSIONED,
        TwinLifecycleStatus.DECOMMISSIONED,
    },
    TwinLifecycleStatus.COMMISSIONED: {
        TwinLifecycleStatus.ACTIVE,
        TwinLifecycleStatus.MAINTENANCE,
        TwinLifecycleStatus.DECOMMISSIONED,
    },
    TwinLifecycleStatus.ACTIVE: {
        TwinLifecycleStatus.DEGRADED,
        TwinLifecycleStatus.MAINTENANCE,
        TwinLifecycleStatus.DECOMMISSIONED,
    },
    TwinLifecycleStatus.DEGRADED: {
        TwinLifecycleStatus.ACTIVE,
        TwinLifecycleStatus.MAINTENANCE,
        TwinLifecycleStatus.DECOMMISSIONED,
    },
    TwinLifecycleStatus.MAINTENANCE: {
        TwinLifecycleStatus.ACTIVE,
        TwinLifecycleStatus.COMMISSIONED,
        TwinLifecycleStatus.DECOMMISSIONED,
    },
    TwinLifecycleStatus.DECOMMISSIONED: set(),
}


def twin_from_record(record: DigitalTwinRecord) -> DigitalTwin:
    raw_data: dict[str, Any] = {
        "twin_id": record.twin_id,
        "asset_id": record.asset_id,
        "external_id": record.external_id,
        "twin_type": record.twin_type,
        "asset_class": record.asset_class,
        "name": record.name,
        "description": record.description,
        "status": record.status,
        "tenant_id": record.tenant_id,
        "portfolio_id": record.portfolio_id,
        "site_id": record.site_id,
        "parent_twin_id": record.parent_twin_id,
        "components": record.components or {},
        "sensors": record.sensors or {},
        "capabilities": record.capabilities or [],
        "configuration": record.configuration or {},
        "state": record.state or {},
        "health": record.health,
        "metadata": record.metadata_ or {},
        "created_at": record.created_at,
        "updated_at": record.updated_at,
    }
    return DigitalTwin.model_validate(raw_data)


def event_from_record(record: TwinEventRecord) -> TwinEvent:
    return TwinEvent.model_validate(
        {
            "event_id": record.event_id,
            "twin_id": record.twin_id,
            "event_type": record.event_type,
            "severity": record.severity,
            "message": record.message,
            "details": record.details or {},
            "timestamp": record.timestamp,
            "provenance": record.provenance,
        }
    )


def validate_parent_hierarchy(session: Session, twin_id: str, parent_twin_id: str | None) -> None:
    if parent_twin_id is None:
        return
    if parent_twin_id == twin_id:
        raise InvalidHierarchyError("A digital twin cannot be its own parent")
    parent = session.get(DigitalTwinRecord, parent_twin_id)
    if parent is None:
        raise InvalidHierarchyError(f"Parent twin '{parent_twin_id}' does not exist")

    # Check for cycles
    current_parent_id = parent.parent_twin_id
    visited: set[str] = {twin_id, parent_twin_id}
    depth = 0
    while current_parent_id is not None:
        depth += 1
        if depth > 50:
            raise InvalidHierarchyError("Hierarchy depth exceeded limit (50)")
        if current_parent_id == twin_id:
            raise InvalidHierarchyError(
                f"Setting parent '{parent_twin_id}' creates a cycle in twin hierarchy"
            )
        if current_parent_id in visited:
            break
        visited.add(current_parent_id)
        curr_rec = session.get(DigitalTwinRecord, current_parent_id)
        current_parent_id = curr_rec.parent_twin_id if curr_rec else None


def create_twin(session: Session, payload: DigitalTwinCreate) -> DigitalTwin:
    if session.get(DigitalTwinRecord, payload.twin_id) is not None:
        raise TwinAlreadyExistsError(f"Twin with ID '{payload.twin_id}' already exists")

    if payload.site_id is not None and session.get(SiteRecord, payload.site_id) is None:
        raise TwinServiceError(f"Site with ID '{payload.site_id}' does not exist")

    validate_parent_hierarchy(session, payload.twin_id, payload.parent_twin_id)

    components_dict = {k: v.model_dump(mode="json") for k, v in payload.components.items()}
    sensors_dict = {k: v.model_dump(mode="json") for k, v in payload.sensors.items()}

    record = DigitalTwinRecord(
        twin_id=payload.twin_id,
        asset_id=payload.asset_id,
        external_id=payload.external_id,
        twin_type=payload.twin_type,
        asset_class=payload.asset_class.value,
        name=payload.name,
        description=payload.description,
        status=payload.status.value,
        tenant_id=payload.tenant_id,
        portfolio_id=payload.portfolio_id,
        site_id=payload.site_id,
        parent_twin_id=payload.parent_twin_id,
        components=components_dict,
        sensors=sensors_dict,
        capabilities=payload.capabilities,
        configuration=payload.configuration,
        state={},
        health=None,
        metadata_=payload.metadata,
    )
    session.add(record)

    init_event = TwinEventRecord(
        twin_id=payload.twin_id,
        event_type=TwinEventType.ASSET_REGISTERED.value,
        severity="INFO",
        message=f"Digital twin '{payload.name}' registered with status {payload.status.value}",
        details={"asset_id": payload.asset_id, "asset_class": payload.asset_class.value},
        provenance={"source": "TWIN_REGISTRY", "source_type": "SYSTEM"},
    )
    session.add(init_event)
    session.flush()

    return twin_from_record(record)


def get_twin(session: Session, twin_id: str) -> DigitalTwin:
    record = session.get(DigitalTwinRecord, twin_id)
    if record is None:
        raise TwinNotFoundError(f"Digital twin '{twin_id}' not found")
    return twin_from_record(record)


def list_twins(
    session: Session,
    site_id: str | None = None,
    asset_class: AssetClass | None = None,
    status: TwinLifecycleStatus | None = None,
    parent_twin_id: str | None = None,
    tenant_id: str | None = None,
) -> list[DigitalTwin]:
    query = select(DigitalTwinRecord).order_by(DigitalTwinRecord.name)
    if site_id is not None:
        query = query.where(DigitalTwinRecord.site_id == site_id)
    if asset_class is not None:
        query = query.where(DigitalTwinRecord.asset_class == asset_class.value)
    if status is not None:
        query = query.where(DigitalTwinRecord.status == status.value)
    if parent_twin_id is not None:
        query = query.where(DigitalTwinRecord.parent_twin_id == parent_twin_id)
    if tenant_id is not None:
        query = query.where(DigitalTwinRecord.tenant_id == tenant_id)

    return [twin_from_record(r) for r in session.scalars(query)]


def update_twin(session: Session, twin_id: str, payload: DigitalTwinUpdate) -> DigitalTwin:
    record = session.get(DigitalTwinRecord, twin_id)
    if record is None:
        raise TwinNotFoundError(f"Digital twin '{twin_id}' not found")

    if payload.parent_twin_id is not None:
        validate_parent_hierarchy(session, twin_id, payload.parent_twin_id)
        record.parent_twin_id = payload.parent_twin_id

    if payload.site_id is not None:
        if session.get(SiteRecord, payload.site_id) is None:
            raise TwinServiceError(f"Site '{payload.site_id}' not found")
        record.site_id = payload.site_id

    if payload.name is not None:
        record.name = payload.name
    if payload.description is not None:
        record.description = payload.description
    if payload.external_id is not None:
        record.external_id = payload.external_id
    if payload.twin_type is not None:
        record.twin_type = payload.twin_type
    if payload.asset_class is not None:
        record.asset_class = payload.asset_class.value
    if payload.tenant_id is not None:
        record.tenant_id = payload.tenant_id
    if payload.portfolio_id is not None:
        record.portfolio_id = payload.portfolio_id
    if payload.capabilities is not None:
        record.capabilities = payload.capabilities
    if payload.configuration is not None:
        record.configuration = payload.configuration
    if payload.metadata is not None:
        record.metadata_ = payload.metadata

    record.updated_at = utc_now()

    event = TwinEventRecord(
        twin_id=twin_id,
        event_type=TwinEventType.CONFIGURATION_CHANGED.value,
        severity="INFO",
        message=f"Digital twin '{twin_id}' configuration/metadata updated",
        details=payload.model_dump(exclude_unset=True, mode="json"),
        provenance={"source": "TWIN_REGISTRY", "source_type": "API"},
    )
    session.add(event)
    session.flush()

    return twin_from_record(record)


def transition_lifecycle(
    session: Session, twin_id: str, payload: LifecycleTransitionRequest
) -> DigitalTwin:
    record = session.get(DigitalTwinRecord, twin_id)
    if record is None:
        raise TwinNotFoundError(f"Digital twin '{twin_id}' not found")

    current_status = TwinLifecycleStatus(record.status)
    target_status = payload.target_status

    allowed = VALID_TRANSITIONS.get(current_status, set())
    if target_status not in allowed:
        allowed_str = [s.value for s in allowed]
        raise InvalidTransitionError(
            f"Cannot transition twin '{twin_id}' from '{current_status.value}' "
            f"to '{target_status.value}'. Allowed transitions: {allowed_str}"
        )

    record.status = target_status.value
    record.updated_at = utc_now()

    severity = (
        "WARNING"
        if target_status
        in (
            TwinLifecycleStatus.DEGRADED,
            TwinLifecycleStatus.MAINTENANCE,
            TwinLifecycleStatus.DECOMMISSIONED,
        )
        else "INFO"
    )

    event = TwinEventRecord(
        twin_id=twin_id,
        event_type=TwinEventType.STATE_CHANGED.value,
        severity=severity,
        message=(
            f"Lifecycle transitioned from {current_status.value} to {target_status.value}. "
            f"Reason: {payload.reason}"
        ),
        details={
            "previous_status": current_status.value,
            "new_status": target_status.value,
            "reason": payload.reason,
            "operator": payload.operator,
        },
        provenance={
            "source": payload.operator,
            "source_type": "OPERATOR",
            "timestamp": utc_now().isoformat(),
        },
    )
    session.add(event)
    session.flush()

    return twin_from_record(record)


def delete_twin(session: Session, twin_id: str) -> None:
    record = session.get(DigitalTwinRecord, twin_id)
    if record is None:
        raise TwinNotFoundError(f"Digital twin '{twin_id}' not found")
    session.delete(record)
    session.flush()


def get_twin_children(session: Session, twin_id: str) -> list[DigitalTwin]:
    if session.get(DigitalTwinRecord, twin_id) is None:
        raise TwinNotFoundError(f"Digital twin '{twin_id}' not found")
    query = (
        select(DigitalTwinRecord)
        .where(DigitalTwinRecord.parent_twin_id == twin_id)
        .order_by(DigitalTwinRecord.name)
    )
    return [twin_from_record(r) for r in session.scalars(query)]


def get_twin_events(session: Session, twin_id: str, limit: int = 100) -> list[TwinEvent]:
    if session.get(DigitalTwinRecord, twin_id) is None:
        raise TwinNotFoundError(f"Digital twin '{twin_id}' not found")
    query = (
        select(TwinEventRecord)
        .where(TwinEventRecord.twin_id == twin_id)
        .order_by(TwinEventRecord.timestamp.desc())
        .limit(limit)
    )
    return [event_from_record(r) for r in session.scalars(query)]


def create_twin_event(session: Session, twin_id: str, payload: TwinEventCreate) -> TwinEvent:
    if session.get(DigitalTwinRecord, twin_id) is None:
        raise TwinNotFoundError(f"Digital twin '{twin_id}' not found")

    record = TwinEventRecord(
        twin_id=twin_id,
        event_type=payload.event_type.value,
        severity=payload.severity,
        message=payload.message,
        details=payload.details,
        provenance=payload.provenance.model_dump(mode="json") if payload.provenance else None,
    )
    session.add(record)
    session.flush()

    return event_from_record(record)
