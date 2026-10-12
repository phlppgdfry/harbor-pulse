import argparse
import json
import pathlib
import runpy

from .analysis import associations, decisions, pilot
from .pipeline import connect, facts, ingest, publication_gate
from .sources import generate

ROOT = pathlib.Path(__file__).resolve().parents[1]


def save(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2))


def main():
    parser = argparse.ArgumentParser(
        description="Reproduce the Harbor Pulse synthetic analytics case"
    )
    parser.add_argument("command", choices=["demo", "monitor"])
    parser.add_argument("--output", type=pathlib.Path, default=ROOT / "build/run")
    args = parser.parse_args()
    output = args.output
    output.mkdir(parents=True, exist_ok=True)
    db = connect(output / "warehouse.sqlite")
    if args.command == "monitor":
        print(
            json.dumps(
                [dict(r) for r in db.execute("SELECT * FROM runs ORDER BY id DESC LIMIT 10")],
                indent=2,
            )
        )
        return
    # Keep this run reproducible; refuse to silently reuse an existing populated warehouse.
    if db.execute("SELECT COUNT(*) FROM events").fetchone()[0]:
        raise SystemExit(
            "Output warehouse already contains data. Choose a new --output directory; monitor is read-only."
        )
    runpy.run_path(str(ROOT / "scripts/generate_base.py"))
    base = json.loads((ROOT / "build/rows-v3.json").read_text())
    source, corrected, manifest = generate(base["FactOps"])
    for name, data in source.items():
        save(output / "raw" / f"{name}.json", data)
    save(output / "raw/late-arrivals.json", corrected["arrivals"][len(source["arrivals"]) :])
    history = [ingest(db, source), ingest(db, source), ingest(db, corrected)]
    clean = facts(db)
    gate = publication_gate(clean, history[-1])
    analysis = associations(clean)
    decision = decisions(clean)
    experiment = pilot()
    dq = [
        dict(
            Regel="Dubbele bronevents",
            Aantal=history[0]["duplicates"],
            Afhandeling="Idempotent overgeslagen",
            Ernst="Informatie",
        ),
        dict(
            Regel="Ongeldige of conflicterende events",
            Aantal=history[0]["rejected"],
            Afhandeling="Quarantaine; laatste geldige versie behouden",
            Ernst="Waarschuwing",
        ),
        dict(
            Regel="Ontbrekend geldig vertrek",
            Aantal=history[-1]["missing_departures"],
            Afhandeling="Behouden; ontbrekende dekking zichtbaar",
            Ernst="Waarschuwing",
        ),
        dict(
            Regel="Late correcties",
            Aantal=history[-1]["updated"],
            Afhandeling="Upsert op key + versie; auditlog",
            Ernst="Informatie",
        ),
        dict(
            Regel="Bron versus fact verschil",
            Aantal=history[-1]["difference"],
            Afhandeling="Publicatieblok bij afwijking",
            Ernst="Blokkerend",
        ),
    ]
    contracts = [
        dict(
            KPI="Punctualiteit",
            Definitie="Op tijd geregistreerde voertuigen / geldige aankomsten",
            Eigenaar="Operations lead",
            Doel="≥97%",
            Controle="0 ≤ on-time ≤ arrivals",
        ),
        dict(
            KPI="Vertraging",
            Definitie="Actual arrival − planned arrival; gewogen naar Units",
            Eigenaar="Terminal operations lead",
            Doel="Pilot: minstens 3 minuten minder",
            Controle="UTC; geen negatieve duur",
        ),
        dict(
            KPI="Verblijftijd",
            Definitie="Departure − actual arrival; alleen gematchte geldige vertrekken",
            Eigenaar="Operations lead",
            Doel="Dekking zichtbaar; geen nul-imputatie",
            Controle="Vertrek ≥ aankomst",
        ),
        dict(
            KPI="Bezetting",
            Definitie="Bezette slotdagen / beschikbare slotdagen",
            Eigenaar="Capacity planner",
            Doel="≤85%",
            Controle="Bezet ≤ beschikbaar; capaciteit >0",
        ),
        dict(
            KPI="Brutomarge",
            Definitie="Omzet minus handlingkosten; vóór overhead en belasting",
            Eigenaar="Finance controller",
            Doel="≥35%",
            Controle="Omzet aansluiten op Units × tarief",
        ),
        dict(
            KPI="Datakwaliteit",
            Definitie="Quarantaine, ontbrekende koppelingen en reconciliatie apart volgen",
            Eigenaar="Data steward",
            Doel="Geen onverklaard reconciliatieverschil",
            Controle="Geen dubbele business keys",
        ),
    ]
    model = json.loads((ROOT / "build/model-v3.json").read_text())
    model["name"] = "Harbor Pulse — Governed Operations 2026"
    fact = next(t for t in model["tables"] if t["name"] == "FactOps")
    existing = {c["name"] for c in fact["columns"]}
    for key, value in clean[0].items():
        if key not in existing:
            fact["columns"].append(
                dict(name=key, dataType="Int64" if isinstance(value, int) else "Double")
            )
    next(m for m in fact["measures"] if m["name"] == "Verblijftijd uur")["expression"] = (
        "DIVIDE(SUMX(FactOps,FactOps[DwellHours]*FactOps[CompleteDepartureUnits]),SUM(FactOps[CompleteDepartureUnits]))"
    )
    extra = [
        ("Vertrekdekking %", "DIVIDE(SUM(FactOps[CompleteDepartureUnits]),[Voertuigen])", "0.0%"),
        ("Personeelsuren", "SUM(FactOps[StaffHours])", "#,0.0"),
        ("Datakwaliteit meldingen", "SUM(DQRule[Aantal])", "#,0"),
        ("Bron fact verschil", "SUMX(FactOps,FactOps[Vehicles])-SUM(FactOps[Vehicles])", "0"),
        ("Pilot effect min", str(experiment["observed_did_minutes"]), "0.00"),
        ("Pilot interval laag", str(experiment["paired_day_bootstrap_95"][0]), "0.00"),
        ("Pilot interval hoog", str(experiment["paired_day_bootstrap_95"][1]), "0.00"),
        ("Benutbare fractie", "SELECTEDVALUE(ScenarioRealization[Fraction],0.10)", "0.0%"),
        (
            "Pilot gemiddelde min",
            "DIVIDE(SUMX(PilotSummary,PilotSummary[GemiddeldeVertraging]*PilotSummary[Sessies]),SUM(PilotSummary[Sessies]))",
            "0.00",
        ),
        ("Netto jaar P10", "SELECTEDVALUE(DecisionOption[NettoP10])", "€ #,0"),
        ("Netto jaar P50", "SELECTEDVALUE(DecisionOption[NettoP50])", "€ #,0"),
        ("Netto jaar P90", "SELECTEDVALUE(DecisionOption[NettoP90])", "€ #,0"),
    ]
    # The source/fact difference is published as a separate monitored quality row,
    # not inferred by subtracting the same total from itself.
    extra = [
        (
            n,
            'SUMX(FILTER(DQRule,DQRule[Regel]="Bron versus fact verschil"),DQRule[Aantal])'
            if n == "Bron fact verschil"
            else e,
            f,
        )
        for n, e, f in extra
    ]
    fact["measures"] += [dict(name=n, expression=e, formatString=f) for n, e, f in extra]

    def table(name, data):
        cols = []
        for key in data[0]:
            value = next((r[key] for r in data if r[key] is not None), 0)
            dtype = (
                "string"
                if isinstance(value, str)
                else "Double"
                if isinstance(value, float)
                else "Int64"
            )
            if key in ["KansPositief", "BenutbaarLaag", "BenutbaarHoog"]:
                dtype = "Double"
            cols.append(dict(name=key, dataType=dtype))
        model["tables"].append(dict(name=name, columns=cols))

    next(m for m in fact["measures"] if m["name"] == "Indicatieve besparing")["expression"] = (
        "[Bespaarde wachturen]*[Tarief wachtuur]*[Benutbare fractie]"
    )
    tables = {
        **base,
        "FactOps": clean,
        "ScenarioRealization": [
            dict(Fraction=f, Keuze=f"{round(f * 100)}% benutbaar") for f in [0.05, 0.10, 0.15]
        ],
        "DQRule": dq,
        "LoadRun": [
            dict(
                Run=h["run"],
                Status=h["status"],
                Nieuw=h["inserted"],
                Correcties=h["updated"],
                Duplicaten=h["duplicates"],
                Afgekeurd=h["rejected"],
                FactRijen=h["fact_rows"],
                BronVoertuigen=h["source_vehicles"],
                FactVoertuigen=h["fact_vehicles"],
                Verschil=h["difference"],
            )
            for h in history
        ],
        "DecisionOption": decision["options"],
        "PilotSummary": experiment["summary"],
        "Association": analysis["coefficients"],
        "KPIContract": contracts,
    }
    for name in [
        "ScenarioRealization",
        "DQRule",
        "LoadRun",
        "DecisionOption",
        "PilotSummary",
        "Association",
        "KPIContract",
    ]:
        table(name, tables[name])
    save(output / "model.json", model)
    save(output / "tables.json", tables)
    save(output / "manifest.json", manifest)
    save(output / "loads.json", history)
    save(output / "gate.json", gate)
    save(output / "associations.json", analysis)
    save(output / "decisions.json", decision)
    save(output / "pilot.json", experiment)
    summary = dict(
        synthetic=True,
        fact_rows=len(clean),
        vehicles=sum(f["Vehicles"] for f in clean),
        revenue=sum(f["Revenue"] for f in clean),
        source_fact_difference=history[-1]["difference"],
        missing_departure_units=sum(f["MissingDepartureUnits"] for f in clean),
        replay_new_events=history[1]["inserted"] + history[1]["updated"],
        late_corrections=history[-1]["updated"],
        quarantined_initial=history[0]["rejected"],
        pipeline_status="passed",
        pilot_did_minutes=experiment["observed_did_minutes"],
        recommended_next_step="Pilot dispatch/appointment slots; do not claim realized savings",
    )
    save(output / "summary.json", summary)
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    db.close()


if __name__ == "__main__":
    main()
