"""Generate a twelve-page Power BI PBIR report entirely from source code."""

import base64
import hashlib
import json
import os
import pathlib
import shutil

ROOT = pathlib.Path(__file__).resolve().parents[1]
OUT = ROOT / "build/report"
SOURCE = ROOT / "templates"
RUN = pathlib.Path(os.environ.get("HARBOR_RUN", str(ROOT / "build/run")))
NAVY, TEAL, PAPER, INK = "#102A43", "#007F86", "#F2F5F9", "#243B53"


def save(p, data):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(data, ensure_ascii=False, indent=2))


for source in SOURCE.rglob("*"):
    if source.is_file() and not str(source.relative_to(SOURCE)).startswith("definition/pages/"):
        dest = OUT / source.relative_to(SOURCE)
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, dest)
themefile = next(OUT.glob("StaticResources/RegisteredResources/*.json"))
theme = json.loads(themefile.read_text())
theme.update(
    name="Harbor Pulse · Maritime Intelligence",
    dataColors=[TEAL, "#5064A0", "#A85F0F", "#3F765A", "#88496A", NAVY],
    foreground=INK,
    background="#FFFFFF",
    tableAccent=TEAL,
)
save(themefile, theme)


def lit(v):
    return {
        "expr": {
            "Literal": {
                "Value": "'" + v.replace("'", "''") + "'"
                if isinstance(v, str)
                else "true"
                if v is True
                else "false"
                if v is False
                else str(v) + "D"
            }
        }
    }


def color(v):
    return {"solid": {"color": lit(v)}}


def obj(**p):
    return [{"properties": p}]


def m(name):
    return ("FactOps", name, True)


def d(table, name):
    return (table, name, False)


def field(ref):
    return {
        ("Measure" if ref[2] else "Column"): {
            "Expression": {"SourceRef": {"Entity": ref[0]}},
            "Property": ref[1],
        }
    }


def project(ref):
    return {
        "field": field(ref),
        "queryRef": ref[0] + "." + ref[1],
        "nativeQueryRef": ref[1],
        **({} if ref[2] else {"active": True}),
    }


visuals = []


def vis(page, key, kind, x, y, w, h, title=None, roles=None, bg="#FFFFFF"):
    name = hashlib.sha1((page + key).encode()).hexdigest()[:20]
    v = {
        "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/visualContainer/2.12.0/schema.json",
        "name": name,
        "position": dict(x=x, y=y, z=len(visuals) + 1, width=w, height=h, tabOrder=len(visuals)),
        "visual": {"visualType": kind, "drillFilterOtherVisuals": True},
    }
    if roles:
        v["visual"]["query"] = {
            "queryState": {
                k: {"projections": [project(r) for r in refs]} for k, refs in roles.items()
            }
        }
    v["visual"]["visualContainerObjects"] = {
        "background": obj(show=lit(True), color=color(bg), transparency=lit(0)),
        "border": obj(show=lit(True), color=color("#E1E7EF"), radius=lit(10)),
        "padding": obj(top=lit(12), bottom=lit(12), left=lit(16), right=lit(16)),
        "title": obj(
            show=lit(bool(title)),
            **(
                dict(text=lit(title), fontColor=color(INK), fontSize=lit(13), bold=lit(True))
                if title
                else {}
            ),
        ),
    }
    visuals.append((page, v))
    return v


def text(page, key, content, x, y, w, h, size=13, bg="#FFFFFF", fg=INK):
    v = vis(page, key, "textbox", x, y, w, h, bg=bg)
    v["visual"]["visualContainerObjects"]["padding"] = obj(
        top=lit(2), bottom=lit(2), left=lit(16), right=lit(16)
    )
    v["visual"]["objects"] = {
        "general": obj(
            paragraphs=[
                {
                    "textRuns": [
                        {
                            "value": line,
                            "textStyle": {
                                "fontFamily": "Segoe UI",
                                "fontSize": f"{size}pt",
                                "color": fg,
                                "fontWeight": "bold" if i == 0 else "normal",
                            },
                        }
                    ]
                }
                for i, line in enumerate(content.split("\n"))
            ]
        )
    }
    return v


def card(page, key, metric, x, y, w=370, h=116):
    return vis(page, key, "cardVisual", x, y, w, h, roles={"Data": [m(metric)]})


def cards(page, metrics, y=200):
    for i, metric in enumerate(metrics):
        card(page, "kpi" + str(i), metric, 24 + i * 394, y)


