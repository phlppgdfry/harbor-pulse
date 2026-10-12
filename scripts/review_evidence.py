"""Generate review artifacts from an existing reproducible run."""

import argparse
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from harbor_pulse.review import diagnostics, pilot_planning, sensitivity

p = argparse.ArgumentParser()
p.add_argument("--run", type=pathlib.Path, default=ROOT / "build/run")
args = p.parse_args()
facts = json.loads((args.run / "tables.json").read_text())["FactOps"]
for name, data in [
    ("diagnostics", diagnostics(facts)),
    ("sensitivity", sensitivity(facts)),
    ("pilot-planning", pilot_planning()),
]:
    (ROOT / "evidence" / f"{name}.json").write_text(json.dumps(data, indent=2))
    print("Generated", name)
