"""Fetch road distances for demo routes once, so the live demo does not depend on the public OSRM/Nominatim servers.

Routes in the case table need nothing. For every other route, and for every carrier HQ → origin pair that
HQ proximity will ask for, this stores the distance in the distance_cache table.

Usage (from backend/):
    .venv/bin/python -m app.warm_cache                       # default demo routes
    .venv/bin/python -m app.warm_cache Miami:Boston Tampa:Tallahassee
"""

import sys

from sqlmodel import Session, select

from app.core.config import Settings
from app.data.case_distances import CASE_DISTANCES
from app.database.models import Carrier
from app.database.session import init_db, make_engine
from app.services.distance import DistanceService
from app.services.osrm_provider import OsrmNominatimProvider

# Off-table routes we may show live, e.g. a free-text Order naming a city outside the case table.
DEFAULT_ROUTES = [("Miami", "Boston"), ("Tallahassee", "Atlanta"), ("Tampa", "Savannah")]


def main(argv: list[str]) -> None:
    if any(arg.count(":") != 1 for arg in argv):
        sys.exit("Kullanım: python -m app.warm_cache [Şehir:Şehir ...]   örn. Miami:Boston")
    routes = [tuple(arg.split(":")) for arg in argv] if argv else DEFAULT_ROUTES
    settings = Settings()
    engine = make_engine(settings.database_url)
    init_db(engine)

    with Session(engine) as session:
        distances = DistanceService(OsrmNominatimProvider(settings.distance_country_codes), session)
        hqs = sorted({c.headquarters_city for c in session.exec(select(Carrier)).all()})
        origins = sorted({city for pair in CASE_DISTANCES for city in pair} | {a for a, _ in routes})

        pairs = list(routes) + [(hq, origin) for hq in hqs for origin in origins]
        for a, b in pairs:
            result = distances.get(a, b)
            shown = f"{result.miles} mil ({result.source})" if result else "bilinmiyor"
            print(f"{a:>16} → {b:<16} {shown}")


if __name__ == "__main__":
    main(sys.argv[1:])
