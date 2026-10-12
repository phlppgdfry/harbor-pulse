"""Generate the adversarial evidence using a reproducible local run."""

import argparse
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from harbor_pulse.challenge import challenge

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--run", type=pathlib.Path, default=ROOT / "build/run")
    args = parser.parse_args()
    result = challenge(json.loads((args.run / "tables.json").read_text())["FactOps"])
    (ROOT / "evidence/challenge.json").write_text(json.dumps(result, indent=2))
    print("Generated six assumption challenges")
