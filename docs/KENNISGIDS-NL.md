# Harbor Pulse — Nederlandstalige kennisgids

Deze gids legt de belangrijkste begrippen uit die in de case, code, analyses en
beheerdocumenten voorkomen. Het is een startpunt, geen vervanging voor de broncode.
Alle organisaties, data, kosten en interventie-uitkomsten zijn fictief. De case is met
substantiële AI-ondersteuning gebouwd; begrijpen en zelfstandig uitvoeren moet je zelf aantonen.

**Leesroutes:** HR: onderdelen 1, 2 en 5 → [interviewbank](INTERVIEWBANK-NL.md).
Analist: onderdelen 2–6 → [zelfstandige demonstratie](DEMONSTRATIE-NL.md).
Senior reviewer: onderdelen 3–7 → [aannames onderzoeken](ASSUMPTION-CHALLENGES.md)
en [werkelijke controlestatus](CONTROL-STATUS.md).

## 1. De case in gewone taal

De vraag is: hoe kan een terminal minder vertraging hebben zonder wachtrijen alleen te
verplaatsen, slechte data te verbergen of tijdwinst automatisch als geldbesparing te tellen?
Vier gesimuleerde bronnen beschrijven aankomsten, vertrekken, capaciteit en personeelsuren.
Python verwerkt fouten en correcties, SQLite bewaart de historie, Power BI toont de cijfers,
en scenario's vergelijken maatregelen. Een gesimuleerde pilot laat zien hoe je een maatregel
zou toetsen. Dispatch/afspraakslots is de eerste pilotkandidaat **onder de gekozen aannames**.
Dat is geen bewijs van werkelijk bespaard geld, een echt interventie-effect of senior ervaring.

## 2. Woordenlijst: data en verwerking

| Term | Betekenis | In Harbor Pulse |
|---|---|---|
| Dispatch / afspraakslots | Aankomsten en verwerking coördineren of tijdvakken afspreken | Voorgestelde pilot, geen bewezen interventie |
| Yardruimte | Opstel-/opslagruimte op de terminal | Meer ruimte verlaagt de berekende bezettingsratio; throughputwinst is niet aangetoond |
| Units | Aantal voertuigen dat een batch vertegenwoordigt | Niet het aantal onafhankelijke waarnemingen |
| Handling capacity / planning | Verwerkingscapaciteit / verwacht volume | Fictieve inputs; volume-capaciteitratio is geen volledig wachtrijmodel |
| Terminal | Locatie waar voertuigen/goederen worden verwerkt | Drie fictieve locaties: Zeebrugge, Antwerpen en Gent |
| Batch | Groep voertuigen met gezamenlijke registratie | Eén tijdstip vertegenwoordigt de batch; geen individuele voertuigverdeling |
| Grain / korrel | Wat één rij precies voorstelt | Bron: transportbatch; fact: één terminal op één datum |
| Business key | Stabiele identiteit van een gebeurtenis | `event_key`; dezelfde batch behoudt haar key bij een correctie |
| Source / bron | Systeem of bestand waar een registratie vandaan komt | Arrivals, departures, capacity, staffing |
| Versie / revision | Nummer van een gewijzigde registratie | Hogere versie mag de geldige huidige versie vervangen |
| Hash / digest | Vingerafdruk van inhoud | Onderscheidt identieke replay van gewijzigde inhoud; geen encryptie |
| Canonicalisatie | Inhoud consequent representeren voordat je vergelijkt | JSON in vaste vorm vóór hashing |
| Duplicaat | Dezelfde registratie verschijnt opnieuw | Zelfde bron, key, versie en hash: geen nieuwe mutatie |
| Versieconflict | Dezelfde key/versie heeft verschillende inhoud | Quarantaine; geen willekeurige overschrijving |
| Late correctie | Wijziging komt later binnen dan de oorspronkelijke registratie | Demo: 36 hogere revisies, samen 72 extra voertuigunits |
| Stale record | Verouderde revisie | Kan de nieuwere huidige versie niet terugdraaien |
| Upsert | Invoegen als de key nieuw is, anders bijwerken | Alleen volgens de versie-/inhoudsregels |
| Idempotentie / replay | Herhalen heeft geen extra effect op de huidige data | Tweede identieke load: nul inserts en updates; een nieuw runlog blijft bestaan |
| Incrementeel | Alleen noodzakelijke veranderingen toepassen | Databasewrites zijn incrementeel; bronbestanden worden volledig gelezen |
| Watermark | Laatst waargenomen updateklok per bron | Monitoring; geen hard filter dat oudere correcties weggooit |
| ETL / ELT | Extractie, transformatie en laden; volgorde verschilt | Case leest bestanden, valideert, bewaart events en bouwt facts; geen cloud-ELT-platform |
| CDC | Wijzigingen aan de bron volgen | Niet geïmplementeerd; snapshotadapter is geen CDC |
| Join / koppeling | Registraties via keys combineren | Aankomst met passend vertrek, terminal en datum |
| Quarantaine | Afgekeurde registraties apart bewaren | Fout en reden blijven inspecteerbaar; fout is niet stil verwijderd |
| Audit trail | Vastlegging van wijzigingen | Oude/nieuwe versie, hashes en runnummer |
| Transactie / atomiciteit | Mutaties slagen samen of worden samen teruggedraaid | Events, revisions, facts en watermarks |
| Reconciliatie | Onafhankelijke totalen laten aansluiten | Laatste geldige bronunits versus factunits: verschil moet nul zijn |
| Publication gate | Controle voordat publicatie is toegestaan | Reconciliatie, vertrekdekking en afkeurpercentage |
| Lineage | Herkomst van een getal kunnen volgen | Bronbatch → huidige eventversie → fact → KPI → visual |
| Snapshot | Vastgelegde datatoestand | Native Power BI-model bevat een gecureerde, ingebedde synthetische snapshot |

