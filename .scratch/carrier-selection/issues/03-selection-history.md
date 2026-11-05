# 03: Selection history and snapshots

**What to build:** Every selection request, whatever its status, is stored as an immutable Selection that holds the input, status, selected Carrier name, cost, route distance, the ranking used and the full response. The dashboard lists the latest Selections with status badges, each one opens a detail page that shows exactly what was decided, and a "Tekrar çalıştır" button re-submits the same input as a new Selection.

**Blocked by:** 02

**Status:** done

- [x] Each call to select a Carrier creates exactly one Selection, including `no_carrier` and `invalid_order` outcomes
- [x] Selections can be listed newest first with a limit, and fetched by id; an unknown id returns 404
- [x] The detail page renders from the stored snapshot, not by recomputing
- [x] Re-running a Selection creates a new Selection and leaves the original unchanged
- [x] The dashboard shows the latest Selections with Turkish status badges
