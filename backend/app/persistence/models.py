from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from sqlalchemy import JSON, DateTime, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class Base(DeclarativeBase):
    pass


class TemplateRecord(Base):
    __tablename__ = "entity_templates"
    __table_args__ = (UniqueConstraint("type", "version", name="uq_entity_template_version"),)

    type: Mapped[str] = mapped_column(String(100), primary_key=True)
    version: Mapped[str] = mapped_column(String(20), primary_key=True)
    definition: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


class SiteRecord(Base):
    __tablename__ = "sites"

    id: Mapped[str] = mapped_column(String(100), primary_key=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(String(1000))
    metadata_: Mapped[dict[str, Any]] = mapped_column(
        "metadata", JSON, nullable=False, default=dict
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now
    )


class EntityRecord(Base):
    __tablename__ = "entities"

    id: Mapped[str] = mapped_column(String(100), primary_key=True)
    site_id: Mapped[str | None] = mapped_column(ForeignKey("sites.id", ondelete="SET NULL"))
    type: Mapped[str] = mapped_column(String(100), nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    template: Mapped[str] = mapped_column(String(100), nullable=False)
    version: Mapped[str] = mapped_column(String(20), nullable=False)
    description: Mapped[str | None] = mapped_column(String(1000))
    properties: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    state: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    metadata_: Mapped[dict[str, Any]] = mapped_column(
        "metadata", JSON, nullable=False, default=dict
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now
    )


class RelationshipRecord(Base):
    __tablename__ = "entity_relationships"
    __table_args__ = (
        UniqueConstraint(
            "source_entity_id",
            "target_entity_id",
            "relationship_type",
            name="uq_entity_relationship",
        ),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    source_entity_id: Mapped[str] = mapped_column(
        ForeignKey("entities.id", ondelete="CASCADE"), nullable=False
    )
    target_entity_id: Mapped[str] = mapped_column(
        ForeignKey("entities.id", ondelete="CASCADE"), nullable=False
    )
    relationship_type: Mapped[str] = mapped_column(String(100), nullable=False)
    metadata_: Mapped[dict[str, Any]] = mapped_column(
        "metadata", JSON, nullable=False, default=dict
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


class DigitalTwinRecord(Base):
    __tablename__ = "digital_twins"

    twin_id: Mapped[str] = mapped_column(String(100), primary_key=True)
    asset_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    external_id: Mapped[str | None] = mapped_column(String(100), index=True)
    twin_type: Mapped[str] = mapped_column(String(100), nullable=False)
    asset_class: Mapped[str] = mapped_column(String(50), nullable=False, default="SOLAR_PV")
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(String(1000))
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="REGISTERED")
    tenant_id: Mapped[str | None] = mapped_column(String(100), index=True)
    portfolio_id: Mapped[str | None] = mapped_column(String(100), index=True)
    site_id: Mapped[str | None] = mapped_column(
        ForeignKey("sites.id", ondelete="SET NULL"), index=True
    )
    parent_twin_id: Mapped[str | None] = mapped_column(
        ForeignKey("digital_twins.twin_id", ondelete="SET NULL"), index=True
    )
    components: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    sensors: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    capabilities: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    configuration: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    state: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    health: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    metadata_: Mapped[dict[str, Any]] = mapped_column(
        "metadata", JSON, nullable=False, default=dict
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now
    )


class TwinEventRecord(Base):
    __tablename__ = "twin_events"

    event_id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid4())
    )
    twin_id: Mapped[str] = mapped_column(
        ForeignKey("digital_twins.twin_id", ondelete="CASCADE"), nullable=False, index=True
    )
    event_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    severity: Mapped[str] = mapped_column(String(20), nullable=False, default="INFO")
    message: Mapped[str] = mapped_column(String(1000), nullable=False)
    details: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    provenance: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, index=True
    )
