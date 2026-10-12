import base64
import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts import native_refresh as refresh


class NativeRefreshTests(unittest.TestCase):
    def exercise(self, fault=None):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            build = root / "build"
            build.mkdir()
            baseline = build / "base"
            baseline.mkdir()
            tables = {"FactOps": [{"Vehicles": 1}]}
            (baseline / "tables.json").write_text(json.dumps(tables))
            state = build / "refresh-state.private.json"
            state.write_text('{"old_verified_state":true}')
            old = state.read_bytes()

            def generate(cmd, **kwargs):
                folder = Path(cmd[cmd.index("--output") + 1])
                for name, data in [
                    ("tables", tables),
                    ("gate", {"checks": {"all": True}}),
                    ("summary", {"vehicles": 1}),
                ]:
                    (folder / (name + ".json")).write_text(json.dumps(data))

            encoded = base64.b64encode(json.dumps(tables["FactOps"]).encode()).decode()
            source = {
                "definition": {
                    "parts": [
                        {
                            "path": "definition/tables/FactOps.tmdl",
                            "payload": base64.b64encode(
                                f'Binary.FromText("{encoded}")'.encode()
                            ).decode(),
                        }
                    ]
                }
            }

            def api(endpoint, method="get", body=None, audience="powerbi"):
                if fault == "expired_auth":
                    raise RuntimeError("Authentication expired")
                if endpoint.endswith("getDefinition"):
                    return {"status_code": 200, "text": source}
                if endpoint.endswith("/refreshes"):
                    if method == "post":
                        return {"status_code": 429 if fault == "429" else 202, "text": {}}
                    import datetime as dt

                    return {
                        "status_code": 200,
                        "text": {
                            "value": [
                                {
                                    "status": "Failed" if fault == "failed" else "Completed",
                                    "startTime": dt.datetime.now(dt.timezone.utc).isoformat(),
                                    "endTime": dt.datetime.now(dt.timezone.utc).isoformat(),
                                }
                            ]
                        },
                    }
                if endpoint.endswith("executeQueries"):
                    return {
                        "status_code": 200,
                        "text": {
                            "results": [
                                {
                                    "tables": [
                                        {
                                            "rows": [
                                                {
                                                    "[Vehicles]": 2
                                                    if fault == "wrong_totals"
                                                    else 1,
                                                    "[Difference]": 0,
                                                    "[Coverage]": 1,
                                                }
                                            ]
                                        }
                                    ]
                                }
                            ]
                        },
                    }
                return {
                    "status_code": 200,
                    "text": {"datasetId": "wrong" if fault == "wrong_binding" else "model"},
                }

            with (
                patch.object(refresh.subprocess, "run", side_effect=generate),
                patch.object(refresh, "api", side_effect=api),
                patch.object(refresh.time, "sleep"),
                patch.object(
                    refresh.time,
                    "monotonic",
                    side_effect=[0, 301] if fault == "timeout" else [0, 1],
                ),
                contextlib.redirect_stdout(io.StringIO()),
            ):
                if fault:
                    with self.assertRaises(RuntimeError):
                        refresh.run_refresh("model", "report", "workspace", baseline, root)
                    self.assertEqual(state.read_bytes(), old)
                else:
                    result = refresh.run_refresh("model", "report", "workspace", baseline, root)
                    self.assertEqual(result["status"], "passed")
                    self.assertEqual(json.loads(state.read_text())["release_status"], "verified")
            log = json.loads((build / "native-refresh-last.private.json").read_text())
            self.assertFalse(log["model_mutations"])
            self.assertEqual(log["status"], "failed" if fault else "passed")

    def test_failed_refresh_preserves_previous_verified_state(self):
        for fault in ["expired_auth", "429", "failed", "timeout", "wrong_totals", "wrong_binding"]:
            with self.subTest(fault=fault):
                self.exercise(fault)

    def test_success_reconciles_before_atomic_state_change(self):
        self.exercise()