def chart(page, key, kind, title, category, metrics, x, y, w, h, series=None):
    roles = {"Category": [category], "Y": [m(n) for n in metrics]}
    if series:
        roles["Series"] = [series]
    v = vis(page, key, kind, x, y, w, h, title, roles)
    sort = category if category[0] == "DimDate" else m(metrics[0])
    v["visual"]["query"]["sortDefinition"] = {
        "sort": [
            {
                "field": field(sort),
                "direction": "Ascending" if category[0] == "DimDate" else "Descending",
            }
        ]
    }
    if series:
        v["visual"]["objects"] = {"legend": obj(show=lit(True), position=lit("Top"))}
    return v


def table(page, key, title, refs, x, y, w, h, sort=None, descending=False):
    v = vis(page, key, "tableEx", x, y, w, h, title, {"Values": refs})
    for projection in v["visual"]["query"]["queryState"]["Values"]["projections"]:
        projection["active"] = True
    v["visual"]["objects"] = {"total": obj(totals=lit(False))}
    if sort:
        v["visual"]["query"]["sortDefinition"] = {
            "sort": [
                {"field": field(sort), "direction": "Descending" if descending else "Ascending"}
            ]
        }
    return v


def slicer(page, key, ref, x, y, w, h=66, single=False, title=None):
    v = vis(page, key, "slicer", x, y, w, h, title, {"Values": [ref]})
    v["visual"]["objects"] = {
        "data": obj(mode=lit("Dropdown")),
        "selection": obj(singleSelect=lit(single), selectAllCheckboxEnabled=lit(not single)),
    }
    return v


pages = [
    ("b48bf8ced055e9f97bbc", "01 · Management"),
    ("hp_operations", "02 · Dagelijkse operaties"),
    ("hp_terminal", "03 · Terminaldetail"),
    ("hp_incidents", "04 · Verstoringsanalyse"),
    ("hp_finance", "05 · Financiën"),
    ("hp_scenarios", "06 · Scenario-lab"),
    ("hp_data", "07 · Data & methode"),
]
for p, title in pages:
    save(
        OUT / f"definition/pages/{p}/page.json",
        {
            "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/page/2.1.0/schema.json",
            "name": p,
            "displayName": title,
            "displayOption": "FitToPage",
            "width": 1600,
            "height": 1000,
            "objects": {"background": obj(color=color(PAPER), transparency=lit(0))},
        },
    )
    text(
        p,
        "header",
        f"HARBOR PULSE  /  {title[5:].upper()}\nDagelijkse terminal intelligence · Fictief scenario 2026",
        24,
        20,
        1552,
        80,
        19,
        NAVY,
        "#FFFFFF",
    )
    if p != "hp_data":
        text(
            p,
            "filterhint",
            "VERKEN EN VERGELIJK\nFilters gelden per pagina. Selecteer een terminal en/of maand.",
            24,
            116,
            790,
            66,
            11,
            PAPER,
        )
        slicer(
            p, "terminal", d("DimTerminal", "Terminal"), 834, 116, 360, single=p == "hp_terminal"
        )
        slicer(p, "month", d("DimDate", "Maand"), 1214, 116, 362)
    text(
        p,
        "footer",
        "FICTIEVE DEMO · 1.095 terminaldagen · Volledig jaar 2026 · Geen actuele bedrijfsgegevens of causale voorspellingen",
        24,
        950,
        1552,
        32,
        10,
        PAPER,
    )
date = d("DimDate", "Datum")
month = d("DimDate", "Maand")
terminal = d("DimTerminal", "Terminal")

p = pages[0][0]
cards(p, ["Voertuigen", "Volume vs planning", "Op tijd %", "Marge %"])
text(
    p,
    "targets",
    "DOELEN: punctualiteit ≥97% · brutomarge ≥35% · bezetting ≤85% · volume ≥planning",
    24,
    330,
    1552,
    40,
    12,
    "#E5F2F1",
)
chart(
    p,
    "volume",
    "lineChart",
    "Maandelijks voertuigvolume per terminal",
    month,
    ["Voertuigen"],
    24,
    390,
    970,
    260,
    terminal,
)
table(
    p,
    "priorities",
    "Top 3 aandachtspunten · binnen selectie",
    [terminal, m("Prioriteit"), m("Aandachtscore"), m("Verbeterpunt")],
    1014,
    390,
    562,
    260,
    m("Prioriteit"),
)
chart(
    p,
    "plan",
    "clusteredColumnChart",
    "Volume versus planning",
    month,
    ["Voertuigen", "Planning"],
    24,
    670,
    970,
    258,
)
table(
    p,
    "status",
    "Prestaties tegenover doel",
    [terminal, m("Status punctualiteit"), m("Status marge"), m("Status bezetting")],
    1014,
    670,
    562,
    258,
)

