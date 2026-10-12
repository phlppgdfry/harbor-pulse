# What these data can and cannot answer

The grain is a transport batch with units, planned/actual arrival, a matching departure,
terminal and date. The warehouse aggregates this into one terminal-day. These data support
vehicle-weighted mean arrival delay, vehicle-weighted punctuality, matched-departure mean
dwell, slot-day occupancy, revenue/cost reconciliation, and associations between daily
operational candidates. They do not prove that an intervention causes an improvement.

A batch timestamp represents its batch, not every vehicle's timestamp. The case cannot
estimate vehicle-level medians, P95/P99 waiting times, within-batch dispersion, individual
queue trajectories, extremes or fairness between vehicle/customer classes. Individual
vehicle IDs, arrival/departure events, queue/stage timestamps, eligibility definitions
and reliable linkage would be needed. Summing batch units does not create independent
vehicle observations; terminal-days and shared incidents create clustered dependence.

The arrival denominator includes all valid latest arrivals. Punctuality divides on-time
vehicle units by arrival units; delay weights batch minutes by units. Dwell divides
matched-duration units by **matched** units, with coverage separately disclosed. Occupancy
uses occupied slot-days divided by available slot-days; revenue margin uses summed revenue
and cost. Averaging daily percentages or dividing matched dwell by all arrivals changes
the estimand and can hide missingness. Capacity is a snapshot; a day with multiple snapshots
would need a documented duration-weighting rule before changing this adapter.

## Independent small calculation

[Three hand-calculated terminal-days](../fixtures/hand-calculated.json) give 60 vehicles,
66.67% punctuality, 23.3333 minutes delay, **4.5 hours matched dwell**, 80% departure coverage,
53.33% occupancy and 33.33% gross margin. The JSON contains each arithmetic expression.
The unweighted dwell average (4.6667 hours) is deliberately different. Tests compare
against the written answers rather than the full generator's output.

## KPI and target judgments

97% punctuality, 85% occupancy, 35% gross margin and a 3-minute pilot minimum are invented
exercise targets. They require operations/finance agreement, service commitments, cost
structure, capacity constraints and minimum useful-effect justification before real use.
[The weight/target grid](ASSUMPTION-CHALLENGES.md) demonstrates how priorities change.
Owners in the KPI contracts are fictional roles, not stakeholder approval.

Selective missing departures, terminal/day aggregation, encoded maintenance and correlated
staffing restrict inference. [Assumption challenges](ASSUMPTION-CHALLENGES.md) disclose
alternative explanations, time windows, dependence, missingness and investment reversals.
