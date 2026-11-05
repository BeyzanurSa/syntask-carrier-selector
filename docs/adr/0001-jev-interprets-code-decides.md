# Jev interprets, deterministic code decides

Jev is used only to turn free text into predefined options: one Choice question per Order field (each with an `unspecified` option), and a Noul question asking whether a Carrier note signals a risk for the Order. Confidence thresholds, Constraint checks, cost calculation, ranking and tie-breaking all live in Python code. That code is reproducible under the same input and Rule set, and it is unit-tested without Jev. A low or missing confidence on any field puts the Order into Review instead of guessing. Jev never selects a Carrier or computes a price.

## Considered Options

- Let Jev extract the full Order as free-form JSON. Rejected because Jev answers typed questions over given options and does not generate free text.
- Let Jev pick the Carrier. Rejected because the decision must be explainable, auditable and testable.
- Turn Carrier notes into Constraints automatically. Rejected because one misread note would wrongly remove a Carrier. Notes only raise Note warnings.
