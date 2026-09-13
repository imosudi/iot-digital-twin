from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.domain.enums import AssetClass, TwinLifecycleStatus
from app.domain.twin import (
    DigitalTwin,
    DigitalTwinCreate,
    DigitalTwinUpdate,
    LifecycleTransitionRequest,
    TwinEvent,
    TwinEventCreate,
)
from app.persistence.database import get_session
from app.services.twin_service import (
    InvalidHierarchyError,
    InvalidTransitionError,
    TwinAlreadyExistsError,
    TwinNotFoundError,
    TwinServiceError,
    create_twin,
    create_twin_event,
    delete_twin,
    get_twin,
    get_twin_children,
    get_twin_events,
    list_twins,
    transition_lifecycle,
    update_twin,
)

router = APIRouter(prefix="/api/v1/twins", tags=["Digital Twins"])


@router.get("", response_model=list[DigitalTwin])
def get_twins(
    site_id: str | None = Query(default=None),
    asset_class: AssetClass | None = Query(default=None),
    status_filter: TwinLifecycleStatus | None = Query(default=None, alias="status"),
    parent_twin_id: str | None = Query(default=None),
    tenant_id: str | None = Query(default=None),
    session: Session = Depends(get_session),
) -> list[DigitalTwin]:
    return list_twins(
        session,
        site_id=site_id,
        asset_class=asset_class,
        status=status_filter,
        parent_twin_id=parent_twin_id,
        tenant_id=tenant_id,
    )


@router.post("", response_model=DigitalTwin, status_code=status.HTTP_201_CREATED)
def register_twin(
    payload: DigitalTwinCreate, session: Session = Depends(get_session)
) -> DigitalTwin:
    try:
        twin = create_twin(session, payload)
        session.commit()
        return twin
    except TwinAlreadyExistsError as error:
        session.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(error)) from error
    except (InvalidHierarchyError, TwinServiceError) as error:
        session.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error


@router.get("/{twin_id}", response_model=DigitalTwin)
def get_single_twin(twin_id: str, session: Session = Depends(get_session)) -> DigitalTwin:
    try:
        return get_twin(session, twin_id)
    except TwinNotFoundError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error)) from error


@router.patch("/{twin_id}", response_model=DigitalTwin)
def patch_twin(
    twin_id: str, payload: DigitalTwinUpdate, session: Session = Depends(get_session)
) -> DigitalTwin:
    try:
        updated = update_twin(session, twin_id, payload)
        session.commit()
        return updated
    except TwinNotFoundError as error:
        session.rollback()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error)) from error
    except (InvalidHierarchyError, TwinServiceError) as error:
        session.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error


@router.delete("/{twin_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_twin(twin_id: str, session: Session = Depends(get_session)) -> None:
    try:
        delete_twin(session, twin_id)
        session.commit()
    except TwinNotFoundError as error:
        session.rollback()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error)) from error


@router.post("/{twin_id}/transition", response_model=DigitalTwin)
def transition_twin_lifecycle(
    twin_id: str,
    payload: LifecycleTransitionRequest,
    session: Session = Depends(get_session),
) -> DigitalTwin:
    try:
        twin = transition_lifecycle(session, twin_id, payload)
        session.commit()
        return twin
    except TwinNotFoundError as error:
        session.rollback()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error)) from error
    except InvalidTransitionError as error:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(error)
        ) from error


@router.get("/{twin_id}/children", response_model=list[DigitalTwin])
def get_children(twin_id: str, session: Session = Depends(get_session)) -> list[DigitalTwin]:
    try:
        return get_twin_children(session, twin_id)
    except TwinNotFoundError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error)) from error


@router.get("/{twin_id}/events", response_model=list[TwinEvent])
def get_events(
    twin_id: str,
    limit: int = Query(default=100, ge=1, le=500),
    session: Session = Depends(get_session),
) -> list[TwinEvent]:
    try:
        return get_twin_events(session, twin_id, limit=limit)
    except TwinNotFoundError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error)) from error


@router.post("/{twin_id}/events", response_model=TwinEvent, status_code=status.HTTP_201_CREATED)
def add_twin_event(
    twin_id: str,
    payload: TwinEventCreate,
    session: Session = Depends(get_session),
) -> TwinEvent:
    try:
        event = create_twin_event(session, twin_id, payload)
        session.commit()
        return event
    except TwinNotFoundError as error:
        session.rollback()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error)) from error
