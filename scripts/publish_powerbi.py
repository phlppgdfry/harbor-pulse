"""Publish a validated immutable model snapshot through an authenticated Fabric CLI.

Account-specific receipts live under ignored build/. No passwords or tokens are
handled by this script. Existing snapshots are never cleared to apply corrections.
"""

import argparse
import json
import pathlib
import subprocess
import tempfile

ROOT = pathlib.Path(__file__).resolve().parents[1]


def call(url, method="get", body=None, audience="fabric", receipt=None):
    if url.startswith("https://api.powerbi.com/v1.0/myorg/"):
        url = url.split("/v1.0/myorg/", 1)[1]
    cmd = ["fab", "api", url, "-X", method, "-A", audience, "--output_format", "json"]
    request = None
    if body is not None:
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".private.json", dir=ROOT / "build", delete=False
        ) as file:
            json.dump(body, file, ensure_ascii=False)
            request = pathlib.Path(file.name)
        cmd += ["-i", str(request)]
    try:
        response = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    finally:
        if request:
            request.unlink(missing_ok=True)
    if response.returncode:
        raise RuntimeError(response.stderr + response.stdout)
    result = json.loads(response.stdout)
    if receipt:
        receipt.write_text(json.dumps(result, indent=2))
    if result.get("status") != "Success":
        raise RuntimeError(str(result))
    data = result["result"]["data"][0]
    if data["status_code"] not in (200, 201, 202):
        raise RuntimeError(str(data))
    return data


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--run", type=pathlib.Path, default=ROOT / "build/run")
    args = p.parse_args()
    receipt = ROOT / "build/publication.private.json"
    if receipt.exists():
        raise SystemExit(
            "A model publication receipt already exists. Refusing duplicate snapshot creation."
        )
    gate = json.loads((args.run / "gate.json").read_text())
    assert all(gate["checks"].values()), gate
    model = json.loads((args.run / "model.json").read_text())
    tables = json.loads((args.run / "tables.json").read_text())
    d = call("https://api.powerbi.com/v1.0/myorg/datasets", "post", model, "powerbi")
    created = d["text"]
    assert created.get("id"), d
    receipt.write_text(json.dumps(created, indent=2))
    model_id = created["id"]
    for name, rows in tables.items():
        call(
            f"https://api.powerbi.com/v1.0/myorg/datasets/{model_id}/tables/{name}/rows",
            "post",
            {"rows": rows},
            "powerbi",
            ROOT / "build" / f"published-{name}.private.json",
        )
        print(f"Published {name}: {len(rows)} rows", flush=True)
    print("Published model snapshot:", model_id)


if __name__ == "__main__":
    main()