Bronnen: [pipeline](PIPELINE.md), [broncontracten](../contracts/source-contracts.json),
[generator](../harbor_pulse/sources.py), [validatie en ingestie](../harbor_pulse/pipeline.py).

## 3. Woordenlijst: KPI's en Power BI

| Term | Betekenis | Belangrijk onderscheid |
|---|---|---|
| KPI | Indicator voor een afgesproken vraag/doel | Een KPI-doel is beleid; geen natuurwet |
| Teller / noemer | Wat je telt / waar je het door deelt | Verkeerde noemer kan een overtuigend maar verkeerd percentage geven |
| Gewogen gemiddelde | Waarnemingen tellen naar hun relevante omvang mee | Delay naar voertuigunits; dwell naar geldige gematchte units |
| Punctualiteit | Op tijd geregistreerde units / geldige aankomstunits | On-time count komt uit de bron; niet uit één gemiddeld batchtijdstip |
| Delay / vertraging | Actual arrival minus planned arrival, in minuten | Vroege aankomst geeft nul vertraging, geen negatieve vertraging |
| Dwell / verblijftijd | Tijd tussen aankomst en vertrek | Ontbrekend vertrek geeft geen verblijf van nul uur |
| Vertrekdekking | Geldig gematchte vertrekunits / aankomstunits | Apart tonen naast gemiddelde dwell |
| Slot-day / slotdag | Eén beschikbare of bezette plek gedurende een dag | Ratio van sommen; geen ongewogen gemiddelde van dagpercentages |
| Bezetting | Bezette slotdagen / beschikbare slotdagen | Zegt zonder verdere data niet hoe lang een individuele wachtrij is |
| Brutomarge | Omzet minus handlingkosten, gedeeld door omzet | Geen nettowinst; overhead, financiering en belasting ontbreken |
| Fact table | Feiten op een expliciete grain | `FactOps`: terminal-dag met units en operationele waarden |
| Dimension table | Beschrijvende attributen voor groeperen/filteren | `DimDate` en `DimTerminal` |
| Stermodel | Facts centraal, dimensies daaromheen | Voorkomt dat alle bedrijfsbegrippen in één onduidelijke tabel verdwijnen |
| Relationship | Verbinding tussen modeltabellen | Datum- en terminalselectie moeten facts correct filteren |
| Semantisch model | Data, relaties, typen en berekeningen voor analyse | Een model is geen rapport of dashboard |
| Measure | Berekening die op de huidige selectie reageert | Bijvoorbeeld `[Voertuigen]`; geen vast ingevuld getal |
| DAX | Taal voor berekeningen in Power BI | `SUM`, `DIVIDE`, filtercontext; geselecteerde voorbeelden zijn gedocumenteerd |
| Filtercontext | Selectie waarin een measure wordt berekend | Antwerpen in april is een ander totaal dan alle terminals in het jaar |
| Slicer | Selectie-element in het rapport | Terminal, maand en scenarioparameters |
| M / Power Query | Taal voor bron-/transformatielogica in het model | Getypeerde import uit de ingebedde snapshot |
| TMDL / BIM | Representaties van een tabular model | Inspecteerbare modeldefinitie; geen screenshot |
| PBIR | Bronformaat van een Power BI-rapportdefinitie | Pagina's, visuals, filters en opmaak als bestanden |
| Rapport | Interactieve pagina's met visuals | Harbor Pulse heeft twaalf pagina's |
| Dashboard | Overzicht met tegels in Power BI Service | Ander itemtype dan een meerpagina-rapport |
| RLS | Row-level security: rijen beperken per rol/gebruiker | Rollen zijn gedeployed; viewerhandhaving blijft license-blocked |
| SDK / API / CLI | Bibliotheek / programmeerinterface / commandoregeltool | SDK-rendering draait geïsoleerd headless; geen gebruikersbrowserovername |
| Refresh | Data opnieuw laden/verwerken in het model | Dezelfde ingebedde bron refreshen is geen nieuwe operationele bron ophalen |

