# 02: Carrier selection for structured Orders

**What to build:** An operator fills in origin, destination, container size and cargo type on the "Yeni Sipariş" page and gets the selected Carrier, total cost, route distance (with source), a Turkish reason, the Outranked carriers in rank order with what they lost on, and the Rejected carriers with every failed Constraint. The four case Carriers are seeded, the case distance table is used, and the Rule set is loaded (read-only) from `rules.yaml` with Constraints distance_range, container_size, cargo_type, active and Ranking criteria total_cost then hq_proximity. Carrier names never appear in decision code. See ADR 0001 and the response shape in the spec.

**Blocked by:** 01

**Status:** ready-for-agent

- [ ] All seven case Orders return the expected result through the API: M-Logistics $30, S-Logistics $94, B-Logistics $660 (tie broken by HQ proximity), A-Logistics $280, S-Logistics $80, no Carrier, M-Logistics $85
- [ ] Distances of exactly 200, 250 and 300 miles count as inside the range (inclusive bounds)
- [ ] Container size mismatch and cargo type mismatch each produce a Rejected carrier with a clear Turkish reason; a Carrier failing several Constraints lists all of them
- [ ] A tie on cost goes to the closer HQ; a tie that remains goes to the Carrier name alphabetically
- [ ] HQ proximity is 0 when the HQ is the origin city
- [ ] No Eligible carrier returns status `no_carrier` with every Carrier's reasons
- [ ] Same origin and destination, unsupported values, or a malformed body give `invalid_order` / 422 as specified
- [ ] Money is a 2-decimal decimal value, never a float
- [ ] City names match case-insensitively and through the alias map
- [ ] The result screen shows selected Carrier, cost, distance + source, reason, Outranked and Rejected lists
- [ ] Tests run through the HTTP API only (no engine-internal tests)
