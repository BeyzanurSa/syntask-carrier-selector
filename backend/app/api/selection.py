from fastapi import APIRouter

from app.api.deps import SelectionServiceDep
from app.schemas.selection import SelectionResponse, StructuredOrder

router = APIRouter(tags=["selection"])


@router.post("/select-carrier", response_model=SelectionResponse)
def select_carrier(order: StructuredOrder, service: SelectionServiceDep) -> SelectionResponse:
    """Pick the best carrier for an Order. Business outcomes are reported in `status`, always with HTTP 200."""
    return service.run(order)
