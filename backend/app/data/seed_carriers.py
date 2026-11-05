"""The four carriers given in the case. Loaded into an empty database on startup."""

from decimal import Decimal

SEED_CARRIERS: list[dict] = [
    {
        "name": "S-Logistics",
        "headquarters_city": "Tampa",
        "min_distance": None,
        "max_distance": 300,
        "supported_container_sizes": [40, 45],
        "supported_cargo_types": ["Dry"],
        "price_per_mile": Decimal("0.40"),
    },
    {
        "name": "B-Logistics",
        "headquarters_city": "Fort Lauderdale",
        "min_distance": 250,
        "max_distance": None,
        "supported_container_sizes": [20],
        "supported_cargo_types": ["Dry", "Reefer"],
        "price_per_mile": Decimal("1.00"),
    },
    {
        "name": "A-Logistics",
        "headquarters_city": "Jacksonville",
        "min_distance": None,
        "max_distance": 200,
        "supported_container_sizes": [45],
        "supported_cargo_types": ["Dry", "Hazardous"],
        "price_per_mile": Decimal("2.00"),
    },
    {
        "name": "M-Logistics",
        "headquarters_city": "Houston",
        "min_distance": None,
        "max_distance": None,
        "supported_container_sizes": [20, 40],
        "supported_cargo_types": ["Dry", "Reefer", "Hazardous"],
        "price_per_mile": Decimal("1.00"),
    },
]