Verdieping: [KPI-contracten](KPI-CONTRACTS.md), [DAX-voorbeelden](DAX-EXAMPLES.md),
[modelbuilder](../scripts/build_native_model.py), [rapportbuilder](../scripts/build_report.py),
[datafitness](DATA-FITNESS.md). De 97% punctualiteit, 85% bezetting en 35% marge zijn oefendoelen.

## 4. Woordenlijst: analyse, investeringen en experimenten

| Term | Betekenis | Valkuil in deze case |
|---|---|---|
| Associatie / correlatie | Variabelen bewegen samen | Meer personeel kan een reactie op drukte zijn |
| Causaliteit | Een verandering veroorzaakt een effect | Regressie op synthetische observaties bewijst dit niet |
| Confounding | Andere factoren beïnvloeden oorzaak én uitkomst | Volume, onderhoud of managementpraktijk kunnen een verklaring vertekenen |
| OLS / regressie | Coëfficiënten kiezen die gekwadrateerde voorspellingsfouten beperken | Coëfficiënten hebben verschillende eenheden; geen automatische feature importance |
| Residual / residu | Werkelijke uitkomst minus modelvoorspelling | Patronen wijzen op niet verklaarde structuur |
| RMSE | Wortel van gemiddelde gekwadrateerde fouten | Eenheid hier minuten; grote fouten tellen zwaar mee |
| Holdout | Data buiten de fit gebruiken voor toetsing | Chronologisch Q4; bevat geen onderhoudsincident |
| Leakage | Toekomstinformatie of toetsdata in training gebruiken | Een te mooie score kan hierdoor onbetrouwbaar zijn |
| VIF / multicollineariteit | Diagnose van overlappende verklarende informatie | Instabiele coëfficiënten zijn geen causaal bewijs |
| Bootstrap | Herhaald resamplen om onzekerheid te onderzoeken | Resample hele weken of gekoppelde dagen, passend bij afhankelijkheid |
| Cluster / block | Waarnemingen die samen afhankelijk kunnen zijn | Dagen/terminals delen incidenten; voertuigunits zijn geen onafhankelijke proefpersonen |
| Betrouwbaarheidsinterval | Intervalprocedure die onder aannames bij herhaling dekking geeft | Een frequentistisch 95%-interval betekent niet 95% kans voor de vaste parameter in dit ene interval |
| Monte Carlo | Veel trekkingen uit gekozen aannames doorrekenen | Gekozen verdelingen zijn hier fictief, niet uit operationele data geschat |
| P10 / P50 / P90 | 10e, 50e en 90e percentiel van een verdeling | Scenario-percentielen zijn geen statistische betrouwbaarheidsgrenzen |
| Sensitiviteit | Uitkomst onderzoeken bij andere invoer | Laat omslagpunten zien; geen waarschijnlijkheidsvoorspelling |
| Afhankelijkheid | Aannames hangen samen | Meer tijdwinst kan meer personeelskosten vereisen |
| Benutbare fractie | Deel van tijdwinst dat economisch kan worden benut | Minder wachten is niet automatisch minder loonkosten |
| Opex / capex | Terugkerende kosten / eenmalige investering | Jaarlijkse netto waarde en kasstroom in jaar één verschillen |
| Break-even | Opbrengst en gekozen kosten zijn gelijk | Geef aan of implementatiekosten zijn inbegrepen |
| Selectieve missingness | Ontbreken hangt samen met de uitkomst | Juist vertraagde batches missen vertrekregistraties |
| MCAR / MAR / MNAR | Onafhankelijk van data / conditioneel op geobserveerde data onafhankelijk van ontbrekende waarden / die onafhankelijkheid ontbreekt | De case schat geen echt missingnessmechanisme; simuleert alternatieven |
| Identificatiegrens | Bandbreedte onder expliciete aannames over onbekende waarden | 0–72 uur is een veronderstelde dwellgrens, geen vastgesteld maximum |
| Pilot / randomisatie | Kleine proef / behandeling door toeval toewijzen | De pilot is gesimuleerd, niet uitgevoerd in een terminal |
| DiD | Verandering interventiegroep minus verandering controlegroep | Randomisatie helpt, maar spillover en carryover blijven ontwerpvragen |
| Placebo / nulscenario | Toets zonder echte interventiewinst | Kan schijnsucces zichtbaar maken |
| Power / type-I-fout | Kans een gekozen effect te detecteren / fout-positief onder de nul | Afhankelijk van effect, variatie, steekproef en toetsaannames |
| Spillover / carryover | Effect bereikt controlegroep / werkt na een wissel door | Kan lane-day-randomisatie ongeschikt maken |
| Minimum useful effect | Kleinste verbetering die praktisch telt | Drie minuten is een oefenkeuze; significantie alleen volstaat niet |
| Guardrail | Uitkomst die niet slechter mag worden | Bijvoorbeeld veiligheid, capaciteit of verplaatsen van wachtrijen; hier niet echt gemeten |
| Pre-registratie | Ontwerp en beslisregels vooraf vastleggen | Er is een protocolspecificatie, geen extern geregistreerde echte pilot |

