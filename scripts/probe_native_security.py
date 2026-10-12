"""Isolated native semantic-model capability probe; never alters live model."""

import argparse
import base64
import datetime as dt
import json

from cloud_operations import ROOT, api, completion

model = {
    "name": "HarborPulseSecurityProbe",
    "compatibilityLevel": 1601,
    "model": {
        "culture": "en-US",
        "defaultPowerBIDataSourceVersion": "powerBI_V3",
        "defaultMode": "import",
        "tables": [
            {
                "name": "FactOps",
                "columns": [
                    {
                        "name": n,
                        "dataType": "int64",
                        "sourceColumn": "[" + n + "]",
                        "type": "calculatedTableColumn",
                    }
                    for n in ["TerminalKey", "Vehicles"]
                ],
                "measures": [{"name": "VehicleTotal", "expression": "SUM(FactOps[Vehicles])"}],
                "partitions": [
                    {
                        "name": "FactOps",
                        "mode": "import",
                        "source": {
                            "type": "calculated",
                            "expression": 'DATATABLE("TerminalKey", INTEGER, "Vehicles", INTEGER, {{1,100},{2,200},{3,300}})',
                        },
                    }
                ],
            }
        ],
        "roles": [
            {
                "name": "Zeebrugge",
                "modelPermission": "read",
                "tablePermissions": [{"name": "FactOps", "filterExpression": "[TerminalKey] = 1"}],
            }
        ],
    },
}
(ROOT / "powerbi/security").mkdir(exist_ok=True)
(ROOT / "powerbi/security/probe-model.bim").write_text(json.dumps(model, indent=2))
parts = [
    {
        "path": n,
        "payloadType": "InlineBase64",
        "payload": base64.b64encode(json.dumps(v).encode()).decode(),
    }
    for n, v in [("model.bim", model), ("definition.pbism", {"version": "1.0", "settings": {}})]
]
request = {
    "displayName": "Harbor Pulse - isolated native security probe",
    "definition": {"parts": parts},
}
parser = argparse.ArgumentParser()
parser.add_argument("--workspace", required=True)
workspace = parser.parse_args().workspace
d = api(f"workspaces/{workspace}/semanticModels", "post", request, "fabric")
(ROOT / "build/native-security-create.private.json").write_text(json.dumps(d))
result = {
    "checked_at": dt.datetime.now(dt.timezone.utc).isoformat(),
    "http_status": d["status_code"],
    "production_model_modified": False,
    "test_users_created": False,
}
if d["status_code"] >= 400:
    result["error"] = d.get("text")
    print(json.dumps(result))
    (ROOT / "evidence/native-security-capability.json").write_text(json.dumps(result, indent=2))
else:
    try:
        item = completion(d)
        (ROOT / "build/native-security-item.private.json").write_text(json.dumps(item))
        result["model_created"] = True
        (ROOT / "evidence/native-security-capability.json").write_text(json.dumps(result, indent=2))
        print("Native security probe created; private identity recorded")
    except Exception as e:
        result["error"] = str(e)
        print(json.dumps(result))
        (ROOT / "evidence/native-security-capability.json").write_text(json.dumps(result, indent=2))
