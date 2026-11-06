"""Constraints: rules a carrier must satisfy to be Eligible. Each returns a Turkish reason when it fails."""

from typing import Protocol

from app import messages
from app.engine.types import CarrierSpec, OrderContext


class Constraint(Protocol):
    name: str
    label: str

    def check(self, carrier: CarrierSpec, ctx: OrderContext) -> list[str]:
        """The reasons the carrier fails; empty if it passes."""
        ...


class ActiveConstraint:
    name = "active"
    label = "Firma aktif"

    def check(self, carrier: CarrierSpec, ctx: OrderContext) -> list[str]:
        return [] if carrier.is_active else [messages.INACTIVE]


class DistanceRangeConstraint:
    """Bounds are inclusive (the case says <= and >=). A missing bound means no limit."""

    name = "distance_range"
    label = "Mesafe aralığı"

    def check(self, carrier: CarrierSpec, ctx: OrderContext) -> list[str]:
        miles = ctx.route_miles
        if carrier.min_distance is not None and miles < carrier.min_distance:
            return [messages.below_min_distance(miles, carrier.min_distance)]
        if carrier.max_distance is not None and miles > carrier.max_distance:
            return [messages.above_max_distance(miles, carrier.max_distance)]
        return []


class ContainerSizeConstraint:
    name = "container_size"
    label = "Konteyner boyutu"

    def check(self, carrier: CarrierSpec, ctx: OrderContext) -> list[str]:
        size = ctx.order.container_size
        if size in carrier.supported_container_sizes:
            return []
        return [messages.unsupported_container(size, carrier.supported_container_sizes)]


class CargoTypeConstraint:
    name = "cargo_type"  # rule name kept stable for rules.yaml
    label = "Yük tipi"

    def check(self, carrier: CarrierSpec, ctx: OrderContext) -> list[str]:
        """Every requested cargo type must be supported; each missing one is its own reason."""
        return [
            messages.unsupported_cargo(cargo, carrier.supported_cargo_types)
            for cargo in ctx.order.cargo_types
            if cargo not in carrier.supported_cargo_types
        ]


CONSTRAINTS: dict[str, Constraint] = {
    c.name: c
    for c in (ActiveConstraint(), DistanceRangeConstraint(), ContainerSizeConstraint(), CargoTypeConstraint())
}
