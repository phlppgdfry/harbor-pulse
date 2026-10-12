"""Local reference walkthrough; does not assess personal mastery or call cloud APIs."""

import argparse
import copy
import json
import pathlib
import sqlite3
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from harbor_pulse.challenge import weighted_kpis
from harbor_pulse.pipeline import SOURCES, connect, facts, ingest, publication_gate
from harbor_pulse.review import sensitivity


def walkthrough(run):
    run = pathlib.Path(run)
    original = {name: json.loads((run / "raw" / f"{name}.json").read_text()) for name in SOURCES}
    db = sqlite3.connect((run / "warehouse.sqlite").resolve().as_uri() + "?mode=ro", uri=True)
    db.row_factory = sqlite3.Row
    try:
        change = db.execute(
            "SELECT * FROM audit WHERE source='arrivals' AND old_version IS NOT NULL ORDER BY run,event_key LIMIT 1"
        ).fetchone()
        if change is None:
            raise ValueError("No corrected arrival found; reproduce the complete demo first")
        current = json.loads(
            db.execute(
                "SELECT payload FROM events WHERE source='arrivals' AND event_key=?",
                (change["event_key"],),
            ).fetchone()["payload"]
        )
        previous = next(
            row
            for row in original["arrivals"]
            if row["key"] == change["event_key"] and row["version"] == change["old_version"]
        )
        daily = json.loads(
            db.execute(
                "SELECT payload FROM facts WHERE date_key=? AND terminal_key=?",
                (current["DateKey"], current["TerminalKey"]),
            ).fetchone()["payload"]
        )
        trail = dict(
            key=change["event_key"],
            run=change["run"],
            old_version=change["old_version"],
            new_version=change["new_version"],
            old_units=previous["Units"],
            new_units=current["Units"],
            unit_change=current["Units"] - previous["Units"],
            date=current["DateKey"],
            terminal=current["TerminalKey"],
            daily_fact_units=daily["Vehicles"],
        )
    finally:
        db.close()
    if trail["unit_change"] != 2 or trail["new_version"] <= trail["old_version"]:
        raise RuntimeError("Reference correction no longer matches the documented exercise")
    fixture = json.loads((ROOT / "fixtures/hand-calculated.json").read_text())
    computed = weighted_kpis(fixture["rows"])
    for key, expected in fixture["expected"].items():
        if computed[key] is None or abs(computed[key] - expected) > 1e-9:
            raise RuntimeError("Hand-calculation mismatch: " + key)
    clean = json.loads((run / "tables.json").read_text())["FactOps"]
    grid = sensitivity(clean)["grid"]
    scenarios = [
        next(row for row in grid if row["fraction"] == fraction and row["hour_value"] == 45)
        for fraction in [0.1, 0]
    ]
    if (
        scenarios[0]["preferred"] != "Dispatch / slots"
        or scenarios[1]["preferred"] != "Do not implement"
    ):
        raise RuntimeError("Expected assumption reversal did not occur")
    latest = json.loads((run / "loads.json").read_text())[-1]
    gate = publication_gate(clean, latest)
    try:
        publication_gate(clean, latest, minimum_coverage=0.999)
    except ValueError as error:
        if "publication_gate_failed" not in str(error):
            raise
        strict_gate = dict(blocked=True, reason=str(error), threshold=0.999)
    else:
        raise RuntimeError("Expected stricter coverage gate to block this demo")
    # Copy a single terminal-day into a disposable warehouse. Inject a failure
    # after its first higher-version mutation, never into the existing run.
    small = {
        name: [
            row
            for row in rows
            if row.get("DateKey") == current["DateKey"]
            and row.get("TerminalKey") == current["TerminalKey"]
        ]
        for name, rows in original.items()
    }
    corrected = copy.deepcopy(small)
    corrected["arrivals"].append(copy.deepcopy(current))
    with tempfile.TemporaryDirectory(prefix="harbor-practice-") as folder:
        scratch = connect(pathlib.Path(folder) / "scratch.sqlite")
        try:
            ingest(scratch, small)
            before = facts(scratch)
            marks_before = [
                tuple(row) for row in scratch.execute("SELECT * FROM watermarks ORDER BY source")
            ]
            try:
                ingest(scratch, corrected, fail_after=1)
            except RuntimeError as error:
                if str(error) != "injected_failure":
                    raise
            else:
                raise RuntimeError("Expected injected failure did not occur")
            if (
                facts(scratch) != before
                or [
                    tuple(row)
                    for row in scratch.execute("SELECT * FROM watermarks ORDER BY source")
                ]
                != marks_before
            ):
                raise RuntimeError("Rollback changed previously verified data")
            rollback = dict(
                failure="injected_failure",
                facts_preserved=True,
                watermarks_preserved=True,
                failed_run_recorded=scratch.execute(
                    "SELECT status FROM runs ORDER BY id DESC LIMIT 1"
                ).fetchone()[0]
                == "failed",
            )
            if not rollback["failed_run_recorded"]:
                raise RuntimeError("Failure not logged")
        finally:
            scratch.close()
    return dict(
        status="passed",
        scope="Automated local reference run; personal independent execution is not assessed",
        cloud_called=False,
        existing_warehouse_read_only=True,
        correction=trail,
        hand_kpis=computed,
        assumption_change=scenarios,
        coverage_gate=dict(
            actual=gate["departure_coverage"], default_threshold=0.99, strict=strict_gate
        ),
        rollback=rollback,
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", type=pathlib.Path, default=ROOT / "build/run")
    parser.add_argument(
        "--output", type=pathlib.Path, default=ROOT / "build/practice-reference.json"
    )
    args = parser.parse_args()
    result = walkthrough(args.run)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2))
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
