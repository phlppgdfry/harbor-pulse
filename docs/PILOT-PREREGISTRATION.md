# Pilot pre-registration specification

Status: completed case protocol; **not registered externally, signed off or run in a real terminal**. All existing observations are synthetic.

## Intervention, eligibility and estimand

Dispatch/appointment slots for eligible comparable lanes; exclude hazardous cargo and abnormal outages under rules fixed before assignment. Primary estimand: intention-to-treat change in vehicle-weighted arrival delay in minutes for eligible traffic. Use lane-day aggregates with explicit vehicle denominators. Baseline and post-period group contrast is the demonstration estimator.

Randomize within day blocks only when dispatch changes can switch between lanes without carryover. If that is infeasible, assign persistent independent lane/terminal clusters and calculate power at that cluster level. Avoid giving operators discretionary assignment.

## Sample size and analysis lock

Minimum worthwhile reduction: 3 minutes, subject to operations/finance agreement. Two-sided alpha .05; target 80% power for the agreed estimand. Estimate paired-day variance from historical operational data. The executable planning grid uses an invented SD of 3 minutes, 14 baseline days and 14/28/42/56 post days. Its null rejection rate reveals the limitations of normal critical values. These simulations are not a validated real sample-size calculation. The supplied power rates concern rejection of zero effect at a specified true effect; they do not give the probability that an interval establishes at least a three-minute benefit. If that is the decision criterion, power must be recalculated for a margin test using a larger plausible effect.

Lock eligibility, assignment seed/procedure, exclusions, outcomes, estimator, bootstrap unit and stopping rules before exposure. Log dated amendments. Analyze all assigned eligible lane-days; separately report adherence and per-protocol results without replacing intention-to-treat.

## Outcomes and guardrails

| Outcome | Proposed decision rule | Owner |
|---|---|---|
| Vehicle-weighted delay | Report point estimate and cluster interval; reduction must meet the agreed meaningful threshold | Operations |
| Safety | Stop immediately for a plausibly intervention-related serious incident | Safety lead |
| Punctuality | No deterioration greater than agreed 1 percentage point | Operations |
| Overtime/workload | No increase beyond agreed 5% without explicit staffing approval | Planning |
| Downstream queue | No increase beyond agreed 10%; measure destination queue | Terminal lead |
| Cost/redeployment | Evidence of changed resource allocation; account for implementation and recurring cost | Finance |

Thresholds are proposed case assumptions, not industry standards. Guardrail observations are not present in the simulated data and no passing result is claimed.

## Missingness, spillover and inference

Record reasons and counts by assigned group. Do not replace missing outcomes with zero. Report complete-pair analysis, missingness balance and bounded/sensitivity alternatives. Random missingness simulation does not establish robustness to selective reporting. Measure adjacent control queues for spillover; the supplied 25%/50% simulations show effect attenuation.

Use paired-day resampling for the switching design; use cluster resampling or randomization inference for persistent clusters. Examine pre-period contrasts and a null/placebo design. A post-hoc significance threshold cannot replace the pre-agreed practical decision rule.

## Stopping, approval and audit

Stop for safety, infeasible adherence or insufficient data coverage; document the reason and retain all collected records. Avoid repeated unplanned significance checks. Final approval requires operations, safety and finance review of the locked analysis, guardrails, costs and sensitivity results. Store assignment, protocol version, changes and final sign-off with the release.
