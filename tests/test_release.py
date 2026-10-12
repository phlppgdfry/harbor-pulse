"""Release fault injection uses an in-memory cloud; never creates a real model."""

import base64
import copy
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts import release_report as release


def definition(title):
    return {
        "definition": {
            "format": "PBIR",
            "parts": [
                {
                    "path": "definition/pages/p/page.json",
                    "payload": base64.b64encode(
                        json.dumps({"displayName": title}).encode()
                    ).decode(),
                    "payloadType": "InlineBase64",
                }
            ],
        }
    }


class ReleaseTests(unittest.TestCase):
    def run_case(self, fault=None, rollback_fault=False):
        before = definition("before")
        source = definition("after")
        state = {"definition": copy.deepcopy(before), "binding": "model", "updates": 0, "calls": []}

        def get_definition(workspace, report):
            if fault == "verification_timeout" and state["updates"] == 1:
                raise TimeoutError("read timeout")
            return copy.deepcopy(state["definition"])

        def api(endpoint, method="get", body=None, audience="powerbi"):
            state["calls"].append((endpoint, method))
            if endpoint.endswith("updateDefinition"):
                state["updates"] += 1
                if rollback_fault and state["updates"] > 1:
                    return {"status_code": 503, "text": {}}
                state["definition"] = copy.deepcopy(body)
                if state["updates"] == 1:
                    if fault == "wrong_definition":
                        state["definition"] = definition("corrupted")
                    if fault == "wrong_binding":
                        state["binding"] = "wrong"
                    if fault == "update_timeout":
                        raise TimeoutError("response lost after commit")
                    if fault == "429":
                        return {"status_code": 429, "text": {}}
                return {"status_code": 200, "text": {}}
            if endpoint.endswith("/Rebind"):
                state["binding"] = body["datasetId"]
                return {"status_code": 200, "text": {}}
            return {"status_code": 200, "text": {"datasetId": state["binding"]}}

        with (
            tempfile.TemporaryDirectory() as temp,
            patch.object(release, "definition", side_effect=get_definition),
            patch.object(release, "api", side_effect=api),
        ):
            if fault:
                with self.assertRaisesRegex(
                    RuntimeError, "unverified" if rollback_fault else "restored and verified"
                ):
                    release.release("workspace", "report", source, "model", Path(temp))
            else:
                self.assertEqual(
                    release.release("workspace", "report", source, "model", Path(temp))["status"],
                    "passed",
                )
            result = json.loads((Path(temp) / "evidence/report-release-control.json").read_text())
        self.assertFalse(
            any(url.endswith("/items") or url == "datasets" for url, _ in state["calls"])
        )
        return state, result, before

    def test_success_updates_existing_report_only(self):
        state, result, _ = self.run_case()
        self.assertEqual(state["updates"], 1)
        self.assertFalse(result["rollback_attempted"])

    def test_failed_verification_restores_definition_and_binding(self):
        for fault in [
            "wrong_definition",
            "wrong_binding",
            "update_timeout",
            "verification_timeout",
            "429",
        ]:
            with self.subTest(fault=fault):
                state, result, before = self.run_case(fault)
                self.assertTrue(result["rollback_verified"])
                self.assertEqual(state["definition"], before)
                self.assertEqual(state["binding"], "model")
                self.assertEqual(result["status"], "failed")

    def test_rollback_failure_cannot_claim_success(self):
        _, result, _ = self.run_case("wrong_definition", True)
        self.assertFalse(result["rollback_verified"])
        self.assertEqual(result["status"], "failed")

    def test_expired_authentication_prevents_any_mutation(self):
        with (
            tempfile.TemporaryDirectory() as temp,
            patch.object(release, "definition", side_effect=RuntimeError("Authentication expired")),
            patch.object(release, "api") as api,
        ):
            with self.assertRaisesRegex(RuntimeError, "Authentication expired"):
                release.release("workspace", "report", definition("new"), "model", Path(temp))
            api.assert_not_called()
