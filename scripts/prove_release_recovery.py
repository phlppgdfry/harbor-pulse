"""Live isolated report-copy drill with an injected read-back verification failure."""

import argparse
import base64
import copy
import datetime as dt
import json
import pathlib
import sys
from unittest.mock import patch

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts import release_report
from scripts.cloud_operations import api, completion, definition, successful


def prove(workspace, report):
    original = definition(workspace, report)
    model = successful(api("reports/" + report))["datasetId"]
    created = completion(
        api(
            f"workspaces/{workspace}/items",
            "post",
            {
                "displayName": "Harbor Pulse - automatic rollback proof",
                "type": "Report",
                "definition": original["definition"],
            },
            "fabric",
        )
    )
    clone = created["id"]
    result = {
        "checked_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "scope": "Live isolated report copy; deliberately injected verification fault after actual update",
        "model_created": False,
        "production_modified": False,
        "automatic_restore_verified": False,
        "clone_deleted": False,
        "status": "failed",
    }
    try:
        backup = definition(workspace, clone)
        changed = copy.deepcopy(backup)
        part = next(p for p in changed["definition"]["parts"] if p["path"].endswith("/page.json"))
        page = json.loads(base64.b64decode(part["payload"]))
        page["displayName"] = "TEMPORARY ROLLBACK PROOF"
        part["payload"] = base64.b64encode(json.dumps(page).encode()).decode()
        calls = 0

        def injected_readback(workspace, item):
            nonlocal calls
            value = definition(workspace, item)
            calls += 1
            if calls == 2:
                raise RuntimeError("Injected verifier failure after real cloud update")
            return value

        with patch.object(release_report, "definition", side_effect=injected_readback):
            try:
                release_report.release(
                    workspace, clone, changed, model, receipt_name="automatic-rollback-release.json"
                )
            except RuntimeError as error:
                if "restored and verified" not in str(error):
                    raise
            else:
                raise RuntimeError("Injected verification fault did not fail the release")
        restored = definition(workspace, clone)
        result["automatic_restore_verified"] = release_report.canonical_parts(
            restored
        ) == release_report.canonical_parts(backup)
        result["production_unchanged"] = release_report.canonical_parts(
            definition(workspace, report)
        ) == release_report.canonical_parts(original)
        result["binding_restored"] = successful(api("reports/" + clone))["datasetId"] == model
    finally:
        result["clone_deleted"] = api("reports/" + clone, "delete")["status_code"] in (200, 204)
        result["status"] = (
            "passed"
            if all(
                result.get(k, False)
                for k in [
                    "automatic_restore_verified",
                    "production_unchanged",
                    "binding_restored",
                    "clone_deleted",
                ]
            )
            else "failed"
        )
        (ROOT / "evidence/automatic-rollback-drill.json").write_text(json.dumps(result, indent=2))
    if result["status"] != "passed":
        raise RuntimeError("Automatic recovery drill did not pass every check")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--workspace", required=True)
    parser.add_argument("--report", required=True)
    args = parser.parse_args()
    prove(args.workspace, args.report)
