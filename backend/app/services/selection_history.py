"""Read access to stored Selections. Selections are never updated or deleted."""

from sqlmodel import Session, col, select

from app.database.models import Selection
from app.schemas.selection import SelectionRecord, SelectionSummary


def list_selections(session: Session, limit: int) -> list[SelectionSummary]:
    rows = session.exec(select(Selection).order_by(col(Selection.id).desc()).limit(limit)).all()
    return [
        SelectionSummary(
            id=row.id,
            created_at=row.created_at,
            status=row.status,
            input_text=row.input.get("text"),
            **_order_fields(row),
            selected_carrier_name=row.selected_carrier_name,
            total_cost=row.total_cost,
        )
        for row in rows
    ]


def get_selection(session: Session, selection_id: int) -> SelectionRecord | None:
    row = session.get(Selection, selection_id)
    if row is None:
        return None
    return SelectionRecord(
        id=row.id,
        created_at=row.created_at,
        input_kind=row.input_kind,
        input=row.input,
        ranking_used=row.ranking_used,
        status=row.status,
        response=row.response,
    )


def _order_fields(row: Selection) -> dict:
    """Route and load of the decided Order; empty when the text never became an Order (review, Jev down)."""
    order = row.response.get("order") or {}
    cargo_types = order.get("cargo_types") or ([order["cargo_type"]] if order.get("cargo_type") else None)
    return {**{key: order.get(key) for key in ("origin", "destination", "container_size")}, "cargo_types": cargo_types}
