# Carrier Selection

Picks the most suitable carrier for an incoming container transport order, explains why, and records the decision.

## Orders

**Order**:
A request to move one container from an origin city to a destination city, with a container size and a cargo type. Shown in the UI as "Sipariş".
_Avoid_: Shipment, request, job

**Route distance**:
The road distance in miles between an Order's origin and destination.
_Avoid_: Length, km

**Interpretation**:
The reading of a free-text Order into its fields, with a confidence per field.
_Avoid_: Parsing, extraction

**Review**:
The state of an Order whose Interpretation is too uncertain to act on, so a person must confirm the fields first.
_Avoid_: Manual check

## Carriers

**Carrier**:
A firm that can transport Orders, with the distances, container sizes and cargo types it accepts and its price per mile.
_Avoid_: Vendor, provider, company

**Headquarters (HQ)**:
The city a Carrier operates from.
_Avoid_: Base, depot

**Carrier note**:
A Carrier's free-text description. Never a Constraint.
_Avoid_: Description rule

**Note warning**:
A sign that a Carrier note mentions a restriction or risk relevant to a given Order.
_Avoid_: Flag, alert

## Rules

**Constraint**:
A rule a Carrier must satisfy to be considered for an Order: distance range, container size, cargo type, being active.
_Avoid_: Filter rule, requirement

**Ranking criterion**:
A measure that orders Eligible carriers, such as total cost or HQ proximity.
_Avoid_: Sort key, priority rule

**HQ proximity**:
The distance from a Carrier's Headquarters to the Order's origin.
_Avoid_: Closeness, nearness

**Rule set**:
The active Constraints, the ordered Ranking criteria and the confidence thresholds.
_Avoid_: Config, policy

## Outcomes

**Eligible carrier**:
A Carrier that satisfies every Constraint for an Order.
_Avoid_: Valid, matching

**Rejected carrier**:
A Carrier that fails at least one Constraint for an Order.
_Avoid_: Filtered out

**Outranked carrier**:
An Eligible carrier that placed below the selected one under the Ranking criteria.
_Avoid_: Rejected

**Selection**:
The immutable record of the decision made for one Order, including the Rule set used.
_Avoid_: Result log, history
