from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import carriers, rules, selection
from app.core.config import Settings
from app.database.session import init_db, make_engine
from app.services.distance import DistanceProvider


def create_app(settings: Settings | None = None, *, distance_provider: DistanceProvider | None = None) -> FastAPI:
    settings = settings or Settings()
    db_engine = make_engine(settings.database_url)

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        init_db(db_engine)
        yield
        db_engine.dispose()

    app = FastAPI(title="Carrier Selector API", lifespan=lifespan)
    app.state.settings = settings
    app.state.db_engine = db_engine
    app.state.distance_provider = distance_provider

    app.add_middleware(
        CORSMiddleware,
        allow_origins=[settings.frontend_origin],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    app.include_router(selection.router)
    app.include_router(carriers.router)
    app.include_router(rules.router)
    return app


app = create_app()
