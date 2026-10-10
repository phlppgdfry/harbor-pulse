# KPI contracts

These are role-owned definitions for the fictional case. They are not claims that actual individuals approved them.

| KPI | Definition and grain | Denominator / exclusions | Role owner | Release check |
|---|---|---|---|---|
| Vehicles | Sum of latest valid arrival-batch Units; terminal-day | Bad/conflicting revisions quarantined | Transport operations lead | No duplicate business keys; source/fact match |
| Punctuality | OnTimeUnits / valid arrival Units | SLA count is supplied upstream; not inferred from a batch-average timestamp | Operations lead | `0 ≤ OnTimeUnits ≤ Units`; threshold agreement required for real data |
| Delay | `max(0, actual − planned)` in minutes, vehicle-weighted | UTC batch timestamps; early arrivals contribute zero delay | Terminal operations lead | Parseable zoned timestamps; planned date matches business date |
| Dwell | Departure − arrival in hours, weighted by matched Units | Missing or invalid departures excluded from duration denominator; coverage shown separately | Operations lead | Departure ≥ actual arrival; join keys and terminal/date match |
| Departure coverage | Matched valid departure Units / valid arrival Units | Missing records remain visible | Data steward | ≥99% for this demo's publication gate |
| Occupancy | Occupied slot-days / available slot-days | Capacity must be positive; do not sum percentages | Capacity planner | Occupied ≤ available; known terminal/date |
| Gross margin | Revenue − handling cost; ratio to revenue | Before overhead, taxes, financing or intervention investment | Finance controller | Units × rate; explicit cost-ratio assumption |
| Scenario economic value | Capped saved vehicle-hours × hour value × usable fraction | No implied throughput uplift; annual opex/investment considered separately in decisions | Finance controller | Zero reduction gives zero value; explicit realization range |
| Priority | Sum of target shortfalls and excess occupancy, ranked in selection | An illustrative policy score, not an optimized scheduling rule | Operations lead | Explain thresholds; no false precision in rank |

Fictional targets: punctuality 97%, gross margin 35%, occupancy at most 85%. A production rollout requires sign-off, versioned definitions and change notices to report consumers.
