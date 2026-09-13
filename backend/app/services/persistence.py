from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.models import (
    DigitalEntity,
    EntityTemplate,
    Relationship,
    RelationshipCreate,
    Site,
    SiteCreate,
)
from app.persistence.models import EntityRecord, RelationshipRecord, SiteRecord, TemplateRecord


class PersistenceError(ValueError):
    """Raised when a persisted resource cannot be created or resolved."""


def template_record(template: EntityTemplate) -> TemplateRecord:
    return TemplateRecord(
        type=template.type,
        version=template.version,
        definition=template.model_dump(mode="json"),
    )


def save_template(session: Session, template: EntityTemplate) -> None:
    record = session.get(TemplateRecord, (template.type, template.version))
    if record is None:
        session.add(template_record(template))
    else:
        record.definition = template.model_dump(mode="json")


def load_templates(session: Session) -> list[EntityTemplate]:
    return [
        EntityTemplate.model_validate(item.definition)
        for item in session.scalars(select(TemplateRecord))
    ]


def create_site(session: Session, payload: SiteCreate) -> Site:
    if session.get(SiteRecord, payload.id) is not None:
        raise PersistenceError("site already exists")
    record = SiteRecord(
        id=payload.id,
        name=payload.name,
        description=payload.description,
        metadata_=payload.metadata,
    )
    session.add(record)
    session.flush()
    return site_from_record(record)


def list_sites(session: Session) -> list[Site]:
    return [site_from_record(item) for item in session.scalars(select(SiteRecord))]


def get_site(session: Session, site_id: str) -> Site:
    record = session.get(SiteRecord, site_id)
    if record is None:
        raise PersistenceError("site not found")
    return site_from_record(record)


def save_entity(session: Session, entity: DigitalEntity) -> DigitalEntity:
    if entity.site_id is not None and session.get(SiteRecord, entity.site_id) is None:
        raise PersistenceError("site not found")
    if session.get(EntityRecord, entity.id) is not None:
        raise PersistenceError("entity already exists")
    record = EntityRecord(
        id=entity.id,
        site_id=entity.site_id,
        type=entity.type,
        name=entity.name,
        template=entity.template,
        version=entity.version,
        description=entity.description,
        properties=entity.properties,
        state=entity.state,
        metadata_=entity.metadata,
    )
    session.add(record)
    session.flush()
    return entity_from_record(record)


def list_entities(session: Session, site_id: str | None = None) -> list[DigitalEntity]:
    query = select(EntityRecord).order_by(EntityRecord.name)
    if site_id is not None:
        query = query.where(EntityRecord.site_id == site_id)
    return [entity_from_record(item) for item in session.scalars(query)]


def get_entity(session: Session, entity_id: str) -> DigitalEntity:
    record = session.get(EntityRecord, entity_id)
    if record is None:
        raise PersistenceError("entity not found")
    return entity_from_record(record)


def create_relationship(session: Session, payload: RelationshipCreate) -> Relationship:
    for entity_id in (payload.source_entity_id, payload.target_entity_id):
        if session.get(EntityRecord, entity_id) is None:
            raise PersistenceError(f"entity not found: {entity_id}")
    duplicate = session.scalar(
        select(RelationshipRecord).where(
            RelationshipRecord.source_entity_id == payload.source_entity_id,
            RelationshipRecord.target_entity_id == payload.target_entity_id,
            RelationshipRecord.relationship_type == payload.relationship_type,
        )
    )
    if duplicate is not None:
        raise PersistenceError("relationship already exists")
    record = RelationshipRecord(
        source_entity_id=payload.source_entity_id,
        target_entity_id=payload.target_entity_id,
        relationship_type=payload.relationship_type,
        metadata_=payload.metadata,
    )
    session.add(record)
    session.flush()
    return relationship_from_record(record)


def list_relationships(session: Session) -> list[Relationship]:
    return [
        relationship_from_record(item)
        for item in session.scalars(
            select(RelationshipRecord).order_by(RelationshipRecord.created_at)
        )
    ]


def site_from_record(record: SiteRecord) -> Site:
    return Site(
        id=record.id,
        name=record.name,
        description=record.description,
        metadata=record.metadata_,
    )


def entity_from_record(record: EntityRecord) -> DigitalEntity:
    return DigitalEntity(
        id=record.id,
        site_id=record.site_id,
        type=record.type,
        name=record.name,
        template=record.template,
        version=record.version,
        description=record.description,
        properties=record.properties,
        state=record.state,
        metadata=record.metadata_,
    )


def relationship_from_record(record: RelationshipRecord) -> Relationship:
    return Relationship(
        id=record.id,
        source_entity_id=record.source_entity_id,
        target_entity_id=record.target_entity_id,
        relationship_type=record.relationship_type,
        metadata=record.metadata_,
    )
