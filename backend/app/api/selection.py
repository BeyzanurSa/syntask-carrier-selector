from typing import Annotated

from fastapi import APIRouter, HTTPException, Query

from app.api.deps import SelectionServiceDep, SessionDep
from app.schemas.selection import SelectionRecord, SelectionResponse, SelectionSummary, StructuredOrder
from app.services.selection_history import get_selection, list_selections

router = APIRouter(tags=["selection"])


@router.post("/select-carrier", response_model=SelectionResponse)
def select_carrier(order: StructuredOrder, service: SelectionServiceDep) -> SelectionResponse:
    """Pick the best carrier for an Order. Business outcomes are reported in `status`, always with HTTP 200."""
    return service.run(order)


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
