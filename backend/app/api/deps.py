"""FastAPI dependencies. Everything the routes need is built here from app.state, so tests can swap it."""

from collections.abc import Iterator
from typing import Annotated

from fastapi import Depends, Request
from sqlmodel import Session

from app.services.distance import DistanceService
from app.services.rules_store import RulesStore
from app.services.selection import SelectionService


def get_session(request: Request) -> Iterator[Session]:
    with Session(request.app.state.db_engine) as session:
        yield session


SessionDep = Annotated[Session, Depends(get_session)]


def get_selection_service(request: Request, session: SessionDep) -> SelectionService:
    state = request.app.state
    return SelectionService(
        session=session,
        distances=DistanceService(state.distance_provider),
        rules=RulesStore(state.settings.rules_path),
    )


SelectionServiceDep = Annotated[SelectionService, Depends(get_selection_service)]