p = pages[1][0]
cards(p, ["Op tijd %", "Vertraging min", "Verblijftijd uur", "Dagen boven bezettingsdoel"])
chart(
    p,
    "daily",
    "lineChart",
    "Dagelijks volume · pieken en dalen",
    date,
    ["Voertuigen"],
    24,
    336,
    970,
    286,
    terminal,
)
chart(
    p,
    "weekday",
    "clusteredColumnChart",
    "Volume per terminaldag · weekdagpatroon",
    d("DimDate", "Weekdag"),
    ["Volume per terminaldag"],
    1014,
    336,
    562,
    286,
)
chart(
    p,
    "occupancy",
    "lineChart",
    "Bezetting versus grens van 85%",
    date,
    ["Bezetting %", "Doel bezetting"],
    24,
    642,
    970,
    286,
)
chart(
    p,
    "ontime",
    "lineChart",
    "Punctualiteit versus doel van 97%",
    month,
    ["Op tijd %", "Doel op tijd"],
    1014,
    642,
    562,
    286,
)

p = pages[2][0]
card(p, "selected", "Gekozen terminal", 24, 200, 760, 92)
text(
    p,
    "hint",
    "TERMINALPROFIEL\nKies één terminal bovenaan. Zonder keuze tonen de KPI’s het totaal; de vergelijking blijft beschikbaar.",
    804,
    200,
    772,
    92,
    12,
    "#E5F2F1",
)
cards(p, ["Voertuigen", "Omzet per voertuig", "Bezetting %", "Op tijd %"], 310)
chart(
    p,
    "volume",
    "lineChart",
    "Geselecteerde terminal · volume en planning",
    date,
    ["Voertuigen", "Planning"],
    24,
    446,
    970,
    222,
)
table(
    p,
    "profile",
    "Profiel en resultaten",
    [terminal, d("DimTerminal", "Regio"), m("Voertuigen"), m("Op tijd %"), m("Marge %")],
    1014,
    446,
    562,
    222,
)
chart(
    p,
    "delay",
    "lineChart",
    "Vertraging per maand (minuten)",
    month,
    ["Vertraging min"],
    24,
    688,
    970,
    240,
)
table(
    p,
    "service",
    "Serviceniveau en ruimte",
    [terminal, m("Verblijftijd uur"), m("Bezetting %"), m("CO2 kg per voertuig")],
    1014,
    688,
    562,
    240,
)

p = pages[3][0]
cards(
    p, ["Incidentdagen", "Incidentvoertuigen", "Incident volumeverschil", "Incident extra kosten"]
)
text(
    p,
    "story",
    "FICTIEVE VERSTORING · ANTWERPEN, 6–19 APRIL\nEen onderhoudsknelpunt verlaagt beschikbare yardruimte en valt samen met langere wachttijden en minder volume. De ingestelde extra kosten zijn onderdeel van het scenario; dit is geen causale schatting uit echte data.",
    24,
    336,
    1552,
    100,
    13,
    "#FFF1DB",
)
chart(
    p,
    "delay",
    "lineChart",
    "Gewogen vertraging tijdens incident versus reguliere dagen",
    date,
    ["Vertraging incident", "Vertraging regulier"],
    24,
    456,
    970,
    250,
)
chart(
    p,
    "gap",
    "clusteredColumnChart",
    "Volumeverschil versus planning per maand",
    month,
    ["Volumeverschil"],
    1014,
    456,
    562,
    250,
)
table(
    p,
    "events",
    "Incidentdagen · selecteer Antwerpen en april voor detail",
    [
        date,
        terminal,
        d("FactOps", "Incident"),
        m("Voertuigen"),
        m("Volumeverschil"),
        m("Vertraging min"),
        m("Bezetting %"),
    ],
    24,
    726,
    970,
    202,
    date,
)
text(
    p,
    "action",
    "ONDERZOEKSPAD\n1. Controleer onderhoud en ruimtebeschikbaarheid.\n2. Vergelijk incident- en reguliere dagen.\n3. Test minder wachttijd in het Scenario-lab.\nPlanningverschil is geen bewezen omzetverlies.",
    1014,
    726,
    562,
    202,
    12,
    "#E5F2F1",
)
# Restrict the incident table to incident records; the charts retain comparison days.
events = visuals[-2][1]
events["filterConfig"] = {
    "filters": [
        {
            "name": "IncidentOnly",
            "field": field(d("FactOps", "IncidentFlag")),
            "type": "Categorical",
            "howCreated": "User",
            "filter": {
                "Version": 2,
                "From": [{"Name": "f", "Entity": "FactOps", "Type": 0}],
                "Where": [
                    {
                        "Condition": {
                            "In": {
                                "Expressions": [
                                    {
                                        "Column": {
                                            "Expression": {"SourceRef": {"Source": "f"}},
                                            "Property": "IncidentFlag",
                                        }
                                    }
                                ],
                                "Values": [[{"Literal": {"Value": "true"}}]],
                            }
                        }
                    }
                ],
            },
        }
    ]
}

