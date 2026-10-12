import json
import pathlib

root = pathlib.Path(__file__).resolve().parents[1]
p = root / "build/run"
summary = json.loads((p / "summary.json").read_text())
loads = json.loads((p / "loads.json").read_text())
assert summary["synthetic"] and summary["pipeline_status"] == "passed"
assert summary["source_fact_difference"] == 0 and summary["replay_new_events"] == 0
assert summary["late_corrections"] == 36 and summary["quarantined_initial"] == 4
assert summary["fact_rows"] == 1095 and summary["vehicles"] == 366910
assert loads[0]["duplicates"] == 216 and loads[-1]["missing_departures"] == 67
pilot = json.loads((p / "pilot.json").read_text())
assert pilot["synthetic"] and len(pilot["sessions"]) == 84
decisions = json.loads((p / "decisions.json").read_text())
assert len(decisions["options"]) == 3
print(
    "PASS reproducible evidence: reconciliation, replay, late revisions, quarantine, pilot and decision assumptions"
)
