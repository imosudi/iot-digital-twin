from collections.abc import Iterable

from app.domain.models import DigitalEntity, EntityCreate, EntityTemplate


class RegistryError(ValueError):
    """Raised when a template or entity cannot be resolved or validated."""


class EntityRegistry:
    def __init__(self, templates: Iterable[EntityTemplate] = ()) -> None:
        self._templates = {(template.type, template.version): template for template in templates}
        self._entities: dict[str, DigitalEntity] = {}

    def list_templates(self) -> list[EntityTemplate]:
        return list(self._templates.values())

    def register_template(self, template: EntityTemplate) -> EntityTemplate:
        self._templates[(template.type, template.version)] = template
        return template

    def create_entity(self, payload: EntityCreate) -> DigitalEntity:
        template = self._templates.get((payload.type, payload.version))
        if template is None or template.type != payload.template:
            raise RegistryError("entity template and version are not registered")
        self._validate_properties(payload.properties, template)
        entity = DigitalEntity(
            id=payload.name.lower().replace(" ", "-"),
            site_id=payload.site_id,
            type=payload.type,
            name=payload.name,
            template=payload.template,
            version=payload.version,
            description=payload.description,
            properties=payload.properties,
            metadata=payload.metadata,
        )
        if entity.id in self._entities:
            raise RegistryError("an entity with this generated id already exists")
        self._entities[entity.id] = entity
        return entity

    def list_entities(self) -> list[DigitalEntity]:
        return list(self._entities.values())

    def get_entity(self, entity_id: str) -> DigitalEntity:
        try:
            return self._entities[entity_id]
        except KeyError as error:
            raise RegistryError("entity not found") from error

    @staticmethod
    def _validate_properties(properties: dict, template: EntityTemplate) -> None:
        missing = [
            name
            for name, definition in template.properties.items()
            if definition.required and name not in properties
        ]
        if missing:
            raise RegistryError(f"missing required properties: {', '.join(missing)}")
