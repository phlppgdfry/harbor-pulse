import json
import unittest
from pathlib import Path

from harbor_pulse.challenge import (
    pilot_usefulness,
    selective_missingness,
    thresholds,
    weighted_kpis,
)


class ChallengeTests(unittest.TestCase):
    def test_hand_calculated_dataset(self):
        fixture = json.loads(
            (Path(__file__).resolve().parents[1] / "fixtures/hand-calculated.json").read_text()
        )
        for key, value in fixture["expected"].items():
            self.assertAlmostEqual(weighted_kpis(fixture["rows"])[key], value)
        self.assertNotEqual(weighted_kpis(fixture["rows"])["dwell"], (2 + 4 + 8) / 3)
        self.assertIsNone(weighted_kpis([])["delay"])

    def test_break_even_is_zero_net_and_execution_failure_raises_threshold(self):
        rows = [{"Vehicles": 6000, "DelayMinutes": 20}]
        for option in thresholds(rows)["options"]:
            self.assertAlmostEqual(
                option["saved_hours"] * 45 * option["annual_break_even_fraction"]
                - option["annual_cost"],
                0,
            )
            self.assertGreater(
                option["failure_adjusted_break_even"][-1]["fraction"],
                option["annual_break_even_fraction"],
            )

    def test_significance_alone_cannot_establish_useful_or_financial_effect(self):
        cases = pilot_usefulness()["cases"]
        self.assertTrue(cases[0]["statistically_detectable"])
        self.assertFalse(cases[0]["minimum_effect_established"])
        self.assertFalse(cases[1]["decision_ready"])
        self.assertTrue(cases[2]["decision_ready"])
        self.assertFalse(cases[3]["decision_ready"])

    def test_selective_loss_understates_known_slow_records(self):
        rows = [
            dict(
                Vehicles=10,
                OnTimeVehicles=10,
                DelayMinutes=i,
                DwellHours=i,
                CompleteDepartureUnits=10,
                AvailableSlots=20,
                OccupiedSlots=10,
                Revenue=100,
                HandlingCost=50,
            )
            for i in range(1, 11)
        ]
        result = selective_missingness(rows)
        selective = result["scenarios"][1]
        self.assertLess(selective["linked_delay_bias"], 0)
        self.assertLess(selective["linked_dwell_bias"], 0)
        lo, hi = selective["dwell_identification_bounds_0_to_72h"]
        self.assertLessEqual(lo, 5.5)
        self.assertGreaterEqual(hi, 5.5)
