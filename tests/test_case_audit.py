"""Mutation tests: reject stale claims and changed screenshot identities."""

import json
import shutil
import tempfile
import unittest
from pathlib import Path

from scripts.audit_case import verify

ROOT = Path(__file__).resolve().parents[1]


class AuditTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        for folder in ["contracts", "evidence", "docs", "powerbi", "output", "fixtures"]:
            shutil.copytree(ROOT / folder, self.root / folder)
        shutil.copy2(ROOT / "README.md", self.root / "README.md")
        run = self.root / "build/run"
        run.mkdir(parents=True)
        for name in ["summary", "loads"]:
            shutil.copy2(ROOT / "evidence" / (name + ".json"), run / (name + ".json"))

    def tearDown(self):
        self.temp.cleanup()

    def test_release_inventory_matches(self):
        self.assertEqual(verify(self.root)["status"], "passed")

    def test_visible_website_kpi_drift_is_rejected(self):
        page = self.root / "docs/index.html"
        page.write_text(page.read_text().replace("<strong>216</strong>", "<strong>217</strong>"))
        with self.assertRaisesRegex(ValueError, "Visible website KPI drift"):
            verify(self.root)

    def test_stale_json_total_is_rejected(self):
        path = self.root / "evidence/summary.json"
        value = json.loads(path.read_text())
        value["vehicles"] += 1
        path.write_text(json.dumps(value))
        with self.assertRaisesRegex(ValueError, "Public JSON summary drift"):
            verify(self.root)

    def test_changed_screenshot_bytes_require_review(self):
        image = self.root / "docs/assets/powerbi/hp_quality.png"
        image.write_bytes(image.read_bytes() + b"changed")
        with self.assertRaisesRegex(ValueError, "Unreviewed artifact drift"):
            verify(self.root)
