---
title: Carrier Selection System (Case 1)
label: ready-for-agent
created: 2026-11-05
glossary: CONTEXT.md
adrs: [0001-jev-interprets-code-decides, 0002-rules-yaml-single-source-of-truth, 0003-road-distance-api-no-estimates]
---

## Problem Statement

An operations team receives container transport Orders, sometimes as structured fields and sometimes as free text ("Miami'den Orlando'ya 40'lık kuru yük"). For each Order they must pick a Carrier that accepts its distance, container size and cargo type, and that costs the least. A tie goes to the Carrier whose Headquarters is closest to the origin. Today this is done by hand. The reasoning is not recorded, Carrier notes are easy to miss, and when the business changes its priorities (for example "proximity matters more than price") every decision has to be re-thought manually. The team needs a system that makes this decision the same way every time, explains it, refuses to guess when the input is unclear, and lets them change the Rule set and the Carrier list without a developer.

## Solution

A web application with a Python backend and a Next.js operations dashboard:

- Operators manage Carriers (create, edit, delete, activate/deactivate, edit the Carrier note) from a Carrier management screen.
- Operators submit an Order either as structured fields or as free text. For free text, Jev interprets the Order into its fields, with a confidence for each one. If any field is uncertain, the Order goes into Review: the form comes back prefilled and asks the operator to confirm the uncertain field. No Carrier is assigned until then.
- Deterministic code checks every Constraint, computes total cost as route distance × price per mile, ranks the Eligible carriers by the Ranking criteria in `rules.yaml`, and returns the selected Carrier, the cost, the route distance with its source, a reason, the Outranked carriers with why they lost, and the Rejected carriers with every failed Constraint.
- Jev also reads each Eligible carrier's note and raises a Note warning when the note signals a risk for this Order. It never changes the decision.
- Every decision is stored as an immutable Selection snapshot, shown on the dashboard and openable later.
- Operators can reorder or toggle the Ranking criteria from a Rule configuration screen. The change is written to `rules.yaml` and applies to the next Order immediately.

## User Stories

### Orders and selection
1. As an operator, I want to submit an Order with origin, destination, container size and cargo type, so that I get the best Carrier without calculating by hand.
2. As an operator, I want to type an Order in free Turkish or English text, so that I can paste what a customer wrote without retyping fields.
3. As an operator, I want to see the selected Carrier, total cost and route distance, so that I can book the transport.
4. As an operator, I want a plain-language reason for the selection, so that I can justify the choice to my manager or the customer.
5. As an operator, I want every Rejected carrier listed with all the Constraints it failed, so that I understand why it was not considered.
6. As an operator, I want every Outranked carrier listed in ranking order with its cost and the criterion it lost on (e.g. "$141 more expensive"), so that I can see the alternatives.
7. As an operator, I want to be told clearly when no Carrier can take the Order, with each Carrier's reasons, so that I can escalate instead of guessing.
8. As an operator, I want ties on cost to be broken by HQ proximity to the origin, so that the closer Carrier is preferred.
9. As an operator, I want ties that remain after HQ proximity to be broken by Carrier name, so that the result never depends on chance or insertion order.
10. As an operator, I want the route distance's source (case table or distance API) shown, so that I know how trustworthy the figure is.
11. As an operator, I want an Order whose origin equals its destination to be rejected as invalid, so that nonsense Orders don't produce a booking.
12. As an operator, I want an Order with an unsupported container size or cargo type to be rejected with a validation message, so that typos are caught early.
13. As an operator, I want an Order on a route that cannot be measured to return "unknown route" instead of an estimate, so that I never book on a made-up price.
14. As an operator, I want distances for routes outside the case table to be looked up from a road distance API and remembered, so that new cities work without manual data entry.
15. As an operator, I want city names to be matched case-insensitively and through common aliases ("Ft. Lauderdale"), so that formatting does not break a lookup.
16. As an operator, I want boundary distances (exactly 200, 250 or 300 miles) to count as inside the range, so that the rules match the case wording (≤, ≥).

### Interpretation and confidence
17. As an operator, I want Jev to fill origin, destination, container size and cargo type from my free text, so that I save typing.
18. As an operator, I want to see the confidence of each interpreted field, so that I know which parts the system is unsure about.
19. As an operator, I want the system to stop and ask me when any field is below the confidence threshold, so that no Carrier is assigned on a guess.
20. As an operator, I want the Review form prefilled with Jev's suggestions and the uncertain fields highlighted with a question ("Konteyner boyutu belirtilmemiş: 20 / 40 / 45?"), so that I only fix what is unclear.
21. As an operator, I want a field Jev marked as unspecified to always go to Review, even if its confidence is high, so that a missing value is never invented.
22. As an operator, I want a city Jev could not match to a known city to go to Review, so that I can enter it explicitly.
23. As an operator, I want a missing confidence value from Jev to be treated as low, so that a gap in the response cannot slip through.
24. As an operator, I want structured Orders to skip Jev completely, so that they work even when Jev is down.
25. As an operator, I want a clear "Jev is unavailable, please use the form" message when Jev cannot be reached, so that I can keep working.
26. As an operator, I want the overall confidence shown as the weakest field's confidence, so that one shaky field is not hidden by an average.

