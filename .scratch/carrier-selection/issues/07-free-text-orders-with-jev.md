# 07: Free-text Orders interpreted by Jev

**What to build:** An operator can type an Order in free text. Jev interprets it with one Choice question per field (cities from the known-city list plus other_city and unspecified; sizes and cargo types plus unspecified). If every field is accepted, the selection runs as for structured Orders and the response shows per-field confidence. Otherwise the Order goes into Review: no Carrier is assigned and the UI shows the form prefilled with Jev's suggestions, with the uncertain fields highlighted and a question for each. When Jev cannot be reached, text Orders return `jev_unavailable` and the UI points to the form, while structured Orders keep working. The review gate is deterministic code with a configurable threshold (default 0.75). See ADR 0001.

**Blocked by:** 02

**Status:** done

- [x] The Jev API key is read only from `TYPESAFE_API_KEY`; it is never logged or exposed
- [x] Confidence below the threshold, a missing confidence, `unspecified` or `other_city` on any field gives `needs_review` with suggestions and a Turkish question (tested with a fake interpreter)
- [x] The response's `confidence.min` is the weakest field's confidence; structured Orders report source `structured` and null confidence
- [x] Interpreter failure gives `jev_unavailable` for text Orders; structured Orders are unaffected
- [x] Adapter tests with a stubbed SDK client cover choice and confidence mapping, missing confidence, sentinel options and SDK errors
- [x] The "Yeni Sipariş" page offers a free-text input, shows per-field confidence, and turns a Review into a prefilled, confirmable form
- [x] One manual run against the real Jev with the user's key succeeds for "Miami'den Orlando'ya 40'lık kuru yük konteyneri taşınacak."
