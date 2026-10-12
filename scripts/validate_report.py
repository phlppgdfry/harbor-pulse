import json
import os
import pathlib
import re
import warnings

import jsonschema

ROOT = pathlib.Path(__file__).resolve().parents[1]
SOURCE = ROOT / "build/report"
RUN = pathlib.Path(os.environ.get("HARBOR_RUN", str(ROOT / "build/run")))
store = {
    "https://developer.microsoft.com/json-schemas/"
    + str(p.relative_to(ROOT / "schemas")): json.loads(p.read_text())
    for p in (ROOT / "schemas").rglob("*.json")
}
model = json.loads((RUN / "model.json").read_text())
rows = json.loads((RUN / "tables.json").read_text())
connection = json.loads((SOURCE / "definition.pbir").read_text())
connection_schema = json.loads((ROOT / "schemas/definition-properties.json").read_text())
jsonschema.Draft7Validator(connection_schema).validate(connection)
columns = {t["name"]: {c["name"] for c in t["columns"]} for t in model["tables"]}
measures = {m["name"] for t in model["tables"] for m in t.get("measures", [])}
for t in model["tables"]:
    for metric in t.get("measures", []):
        expr = metric["expression"]
        for table, col in re.findall(r"(\w+)\[([^]]+)\]", expr):
            assert col in columns[table], (table, col)
        remaining = re.sub(r"\w+\[[^]]+\]", "", expr)
        for name in re.findall(r"\[([^]]+)\]", remaining):
            assert name in measures, name
    for row in rows[t["name"]]:
        assert set(row) == columns[t["name"]]
for rel in model["relationships"]:
    keys = [r[rel["toColumn"]] for r in rows[rel["toTable"]]]
    assert len(keys) == len(set(keys))
    assert {r[rel["fromColumn"]] for r in rows[rel["fromTable"]]} <= set(keys)
assert len(rows["FactOps"]) == 1095
assert len({(r["DateKey"], r["TerminalKey"]) for r in rows["FactOps"]}) == 1095
assert all(
    0 <= r["OnTimeVehicles"] <= r["Vehicles"]
    and r["OccupiedSlots"] <= r["AvailableSlots"]
    and r["DelayMinutes"] >= 0
    for r in rows["FactOps"]
)
assert sum(r["IncidentFlag"] for r in rows["FactOps"]) == 14
counter = 0
for pagefile in (SOURCE / "definition/pages").glob("*/page.json"):
    page = json.loads(pagefile.read_text())
    boxes = []
    for file in [pagefile, *pagefile.parent.glob("visuals/*/visual.json")]:
        obj = json.loads(file.read_text())
        schema = store[obj["$schema"]]
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            resolver = jsonschema.RefResolver(base_uri=obj["$schema"], referrer=schema, store=store)
            jsonschema.Draft7Validator(schema, resolver=resolver).validate(obj)
        if file == pagefile:
            continue
        p = obj["position"]
        assert (
            p["x"] >= 0
            and p["y"] >= 0
            and p["x"] + p["width"] <= page["width"]
            and p["y"] + p["height"] <= page["height"]
        )
        for b in boxes:
            overlap = min(p["x"] + p["width"], b["x"] + b["width"]) > max(p["x"], b["x"]) and min(
                p["y"] + p["height"], b["y"] + b["height"]
            ) > max(p["y"], b["y"])
            assert not overlap, (page["displayName"], "overlap")
        boxes.append(p)

        def fields(value):
            if isinstance(value, dict):
                for key in ["Column", "Measure"]:
                    if key in value:
                        f = value[key]
                        table = f["Expression"]["SourceRef"].get("Entity")
                        if table:
                            assert f["Property"] in (
                                measures if key == "Measure" else columns[table]
                            ), f
                for v in value.values():
                    fields(v)
            elif isinstance(value, list):
                for v in value:
                    fields(v)

        fields(obj)
        counter += 1
    print(page["displayName"], len(boxes), "elements")
print(
    f"PASS: {counter} visuals, {len(measures)} measures, relationships, scenario types, data integrity and non-overlapping layout"
)
