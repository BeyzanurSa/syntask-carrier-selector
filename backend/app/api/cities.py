from typing import Annotated

from fastapi import APIRouter, Query
from pydantic import BaseModel

from app.api.deps import SessionDep
from app.services.city_catalog import check_city, known_cities

router = APIRouter(prefix="/cities", tags=["cities"])


class CityCheck(BaseModel):
    known: bool
    normalized: str
    suggestion: str | None  # closest known city when the name looks like a typo


@router.get("", response_model=list[str])
def list_cities(session: SessionDep) -> list[str]:
    """Cities the system already knows: case table, carrier HQs and cached routes."""
    return known_cities(session)


@router.get("/check", response_model=CityCheck)
def check(name: Annotated[str, Query(min_length=1, max_length=100, pattern=r"\S")], session: SessionDep) -> CityCheck:
    known, normalized, suggestion = check_city(name, known_cities(session))
    return CityCheck(known=known, normalized=normalized, suggestion=suggestion)