### Carrier notes
27. As an operator, I want each Eligible carrier's note checked against the Order, so that I don't miss restrictions written in free text.
28. As an operator, I want a Note warning with the note text shown next to an affected Carrier, so that I can decide whether to call the Carrier first.
29. As an operator, I want Note warnings to never change the selected Carrier, so that an AI misreading cannot silently reroute a booking.
30. As an operator, I want to be told when notes could not be checked because Jev was unavailable, so that I know the warnings list may be incomplete.

### Carrier management
31. As an admin, I want to list all Carriers with their HQ, distance range, container sizes, cargo types, price and status, so that I see the network at a glance.
32. As an admin, I want to add a Carrier through a form, so that a new partner is used in the next selection without any code change.
33. As an admin, I want to edit any field of a Carrier, including its note, so that the data stays current.
34. As an admin, I want to deactivate a Carrier without deleting it, so that I can pause a partner temporarily.
35. As an operator, I want inactive Carriers to appear among the Rejected carriers with "Firma pasif", so that I understand why they were skipped.
36. As an admin, I want to delete a Carrier after a confirmation dialog, so that I don't remove one by accident.
37. As an admin, I want past Selections to stay readable after a Carrier is edited or deleted, so that the audit trail is never broken.
38. As an admin, I want the form to reject a duplicate name, a non-positive price, min distance greater than max distance, and empty container size or cargo type lists, so that bad data never reaches the engine.
39. As an admin, I want to leave the max distance empty to mean "unlimited", so that Carriers like M-Logistics can be modeled.
40. As an admin, I want a warning (not an error) when a new Carrier's HQ city has no known distance, so that I know HQ proximity may rank it last.
41. As an admin, I want a free attributes field (e.g. reliability) on each Carrier, so that new Ranking criteria can use data without a schema change.
42. As an admin, I want the case's four Carriers seeded on first start, so that the system is usable immediately.

### Rule configuration
43. As an admin, I want to see the active Constraints, the ordered Ranking criteria and the thresholds, so that I know how decisions are made.
44. As an admin, I want to move a Ranking criterion up or down and save, so that I can put HQ proximity before cost during the demo.
45. As an admin, I want to enable or disable a Ranking criterion, so that I can test the effect of each one.
46. As an admin, I want saving an empty ranking or an unknown criterion name to be refused, so that I can't break the engine from the UI.
47. As an admin, I want Constraints and thresholds to be read-only in the UI, so that mandatory case rules can't be switched off with one click.
48. As an admin, I want my changes written to `rules.yaml` with its comments kept, so that the file stays the readable source of truth.
49. As a developer, I want to add a new Ranking criterion by writing one class and adding its name to `rules.yaml`, so that new criteria like reliability take minutes.
50. As an operator, I want each Selection to record the ranking that was used, so that I can explain why two runs of the same Order differ.

### Dashboard and history
51. As an operator, I want to see the total and active Carrier counts on the dashboard, so that I know the network status.
52. As an operator, I want to see the latest Selections with a status badge (selected, no carrier, review, unknown route, invalid, Jev unavailable), so that I can follow recent activity.
53. As an operator, I want to open any past Selection and see exactly what was decided and why, so that I can answer questions later.
54. As an operator, I want to re-run a past Order with one click, so that I can show how a rule change alters the result.

### Security and operations
55. As a developer, I want the Jev API key read only from the `TYPESAFE_API_KEY` environment variable, so that it never appears in code, logs, README or the frontend.
56. As a developer, I want a `.env.example` with placeholders and a `.gitignore` that excludes `.env`, so that secrets are never committed.
57. As a developer, I want the whole test suite to run without network access, the real Jev or the distance API, so that tests are fast and reliable.
58. As a reviewer, I want a README that explains the architecture, Jev's role, the deterministic parts, the confidence behavior, setup and example requests, so that I can evaluate the design quickly.

## Implementation Decisions

### Architecture
- Two applications: a FastAPI backend that owns all business logic, and a Next.js (App Router, TypeScript, Tailwind, shadcn/ui) frontend that is a thin client of the backend's HTTP API. Frontend types are generated from the backend's OpenAPI schema. The frontend holds no secrets and no decision logic. It only knows the API base URL.
- SQLite through SQLModel for persistence. No Docker, no auth (single-user local demo; noted in the README as a production gap).
- UI text and reason messages are in Turkish and collected in one messages module. Code, API field names, status values and Jev question texts are in English.

