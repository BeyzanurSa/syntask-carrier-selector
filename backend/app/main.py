from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import carriers, cities, rules, selection
from app.core.config import Settings
from app.database.session import init_db, make_engine
from app.services.distance import DistanceProvider
from app.services.interpreter import Interpreter
from app.services.osrm_provider import OsrmNominatimProvider


def create_app(
    settings: Settings | None = None,
    *,
    distance_provider: DistanceProvider | None = None,
    interpreter: Interpreter | None = None,
) -> FastAPI:
    settings = settings or Settings()
    if interpreter is None and settings.jev_enabled and settings.typesafe_api_key is not None:
        from app.services.typesafe_interpreter import TypeSafeInterpreter

        interpreter = TypeSafeInterpreter.from_settings(settings)
    if distance_provider is None and settings.distance_api_enabled:
        distance_provider = OsrmNominatimProvider(country_codes=settings.distance_country_codes)
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
    app.state.interpreter = interpreter

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
    app.include_router(cities.router)
    return app


app = create_app()