Zie [analyses](ANALYSIS.md), [robuustheid](ROBUSTNESS.md), [zes uitdagingen](ASSUMPTION-CHALLENGES.md),
[pilotprotocol](PILOT-PREREGISTRATION.md), [analyselogica](../harbor_pulse/analysis.py),
[reviewlogica](../harbor_pulse/review.py) en [uitdagingslogica](../harbor_pulse/challenge.py).

## 5. Proces: van bron tot rapport

1. **Vraag en definitie.** Bepaal welk besluit je ondersteunt, welke grain beschikbaar is,
   en welke teller/noemer en eigenaar bij iedere KPI horen.
2. **Bron genereren/lezen.** Vier feeds bevatten batches, snapshots en gecontroleerde fouten.
   Bestanden lezen is niet hetzelfde als een live bron koppelen.
3. **Valideren.** Controleer keys, versies, units, terminal, datum en tijdzone. Ongeldige
   input gaat naar quarantaine; ontbrekende essentiële capaciteit/staffing stopt verwerking.
4. **Versies verwerken.** Duplicaten veranderen niets. Een geldige hogere revisie mag updaten;
   een conflict op dezelfde versie mag niet. Bewaar een audit trail.
5. **Facts bouwen.** Koppel aankomst/vertrek en vorm terminal-dagen. Gewichten en ontbrekende
   vertrekunits blijven zichtbaar. De databasewijzigingen staan in één transactie.