p = pages[4][0]
cards(p, ["Omzet", "Brutomarge", "Marge %", "Omzet vs budget"])
chart(
    p,
    "revenue",
    "clusteredColumnChart",
    "Omzet versus budget",
    month,
    ["Omzet", "Omzetbudget"],
    24,
    336,
    970,
    286,
)
chart(
    p,
    "margin",
    "clusteredBarChart",
    "Brutomarge per terminal",
    terminal,
    ["Brutomarge"],
    1014,
    336,
    562,
    286,
)
chart(
    p,
    "goal",
    "lineChart",
    "Marge versus doel van 35%",
    month,
    ["Marge %", "Doel marge"],
    24,
    642,
    970,
    286,
)
table(
    p,
    "cost",
    "Kosten en opbrengst per terminal",
    [terminal, m("Omzet"), m("Kosten"), m("Omzet per voertuig")],
    1014,
    642,
    562,
    286,
)

p = pages[5][0]
slicer(
    p,
    "capacity",
    d("ScenarioCapacity", "Keuze"),
    24,
    200,
    370,
    104,
    True,
    "Extra yardcapaciteit · standaard 0%",
)
slicer(
    p,
    "delay",
    d("ScenarioDelay", "Keuze"),
    418,
    200,
    370,
    104,
    True,
    "Minder vertraging · standaard 0 minuten",
)
slicer(
    p,
    "rate",
    d("ScenarioCost", "Keuze"),
    812,
    200,
    370,
    104,
    True,
    "Wachtuurwaarde · standaard €45",
)
slicer(
    p,
    "realization",
    d("ScenarioRealization", "Keuze"),
    1206,
    200,
    370,
    104,
    True,
    "Benutbare tijdwinst · standaard 10%",
)
cards(
    p,
    [
        "Scenario bezetting %",
        "Scenario vertraging min",
        "Bespaarde wachturen",
        "Indicatieve besparing",
    ],
    306,
)
chart(
    p,
    "capacity_compare",
    "clusteredBarChart",
    "Bezetting: basis versus scenario",
    terminal,
    ["Bezetting %", "Scenario bezetting %"],
    24,
    442,
    760,
    260,
)
chart(
    p,
    "time_compare",
    "clusteredBarChart",
    "Vertraging: basis versus scenario",
    terminal,
    ["Vertraging min", "Scenario vertraging min"],
    804,
    442,
    772,
    260,
)
table(
    p,
    "benefit",
    "Indicatief voordeel per terminal",
    [
        terminal,
        m("Bespaarde wachturen"),
        m("Indicatieve besparing"),
        m("Scenario voordeel per voertuig"),
    ],
    24,
    722,
    760,
    206,
)
text(
    p,
    "assumptions",
    "AANNAMES EN GRENZEN\nExtra capaciteit verlaagt alleen de berekende bezettingsratio; volume en omzet blijven gelijk. Tijdwinst wordt per record begrensd op bestaande vertraging. Waarde = voertuigwachturen × eurotarief × benutbare fractie. Vergelijk uitvoeringskosten op de pagina Investeringskeuze. Geen investering, overhead, rebound of bewezen productiviteitswinst meegenomen. Kies één waarde per parameter; bij geen/meerdere keuzes gelden de standaardwaarden.",
    804,
    722,
    772,
    206,
    12,
    "#FFF1DB",
)

