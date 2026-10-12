import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts import publish_powerbi as publisher


class PublicationTests(unittest.TestCase):
    def test_uncertain_creation_and_partial_load_cannot_create_duplicates(self):
        for failure in ["timeout", "429", "load_failure"]:
            with self.subTest(failure=failure), tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                run = root / "run"
                run.mkdir()
                (root / "build").mkdir()
                for name, data in [
                    ("gate", {"checks": {"valid": True}}),
                    ("model", {"name": "Demo"}),
                    ("tables", {"FactOps": [{"Vehicles": 1}]}),
                ]:
                    (run / (name + ".json")).write_text(json.dumps(data))

                def call(url, *args, failure=failure):
                    if failure == "timeout":
                        raise subprocess.TimeoutExpired("fab", 120)
                    if failure == "429":
                        raise RuntimeError("429")
                    if url.endswith("/datasets"):
                        return {"text": {"id": "created", "name": "Demo"}}
                    raise RuntimeError("Load failed")

                with (
                    patch.object(publisher, "ROOT", root),
                    patch.object(publisher, "call", side_effect=call) as api,
                    patch("sys.argv", ["publish", "--run", str(run)]),
                ):
                    with self.assertRaises((RuntimeError, subprocess.TimeoutExpired)):
                        publisher.main()
                    count = api.call_count
                    with self.assertRaisesRegex(SystemExit, "Refusing duplicate"):
                        publisher.main()
                    self.assertEqual(api.call_count, count)
                    receipt = json.loads((root / "build/publication.private.json").read_text())
                    self.assertNotEqual(receipt["status"], "complete")

    def test_cli_adapter_cleans_request_on_auth_timeout_and_http_failure(self):
        for failure in ["auth", "timeout", "http", "status"]:
            with self.subTest(failure=failure), tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                (root / "build").mkdir()
                result = {
                    "status": "Success",
                    "result": {
                        "data": [{"status_code": 503 if failure == "http" else 200, "text": {}}]
                    },
                }
                if failure == "status":
                    result["status"] = "Failure"
                with (
                    patch.object(publisher, "ROOT", root),
                    patch.object(publisher.subprocess, "run") as run,
                ):
                    if failure == "timeout":
                        run.side_effect = subprocess.TimeoutExpired("fab", 120)
                    else:
                        run.return_value = subprocess.CompletedProcess(
                            [],
                            1 if failure == "auth" else 0,
                            json.dumps(result),
                            "Authentication expired" if failure == "auth" else "",
                        )
                    with self.assertRaises((RuntimeError, subprocess.TimeoutExpired)):
                        publisher.call(
                            "https://api.powerbi.com/v1.0/myorg/datasets",
                            "post",
                            {"name": "Demo"},
                            "powerbi",
                        )
                    self.assertEqual(list((root / "build").glob("*.private.json")), [])

    def test_cli_adapter_accepts_valid_response_and_keeps_private_receipt(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "build").mkdir()
            receipt = root / "build/response.private.json"
            result = {
                "status": "Success",
                "result": {"data": [{"status_code": 201, "text": {"id": "created"}}]},
            }
            with (
                patch.object(publisher, "ROOT", root),
                patch.object(
                    publisher.subprocess,
                    "run",
                    return_value=subprocess.CompletedProcess([], 0, json.dumps(result), ""),
                ),
            ):
                self.assertEqual(
                    publisher.call("datasets", "post", {"name": "Demo"}, "powerbi", receipt)[
                        "text"
                    ]["id"],
                    "created",
                )
            self.assertTrue(receipt.exists())
            self.assertEqual(list((root / "build").glob("*.private.json")), [receipt])
