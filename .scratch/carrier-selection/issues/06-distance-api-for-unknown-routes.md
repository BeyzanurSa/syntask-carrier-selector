# 06: Road distance API for routes outside the case table

**What to build:** An Order between cities that are not in the case table still gets a route distance from Nominatim geocoding + OSRM road routing, which is then cached, and the UI shows that the distance came from the API. When no distance can be obtained the Order returns `unknown_route` and no Carrier is selected. A Carrier whose HQ proximity cannot be measured is ranked last on that criterion, and the Carrier form warns when a new HQ city has no known distance. No straight-line estimate is ever used. See ADR 0003.

**Blocked by:** 02, 04

**Status:** done

- [x] Resolution order is case table → cache → provider; case-table values always win
- [x] A provider result is cached and the second identical Order does not call the provider (tested with the fake provider)
- [x] Provider failure, timeout or unknown city yields `unknown_route` with a Turkish reason
- [x] Responses show distance source `table` or `api`
- [x] A Carrier with unknown HQ proximity sorts last on that criterion and the explanation says so
- [x] Creating or editing a Carrier with an unmeasurable HQ returns a warning, not an error
- [x] Adapter tests with mocked HTTP cover meters → miles conversion, city not found, timeout and HTTP errors
- [x] The provider sends a descriptive User-Agent, uses a 5 s timeout and keeps to 1 Nominatim request per second
