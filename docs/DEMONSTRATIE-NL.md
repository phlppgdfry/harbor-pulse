# Zelfstandige demonstratie — begrijpen, voorspellen, uitvoeren

Doel: in ongeveer 20–30 minuten vier keuzes uitleggen met bewijs. Doe de opdrachten zelf,
voorspel eerst de uitkomst en controleer daarna. Deze handleiding en een geslaagde helperrun
bewijzen **niet** dat jij de oefening zelfstandig hebt uitgevoerd.

Je gebruikt fictieve data. Er zijn geen cloudcredentials nodig en je wijzigt geen live
Power BI-rapport. De verificatiehelper leest het bestaande warehouse read-only en gebruikt
voor foutinjectie een tijdelijke database. Een nieuwe demo schrijft uitsluitend onder jouw
gekozen outputmap. `uv` moet beschikbaar zijn; [installatie-instructies](DEVELOPMENT.md).

## Voorbereiding

Vanaf de root van de repo:

```sh
uv sync --locked --extra report
uv run --locked python -m harbor_pulse demo --output build/mijn-oefening
```

De CLI weigert een reeds gevuld outputwarehouse. Kies bij herhaling een nieuwe map,
bijvoorbeeld `build/mijn-oefening-2`; verwijder geen bestaande evidence om een fout te verbergen.
Pas in de volgende commando's `--run` en SQL-bestandspad aan die map aan.

Noteer vooraf je voorspellingen en achteraf de werkelijke resultaten. Bewaar je eigen
notities eventueel in `build/mijn-demo-notities.md`; dit staat buiten de gepubliceerde case.

## Opdracht 1 — volg één correctie van bron naar fact

**Voorspel:** overschrijft een hogere revisie de batch, maakt zij een extra batch, of wordt
zij afgekeurd? Wat gebeurt er bij nogmaals laden?

Open `build/mijn-oefening/raw/arrivals.json` en `raw/late-arrivals.json`.
Zoek dezelfde `key` met versie 1 en versie 2. Kies een geaccepteerde correctie; gebruik
de database om vast te stellen welke dat is. Met SQLite CLI, indien geïnstalleerd:

```sh
sqlite3 -readonly build/mijn-oefening/warehouse.sqlite <<'SQL'
SELECT event_key, old_version, new_version, run
FROM audit
WHERE source = 'arrivals' AND old_version IS NOT NULL
ORDER BY run, event_key LIMIT 1;

SELECT event_key, version, json_extract(payload, '$.Units') AS units
FROM events
WHERE source = 'arrivals'
  AND event_key = (
    SELECT event_key FROM audit
    WHERE source = 'arrivals' AND old_version IS NOT NULL
    ORDER BY run, event_key LIMIT 1
  );

SELECT id, status, inserted, updated, duplicates, rejected
FROM runs ORDER BY id;
SQL
```

De helper hieronder biedt dezelfde trace als SQLite CLI ontbreekt. Zoek daarna de
terminal-dag in `tables.json` → `FactOps`. De fact heeft méér batches: het dagtotaal is
niet gelijk aan de units van jouw ene batch.

**Verwacht:** versie 1 → 2, twee extra units in die correctie; de replayrun heeft nul inserts
én updates. De volledige demo heeft 36 correcties en 366.910 voertuigunits. De audit
bevat eerst ook inserts met `old_version=NULL`; die zijn geen correcties.

**Leg uit:** key bepaalt identiteit, versie bepaalt revisie, hash bewaakt inhoud. Een
zelfde-versie-conflict wordt niet als correctie geaccepteerd. Watermarks zijn monitoring,
geen filter dat teruggedateerde correcties uitsluit. [Code](../harbor_pulse/pipeline.py).

## Opdracht 2 — reken een KPI onafhankelijk na

Open [de drie handberekende rijen](../fixtures/hand-calculated.json), maar dek `expected`
en `working` eerst af. Reken zonder code:

1. Totaal voertuigen en punctualiteit.
2. Vehicle-weighted delay.
3. Matched-unit-weighted dwell en aparte vertrekdekking.
4. Bezetting als ratio van slotdagen en marge als ratio van omzet/kosten.

**Controleer pas daarna:** 60 voertuigen; 66,67% punctualiteit; 23,3333 minuten delay;
4,5 uur dwell; 80% dekking; 53,33% bezetting; 33,33% marge.

