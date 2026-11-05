"""Constraints: rules a carrier must satisfy to be Eligible. Each returns a Turkish reason when it fails."""

from typing import Protocol

from app import messages
from app.engine.types import CarrierSpec, OrderContext


class Constraint(Protocol):
    name: str

    def check(self, carrier: CarrierSpec, ctx: OrderContext) -> str | None:
        """None if the carrier passes, otherwise the reason it fails."""
        ...


class ActiveConstraint:
    name = "active"

    def check(self, carrier: CarrierSpec, ctx: OrderContext) -> str | None:
        return None if carrier.is_active else messages.INACTIVE


class DistanceRangeConstraint:
    """Bounds are inclusive (the case says <= and >=). A missing bound means no limit."""

    name = "distance_range"

    def check(self, carrier: CarrierSpec, ctx: OrderContext) -> str | None:
        miles = ctx.route_miles
        if carrier.min_distance is not None and miles < carrier.min_distance:
            return messages.below_min_distance(miles, carrier.min_distance)
        if carrier.max_distance is not None and miles > carrier.max_distance:
            return messages.above_max_distance(miles, carrier.max_distance)
        return None


class ContainerSizeConstraint:
    name = "container_size"

    def check(self, carrier: CarrierSpec, ctx: OrderContext) -> str | None:
        size = ctx.order.container_size
        if size in carrier.supported_container_sizes:
            return None
        return messages.unsupported_container(size, carrier.supported_container_sizes)


class CargoTypeConstraint:
    name = "cargo_type"

    def check(self, carrier: CarrierSpec, ctx: OrderContext) -> str | None:
        cargo = ctx.order.cargo_type
        if cargo in carrier.supported_cargo_types:
            return None
        return messages.unsupported_cargo(cargo, carrier.supported_cargo_types)


CONSTRAINTS: dict[str, Constraint] = {
    c.name: c
    for c in (ActiveConstraint(), DistanceRangeConstraint(), ContainerSizeConstraint(), CargoTypeConstraint())
}
