from sqlalchemy import Engine
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine, select

from app.data.seed_carriers import SEED_CARRIERS
from app.database.models import Carrier


def make_engine(database_url: str) -> Engine:
    if database_url == "sqlite://":
        # In-memory database (tests): one shared connection, usable from the test client's threads.
        return create_engine(database_url, connect_args={"check_same_thread": False}, poolclass=StaticPool)
    return create_engine(database_url, connect_args={"check_same_thread": False})


def init_db(engine: Engine) -> None:
    """Create tables and load the case carriers into an empty database."""
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        if session.exec(select(Carrier)).first() is None:
            session.add_all(Carrier(**data) for data in SEED_CARRIERS)
            session.commit()
