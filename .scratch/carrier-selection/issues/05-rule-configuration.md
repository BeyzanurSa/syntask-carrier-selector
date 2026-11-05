# 05: Rule configuration

**What to build:** An admin opens the "Kurallar" page, sees the Constraints and thresholds (read-only) and the Ranking criteria in their current order, moves or toggles criteria, and saves. The change is written to `rules.yaml` with comments kept, and the next selection uses it. Each response and Selection records the ranking that was used, so re-running an Order after a change shows a different, explained result. See ADR 0002.

**Blocked by:** 02

**Status:** ready-for-agent

- [ ] The Rule set can be read and replaced through the API
- [ ] Saving an unknown criterion name or a ranking with no enabled criterion is refused with 400 and leaves the file untouched
- [ ] Saved changes keep the comments in `rules.yaml`
- [ ] With hq_proximity placed above total_cost, the same Order selects a different Carrier where the case data allows it, and the response's `rules_used` reflects the new order (tested through the API)
- [ ] The UI lets the admin reorder and toggle Ranking criteria; Constraints and thresholds are shown read-only
- [ ] Adding a new Ranking criterion requires only a registered class and a line in `rules.yaml` (documented for the demo)