```sh
uv run --locked python -m unittest discover -s tests -p test_challenge.py -v
```

**Leg uit:** waarom is `(2+4+8)/3` niet de gevraagde dwell? Waarom geef je de twaalf
ongematchte units geen dwell van nul? Een passerende test vervangt je eigen berekening niet.
[Rekenfunctie](../harbor_pulse/challenge.py), [kennisgids](KENNISGIDS-NL.md).

## Opdracht 3 — verander één aanname en probeer het voorstel te weerleggen

Voorspel wat gebeurt bij EUR45 per wachtuur wanneer de benutbare fractie van **10% naar
0%** gaat. Gebruik de interactieve publieke walkthrough of de lokale reference-output.
Wijzig voor deze opdracht geen productieconfiguratie of cloudrapport.

**Verwacht:** bij 10% is dispatch de centrale jaarlijkse voorkeur. Bij 0% is ieder
jaarlijks net negatief en wordt **Do not implement** gekozen. De jaarlijkse kosten zijn
niet nul omdat de veronderstelde tijdwinst financieel onbruikbaar is.

Leg het verschil uit tussen bruto tijdwaarde, jaarlijkse netto waarde en kasstroom in
jaar één. Toon welke invoer fictief is en hoe een financier/operations lead die moet
valideren. Bij de gekozen centrale reductie en EUR45/h is dispatch jaarlijks ongeveer
break-even bij 2,73% usability, inclusief investering in jaar één bij 4,85%.
[Scenariofunctie](../harbor_pulse/review.py), [analytische uitdagingen](ASSUMPTION-CHALLENGES.md).

## Opdracht 4 — verklaar een bewuste fout en het herstel

Voorspel eerst of de echte dekking van de demo de publicatiepoort haalt:

- Bij minimaal **99%**: geslaagd met zichtbare waarschuwingen.
- Bij minimaal **99,9%**: geblokkeerd; de dekking is ongeveer 99,482%.

Een strengere eis blokkeert deze dataset terecht volgens dat beleid. Dat is niet hetzelfde
als kapotte software of bewijs dat de grens bedrijfsmatig juist is.

Daarna injecteert de helper in een tijdelijke database een fout na de eerste update.
Voorspel wat er met facts, watermarks en het failed-runlog gebeurt. **Verwacht:** de eerder
gecommitteerde facts en watermarks blijven gelijk; een mislukte run wordt geregistreerd.
Je mag geen success/fresh-status tonen alsof de load is afgerond. [Rollbacklogica](../harbor_pulse/pipeline.py).

## Verificatiehelper — pas gebruiken na je voorspellingen

```sh
uv run --locked python scripts/practice_demo.py \
  --run build/mijn-oefening \
  --output build/mijn-oefening-reference.json
```

Het JSON-bestand bevat `correction`, `hand_kpis`, `assumption_change`, `coverage_gate` en
`rollback`. `status=passed` betekent dat de **geautomatiseerde referentiecontrole** slaagt,
niet dat jij de opdrachten beheerst. De helper controleert verwachte omkering en rollback;
onverwachte uitkomsten stoppen met een fout in plaats van een succesclaim.

## Zelf beoordelen en laten beoordelen

- [ ] Ik voorspelde de uitkomst vóór uitvoering en bewaarde die voorspelling.
- [ ] Ik kan één key van oude bronregistratie naar huidige eventversie en dagfact volgen.
- [ ] Ik kan teller, noemer en gewichten zonder de helper uitleggen.
- [ ] Ik kan aanwijzen welke aanname het besluit laat omslaan.
- [ ] Ik kan de fout, rollback en het behoud van verified state uitleggen.
- [ ] Ik kan een beperking noemen die de tests niet oplossen: bijvoorbeeld selectieve missingness,
      voertuig-P95, causale identificatie of license-blocked viewer-RLS.
- [ ] Ik heb genoteerd wat ik zelfstandig deed, waar ik hulp gebruikte en wat nog onduidelijk is.

Laat een reviewer één getal, grens of key kiezen dat je niet vooraf uit het hoofd kent.
Een sterke demonstratie is geen foutloze monoloog: een verkeerde voorspelling herkennen,
onderzoeken en corrigeren is ook bewijs van begrip. Gebruik [de interviewbank](INTERVIEWBANK-NL.md)
voor vervolgvragen. Er is geen automatische certificering van jouw ervaring of senioriteit.
