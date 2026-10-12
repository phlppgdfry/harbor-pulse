"""Try to overturn the case's assumptions; all inputs and outputs are synthetic."""

import itertools
import math
import random
import statistics as st

from .analysis import percentile
from .review import design, fit, predict, rmse

OPTIONS = [
    ("Dispatch / slots", 6, 45000, 35000),
    ("Yard expansion", 0.7, 12000, 90000),
    ("Additional staffing", 4.5, 131400, 8000),
]


def weighted_kpis(rows):
    units = sum(r["Vehicles"] for r in rows)
    complete = sum(r["CompleteDepartureUnits"] for r in rows)
    revenue = sum(r["Revenue"] for r in rows)
    available = sum(r["AvailableSlots"] for r in rows)
    return dict(
        vehicles=units,
        punctuality=sum(r["OnTimeVehicles"] for r in rows) / units if units else None,
        delay=sum(r["Vehicles"] * r["DelayMinutes"] for r in rows) / units if units else None,
        dwell=sum(r["CompleteDepartureUnits"] * r["DwellHours"] for r in rows) / complete
        if complete
        else None,
        coverage=complete / units if units else None,
        occupancy=sum(r["OccupiedSlots"] for r in rows) / available if available else None,
        margin=(revenue - sum(r["HandlingCost"] for r in rows)) / revenue if revenue else None,
    )


def hours(facts, minutes):
    return sum(r["Vehicles"] * min(r["DelayMinutes"], minutes) / 60 for r in facts)


def thresholds(facts, value=45):
    options = []
    for name, minutes, opex, capex in OPTIONS:
        h = hours(facts, minutes)
        options.append(
            dict(
                option=name,
                saved_hours=h,
                annual_cost=opex,
                implementation_cost=capex,
                annual_break_even_fraction=opex / (h * value),
                year_one_break_even_fraction=(opex + capex) / (h * value),
                maximum_annual_cost_at_10pct=h * 0.1 * value,
                max_failure_probability_at_10pct=1 - opex / (h * 0.1 * value),
                failure_adjusted_break_even=[
                    dict(failure_probability=p, fraction=opex / (h * value * (1 - p)))
                    for p in [0, 0.25, 0.5, 0.75]
                ],
            )
        )
    crossovers = []
    for a, b in itertools.combinations(options, 2):
        denominator = value * (a["saved_hours"] - b["saved_hours"])
        crossovers.append(
            dict(
                options=[a["option"], b["option"]],
                fraction=(a["annual_cost"] - b["annual_cost"]) / denominator
                if denominator
                else None,
            )
        )
    # Negative crossover or >1 is disclosed, never clipped into a plausible probability.
    return dict(
        hour_value=value,
        options=options,
        crossovers=crossovers,
        rule="Choose no implementation when all annual nets are <=0; first-year cash is a separate constraint.",
        risk_model="Binary execution failure destroys gross benefit but still incurs all costs; invented expected-value scenario.",
    )


def dependent_scenarios(facts, draws=600):
    results = []
    # Shared latent effort couples larger reductions to higher staff cost. Paired
    # random numbers preserve the marginals and make the dependence comparison fair.
    for name, low, mode, high, opex in [
        ("Dispatch / slots", 5, 6, 8, 45000),
        ("Yard expansion", 0, 0.7, 2, 12000),
        ("Additional staffing", 3, 4.5, 6, 131400),
    ]:
        rng = random.Random(991)
        independent = []
        coupled = []
        times = []
        ind_cost = []
        dep_cost = []

        def triangular(u, low=low, mode=mode, high=high):
            cutoff = (mode - low) / (high - low)
            return (
                low + math.sqrt(u * (high - low) * (mode - low))
                if u < cutoff
                else high - math.sqrt((1 - u) * (high - low) * (high - mode))
            )

        for _ in range(draws):
            u, v = rng.random(), rng.random()
            reduction = triangular(u)
            fraction = rng.uniform(0.05, 0.15)
            gross = hours(facts, reduction) * 45 * fraction
            ci = opex * (0.5 + v)
            cd = opex * (0.5 + u)
            independent.append(gross - ci)
            coupled.append(gross - cd)
            times.append(reduction)
            ind_cost.append(ci)
            dep_cost.append(cd)
        results.append(
            dict(
                option=name,
                draws=draws,
                independent=dict(
                    p10=percentile(independent, 0.1),
                    p50=percentile(independent, 0.5),
                    p90=percentile(independent, 0.9),
                    positive_fraction=sum(n > 0 for n in independent) / draws,
                ),
                coupled=dict(
                    p10=percentile(coupled, 0.1),
                    p50=percentile(coupled, 0.5),
                    p90=percentile(coupled, 0.9),
                    positive_fraction=sum(n > 0 for n in coupled) / draws,
                ),
                cost_time_correlation=st.correlation(times, dep_cost),
                independent_correlation=st.correlation(times, ind_cost),
            )
        )
    return dict(
        options=results,
        assumptions="Same triangular time and uniform 0.5–1.5x cost marginals; positive rank dependence versus independent draws. Common 5–15% realizable fraction and EUR45/hour. Distributions are scenarios, not probabilities calibrated from operations.",
    )


