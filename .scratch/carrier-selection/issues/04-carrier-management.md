# 04: Carrier management

**What to build:** An admin manages Carriers from the "Taşıyıcılar" page: list, create, edit (including the Carrier note and attributes), activate/deactivate and delete (with a confirmation dialog). Validation protects the engine from bad data. A new Carrier takes part in the very next selection, inactive Carriers appear as Rejected with "Firma pasif", and deleting a Carrier never breaks a past Selection. The dashboard shows total and active Carrier counts.

**Blocked by:** 02, 03

**Status:** done

- [x] Create, read, update and delete work through the API and the UI
- [x] Duplicate name → 409, unknown id → 404, invalid data → 422 (non-positive price, min > max, empty or unsupported container sizes / cargo types)
- [x] An empty max distance means unlimited
- [x] A newly added Carrier is selected for an Order it wins (tested through the API)
- [x] A deactivated Carrier is listed among Rejected carriers with "Firma pasif" and is never selected
- [x] After a Carrier is deleted, a Selection that chose it still opens with its original data
- [x] The Carrier note can be edited and saved from the UI
- [x] The dashboard shows total and active Carrier counts
