"""Fail closed on inconsistent claims or unregistered public artifact changes."""

import argparse
import base64
import hashlib
import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from pypdf import PdfReader


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify(root=ROOT, run=None):
    root = pathlib.Path(root)
    run = pathlib.Path(run or root / "build/run")
    claim = json.loads((root / "contracts/case-release.json").read_text())
    metrics = claim["metrics"]
    summary = json.loads((run / "summary.json").read_text())
    loads = json.loads((run / "loads.json").read_text())
    for key in ["vehicles", "fact_rows", "late_corrections", "source_fact_difference"]:
        if summary[key] != metrics[key]:
            raise ValueError("Generated summary drift: " + key)
    if loads[0]["duplicates"] != metrics["duplicates"]:
        raise ValueError("Duplicate claim drift")
    native = json.loads((root / "powerbi/native/model.bim").read_text())["model"]
    if len(native["tables"]) != metrics["model_tables"]:
        raise ValueError("Model table claim drift")
    if sum(len(t.get("measures", [])) for t in native["tables"]) != metrics["measures"]:
        raise ValueError("Measure claim drift")
    fact_table = next(t for t in native["tables"] if t["name"] == "FactOps")
    expression = fact_table["partitions"][0]["source"]["expression"]
    if isinstance(expression, list):
        expression = "\n".join(expression)
    payload = re.search(r'Binary\.FromText\("([A-Za-z0-9+/=]+)"', expression)
    if not payload:
        raise ValueError("Native embedded snapshot is not inspectable")
    embedded = json.loads(base64.b64decode(payload[1]))
    if (
        len(embedded) != metrics["fact_rows"]
        or sum(r["Vehicles"] for r in embedded) != metrics["vehicles"]
    ):
        raise ValueError("Native snapshot totals drift")
    viewer = json.loads((root / "evidence/rls-enforcement-capability.json").read_text())
    if claim["rls_viewer_status"] == "license-blocked" and (
        viewer["viewer_render_passed"]
        or "PowerBINotLicensedException" not in viewer["viewer_errors"]
    ):
        raise ValueError("RLS viewer status drift")
    pages = list((root / "powerbi/report/definition/pages").glob("*/page.json"))
    visuals = list((root / "powerbi/report/definition/pages").glob("*/visuals/*/visual.json"))
    if len(pages) != metrics["report_pages"] or len(visuals) != metrics["report_elements"]:
        raise ValueError("Report source claim drift")
    render = json.loads((root / "evidence/powerbi-render.json").read_text())
    if (
        len(render["pages"]) != metrics["report_pages"]
        or sum(p["visuals"] for p in render["pages"]) != metrics["report_elements"]
    ):
        raise ValueError("Screenshot inventory drift")
    for path, pattern in [
        ("README.md", r"<!-- case-claim: (.*?) -->"),
        ("docs/index.html", r'<script type="application/json" id="case-claim">(.*?)</script>'),
    ]:
        text = (root / path).read_text()
        match = re.search(pattern, text, re.S)
        if not match or json.loads(match[1]) != claim:
            raise ValueError("Embedded claim drift: " + path)
        if "366,910" not in text:
            raise ValueError("Visible vehicle total drift: " + path)
    html = (root / "docs/index.html").read_text()
    values = re.findall(r'<div class="metric"><strong>([0-9,]+)</strong>', html)
    if [int(v.replace(",", "")) for v in values] != [
        metrics["vehicles"],
        metrics["duplicates"],
        metrics["late_corrections"],
        metrics["source_fact_difference"],
    ]:
        raise ValueError("Visible website KPI drift")
    readme = (root / "README.md").read_text()
    required_readme = [
        f"{metrics['late_corrections']} audited upserts",
        f"{metrics['duplicates']} skipped without double counting",
        f"{metrics['fact_rows']:,} terminal-days; {metrics['vehicles']:,} vehicles",
    ]
    if not all(text in readme for text in required_readme):
        raise ValueError("Visible README KPI drift")
    public_summary = json.loads((root / "evidence/summary.json").read_text())
    if any(
        public_summary[key] != metrics[key]
        for key in ["vehicles", "fact_rows", "late_corrections", "source_fact_difference"]
    ):
        raise ValueError("Public JSON summary drift")
    for path in ["README.md", "docs/index.html"]:
        if "pilot dispatch" not in (root / path).read_text().lower():
            raise ValueError("Recommendation drift: " + path)
    pdf = PdfReader(root / "output/pdf/harbor-pulse-recruiter-brief.pdf")
    if len(pdf.pages) != 1:
        raise ValueError("Recruiter PDF must remain one page")
    if json.loads(pdf.metadata.subject) != claim:
        raise ValueError("PDF claim metadata drift")
    pdftext = pdf.pages[0].extract_text()
    if (
        "366,910" not in pdftext
        or claim["case_version"] not in pdftext
        or "RLS viewer tests remain license-blocked" not in pdftext
    ):
        raise ValueError("Visible PDF claim drift")
    for key, label in [
        ("model_tables", "model tables"),
        ("measures", "measures"),
        ("report_pages", "pages"),
        ("report_elements", "report elements"),
    ]:
        if f"{metrics[key]} {label}" not in pdftext:
            raise ValueError("Visible PDF inventory drift: " + key)
    manifest = json.loads((root / "evidence/artifact-manifest.json").read_text())
    registered = {entry["path"]: entry["sha256"] for entry in manifest["artifacts"]}
    if len(registered) != len(manifest["artifacts"]):
        raise ValueError("Duplicate artifact paths")
    if manifest["claim"] != claim:
        raise ValueError("Artifact manifest version drift")
    required = {
        "README.md",
        "docs/index.html",
        "output/pdf/harbor-pulse-recruiter-brief.pdf",
        "powerbi/native/model.bim",
        "contracts/case-release.json",
    }
    required.update(p["image"] for p in render["pages"])
    required.update(str(p.relative_to(root)) for p in (root / "powerbi/report").rglob("*.json"))
    required.update(
        [
            "powerbi/report/definition.pbir",
            "evidence/challenge.json",
            "docs/assets/sensitivity.json",
        ]
    )
    if not required <= set(registered):
        raise ValueError("Required artifact missing from manifest")
    for name, expected in registered.items():
        if digest(root / name) != expected:
            raise ValueError("Unreviewed artifact drift: " + name)
    source = json.loads((root / "evidence/sensitivity.json").read_text())
    if source != json.loads((root / "docs/assets/sensitivity.json").read_text()):
        raise ValueError("Website sensitivity differs from analytical evidence")
    if any(r["vehicles"] != metrics["vehicles"] for r in source["grid"]):
        raise ValueError("Sensitivity denominator drift")
    return {
        "status": "passed",
        "case_version": claim["case_version"],
        "registered_artifacts": len(registered),
        "limits": "Hash provenance and structured/selected visible claims; not OCR of every screenshot label or proof of economic validity.",
    }


