from fastapi import FastAPI, HTTPException, status

from app.domain.models import EntityCreate, EntityTemplate
from app.services.registry import EntityRegistry, RegistryError

app = FastAPI(title="IoT Digital Twin API", version="0.1.0")
registry = EntityRegistry()


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
    return registry.register_template(template)


@app.get("/api/v1/entities")
def list_entities():
    return registry.list_entities()


@app.post("/api/v1/entities", status_code=status.HTTP_201_CREATED)
def create_entity(payload: EntityCreate):
    try:
        return registry.create_entity(payload)
    except RegistryError as error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(error)
        ) from error


@app.get("/api/v1/entities/{entity_id}")
def get_entity(entity_id: str):
    try:
        return registry.get_entity(entity_id)
    except RegistryError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error)) from error
