from typing import Annotated

from fastapi import APIRouter, HTTPException, Query

from app.api.deps import SelectionServiceDep, SessionDep
from app.schemas.selection import SelectCarrierRequest, SelectionRecord, SelectionResponse, SelectionSummary
from app.services.selection_history import get_selection, list_selections

router = APIRouter(tags=["selection"])


@router.post("/select-carrier", response_model=SelectionResponse)
def select_carrier(request: SelectCarrierRequest, service: SelectionServiceDep) -> SelectionResponse:
    """Pick the best carrier for an Order given as free text or as fields.

    Business outcomes (including needs_review and jev_unavailable) are reported in `status`, always with HTTP 200.
    """
    return service.run(request)


@router.get("/selections", response_model=list[SelectionSummary])
def selections(session: SessionDep, limit: Annotated[int, Query(ge=1, le=100)] = 20) -> list[SelectionSummary]:
    """Stored Selections, newest first."""
    return list_selections(session, limit)


@router.get("/selections/{selection_id}", response_model=SelectionRecord)
def selection(selection_id: int, session: SessionDep) -> SelectionRecord:
    record = get_selection(session, selection_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Seçim bulunamadı")
    return record
