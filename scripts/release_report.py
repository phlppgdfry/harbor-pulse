"""Update one existing report; restore and verify its complete backup on failure."""

import argparse
import base64
import datetime as dt
import hashlib
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.cloud_operations import api, completion, definition, successful


def canonical_parts(value):
    result = {}
    for part in value["definition"]["parts"]:
        raw = base64.b64decode(part["payload"], validate=True)
        try:
            raw = json.dumps(json.loads(raw), sort_keys=True, separators=(",", ":")).encode()
        except (ValueError, UnicodeDecodeError):
            pass
        result[part["path"]] = hashlib.sha256(raw).hexdigest()
    if not result:
        raise ValueError("Empty report definition")
    return result


def release(
    workspace, report, source, expected_model, root=ROOT, receipt_name="report-release-control.json"
):
    root = pathlib.Path(root)
    folder = root / "build/releases" / dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%S%f")
    folder.mkdir(parents=True)
    intended = canonical_parts(source)
    before = definition(workspace, report)
    original_binding = successful(api("reports/" + report))["datasetId"]
    if original_binding != expected_model:
        raise RuntimeError("Existing binding differs from expected model; no update attempted")
    (folder / "before.private.json").write_text(json.dumps(before))
    original = canonical_parts(before)
    receipt = dict(
        status="started",
        backup_captured=True,
        model_created=False,
        rollback_attempted=False,
        rollback_verified=False,
    )
    try:
        completion(
            api(f"workspaces/{workspace}/items/{report}/updateDefinition", "post", source, "fabric")
        )
        after = definition(workspace, report)
        received = canonical_parts(after)
        if any(received.get(key) != value for key, value in intended.items()):
            raise RuntimeError("Published report definition differs from intended release")
        if successful(api("reports/" + report))["datasetId"] != expected_model:
            raise RuntimeError("Post-publication model binding mismatch")
        receipt.update(
            status="passed", matched_definition_parts=len(intended), model_binding_preserved=True
        )
        return receipt
    except Exception as failure:
        receipt.update(status="failed", error_type=type(failure).__name__, rollback_attempted=True)
        try:
            completion(
                api(
                    f"workspaces/{workspace}/items/{report}/updateDefinition",
                    "post",
                    before,
                    "fabric",
                )
            )
            if successful(api("reports/" + report))["datasetId"] != original_binding:
                successful(
                    api("reports/" + report + "/Rebind", "post", {"datasetId": original_binding})
                )
            restored = definition(workspace, report)
            if canonical_parts(restored) != original:
                raise RuntimeError("Restored definition does not match complete backup")
            if successful(api("reports/" + report))["datasetId"] != original_binding:
                raise RuntimeError("Restored model binding does not match backup")
            receipt["rollback_verified"] = True
        except Exception as rollback_failure:
            receipt["rollback_error_type"] = type(rollback_failure).__name__
            raise RuntimeError(
                "Release failed and rollback remains unverified; inspect private receipt"
            ) from rollback_failure
        raise RuntimeError(
            "Release failed; previous report definition and binding restored and verified"
        ) from failure
    finally:
        receipt["finished_at"] = dt.datetime.now(dt.timezone.utc).isoformat()
        (folder / "release.private.json").write_text(json.dumps(receipt, indent=2))
        public = root / "evidence" / receipt_name
        public.parent.mkdir(exist_ok=True)
        public.write_text(json.dumps(receipt, indent=2))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace", required=True)
    parser.add_argument("--report", required=True)
    parser.add_argument("--source", type=pathlib.Path, default=ROOT / "build/update.json")
    parser.add_argument("--expected-model")
    args = parser.parse_args()
    expected = (
        args.expected_model
        or json.loads((ROOT / "build/publication.private.json").read_text())["id"]
    )
    print(
        json.dumps(
            release(args.workspace, args.report, json.loads(args.source.read_text()), expected),
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
