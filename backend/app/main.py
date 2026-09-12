from fastapi import Depends, FastAPI, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.domain.models import (
    DigitalEntity,
    EntityCreate,
    EntityTemplate,
    Relationship,
    RelationshipCreate,
    Site,
    SiteCreate,
)
from app.persistence.database import SessionLocal, get_session, init_db
from app.services.persistence import (
    PersistenceError,
    create_relationship,
    create_site,
    list_relationships,
    list_sites,
    load_templates,
    save_entity,
    save_template,
)
from app.services.persistence import (
    get_entity as get_persisted_entity,
)
from app.services.persistence import (
    list_entities as list_persisted_entities,
)
from app.services.registry import EntityRegistry, RegistryError

app = FastAPI(title="IoT Digital Twin API", version="0.1.0")
init_db()
registry = EntityRegistry()
with SessionLocal() as session:
    for template in load_templates(session):
        registry.register_template(template)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/ready")
def ready() -> dict[str, str]:
    return {"status": "ready"}


@app.get("/api/v1/templates", response_model=list[EntityTemplate])
def list_templates() -> list[EntityTemplate]:
    return registry.list_templates()


@app.post("/api/v1/templates", response_model=EntityTemplate, status_code=status.HTTP_201_CREATED)
def register_template(template: EntityTemplate) -> EntityTemplate:
    registered = registry.register_template(template)
    with SessionLocal() as session:
        save_template(session, registered)
        session.commit()
    return registered


@app.get("/api/v1/sites", response_model=list[Site])
def get_sites(session: Session = Depends(get_session)) -> list[Site]:
    return list_sites(session)


@app.post("/api/v1/sites", response_model=Site, status_code=status.HTTP_201_CREATED)
def register_site(payload: SiteCreate, session: Session = Depends(get_session)) -> Site:
    try:
        site = create_site(session, payload)
        session.commit()
        return site
    except PersistenceError as error:
        session.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(error)) from error


@app.get("/api/v1/entities", response_model=list[DigitalEntity])
def get_entities(
    site_id: str | None = Query(default=None), session: Session = Depends(get_session)
) -> list[DigitalEntity]:
    return list_persisted_entities(session, site_id=site_id)


@app.post("/api/v1/entities", response_model=DigitalEntity, status_code=status.HTTP_201_CREATED)
def create_entity(
    payload: EntityCreate, session: Session = Depends(get_session)
) -> DigitalEntity:
    try:
        entity = registry.create_entity(payload)
        persisted_entity = save_entity(session, entity)
        session.commit()
        return persisted_entity
    except RegistryError as error:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(error)
        ) from error
    except PersistenceError as error:
        session.rollback()
        status_code = (
            status.HTTP_404_NOT_FOUND
            if str(error) == "site not found"
            else status.HTTP_409_CONFLICT
        )
        raise HTTPException(status_code=status_code, detail=str(error)) from error


@app.get("/api/v1/entities/{entity_id}", response_model=DigitalEntity)
def get_entity(entity_id: str, session: Session = Depends(get_session)) -> DigitalEntity:
    try:
        return get_persisted_entity(session, entity_id)
    except PersistenceError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error)) from error


@app.get("/api/v1/relationships", response_model=list[Relationship])
def get_relationships(session: Session = Depends(get_session)) -> list[Relationship]:
    return list_relationships(session)


@app.post(
    "/api/v1/relationships",
    response_model=Relationship,
    status_code=status.HTTP_201_CREATED,
)
def register_relationship(
    payload: RelationshipCreate, session: Session = Depends(get_session)
) -> Relationship:
    try:
        relationship = create_relationship(session, payload)
        session.commit()
        return relationship
    except PersistenceError as error:
        session.rollback()
        status_code = (
            status.HTTP_404_NOT_FOUND
            if str(error).startswith("entity not found")
            else status.HTTP_409_CONFLICT
        )
        raise HTTPException(status_code=status_code, detail=str(error)) from error