def selective_missingness(facts, drop_fraction=0.2):
    truth = weighted_kpis(facts)
    count = int(len(facts) * drop_fraction)
    random_indices = set(random.Random(992).sample(range(len(facts)), count))
    delayed_indices = set(
        sorted(range(len(facts)), key=lambda i: facts[i]["DelayMinutes"], reverse=True)[:count]
    )
    slow_indices = set(
        sorted(range(len(facts)), key=lambda i: facts[i]["DwellHours"], reverse=True)[:count]
    )
    scenarios = []
    for label, removed in [
        ("random_terminal_days", random_indices),
        ("most_delayed_terminal_days", delayed_indices),
        ("longest_dwell_terminal_days", slow_indices),
    ]:
        observed = [r for i, r in enumerate(facts) if i not in removed]
        units = sum(r["Vehicles"] for r in observed)
        delay = sum(r["Vehicles"] * r["DelayMinutes"] for r in observed) / units
        dwell = sum(r["Vehicles"] * r["DwellHours"] for r in observed) / units
        full_dwell = sum(r["Vehicles"] * r["DwellHours"] for r in facts) / truth["vehicles"]
        coverage = units / truth["vehicles"]
        scenarios.append(
            dict(
                mechanism=label,
                removed_terminal_days=len(removed),
                observed_unit_coverage=coverage,
                linked_delay_mean=delay,
                linked_delay_bias=delay - truth["delay"],
                linked_dwell_mean=dwell,
                linked_dwell_bias=dwell - full_dwell,
                dwell_identification_bounds_0_to_72h=[
                    coverage * dwell,
                    coverage * dwell + (1 - coverage) * 72,
                ],
            )
        )
    return dict(
        truth=truth,
        scenarios=scenarios,
        scope="Synthetic loss of all departure links for selected terminal-days; daily batch-mean dwell is treated as invented full-data truth. Not a reconstruction of unrecorded real departures.",
        caution="Delay is available from all arrivals; bias arises if analysts incorrectly restrict delay to matched departures. Dwell bounds assume 0–72 hours, an explicit unvalidated bound.",
    )