6. **Publicatie toestaan of stoppen.** Vergelijk bron- en factunits, dekking en afkeurpercentage.
   De poort kan slagen mét waarschuwingen. Een strengere grens is een beleidswijziging.
7. **Modelleren en presenteren.** De native snapshot voedt dimensies, facts en DAX-measures.
   PBIR definieert het rapport. Filtercontext bepaalt wat de visuals laten zien.
8. **Analyseren en besluiten.** Vergelijk kosten, benutbare winst, alternatieve verklaringen,
   ontbrekende data en perioden. Stel een pilot voor; presenteer geen echte winstclaim.
9. **Publiceren en verifiëren.** Maak een backup, update het bestaande rapport, lees terug,
   controleer modelkoppeling en queries. Een fout activeert herstel; herstel wordt geverifieerd.
10. **Beheren en bewijzen.** Refresh wijzigt pas de verified state na aansluiting. Freshness
    gebruikt de gecontroleerde ingestieklok, niet toekomstige fictieve eventdatums. CI en het
    artifactregister signaleren inconsistenties. Werkelijke blokkades blijven zichtbaar.

Het [demonstratiedraaiboek](DEMONSTRATIE-NL.md) volgt deze stappen met echte lokale outputs.

## 6. Uitgewerkt rekenvoorbeeld

[De handmatig narekenbare fixture](../fixtures/hand-calculated.json) bevat drie terminal-dagen:

| Rij | Voertuigen | Op tijd | Delay min | Gematchte units | Dwell uur | Slots beschikbaar/bezet | Omzet/kosten |
|---|---:|---:|---:|---:|---:|---|---|
| A | 10 | 9 | 0 | 8 | 2 | 100 / 40 | 300 / 200 |
| B | 30 | 21 | 20 | 30 | 4 | 50 / 45 | 900 / 700 |
| C | 20 | 10 | 40 | 10 | 8 | 150 / 75 | 600 / 300 |

- Voertuigen: `10 + 30 + 20 = 60`.
- Punctualiteit: `(9 + 21 + 10) / 60 = 66,67%`.
- Delay: `(10×0 + 30×20 + 20×40) / 60 = 23,3333 minuten`.
- Dwell: `(8×2 + 30×4 + 10×8) / 48 = 4,5 uur`.
- Vertrekdekking: `48 / 60 = 80%`.
- Bezetting: `(40 + 45 + 75) / (100 + 50 + 150) = 53,33%`.
- Brutomarge: `(1.800 − 1.200) / 1.800 = 33,33%`.

Het simpele dwellgemiddelde `(2+4+8)/3 = 4,6667` is een andere vraag: een gemiddelde
van drie rijen, niet van gematchte voertuigunits. De 12 ongematchte units krijgen geen
verzonnen dwell van nul. [De onafhankelijke tests](../tests/test_challenge.py) vergelijken
met de geschreven verwachte uitkomsten, niet alleen met dezelfde formule opnieuw.

## 7. Woordenlijst: beheer, kwaliteit en grenzen

