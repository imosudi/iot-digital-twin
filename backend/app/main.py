import os
from fastapi.responses import FileResponse, Response
from fastapi.openapi.docs import get_swagger_ui_html, get_redoc_html
from typing import Any
import time

from fastapi import Depends, FastAPI, HTTPException, Query, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from app.config import settings
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
from app.routers.twins import router as twins_router
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

STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")
FAVICON_ICO_PATH = os.path.join(STATIC_DIR, "favicon.ico")
FAVICON_SVG_PATH = os.path.join(STATIC_DIR, "favicon.svg")

FAVICON_FALLBACK_SVG = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">
  <rect width="64" height="64" rx="14" fill="#0f766e"/>
  <text x="32" y="43" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif" font-size="28" font-weight="800" fill="#ffffff" text-anchor="middle" letter-spacing="-0.5">DT</text>
</svg>"""

app = FastAPI(
    title="TwinField — REGENOVA Digital Twin Sub-API",
    version="0.3.0",
    description="Dedicated Digital Twin sub-API for the REGENOVA Framework.",
    docs_url=None,
    redoc_url=None,
)

@app.get("/docs", include_in_schema=False)
async def custom_swagger_ui():
    return get_swagger_ui_html(
        openapi_url=app.openapi_url,
        title=f"{app.title} - Swagger UI",
        swagger_favicon_url="/favicon.ico",
    )

@app.get("/redoc", include_in_schema=False)
async def custom_redoc_ui():
    return get_redoc_html(
        openapi_url=app.openapi_url,
        title=f"{app.title} - ReDoc",
        redoc_favicon_url="/favicon.ico",
    )

@app.api_route("/favicon.ico", methods=["GET", "HEAD"], include_in_schema=False)
def favicon_ico():
    if os.path.exists(FAVICON_ICO_PATH):
        return FileResponse(FAVICON_ICO_PATH, media_type="image/x-icon")
    return Response(content=FAVICON_FALLBACK_SVG, media_type="image/svg+xml")

@app.api_route("/favicon.svg", methods=["GET", "HEAD"], include_in_schema=False)
def favicon_svg():
    if os.path.exists(FAVICON_SVG_PATH):
        return FileResponse(FAVICON_SVG_PATH, media_type="image/svg+xml")
    return Response(content=FAVICON_FALLBACK_SVG, media_type="image/svg+xml")


app.include_router(twins_router)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def add_process_time_header(request, call_next):
    start_time = time.perf_counter()
    response = await call_next(request)
    process_time = time.perf_counter() - start_time
    response.headers["X-Process-Time"] = f"{process_time:.6f}"
    return response


init_db()
registry = EntityRegistry()
with SessionLocal() as session:
    for template in load_templates(session):
        registry.register_template(template)


@app.get("/")
def root() -> dict[str, Any]:
    return {
        "service": "TwinField — REGENOVA Digital Twin Sub-API",
        "framework": "REGENOVA (incorporating REAMP Engine Architecture)",
        "status": "healthy",
        "version": "0.3.0",
        "api_endpoint": "https://twinfield.regenova.cloud/",
        "docs": "https://twinfield.regenova.cloud/docs",
        "openapi": "https://twinfield.regenova.cloud/openapi.json",
        "health": "https://twinfield.regenova.cloud/health",
        "ready": "https://twinfield.regenova.cloud/ready",
        "endpoints": [
            "/api/v1/twins",
            "/api/v1/twins/{twin_id}",
            "/api/v1/twins/{twin_id}/transition",
            "/api/v1/twins/{twin_id}/telemetry",
            "/api/v1/twins/{twin_id}/predict",
            "/api/v1/entities",
            "/api/v1/entities/{entity_id}",
            "/api/v1/sites",
            "/api/v1/relationships",
            "/api/v1/templates",
            "/health",
            "/ready",
            "/docs",
            "/openapi.json"
        ],
        "integrated_portals": {
            "operations_portal": "https://regenova.cloud/portal.html",
            "superadmin_backoffice": "https://backoffice.regenova.cloud/",
            "framework_home": "https://regenova.cloud/"
        }
    }


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
def create_entity(payload: EntityCreate, session: Session = Depends(get_session)) -> DigitalEntity:
    try:
        entity = registry.create_entity(payload)
        persisted_entity = save_entity(session, entity)
        session.commit()
        return persisted_entity
    except RegistryError as error:
        session.rollback()
        unprocessable_status = getattr(
            status, "HTTP_422_UNPROCESSABLE_CONTENT", status.HTTP_422_UNPROCESSABLE_ENTITY
        )
        raise HTTPException(status_code=unprocessable_status, detail=str(error)) from error
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
