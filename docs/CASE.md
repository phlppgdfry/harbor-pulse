# Case brief

Harbor Pulse is a fictional Belgian terminal network. Its manager wants to reduce arrival delay while avoiding three common mistakes: expanding space when the constraint is dispatch, valuing every waiting hour as cash savings, and trusting dashboards whose missing departures have been imputed as zero dwell time.

The case asks: **which intervention should earn a pilot, based on data we can reconcile and assumptions we can inspect?**

## Stakeholders and decisions

| Role (fictional) | Decision | Evidence required |
|---|---|---|
| Terminal operations lead | Run a dispatch pilot | Delay, queue/maintenance context, service guardrails |
| Capacity planner | Request more space | Occupied/available slot-days and competing constraints |
| Workforce planner | Redeploy staffing | Staff hours, usable time gain and operating cost |
| Finance controller | Fund an intervention | Investment, annual opex, loss cases and payback |
| Data steward | Permit a report release | Contracts, quarantine, coverage and reconciliation |
| Release owner | Publish or roll back | Validated snapshot, model binding, backup and run log |

Success for this portfolio case is executable control evidence and a defensible pilot recommendation. Success for a real deployment would additionally require actual users, agreed definitions, independent safety/service observations and measured intervention outcomes.

## Assumptions register

- A transport batch contains multiple vehicles. `Units` is its count, not a sampling weight.
- Batch timestamps summarize that batch; `OnTimeUnits` is a separately supplied aggregate SLA count. Vehicle-level flags are required to audit a real SLA threshold.
- All timestamps carry UTC offsets. Delay is `max(0, actual − planned)`; early arrivals are valid.
- Maintenance, costs, staffing and pilot outcomes are synthetic. They are not estimates about any actual terminal company.
- An April maintenance episode is inserted into the generator. Regression detecting it is a demonstration, not discovery of an unknown real cause.
- Revenue and handling costs are generated from units, tariffs and synthetic cost ratios. They are not ledger extracts.
- Time savings need genuine redeployment or another measurable benefit before they become cash savings.

## Acceptance

The case must demonstrate an idempotent replay, corrected latest-version totals, visible missing departure coverage, an atomic failed load, a publication gate, independently checked DAX, cost-aware scenarios and a transparent simulated pilot. CI reproduces the local controls. Actual cloud publication remains an explicit operator action.