| Term | Uitleg | Waar je dit controleert |
|---|---|---|
| Release / rollback | Wijziging publiceren / vorige toestand herstellen | [Releasecontrol](../scripts/release_report.py) |
| Read-back / modelbinding | Gepubliceerde inhoud teruglezen / rapport-modelkoppeling | Definitie én koppeling moeten overeenkomen |
| Timeout / HTTP429 | Antwoord te laat / limiet op aanvragen | Een timeout bewijst niet dat een create-aanvraag niet is uitgevoerd |
| Retry / backoff | Opnieuw proberen / wachten tussen pogingen | Alleen veilig herhalen; niet zomaar een tweede model maken |
| Atomic state replacement | Verified beheerstatus in één stap vervangen | Geen fresh/success-status na een mislukte refresh |
| SLA / freshness | Afspraak over kwaliteit/tijd / hoe recent een ingestie is | 26 uur is casebeleid; lokale scheduler heeft machine en auth nodig |
| Authentication / authorization | Identiteit aantonen / bepalen wat die identiteit mag | Een eigenaarstest bewijst geen RLS-handhaving voor een viewer |
| Least privilege | Alleen noodzakelijke rechten | CI heeft leesrechten; geen extra gebruikers toegekend |
| Secret / receipt | Geheime toegangsinformatie / uitvoeringsbewijs | Tokens niet publiceren; private receipts staan in genegeerd `build/` |
| Python / SQL / SQLite | Programmeertaal / querytaal / lokale database-engine | Python verwerkt; SQL bevraagt het SQLite-warehouse |
| JSON / CSV | Gestructureerd tekstformaat / tabeltekstformaat | JSON bewaart model/evidence; CSV wordt onder meer gebruikt bij SDK-exports |
| UTC / tijdzone | Referentietijd / relatie van lokale tijd tot die referentie | Gezoneerde timestamps voorkomen onduidelijke duur-/datumvergelijkingen |
| Git / GitHub / repo | Versiebeheer / hosting en samenwerking / verzameling bronbestanden en geschiedenis | Repo is inspecteerbaar; een mooie repo bewijst geen echte bedrijfsimpact |
| Commit / branch / PR | Vastgelegde wijziging / ontwikkellijn / wijzigingsvoorstel voor review | CI controleert een specifieke commit; een oude groene run bewijst geen nieuwe versie |
| uv / virtualenv / dependency | Omgevings- en dependencytool / geïsoleerde Python-omgeving / benodigd pakket | Lockfile fixeert versies; report-dependencies zijn optioneel voor de kern |
| Hypothesis | Tool voor gegenereerde property-testvoorbeelden | Test invariant over veel invoer; niet ieder mogelijk geval |
| Schema / datatype | Structuurafspraak / soort waarde | De reportvalidator controleert structuur, niet alle betekenis of zichtbare pixels |
| CI / lockfile | Automatische checks / vastgelegde dependencies | GitHub Actions, `uv.lock` en `package-lock.json` |
| Lint / formatter | Mogelijke codefouten signaleren / consistente opmaak | Ruff en SQLFluff; bewijzen geen juiste bedrijfsvraag |
| Unittest / property test | Vast voorbeeld / veel gegenereerde voorbeelden | Hypothesis onderzoekt versies, laadvolgorde en rollback |
| Coverage | Welke statements/takken zijn uitgevoerd | Hoge dekking is geen bewijs dat alle assertions of scenario's goed zijn |
| pre-commit / Gitleaks | Checks vóór commit / mogelijke secrets detecteren | Detectie is geen garantie dat ieder geheim wordt gevonden |
| Playwright / axe | Browserinteracties toetsen / toegankelijkheidsregels toetsen | Headless sessie; automatische axe-pass is geen volledige WCAG-certificering |
| Alt-tekst / tabvolgorde / contrast | Beschrijving / toetsenbordroute / leesbaar kleurverschil | Websitechecks, rapportbron en visuele review |
| Artifact / provenance | Opgeleverd bestand / herkomstbewijs | Hashes bewijzen identiteit; geen OCR van iedere screenshottekst |
| Schone checkout | Bron zonder bestaande lokale cache-/buildtoestand | Nieuw git-archief en omgeving; downloadcache mag worden hergebruikt |

Een lokale scheduler is geen beheerd productieplatform. De actieve native import is geen
bron-CDC of native incremental partition refresh. De live herstelproef herstelt een rapport,
geen semantisch-modeldata. RLS-viewerhandhaving is **license-blocked**. Zie [releasecontroles](RELEASE-CONTROLS.md),
[development](DEVELOPMENT.md), [controlestatus](CONTROL-STATUS.md) en [eigen bijdrage](OWNERSHIP.md).
