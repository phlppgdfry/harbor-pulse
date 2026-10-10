# Pilot protocol and simulated estimator

The executable demonstration uses 42 days × two lanes = 84 lane-day sessions. Each day is a block with one randomly assigned intervention lane and one control lane, at equal vehicle volume. The first 14 days are baseline; the next 28 apply an invented six-minute treatment reduction.

The observed estimate is difference-in-differences. A 2,000-draw bootstrap resamples paired lane-day differences within pre/post periods. [Evidence](../evidence/pilot.json) includes the generated effect, observed estimate and interval. All outcomes are simulated. The observed estimate differs from the generated six-minute effect because of noise.

## Before a real pilot

1. Agree on eligible lanes, treatment content and assignment unit.
2. Pre-register a minimum worthwhile reduction, for example three minutes, with operations and finance.
3. Choose enough independent days based on actual historical variability; this repository does not claim a powered real sample size.
4. Define safety, punctuality, workload and queue-shifting guardrails and stopping rules.
5. Record implementation costs and whether freed time is actually redeployed.
6. Check cross-lane spillover, adherence, missing outcomes and assignment balance.
7. Estimate uncertainty at the assignment/cluster level; do not treat vehicle rows as independent when assignment is lane-day.

The simulation has balanced counts and no implemented spillover. Actual safety and workload guardrails are part of the protocol, not measured outcomes in this demonstration. A simulated confidence interval cannot justify a real go-live.
