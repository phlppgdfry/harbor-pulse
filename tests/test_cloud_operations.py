"""Offline contract tests: subprocess/API responses are mocked, no tenant writes."""

import base64
import copy
import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts import cloud_operations as cloud


def response(status=200, text=None, headers=None):
    return dict(status_code=status, text=text, headers=headers or {})


def process(data):
    return subprocess.CompletedProcess([], 0, json.dumps({"result": {"data": [data]}}), "")


class CloudTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        (self.root / "build").mkdir()
        (self.root / "evidence").mkdir()
        self.root_patch = patch.object(cloud, "ROOT", self.root)
        self.root_patch.start()

    def tearDown(self):
        self.root_patch.stop()
        self.temp.cleanup()

    def test_rate_limit_retries_read_then_succeeds(self):
        with (
            patch.object(
                cloud.subprocess,
                "run",
                side_effect=[
                    process(response(429, headers={"Retry-After": "1"})),
                    process(response(text={"ok": True})),
                ],
            ) as run,
            patch.object(cloud.time, "sleep") as sleep,
        ):
            self.assertEqual(cloud.api("reports/r")["text"], {"ok": True})
            self.assertEqual(run.call_count, 2)
            sleep.assert_called_once_with(1)

    def test_create_is_not_retried_and_request_file_is_removed(self):
        def run(cmd, **kwargs):
            body = Path(cmd[cmd.index("-i") + 1])
            self.assertEqual(json.loads(body.read_text()), {"displayName": "test"})
            return process(response(503))

        with patch.object(cloud.subprocess, "run", side_effect=run) as execute:
            self.assertEqual(
                cloud.api("workspaces/w/items", "post", {"displayName": "test"})["status_code"], 503
            )
            self.assertEqual(execute.call_count, 1)
        self.assertEqual(list((self.root / "build").glob("*.private.json")), [])

    def test_credentials_failure_and_subprocess_timeout_clean_up(self):
        for effect in [
            subprocess.CompletedProcess([], 1, "", "Authentication required"),
            subprocess.TimeoutExpired("fab", 150),
        ]:
            with (
                self.subTest(effect=type(effect).__name__),
                patch.object(cloud.subprocess, "run") as execute,
            ):
                if isinstance(effect, Exception):
                    execute.side_effect = effect
                else:
                    execute.return_value = effect
                with self.assertRaises((RuntimeError, subprocess.TimeoutExpired)):
                    cloud.api("executeQueries", "post", {"queries": []})
                self.assertEqual(list((self.root / "build").glob("*.private.json")), [])

    def test_retry_exhaustion_returns_failure_for_caller(self):
        with (
            patch.object(
                cloud.subprocess,
                "run",
                return_value=process(response(503, text={"error": "unavailable"})),
            ) as execute,
            patch.object(cloud.time, "sleep"),
        ):
            with self.assertRaisesRegex(RuntimeError, "503"):
                cloud.successful(cloud.api("reports/r"))
            self.assertEqual(execute.call_count, 3)

    def test_poll_success_failure_no_result_and_timeout(self):
        accepted = response(202, headers={"x-ms-operation-id": "op"})
        with (
            patch.object(cloud.time, "sleep"),
            patch.object(
                cloud,
                "api",
                side_effect=[
                    response(text={"status": "Succeeded"}),
                    response(text={"id": "report"}),
                ],
            ),
        ):
            self.assertEqual(cloud.completion(accepted), {"id": "report"})
        with (
            patch.object(cloud.time, "sleep"),
            patch.object(
                cloud,
                "api",
                side_effect=[
                    response(text={"status": "Succeeded"}),
                    response(400, {"errorCode": "OperationHasNoResult"}),
                ],
            ),
        ):
            self.assertIsNone(cloud.completion(accepted))
        with (
            patch.object(cloud.time, "sleep"),
            patch.object(cloud, "api", return_value=response(text={"status": "Failed"})),
        ):
            with self.assertRaisesRegex(RuntimeError, "Failed"):
                cloud.completion(accepted)
        with patch.object(cloud.time, "monotonic", side_effect=[0, 241]):
            with self.assertRaisesRegex(RuntimeError, "timed out"):
                cloud.completion(accepted)
        self.assertEqual(cloud.completion(response(text={"ok": True})), {"ok": True})

    def test_health_checks_binding_reconciliation_access_and_freshness(self):
        import datetime as dt

        now = dt.datetime.now(dt.timezone.utc)
        stamp = now.isoformat()
        manifest = dict(
            ingested_at=stamp,
            source_kind="synthetic",
            source_fact_difference=0,
            departure_coverage=1,
            release_status="verified",
        )
        state = self.root / "build/refresh-state.private.json"
        state.write_text(json.dumps(manifest))
        data = [
            response(text={"datasetId": "model"}),
            response(
                text={
                    "results": [
                        {
                            "tables": [
                                {
                                    "rows": [
                                        {"[Difference]": 0, "[Vehicles]": 366910, "[Coverage]": 1}
                                    ]
                                }
                            ]
                        }
                    ]
                }
            ),
            response(
                text={"value": [{"status": "Completed", "startTime": stamp, "endTime": stamp}]}
            ),
            response(text={"value": [{"identifier": "owner", "reportUserAccessRight": "Owner"}]}),
            response(text={"value": [{"identifier": "owner", "datasetUserAccessRight": "Owner"}]}),
        ]
        with patch.object(cloud, "api", side_effect=data):
            self.assertTrue(cloud.health("report", "model", "workspace")["healthy"])
        failures = {
            "binding": (0, response(text={"datasetId": "wrong"})),
            "reconciliation": (1, response(text={"results": [{"tables": [{"rows": []}]}]})),
            "no_refresh": (2, response(text={"value": []})),
            "stale_refresh": (
                2,
                response(
                    text={
                        "value": [
                            {
                                "status": "Completed",
                                "startTime": stamp,
                                "endTime": (now - dt.timedelta(hours=30)).isoformat(),
                            }
                        ]
                    }
                ),
            ),
            "failed_latest_refresh": (
                2,
                response(
                    text={
                        "value": [
                            {
                                "status": "Completed",
                                "startTime": (now - dt.timedelta(hours=1)).isoformat(),
                                "endTime": stamp,
                            },
                            {"status": "Failed", "startTime": stamp},
                        ]
                    }
                ),
            ),
            "access_drift": (
                4,
                response(
                    text={"value": [{"identifier": "different", "datasetUserAccessRight": "Owner"}]}
                ),
            ),
            "api_denied": (3, response(403, {"error": {"code": "Denied"}})),
        }
        for name, (index, bad) in failures.items():
            variant = copy.deepcopy(data)
            variant[index] = bad
            with self.subTest(name=name), patch.object(cloud, "api", side_effect=variant):
                self.assertFalse(cloud.health("report", "model", "workspace")["healthy"])
        state.unlink()
        with patch.object(cloud, "api", side_effect=data):
            self.assertFalse(cloud.health("report", "model", "workspace")["healthy"])

    def test_recovery_changes_restores_and_deletes_only_clone(self):
        original = {
            "definition": {
                "parts": [
                    {
                        "path": "definition/pages/p/page.json",
                        "payload": base64.b64encode(b'{"displayName":"Original"}').decode(),
                    }
                ]
            }
        }
        changed = copy.deepcopy(original)
        changed["definition"]["parts"][0]["payload"] = base64.b64encode(
            b'{"displayName":"Changed"}'
        ).decode()
        calls = []

        def api(endpoint, method="get", body=None, audience="powerbi"):
            calls.append((endpoint, method))
            if endpoint.endswith("/items"):
                return response(201, {"id": "clone"})
            if method == "delete":
                return response(204)
            return response(text={"datasetId": "model"})

        with (
            patch.object(
                cloud, "definition", side_effect=[original, original, changed, original, original]
            ),
            patch.object(cloud, "api", side_effect=api),
        ):
            result = cloud.drill("production", "workspace")
        self.assertTrue(result["passed"])
        self.assertTrue(result["temporary_clone_deleted"])
        self.assertEqual([c for c in calls if c[1] == "delete"], [("reports/clone", "delete")])
        self.assertFalse(any("production" in url and method != "get" for url, method in calls))

    def test_recovery_failure_still_deletes_clone(self):
        original = {
            "definition": {
                "parts": [
                    {
                        "path": "definition/pages/p/page.json",
                        "payload": base64.b64encode(b"{}").decode(),
                    }
                ]
            }
        }
        with (
            patch.object(cloud, "definition", return_value=original),
            patch.object(
                cloud,
                "api",
                side_effect=[
                    response(201, {"id": "clone"}),
                    response(500, {"error": "write failed"}),
                    response(204),
                ],
            ) as execute,
        ):
            with self.assertRaisesRegex(RuntimeError, "500"):
                cloud.drill("production", "workspace")
        self.assertEqual(execute.call_args.args, ("reports/clone", "delete"))

    def test_backup_failure_still_deletes_newly_created_clone(self):
        original = {"definition": {"parts": []}}
        with (
            patch.object(
                cloud, "definition", side_effect=[original, RuntimeError("backup failed")]
            ),
            patch.object(
                cloud, "api", side_effect=[response(201, {"id": "clone"}), response(204)]
            ) as execute,
        ):
            with self.assertRaisesRegex(RuntimeError, "backup failed"):
                cloud.drill("production", "workspace")
        self.assertEqual(execute.call_args.args, ("reports/clone", "delete"))
