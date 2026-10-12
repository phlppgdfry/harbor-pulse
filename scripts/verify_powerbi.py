"""Execute every distinct PBIR query and reconcile the published snapshot."""

import argparse
import concurrent.futures
import json
import pathlib

from publish_powerbi import ROOT, call


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--run", type=pathlib.Path, default=ROOT / "build/run")
    p.add_argument("--model")
    args = p.parse_args()
    model = json.loads((ROOT / "build/publication.private.json").read_text())
    model_id = args.model or model["id"]
    output = ROOT / "build/query-verification"
    output.mkdir(exist_ok=True)

    def query(dax, key):
        data = call(
            f"datasets/{model_id}/executeQueries",
            "post",
            {"queries": [{"query": dax}], "serializerSettings": {"includeNulls": True}},
            "powerbi",
            output / (key + ".private.json"),
        )
        j = data["text"]
        if j.get("error") or any(r.get("error") for r in j.get("results", [])):
            raise RuntimeError(str(j))
        return j["results"][0]["tables"][0]["rows"]

    jobs = {}
    for f in (ROOT / "build/report/definition/pages").glob("*/visuals/*/visual.json"):
        v = json.loads(f.read_text())
        state = v["visual"].get("query", {}).get("queryState")
        if not state:
            continue
        cols = set()
        measures = set()
        for role in state.values():
            for projection in role["projections"]:
                field = projection["field"]
                if "Column" in field:
                    ref = field["Column"]
                    cols.add(ref["Expression"]["SourceRef"]["Entity"] + "[" + ref["Property"] + "]")
                if "Measure" in field:
                    measures.add(field["Measure"]["Property"])
        values = [item for m in sorted(measures) for item in ['"' + m + '"', "[" + m + "]"]]
        expression = (
            "SUMMARIZECOLUMNS(" + ",".join([*sorted(cols), *values]) + ")"
            if cols
            else "ROW(" + ",".join(values) + ")"
        )
        if any(
            f.get("name") == "IncidentOnly" for f in v.get("filterConfig", {}).get("filters", [])
        ):
            expression = "CALCULATETABLE(" + expression + ",FactOps[IncidentFlag]=TRUE())"
        jobs["EVALUATE " + expression] = v["name"]
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
        futures = [pool.submit(query, dax, key) for dax, key in jobs.items()]
        for future in futures:
            future.result()
    totals = query(
        'EVALUATE ROW("Vehicles",[Voertuigen],"Revenue",[Omzet],"Coverage",[Vertrekdekking %],"Difference",[Bron fact verschil],"Dwell",[Verblijftijd uur],"Pilot",[Pilot effect min])',
        "totals",
    )[0]
    tables = json.loads((args.run / "tables.json").read_text())
    facts = tables["FactOps"]
    units = sum(f["Vehicles"] for f in facts)

    def near(actual, expected):
        assert abs(actual - expected) <= 1e-7 * max(1, abs(expected)), (actual, expected)

    near(totals["[Vehicles]"], units)
    near(totals["[Revenue]"], sum(f["Revenue"] for f in facts))
    complete = sum(f["CompleteDepartureUnits"] for f in facts)
    near(totals["[Coverage]"], complete / units)
    near(totals["[Difference]"], 0)
    near(
        totals["[Dwell]"],
        sum(f["DwellHours"] * f["CompleteDepartureUnits"] for f in facts) / complete,
    )
    pilot = json.loads((args.run / "pilot.json").read_text())
    near(totals["[Pilot]"], pilot["observed_did_minutes"])
    scenario = query(
        'EVALUATE CALCULATETABLE(ROW("Value",[Indicatieve besparing]),ScenarioDelay[Minutes]=10,ScenarioCost[EUR]=45,ScenarioRealization[Fraction]=0.10)',
        "scenario",
    )[0]
    near(
        scenario["[Value]"],
        sum(f["Vehicles"] * min(f["DelayMinutes"], 10) / 60 for f in facts) * 45 * 0.10,
    )
    filtered = query(
        'EVALUATE CALCULATETABLE(ROW("Vehicles",[Voertuigen]),DimTerminal[Terminal]="Antwerpen",DimDate[Maand]="2026-04")',
        "relationships",
    )[0]
    near(
        filtered["[Vehicles]"],
        sum(
            f["Vehicles"]
            for f in facts
            if f["TerminalKey"] == 2 and 20260401 <= f["DateKey"] <= 20260430
        ),
    )
    summary = dict(
        status="passed",
        distinct_report_queries=len(jobs),
        vehicles=units,
        revenue=totals["[Revenue]"],
        departure_coverage=totals["[Coverage]"],
        source_fact_difference=0,
        scenario_uses_realizable_fraction=True,
        browser_used=False,
    )
    (ROOT / "build/powerbi-verification.json").write_text(json.dumps(summary, indent=2))
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