p = pages[6][0]
text(
    p,
    "model",
    "DATAMODEL\nDimDate (365 dagen) → FactOps (1.095 terminaldagen) ← DimTerminal (3 terminals).\nTwee relaties sturen datum- en terminalfilters naar dagelijkse feiten.\nVier losstaande scenariotabellen sturen DAX-aannames zonder de brondata te wijzigen.\n56 measures: totalen, doelen, gewogen KPI’s, prioriteiten en scenario-uitkomsten.",
    24,
    120,
    1552,
    150,
    14,
    "#E5F2F1",
)
text(
    p,
    "definitions",
    "KPI-DEFINITIES\nPunctualiteit = op tijd afgehandelde voertuigen / totaal.\nVertraging is gewogen naar voertuigen; verblijftijd gebruikt alleen geldig gematchte vertrekunits.\nBezetting = bezette slotdagen / beschikbare slotdagen.\nBrutomarge = omzet − handlingkosten, vóór overhead en belastingen.\nPrioriteit combineert afwijkingen van planning, punctualiteit, bezetting en marge; het is een demo-score.",
    24,
    290,
    760,
    250,
    13,
)
text(
    p,
    "limits",
    "HERKOMST EN INTERPRETATIE\nAlle data is deterministisch gegenereerd en fictief, ook toekomstige maanden in 2026.\nIncidenten en kostenopslagen zijn ingebouwde aannames.\nDe doelwaarden 97%, 35% en 85% zijn oefendoelen.\nFilters gelden per pagina; top 3 gaat over de geselecteerde terminals.\nGebouwd en gevalideerd via CLI/API; geen browserbediening.",
    804,
    290,
    772,
    250,
    13,
)
table(
    p,
    "detail",
    "Dagelijkse data en KPI’s · filters beschikbaar via het filterpaneel",
    [
        date,
        terminal,
        m("Voertuigen"),
        m("Planning"),
        m("Op tijd %"),
        m("Vertraging min"),
        m("Omzet"),
    ],
    24,
    560,
    1552,
    368,
    date,
)

from types import SimpleNamespace

from report_operating_model import add_pages

add_pages(
    SimpleNamespace(
        pages=pages,
        save=save,
        OUT=OUT,
        obj=obj,
        color=color,
        PAPER=PAPER,
        lit=lit,
        text=text,
        NAVY=NAVY,
        cards=cards,
        table=table,
        d=d,
        chart=chart,
        m=m,
        card=card,
    )
)

save(
    OUT / "definition/pages/pages.json",
    {
        "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/pagesMetadata/1.1.0/schema.json",
        "pageOrder": [p for p, _ in pages],
        "activePageName": pages[0][0],
    },
)
# Reading order follows the visible layout on each page; alt text describes
# changing filters without claiming fixed values. Never encode meaning by color alone.
for page_name, _ in pages:
    ordered = sorted(
        [v for p, v in visuals if p == page_name],
        key=lambda v: (v["position"]["y"], v["position"]["x"]),
    )
    for order, v in enumerate(ordered):
        v["position"]["tabOrder"] = order
        fields = [
            projection.get("nativeQueryRef", "")
            for role in v["visual"].get("query", {}).get("queryState", {}).values()
            for projection in role["projections"]
        ]
        description = (
            (
                "Current selection: "
                + ", ".join(dict.fromkeys(fields))
                + ". Synthetic portfolio data; inspect labels and values, not color alone."
            )
            if fields
            else "Report explanation or navigation. Synthetic portfolio case; no realized business impact claimed."
        )
        v["visual"]["visualContainerObjects"]["general"] = obj(altText=lit(description[:250]))
        if v["visual"]["visualType"] == "lineChart":
            v["visual"].setdefault("objects", {})["lineStyles"] = obj(
                showMarker=lit(True), showMarkerByDefault=lit(True), markerSize=lit(6)
            )
for p, v in visuals:
    save(OUT / f"definition/pages/{p}/visuals/{v['name']}/visual.json", v)
model = (
    json.loads((ROOT / "build/publication.private.json").read_text())
    if (ROOT / "build/publication.private.json").exists()
    else None
)
if model and model.get("id"):
    ref = json.loads((OUT / "definition.pbir").read_text())
    ref["datasetReference"]["byConnection"]["connectionString"] = (
        f'Data Source="powerbi://api.powerbi.com/v1.0/myorg/My workspace";initial catalog="{model["name"]}";integrated security=ClaimsToken;semanticmodelid={model["id"]}'
    )
    save(OUT / "definition.pbir", ref)
parts = [
    dict(
        path=str(p.relative_to(OUT)),
        payload=base64.b64encode(p.read_bytes()).decode(),
        payloadType="InlineBase64",
    )
    for p in sorted(OUT.rglob("*"))
    if p.is_file()
]
save(ROOT / "build/update.json", {"definition": {"format": "PBIR", "parts": parts}})
print(f"Built {len(pages)} pages, {len(visuals)} report elements and {len(parts)} definition parts")
