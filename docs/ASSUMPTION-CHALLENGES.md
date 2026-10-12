# Try to overturn the recommendation

This is an analytical appendix, not evidence of actual financial impact. Reproduce it
with `uv run --locked python scripts/challenge_evidence.py` after the demo.
[Machine-readable results](../evidence/challenge.json) expose all inputs and six challenges.

## When investment is unwise

At the invented EUR45 per waiting hour and central reductions, annual break-even
realizable fractions are **2.73% dispatch, 6.23% yard and 10.61% staffing**. Including
implementation costs in year-one cash raises these to **4.85%, 52.95% and 11.26%**.
Below an option's threshold its modeled annual net is negative; when every option is
negative, choose no implementation. The JSON also gives pairwise crossover fractions,
maximum affordable recurring cost, and break-even fractions under 0/25/50/75% execution
failure. Costs are incurred even when implementation fails. Negative thresholds or
failure probabilities are disclosed as infeasibility, not clipped into plausible values.

The exercise distinguishes annual ranking from cash affordability. It excludes financing,
tax, depreciation, implementation time, ramp-up and opportunity costs. Finance would need
to replace every invented rate and cost before an investment decision.

## Dependent assumptions

The dependence experiment preserves each marginal time/cost distribution while coupling
higher reductions to higher effort and staff cost using the same latent rank. It compares
600 paired draws per option against independent ranks. This isolates the effect of
**dependence**, rather than changing costs and correlation at once. The experiment uses
its own disclosed 0.5–1.5x recurring-cost range and a common 5–15% realizable fraction;
its percentiles are not directly interchangeable with the original Monte Carlo.

Positive dependence here narrows net-value uncertainty: dispatch P10 moves from roughly
EUR57.9k to EUR59.1k; yard P10 changes from negative to positive. That does **not** establish
that actual dependence is beneficial. Shared disruption, negative benefit-realization
correlation, nonlinear overtime and different cost marginals could worsen outcomes.
The chosen coupling is a stress scenario, not an estimated operational relationship.

## Selectively missing records

Remove departure links for 20% of terminal-days, either randomly, from the most delayed
days, or from the longest-dwell days. In this controlled invented truth, random removal
barely changes means, while losing the most delayed days understates linked delay by
about **1.56 minutes** and linked dwell by **0.29 hours**. Losing longest-dwell days
understates dwell by about **0.37 hours**. Coverage and 0–72-hour identification bounds
are exposed. Those bounds are assumptions, not validated physical limits.

Arrival delay remains available from all arrivals: it becomes biased only if an analyst
unnecessarily restricts it to records with a departure match. Missing real departures
cannot be recovered by treating missing dwell as zero. The simulation removes whole
terminal-days and uses known batch means; it does not invent individual vehicle tails.

## Time periods and plausible explanations

Quarterly delay means fall from roughly **18.34 minutes in Q1 to 15.05 in Q4**. Removing
the encoded incident changes the full-year weighted mean from **16.92 to 16.56 minutes**;
the positive central dispatch net persists. Quarterly recurring costs are prorated by
calendar days, which is an analytical convention; real fixed costs may not scale down.

Competing chronological Q4 models give RMSE of **4.13** for terminal effects only,
**3.94** with load/weekday, **4.05** after adding staffing, and **3.56** with the incident
term in training. Adding staffing worsens this holdout, so a staffing explanation cannot
be justified by in-sample fit alone. Q4 has no maintenance incident: its holdout cannot
independently validate the incident effect. Staffing can respond to congestion rather
than cause it; weather, queue routing and management practice are not independently
identified in these data. No coefficient is a causal treatment effect.

## Priority score sensitivity

The grid evaluates **2,187** combinations of targets and 0.5/1/2 weights. It reproduces
the report's percentage-point shortfalls for punctuality, occupancy, planning and margin.
Antwerpen ranks first in all these combinations; Gent and Zeebrugge swap second/third
place (**1,215 versus 972** cases). This is stability over a chosen grid, not statistical
confidence. Equal weights imply that one percentage-point service gap trades off with
one percentage-point margin gap; that value judgment requires stakeholder agreement.
The 97% punctuality, 85% occupancy and 35% margin targets are **exercise assumptions**,
not port industry standards. The priority score supports investigation, not investment
or causal attribution. Ties are counted and ordered by terminal key only for tabulation.

## A pilot can be significant and still unhelpful

The examples separate three gates: confidence interval excludes zero; its lower bound
supports at least **3 minutes** useful improvement; and realizable annual net is positive.
A precise 1.5-minute effect can pass significance and fail usefulness. A 6-minute effect
with just 1% usable time can pass both statistical gates and lose money. Zero usability
has no financial benefit. Operational guardrails, carryover/spillover, real paired-day
variability and actual implementability still need agreement and measurement.
These are normal-approximation examples, not independent validation of the simulated pilot.