### Modules and their interfaces
- **SelectionEngine** (pure, no I/O): given an Order, the Carriers, the Rule set and a distance lookup, it returns the outcome: selected Carrier, total cost, Eligible carriers in rank order with their loss explanation, Rejected carriers with all failed Constraints, and a reason. Constraints and Ranking criteria are Strategy objects held in name-keyed registries. Ranking sorts Eligible carriers by a tuple of the enabled criteria in `rules.yaml` order, with the Carrier name as the final key. A Carrier's "lost on" explanation comes from the first criterion where its value differs from the winner's. Every criterion is "smaller is better". A criterion where larger is better (e.g. reliability) negates its value.
- **Constraints**: distance range (inclusive, null max = unlimited, null min = 0), container size, cargo type, active. All failed Constraints are reported, not just the first.
- **Ranking criteria**: total cost; HQ proximity (distance from HQ to the Order's origin, 0 when they are the same city, unknown sorts last and is noted in the explanation). New criteria read from the Carrier's attributes.
- **DistanceService**: one operation, "distance between two cities", returning miles and source, or nothing. Resolution order: normalized city names → case table (symmetric) → database cache → distance provider (result written to the cache) → nothing. It never estimates (ADR 0003).
- **DistanceProvider** (port): road distance in miles between two city names. Production adapter: Nominatim geocoding + OSRM routing, no key, 5 s timeout, a descriptive User-Agent, at most 1 Nominatim request per second, meters converted to miles. Test adapter: an in-memory fake.
- **Interpreter** (port): (a) interpret free text against a list of known cities, returning for each field (origin, destination, container size, cargo type) the chosen option and its confidence (which may be missing). (b) Assess Carrier notes for an Order, returning a yes-probability per Carrier. Production adapter: the TypeSafe Python SDK, with one `system_one` request per operation. Interpretation sends one Choice question per field. City options are the known cities plus `other_city` and `unspecified`. Size options are 20/40/45/`unspecified`. Cargo options are Dry/Reefer/Hazardous/`unspecified`. Note assessment sends one Noul question per Carrier note. Any SDK or network failure surfaces as "interpreter unavailable". Test adapter: a scripted fake.
- **SelectionService**: the single entry point the API uses for a selection request. Flow: validate input → if text, interpret and apply the review gate → resolve the route distance → load Carriers → run the engine → assess notes of Eligible carriers → store the Selection snapshot → return the response. The review gate (threshold comparison, unspecified / other_city / missing-confidence handling) lives here, in deterministic code, not in the adapter (ADR 0001).
- **RulesStore**: load and save the Rule set from `rules.yaml`. Save validates against the registries (known names only, at least one enabled Ranking criterion) and preserves comments.
- **Known cities**: the union of case-table cities, Carrier HQ cities and cached cities, plus a deterministic alias map for normalization.

### Rule set file shape
```yaml
constraints: [distance_range, container_size, cargo_type, active]
ranking:
  - {name: total_cost, enabled: true}
  - {name: hq_proximity, enabled: true}
thresholds:
  field_confidence: 0.75
  note_warning: 0.7
```

### Schema
- **carrier**: id, name (unique), headquarters_city, min_distance (nullable), max_distance (nullable = unlimited), supported_container_sizes (JSON list of 20/40/45, non-empty), supported_cargo_types (JSON list of Dry/Reefer/Hazardous, non-empty), price_per_mile (decimal > 0), is_active, description (nullable Carrier note), attributes (JSON object), created_at, updated_at. The four case Carriers are seeded when the table is empty.
- **distance_cache**: city_a and city_b (normalized, stored in alphabetical order; together the key), miles, provider, fetched_at.
- **selection**: id, created_at, input_kind (text | structured), input (JSON), status, selected_carrier_name (nullable), total_cost (nullable), route_miles (nullable), ranking_used (JSON), response (JSON, the full response as returned). Rows are never updated or deleted.
- The case's seven distances live in a fixed in-code table, not in the database, and always win over the cache.

### API contract
- `GET /carriers`, `POST /carriers`, `GET /carriers/{id}`, `PUT /carriers/{id}`, `DELETE /carriers/{id}`: CRUD with the validation rules above. Duplicate name → 409, missing → 404, invalid → 422. Create and update responses carry a `warnings` list (e.g. unknown HQ distance).
- `POST /select-carrier`: accepts either `{text}` or `{origin, destination, container_size, cargo_type}` (exactly one form). It always returns 200 with a `status` for business outcomes. Malformed bodies get 422.
- `GET /selections?limit=N`, `GET /selections/{id}`: Selection history, newest first.
- `GET /rules`, `PUT /rules`: read and replace the Rule set. Invalid → 400 with the offending names.
- `GET /stats` (or the equivalent dashboard fields): total and active Carrier counts.

Selection response shape (decided during design):
```
selection_id, status: selected | no_carrier | needs_review | unknown_route | invalid_order | jev_unavailable
selected_carrier: {id, name, headquarters_city} | null
distance: {miles, source: table | api} | null
total_cost: decimal string | null
reason: string (Turkish)
eligible_carriers: [{name, total_cost, hq_distance, lost_on}]      # Outranked, in rank order
rejected_carriers: [{name, reasons: [string]}]                      # every failed Constraint
confidence: {source: text | structured, min: number | null, fields: {field: {value, confidence, accepted}}}
review: {fields: [string], suggestions: {field: value}, question: string} | null
warnings: [{carrier, note, probability}]
notes_checked: boolean
rules_used: [criterion names in order]
```

### Money and units
- Money is a decimal, rounded to 2 places. It is never a float. Distances are in miles and money is in USD.

## Testing Decisions

- **What makes a good test here**: it drives the system through its public HTTP interface and asserts on the observable response and stored Selections, never on internal functions or call counts. A test must survive a refactor of the engine's internals.
- **Main seam: the HTTP API.** Tests use FastAPI's test client. Only the two true externals are replaced through dependency overrides: the Interpreter (scripted fake) and the DistanceProvider (in-memory fake). The database is a fresh in-memory SQLite per test. `rules.yaml` is a copy in a temporary directory.
- **Covered at the main seam**:
  - the seven case Orders (M $30, S $94, B $660 on HQ proximity, A $280, S $80, no Carrier, M $85);
  - the inclusive boundaries at exactly 200, 250 and 300 miles;
  - container and cargo mismatch;
  - the tie broken by HQ proximity, and the tie broken by name;
  - no Eligible carrier;
  - unknown route (provider returns nothing, or fails);
  - an Order whose distance comes from the provider and is then served from the cache;
  - invalid Orders (same city, unsupported values, both or neither input form);
  - low confidence, unspecified, other_city and missing confidence → needs_review with suggestions;
  - interpreter unavailable for text Orders → jev_unavailable, while structured Orders still succeed;
  - a Note warning appearing without changing the selection, and `notes_checked` false when assessment fails;
  - an inactive Carrier listed as Rejected;
  - adding a Carrier and seeing it selected on the next Order;
  - putting HQ proximity before total cost via `PUT /rules` and seeing the same Order's result change;
  - `PUT /rules` rejecting unknown names and an empty ranking;
  - a Selection staying readable after its Carrier is deleted;
  - Carrier CRUD validation (409, 404, 422).
- **Adapter tests** (needed because the fakes bypass these adapters):
  - The TypeSafe adapter, with the SDK client stubbed (no network): mapping of choices and confidences, missing confidence, sentinel options, Noul probabilities, SDK errors becoming "unavailable".
  - The OSRM/Nominatim adapter, with HTTP mocked: meters → miles, city not found, timeout and HTTP errors.
- **Not tested separately**: the engine (fully observable through the API; no layered duplicate tests), repositories (real SQLite is used). The frontend has no automated tests. It is checked by the TypeScript compiler against generated API types and by a scripted manual demo run.
- **Prior art**: none in this repository (new project). Follow the FastAPI dependency-override testing pattern and pytest parametrization for the seven case Orders.

## Out of Scope

- Authentication, users and roles.
- Docker, deployment, CI.
- Turning Carrier notes into structured fields automatically (a possible later addition, where Jev suggests fields in the form and an admin confirms).
- Adding new container sizes or cargo types without code changes (they are deliberate code-level enums).
- Editing the case distance table or a routes management screen.
- Multi-container Orders, pricing surcharges, delivery dates and capacity.
- Frontend automated tests (e.g. Playwright).
- Internationalization beyond Turkish UI text.

## Further Notes

- **Prerequisite**: the machine currently has Python 3.9.6. The TypeSafe SDK needs 3.10+ and this project targets 3.11+, so a newer Python must be installed before development. Node 25 is present.
- The folder is not a git repository and no issue tracker is configured. This spec and its tickets live under `docs/specs/` with the `ready-for-agent` label in frontmatter until they are moved to a tracker.
- The Jev API key is never read from any text file in the workspace. The developer places it in `.env` manually.
- Before a live demo, run the Orders you plan to show once, so their routes are in the distance cache and the demo does not depend on the public OSRM/Nominatim servers.
- Live demo script: add a Carrier → edit a Carrier note → create an Order → show the selection and the reason → move HQ proximity above total cost → re-run the same Order from history and compare the two Selections.
