"""Carrier CRUD. Carriers are plain data: nothing here knows about any specific carrier."""

from datetime import UTC, datetime

from sqlmodel import Session, select

from app.database.models import Carrier
from app.schemas.carrier import CarrierIn


class CarrierNotFound(LookupError):
    pass


class DuplicateCarrierName(ValueError):
    pass


def list_carriers(session: Session) -> list[Carrier]:
    return list(session.exec(select(Carrier).order_by(Carrier.name)).all())


def get_carrier(session: Session, carrier_id: int) -> Carrier:
    carrier = session.get(Carrier, carrier_id)
    if carrier is None:
        raise CarrierNotFound(carrier_id)
    return carrier


def create_carrier(session: Session, data: CarrierIn) -> Carrier:
    _ensure_name_free(session, data.name)
    carrier = Carrier(**data.model_dump())
    session.add(carrier)
    session.commit()
    session.refresh(carrier)
    return carrier


def replace_carrier(session: Session, carrier_id: int, data: CarrierIn) -> Carrier:
    carrier = get_carrier(session, carrier_id)
    _ensure_name_free(session, data.name, except_id=carrier_id)
    for field, value in data.model_dump().items():
        setattr(carrier, field, value)
    carrier.updated_at = datetime.now(UTC)
    session.add(carrier)
    session.commit()
    session.refresh(carrier)
    return carrier


def delete_carrier(session: Session, carrier_id: int) -> None:
    """Hard delete. Past Selections keep their own snapshot, so they stay readable."""
    session.delete(get_carrier(session, carrier_id))
    session.commit()


def _ensure_name_free(session: Session, name: str, except_id: int | None = None) -> None:
    existing = session.exec(select(Carrier).where(Carrier.name == name)).first()
    if existing is not None and existing.id != except_id:
        raise DuplicateCarrierName(name)
