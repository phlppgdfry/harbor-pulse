"""Reproducible sensitivity, regression diagnostics and pilot planning checks.

Standard-library implementation. Outputs describe synthetic data only.
"""

import datetime as dt
import math
import random
import statistics as st

from .analysis import percentile, solve

NAMES = [
    "Intercept",
    "Incident",
    "Volume/capacity",
    "Monday",
    "Staff hours/100 vehicles",
    "Antwerpen",
    "Gent",
]


def design(facts):
    x = [
        [
            1,
            int(f["IncidentFlag"]),
            f["Vehicles"] / f["HandlingCapacity"],
            int(dt.datetime.strptime(str(f["DateKey"]), "%Y%m%d").weekday() == 0),
            f["StaffHours"] / f["Vehicles"] * 100,
            int(f["TerminalKey"] == 2),
            int(f["TerminalKey"] == 3),
        ]
        for f in facts
    ]
    return x, [f["DelayMinutes"] for f in facts]


def fit(x, y):
    n = len(x[0])
    return solve(
        [[sum(r[i] * r[j] for r in x) for j in range(n)] for i in range(n)],
        [sum(r[i] * v for r, v in zip(x, y, strict=True)) for i in range(n)],
    )


def predict(x, beta):
    return [sum(a * b for a, b in zip(r, beta, strict=True)) for r in x]


def rmse(actual, predicted):
    return math.sqrt(st.mean((a - p) ** 2 for a, p in zip(actual, predicted, strict=True)))


def correlation(a, b):
    aa = [v - st.mean(a) for v in a]
    bb = [v - st.mean(b) for v in b]
    den = math.sqrt(sum(v * v for v in aa) * sum(v * v for v in bb))
    return sum(v * w for v, w in zip(aa, bb, strict=True)) / den if den else None


