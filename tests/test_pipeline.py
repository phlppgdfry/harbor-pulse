import copy
import tempfile
import unittest
from pathlib import Path

from harbor_pulse.analysis import decisions, pilot
from harbor_pulse.pipeline import connect, facts, ingest, publication_gate
from harbor_pulse.sources import generate


def base():
    return [
        dict(
            DateKey=20260101,
            TerminalKey=1,
            Vehicles=120,
            OnTimeVehicles=114,
            DelayMinutes=20,
            DwellHours=18,
            AvailableSlots=200,
            OccupiedSlots=90,
            HandlingCapacity=180,
            PlannedVehicles=125,
            IncidentFlag=False,
            Incident="Regulier",
            CO2Kg=300,
            Revenue=3600,
            HandlingCost=2400,
        )
    ]


class PipelineTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.db = connect(Path(self.temp.name) / "test.sqlite")
        self.source, self.corrected, _ = generate(base())

    def tearDown(self):
        self.db.close()
        self.temp.cleanup()

    def test_replay_is_idempotent(self):
        first = ingest(self.db, self.source)
        second = ingest(self.db, self.source)
        self.assertEqual((second["inserted"], second["updated"]), (0, 0))
        self.assertEqual(first["fact_vehicles"], second["fact_vehicles"])

    def test_late_correction_changes_only_latest_business_key(self):
        ingest(self.db, self.source)
        result = ingest(self.db, self.corrected)
        self.assertEqual(result["updated"], 1)
        self.assertEqual(result["fact_vehicles"], 122)
        self.assertEqual(len(facts(self.db)), 1)

    def test_invalid_records_and_version_conflict_are_quarantined(self):
        result = ingest(self.db, self.source)
        self.assertEqual(result["rejected"], 4)
        self.assertEqual(result["fact_vehicles"], 120)
        reasons = {r["reason"] for r in self.db.execute("SELECT reason FROM quarantine")}
        self.assertIn("invalid_units", reasons)
        self.assertIn("conflicting_same_version", reasons)

    def test_missing_departure_is_visible_not_counted_as_zero_dwell(self):
        result = ingest(self.db, self.source)
        fact = facts(self.db)[0]
        self.assertEqual(result["missing_departures"], 1)
        self.assertEqual(fact["DwellHours"], 18)
        self.assertLess(fact["CompleteDepartureUnits"], fact["Vehicles"])

    def test_transaction_failure_leaves_no_partial_events_or_watermarks(self):
        with self.assertRaisesRegex(RuntimeError, "injected_failure"):
            ingest(self.db, self.source, fail_after=2)
        self.assertEqual(self.db.execute("SELECT COUNT(*) FROM events").fetchone()[0], 0)
        self.assertEqual(self.db.execute("SELECT COUNT(*) FROM watermarks").fetchone()[0], 0)
        self.assertEqual(self.db.execute("SELECT status FROM runs").fetchone()[0], "failed")

    def test_stale_revision_cannot_overwrite_correction(self):
        ingest(self.db, self.corrected)
        latest = facts(self.db)[0]["Vehicles"]
        ingest(self.db, self.source)
        self.assertEqual(facts(self.db)[0]["Vehicles"], latest)

    def test_reconciliation_matches_latest_valid_source(self):
        result = ingest(self.db, self.corrected)
        self.assertEqual(result["source_vehicles"], result["fact_vehicles"])
        self.assertEqual(result["difference"], 0)

    def test_bad_chronology_is_excluded_from_departure_coverage(self):
        source = copy.deepcopy(self.source)
        departure = source["departures"][0]
        departure["departure"] = "2025-12-31T00:00:00Z"
        result = ingest(self.db, source)
        self.assertEqual(result["invalid_departures"], 1)
        self.assertEqual(result["missing_departures"], 2)

    def test_publication_blocks_insufficient_departure_coverage(self):
        run = ingest(self.db, self.source)
        with self.assertRaisesRegex(ValueError, "publication_gate_failed"):
            publication_gate(facts(self.db), run)

    def test_early_arrival_is_valid_and_does_not_create_negative_delay(self):
        source = copy.deepcopy(self.source)
        arrival = source["arrivals"][2]
        arrival["actual"] = "2026-01-01T05:00:00Z"
        run = ingest(self.db, source)
        self.assertEqual(run["rejected"], 4)
        self.assertGreaterEqual(facts(self.db)[0]["DelayMinutes"], 0)

    def test_non_string_timestamp_is_quarantined_not_a_partial_failure(self):
        source = copy.deepcopy(self.source)
        row = copy.deepcopy(source["arrivals"][2])
        row.update(key="null-time", actual=None)
        source["arrivals"].append(row)
        run = ingest(self.db, source)
        self.assertEqual(run["status"], "succeeded")
        self.assertEqual(run["rejected"], 5)


class AnalysisTests(unittest.TestCase):
    def test_simulated_pilot_is_balanced_and_effect_has_expected_sign(self):
        p = pilot()
        self.assertEqual(len(p["sessions"]), 84)
        for day in {r["Dag"] for r in p["sessions"]}:
            rows = [r for r in p["sessions"] if r["Dag"] == day]
            self.assertEqual({r["Groep"] for r in rows}, {"Interventie", "Controle"})
            self.assertEqual(rows[0]["Vehicles"], rows[1]["Vehicles"])
        self.assertLess(p["paired_day_bootstrap_95"][1], 0)

    def test_decisions_include_opex_and_implementation_separately(self):
        d = decisions(base(), draws=100)
        for option in d["options"]:
            self.assertGreater(option["ImplementatieEUR"], 0)
            self.assertEqual(option["NettoP50"], option["BrutoP50"] - option["JaarlijkseOpexEUR"])
            self.assertLessEqual(option["NettoP10"], option["NettoP50"])
            self.assertLessEqual(option["NettoP50"], option["NettoP90"])


if __name__ == "__main__":
    unittest.main()