def register(root=ROOT):
    root = pathlib.Path(root)
    claim = json.loads((root / "contracts/case-release.json").read_text())
    files = [root / "README.md", root / "docs/index.html", root / "contracts/case-release.json"]
    files += [
        p
        for folder in [
            "evidence",
            "docs",
            "contracts",
            "fixtures",
            "powerbi/report",
            "powerbi/native",
            "output/pdf",
        ]
        for p in (root / folder).rglob("*")
        if p.is_file() and p.name not in ["artifact-manifest.json", "case-consistency.json"]
    ]
    result = {
        "claim": claim,
        "provenance": "Reviewed release inventory; changing hashes requires explicit re-registration and review. SDK receipts establish renderer origin; hashes establish identity, not image contents.",
        "artifacts": [
            dict(path=str(p.relative_to(root)), sha256=digest(p)) for p in sorted(set(files))
        ],
    }
    (root / "evidence/artifact-manifest.json").write_text(json.dumps(result, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--run", type=pathlib.Path, default=ROOT / "build/run")
    parser.add_argument(
        "--register",
        action="store_true",
        help="Explicit reviewed-release operation; never run automatically in CI",
    )
    args = parser.parse_args()
    if args.register:
        register()
    result = verify(run=args.run)
    (ROOT / "build").mkdir(exist_ok=True)
    (ROOT / "build/case-consistency.json").write_text(json.dumps(result, indent=2))
    print(json.dumps(result, indent=2))
