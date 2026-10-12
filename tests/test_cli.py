"""End-to-end local reproduction plus refusal to overwrite an existing warehouse."""

import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from harbor_pulse.__main__ import main


class CliTests(unittest.TestCase):
    def test_reproduction_monitor_and_overwrite_guard(self):
        with tempfile.TemporaryDirectory() as folder:
            output = Path(folder) / "case"
            with (
                patch("sys.argv", ["harbor-pulse", "demo", "--output", str(output)]),
                contextlib.redirect_stdout(io.StringIO()),
            ):
                main()
            summary = json.loads((output / "summary.json").read_text())
            self.assertEqual(summary["vehicles"], 366910)
            self.assertEqual(summary["source_fact_difference"], 0)
            self.assertEqual(summary["replay_new_events"], 0)
            with (
                patch("sys.argv", ["harbor-pulse", "monitor", "--output", str(output)]),
                contextlib.redirect_stdout(io.StringIO()) as captured,
            ):
                main()
            self.assertEqual(len(json.loads(captured.getvalue())), 3)
            with patch("sys.argv", ["harbor-pulse", "demo", "--output", str(output)]):
                with self.assertRaisesRegex(SystemExit, "already contains data"):
                    main()