def diagnostics(facts, draws=300):
    facts = sorted(facts, key=lambda f: (f["DateKey"], f["TerminalKey"]))
    x, y = design(facts)
    beta = fit(x, y)
    fitted = predict(x, beta)
    residual = [a - p for a, p in zip(y, fitted, strict=True)]
    cut = 20261001
    train = [i for i, f in enumerate(facts) if f["DateKey"] < cut]
    test = [i for i, f in enumerate(facts) if f["DateKey"] >= cut]
    train_x = [x[i] for i in train]
    train_y = [y[i] for i in train]
    held = predict([x[i] for i in test], fit(train_x, train_y))
    actual = [y[i] for i in test]
    # VIF uses the same intercept and explanatory variables. Do not silently
    # regularize an unidentified design; a singular matrix is a visible failure.
    vifs = {}
    for j in range(1, len(NAMES)):
        target = [r[j] for r in x]
        others = [[v for k, v in enumerate(r) if k != j] for r in x]
        estimates = predict(others, fit(others, target))
        tss = sum((v - st.mean(target)) ** 2 for v in target)
        unexplained = sum((a - b) ** 2 for a, b in zip(target, estimates, strict=True))
        vifs[NAMES[j]] = tss / unexplained if unexplained > 1e-12 else None
    blocks = {}
    for i, f in enumerate(facts):
        date = dt.datetime.strptime(str(f["DateKey"]), "%Y%m%d").date()
        week = date - dt.timedelta(days=date.weekday())
        blocks.setdefault(week, []).append(i)
    rng = random.Random(707)
    keys = list(blocks)
    samples = []
    failed = 0
    for _ in range(draws):
        indices = [i for key in rng.choices(keys, k=len(keys)) for i in blocks[key]]
        try:
            samples.append(fit([x[i] for i in indices], [y[i] for i in indices]))
        except ValueError:
            failed += 1
    serial = {}
    for terminal in (1, 2, 3):
        r = [residual[i] for i, f in enumerate(facts) if f["TerminalKey"] == terminal]
        serial[str(terminal)] = correlation(r[:-1], r[1:])
    by_month = []
    for month in range(1, 13):
        r = [residual[i] for i, f in enumerate(facts) if f["DateKey"] // 100 == 202600 + month]
        by_month.append(
            dict(month=month, mean=st.mean(r), rmse=math.sqrt(st.mean(v * v for v in r)))
        )
    return dict(
        synthetic=True,
        method="OLS; whole-week cluster bootstrap; chronological Q4 holdout",
        observations=len(facts),
        train_rows=len(train),
        test_rows=len(test),
        holdout_rmse=rmse(actual, held),
        training_mean_baseline_rmse=rmse(actual, [st.mean(train_y)] * len(actual)),
        full_sample_rmse=rmse(y, fitted),
        bootstrap_attempts=draws,
        bootstrap_singular_draws=failed,
        coefficients=[
            dict(
                factor=name,
                value=beta[j],
                cluster_bootstrap_95=[
                    percentile([b[j] for b in samples], 0.025),
                    percentile([b[j] for b in samples], 0.975),
                ],
            )
            for j, name in enumerate(NAMES)
        ],
        variance_inflation_factors=vifs,
        lag1_residual_correlation_by_terminal=serial,
        residuals_by_month=by_month,
        caution="Q4 lacks the invented maintenance event: holdout does not validate the incident effect. Weekly bootstrap is a diagnostic, not causal identification.",
        residual_plot=[
            dict(date=f["DateKey"], terminal=f["TerminalKey"], fitted=p, residual=r)
            for f, p, r in zip(facts, fitted, residual, strict=True)
        ],
    )


def sensitivity(facts):
    total = sum(f["Vehicles"] for f in facts)
    # Fixed central reduction assumptions. Vary the common realizable fraction
    # and time value, including zero benefit. First-year cash deducts investment.
    options = [
        ("Dispatch / slots", 6, 45000, 35000),
        ("Yard expansion", 0.7, 12000, 90000),
        ("Additional staffing", 4.5, 131400, 8000),
    ]
    result = []
    for fraction in (0, 0.03, 0.05, 0.075, 0.10, 0.125, 0.15, 0.20):
        for value in (25, 35, 45, 60):
            rows = []
            for name, minutes, opex, capex in options:
                hours = sum(f["Vehicles"] * min(f["DelayMinutes"], minutes) / 60 for f in facts)
                net = hours * fraction * value - opex
                rows.append(
                    dict(
                        option=name,
                        annual_net=round(net, 2),
                        year_one_cash=round(net - capex, 2),
                        break_even_realizable_fraction=opex / (hours * value),
                    )
                )
            winner = max(rows, key=lambda r: r["annual_net"])
            result.append(
                dict(
                    fraction=fraction,
                    hour_value=value,
                    vehicles=total,
                    preferred=winner["option"] if winner["annual_net"] > 0 else "Do not implement",
                    options=rows,
                )
            )
    return dict(
        synthetic=True,
        scope="Annual, all terminals; deterministic central time reduction; common realizable fraction",
        grid=result,
        caution="A sensitivity surface over invented inputs, not a probability forecast. Ranking by annual value; year-one cash is shown separately.",
    )


def pilot_planning(draws=1000):
    rng = random.Random(808)
    # Paired lane-day difference SD=3 min; baseline estimate adds uncertainty.
    # Normal critical values are planning approximations; simulation directly
    # measures rejection under null and assumed alternatives.
    results = []
    for days in (14, 28, 42, 56):
        for effect in (0, 1.5, 3, 6):
            estimates = []
            rejected = 0
            for _ in range(draws):
                pre = [rng.gauss(0, 3) for _ in range(14)]
                post = [rng.gauss(-effect, 3) for _ in range(days)]
                estimate = st.mean(post) - st.mean(pre)
                se = math.sqrt(st.variance(pre) / 14 + st.variance(post) / days)
                rejected += abs(estimate) > 1.96 * se
                estimates.append(estimate)
            results.append(
                dict(
                    post_days=days,
                    baseline_days=14,
                    effect_minutes=effect,
                    rejection_rate=rejected / draws,
                    mean_estimate=st.mean(estimates),
                )
            )
    # A separate no-intervention early/late baseline placebo.
    placebo = []
    for _ in range(draws):
        before = [rng.gauss(0, 3) for _ in range(14)]
        after = [rng.gauss(0, 3) for _ in range(14)]
        placebo.append(st.mean(after) - st.mean(before))
    missing = []
    for spillover in (0, 0.25, 0.50):
        for dropout in (0, 0.10, 0.25):
            observed = []
            retained = []
            for _ in range(draws):
                pre = [rng.gauss(0, 3) for _ in range(14)]
                post = [
                    rng.gauss(-6 * (1 - spillover), 3) for _ in range(28) if rng.random() >= dropout
                ]
                if len(post) >= 2:
                    observed.append(st.mean(post) - st.mean(pre))
                    retained.append(len(post))
            missing.append(
                dict(
                    spillover_fraction=spillover,
                    random_missing_fraction=dropout,
                    mean_estimate=st.mean(observed),
                    mean_retained_days=st.mean(retained),
                )
            )
    return dict(
        synthetic=True,
        draws_per_cell=draws,
        paired_difference_sd_minutes=3,
        planning=results,
        placebo_95=[percentile(placebo, 0.025), percentile(placebo, 0.975)],
        spillover_missingness=missing,
        caveats=[
            "Normal 1.96 critical value approximates small-sample inference; empirical null rate is disclosed.",
            "Random missingness only: nonrandom loss can bias estimates.",
            "Historical paired-day variability must replace the invented SD before a real pilot.",
            "Daily assignment assumes intervention can switch without carryover; otherwise randomize persistent clusters.",
        ],
    )
