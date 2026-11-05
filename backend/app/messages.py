"""All user-facing Turkish texts in one place, so wording changes never touch decision code."""

from collections.abc import Iterable
from decimal import Decimal


def money(amount: Decimal) -> str:
    return f"${amount:,.2f}"


def miles(value: Decimal) -> str:
    return f"{value.normalize():f} mil"


def _join(values: Iterable) -> str:
    return ", ".join(str(v) for v in values)


# Constraints
INACTIVE = "Firma pasif"


def below_min_distance(route: Decimal, minimum: int) -> str:
    return f"Mesafe alt sınırın altında: {miles(route)} < {minimum} mil"


def above_max_distance(route: Decimal, maximum: int) -> str:
    return f"Mesafe üst sınırı aşıyor: {miles(route)} > {maximum} mil"


def unsupported_container(size: int, supported: Iterable[int]) -> str:
    return f"{size} ft konteyner desteklenmiyor (desteklenen: {_join(supported)} ft)"


def unsupported_cargo(cargo: str, supported: Iterable[str]) -> str:
    return f"{cargo} yük tipi desteklenmiyor (desteklenen: {_join(supported)})"


# Carriers
def hq_distance_unknown(city: str) -> str:
    return (
        f"{city} için mesafe bilinmiyor: merkez yakınlığı ölçülemez, "
        "bu firma o kriterde sıralamanın sonuna kalır."
    )


# Ranking
HQ_DISTANCE_UNKNOWN = "Merkezin çıkış şehrine mesafesi bilinmiyor"
HQ_DISTANCE_UNKNOWN_SHORT = "bilinmiyor"
LOST_ON_NAME = "Tüm kriterler eşit; isim sırasında geride"


def cost_higher_by(difference: Decimal) -> str:
    return f"Toplam ücret {money(difference)} daha yüksek"


def hq_farther_by(origin: str, difference: Decimal) -> str:
    return f"Merkezi çıkış şehrine ({origin}) {miles(difference)} daha uzak"


# Outcomes
NO_ELIGIBLE_CARRIER = "Uygun taşıyıcı bulunamadı: hiçbir firma tüm zorunlu koşulları sağlamıyor."
SAME_CITY = "Çıkış ve varış şehri aynı olamaz."


def unknown_route(origin: str, destination: str) -> str:
    return f"Rota mesafesi bilinmiyor ({origin} → {destination}). Tahmin yapılmadı, taşıyıcı seçilmedi."


def only_eligible(name: str, total: Decimal) -> str:
    return f"{name} seçildi: tüm zorunlu koşulları sağlayan tek firma (toplam ücret {money(total)})."


def tie_on(label: str, value: str) -> str:
    return f"{label.lower()} eşit ({value})"


def won_on(
    name: str,
    runner_up: str,
    label: str,
    winner_value: str,
    runner_up_value: str,
    ties: list[str],
) -> str:
    parts = [*ties, f"{label.lower()} daha avantajlı ({winner_value}; sıradaki {runner_up}: {runner_up_value})"]
    return f"{name} seçildi: {', '.join(parts)}."


def won_on_name(name: str, runner_up: str, ties: list[str]) -> str:
    return f"{name} seçildi: {', '.join(ties)}; eşitlik isim sırasıyla bozuldu ({runner_up} geride)."
