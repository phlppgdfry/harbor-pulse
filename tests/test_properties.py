"""Generated ingestion cases: independent latest-version oracle and atomic rollback."""

import copy
import tempfile
import unittest
from pathlib import Path

from hypothesis import given, settings
from hypothesis import strategies as st
from test_pipeline import base

from harbor_pulse.pipeline import connect, facts, ingest, validate
from harbor_pulse.sources import generate


def clean_source():
    source, _, _ = generate(base())
    arrivals = {}
    for row in source["arrivals"]:
        try:
            validate("arrivals", row)
        except (ValueError, KeyError, TypeError):
            continue
        arrivals.setdefault(row["key"], row)
    source["arrivals"] = list(arrivals.values())
    return source


class PropertyTests(unittest.TestCase):
    @settings(max_examples=60, deadline=None, derandomize=True)
    @given(st.lists(st.integers(min_value=1, max_value=8), min_size=1, max_size=30))
    def test_latest_revision_wins_regardless_of_order_or_duplicates(self, versions):
        source = clean_source()
        first = source["arrivals"][0]
        other = sum(r["Units"] for r in source["arrivals"][1:])
        source["arrivals"] = source["arrivals"][1:] + [
            dict(first, version=v, Units=10 + v, OnTimeUnits=0) for v in versions
        ]
        with tempfile.TemporaryDirectory() as folder:
            db = connect(Path(folder) / "property.sqlite")
            try:
                result = ingest(db, source)
                self.assertEqual(result["fact_vehicles"], other + 10 + max(versions))
                self.assertEqual(result["difference"], 0)
                replay = ingest(db, source)
                self.assertEqual((replay["inserted"], replay["updated"]), (0, 0))
                self.assertEqual(replay["fact_vehicles"], result["fact_vehicles"])
            finally:
                db.close()

    @settings(max_examples=25, deadline=None, derandomize=True)
    @given(st.integers(min_value=1, max_value=3), st.integers(min_value=1, max_value=100))
    def test_failure_preserves_previously_committed_facts(self, fail_after, extra):
        source = clean_source()
        with tempfile.TemporaryDirectory() as folder:
            db = connect(Path(folder) / "rollback.sqlite")
            try:
                ingest(db, source)
                before = facts(db)
                watermarks = [tuple(r) for r in db.execute("SELECT * FROM watermarks")]
                changed = copy.deepcopy(source)
                for r in changed["arrivals"]:
                    r.update(version=2, Units=r["Units"] + extra)
                with self.assertRaisesRegex(RuntimeError, "injected_failure"):
                    ingest(db, changed, fail_after=fail_after)
                self.assertEqual(facts(db), before)
                self.assertEqual(
                    [tuple(r) for r in db.execute("SELECT * FROM watermarks")], watermarks
                )
            finally:
                db.close()