def temporal_checks(facts):
    windows = [
        ("full_year", facts),
        ("without_incident", [r for r in facts if not r["IncidentFlag"]]),
    ]
    windows += [
        (f"Q{quarter}", [r for r in facts if (r["DateKey"] // 100 % 100 - 1) // 3 + 1 == quarter])
        for quarter in range(1, 5)
    ]
    results = []
    for label, rows in windows:
        kpis = weighted_kpis(rows)
        net = hours(rows, 6) * 0.1 * 45 - 45000 * len({r["DateKey"] for r in rows}) / 365
        results.append(
            dict(
                window=label,
                terminal_days=len(rows),
                kpis=kpis,
                dispatch_net_for_period=net,
                incident_days=sum(r["IncidentFlag"] for r in rows),
            )
        )
    # Genuine chronological holdout for competing explanations. An all-zero
    # incident column is removed, rather than disguised with regularization.
    x, y = design(facts)
    train = [i for i, r in enumerate(facts) if r["DateKey"] < 20261001]
    test = [i for i, r in enumerate(facts) if r["DateKey"] >= 20261001]
    explanations = []
    for name, cols in [
        ("terminal_only", [0, 5, 6]),
        ("load_and_weekday", [0, 2, 3, 5, 6]),
        ("staffing_and_load", [0, 2, 3, 4, 5, 6]),
        ("including_incident", [0, 1, 2, 3, 4, 5, 6]),
    ]:
        tx = [[x[i][c] for c in cols] for i in train]
        ty = [y[i] for i in train]
        beta = fit(tx, ty)
        prediction = predict([[x[i][c] for c in cols] for i in test], beta)
        explanations.append(
            dict(
                explanation=name,
                parameters=len(cols),
                q4_rmse=rmse([y[i] for i in test], prediction),
            )
        )
    return dict(
        windows=results,
        explanations=explanations,
        caution="Period costs prorated by observed calendar days; scale-down feasibility is unproven. Staffing may respond to congestion. Maintenance, weather, demand and management practices cannot be causally disentangled by this generator. Q4 has no maintenance incident.",
    )


def priority_stability(facts):
    totals = {
        terminal: weighted_kpis([r for r in facts if r["TerminalKey"] == terminal])
        for terminal in (1, 2, 3)
    }
    planned = {
        terminal: sum(r["Vehicles"] for r in facts if r["TerminalKey"] == terminal)
        / sum(r["PlannedVehicles"] for r in facts if r["TerminalKey"] == terminal)
        - 1
        for terminal in totals
    }
    ranking_counts = {str(t): [0, 0, 0] for t in totals}
    unique = {}
    cases = 0
    ties = 0
    for punctuality, occupancy, margin in itertools.product(
        [0.95, 0.97, 0.99], [0.75, 0.85, 0.95], [0.30, 0.35, 0.40]
    ):
        for weights in itertools.product([0.5, 1, 2], repeat=4):
            scores = {
                t: 100
                * sum(
                    w * g
                    for w, g in zip(
                        weights,
                        [
                            max(0, punctuality - k["punctuality"]),
                            max(0, k["occupancy"] - occupancy),
                            max(0, -planned[t]),
                            max(0, margin - k["margin"]),
                        ],
                        strict=True,
                    )
                )
                for t, k in totals.items()
            }
            order = tuple(sorted(scores, key=lambda t: (-scores[t], t)))
            ties += len(set(round(v, 10) for v in scores.values())) < 3
            unique[str(order)] = unique.get(str(order), 0) + 1
            for rank, t in enumerate(order):
                ranking_counts[str(t)][rank] += 1
            cases += 1
    return dict(
        cases=cases,
        rank_counts=ranking_counts,
        rankings=unique,
        cases_with_ties=ties,
        weights=[0.5, 1, 2],
        targets=dict(
            punctuality=[0.95, 0.97, 0.99], occupancy=[0.75, 0.85, 0.95], margin=[0.30, 0.35, 0.40]
        ),
        rationale="Reproduces DAX shortfall score: percentage-point gaps in punctuality, occupancy, planning and margin, equal weight by default. No empirical justification for equal weights or targets; use as triage, not causal priority. Ties ordered by terminal key for counting only.",
    )


def pilot_usefulness():
    cases = []
    for estimate, se, realizable, opex in [
        (1.5, 0.3, 0.1, 45000),
        (3, 0.5, 0, 45000),
        (6, 1, 0.1, 45000),
        (6, 1, 0.01, 45000),
    ]:
        interval = [estimate - 1.96 * se, estimate + 1.96 * se]
        usable_value = 366910 * estimate / 60 * 45 * realizable
        cases.append(
            dict(
                improvement_minutes=estimate,
                normal_95_interval=interval,
                statistically_detectable=interval[0] > 0,
                minimum_useful_effect_minutes=3,
                minimum_effect_established=interval[0] >= 3,
                realizable_fraction=realizable,
                annual_net=usable_value - opex,
                decision_ready=interval[0] >= 3 and usable_value - opex > 0,
            )
        )
    return dict(
        cases=cases,
        rule="Separate detectable improvement, lower confidence bound >=3 minutes, positive usable net value and operational guardrails. These examples are invented normal approximations, not a reanalysis of pilot data.",
    )


def challenge(facts):
    return dict(
        synthetic=True,
        thresholds=thresholds(facts),
        dependence=dependent_scenarios(facts),
        missingness=selective_missingness(facts),
        periods=temporal_checks(facts),
        priority=priority_stability(facts),
        pilot_usefulness=pilot_usefulness(),
    )
