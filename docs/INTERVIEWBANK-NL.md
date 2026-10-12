# Interviewbank — HR en senior data-analisten

Gebruik dit als voorbereiding, niet als uit het hoofd geleerd bewijs van ervaring.
**Antwoordrichtingen zijn geen verklaring dat jij iets zelfstandig hebt uitgevoerd.**
Vul persoonlijke voorbeelden alleen in met wat werkelijk gebeurde. Een sterk antwoord
legt uit: vraag → keuze → bewijs → beperking → volgende stap.

Start met de [kennisgids](KENNISGIDS-NL.md) en voer het [demonstratiedraaiboek](DEMONSTRATIE-NL.md)
zelf uit. Beschikbare bestanden bewijzen projectwerk; uitleg en live wijzigingen laten jouw begrip zien.

## HR: motivatie, communicatie en bijdrage

| Vraag | Antwoordrichting | Bewijs / doorvraag |
|---|---|---|
| 1. Wat is Harbor Pulse? | Een AI-ondersteunde fictieve terminalcase die onbetrouwbare bronregistraties omzet in controleerbare cijfers en een onderbouwd pilotvoorstel | Toon de publieke walkthrough; leg het zonder toolsnamen in 30 seconden uit |
| 2. Welk probleem los je op? | Minder wachten zonder slechte data te verbergen of tijdwinst automatisch geld te noemen | Welke beslissing kan management nu beoordelen? |
| 3. Waarom koos je dit onderwerp? | Vul jouw echte motivatie in: interesse, leerdoel en aansluiting op de functie | Geen verzonnen werkgever, klantvraag of havenervaring |
| 4. Wat heb jij persoonlijk gedaan? | Benoem werkelijk genomen keuzes, controles en zelf uitgevoerde aanpassingen; onderscheid AI-implementatie van jouw werk | Laat één concrete wijziging en jouw uitleg zien |
| 5. Hoe gebruikte je AI? | Substantiële implementatiehulp; resultaten moeten controleerbaar blijven. Beschrijf jouw echte verificatie, ook waar je nog hulp nodig hebt | [Ownership](OWNERSHIP.md); welke fout heb je zelf ontdekt? |
| 6. Wat is het resultaat? | Reproduceerbare case met pipeline, rapport, analyses en controls; geen echte gerealiseerde besparing | Scheid een werkend artifact van zakelijke impact |
| 7. Waarom is de data fictief? | De case is bedoeld voor inspecteerbare oefening en portfolio; geen echte bronbeschikbaarheid claimen | Wat verandert met echte registraties? |
| 8. Wat ging er mis en wat leerde je? | Kies een fout die je daadwerkelijk begrijpt; leg symptoom, oorzaak, herstel en controle uit | Bijvoorbeeld clipping of de schone-checkout-outputmap; geen eigen ontdekking claimen als die door AI/CI gevonden werd |
| 9. Hoe leg je dit uit aan management? | Besluit, kosten, onzekerheid en benodigde pilotinformatie vóór technische details | Geef één reden om niet te investeren |
| 10. Hoe prioriteer je werk? | Eerst juiste definities/denominatoren en blokkerende fouten; daarna analyse, bewijs en presentatie | Waarom is een extra visual minder nuttig dan een onafhankelijke berekening? |
| 11. Wat moet nog beter? | Echte bronnen, viewer-RLS-test, toegankelijkheid met gebruikers, beheerde operationele omgeving | [Controlestatus](CONTROL-STATUS.md); noem concreet welke claim niet bewezen is |
| 12. Wat wil je verder leren? | Vul jouw daadwerkelijke leervraag in en koppel haar aan een aantoonbare oefening | Vermijd een onbewezen claim dat de case jou senior maakt |

**Eerlijke korte formulering:** “Dit is mijn AI-ondersteunde portfolio-case. De repo maakt
keuzes en controles inspecteerbaar. Ik kan laten zien welke onderdelen ik begrijp en
zelfstandig kan veranderen; ik claim geen echte bedrijfsbesparing of volledige unaided auteurschap.”
Pas dit aan jouw werkelijke begrip aan; het is geen opgelegde persoonlijke uitspraak.

## Senior: data, definities en verwerking

| Vraag | Wat een goed antwoord uitlegt | Controleerbaar bewijs |
|---|---|---|
| 1. Wat is de grain? | Transportbatch in de bron, terminal-dag in de fact. Units zijn geen onafhankelijke individuele observaties | [Datafitness](DATA-FITNESS.md), broncontracten |
| 2. Kun je P95 voertuigwachttijd bepalen? | Niet uit batchgemiddelden/tijdstippen; individuele events en betrouwbare linkage ontbreken | Geen percentielen van daggemiddelden als voertuig-P95 verkopen |
| 3. Waarom deze denominatoren? | Arrivalunits voor punctualiteit/delay; gematchte units voor dwell; slotdagen voor occupancy | Reken de fixture uit: dwell 4,5 uur, dekking 80% |
| 4. Waarom niet gemiddelden middelen? | Kleine en grote batches/dagen krijgen dan hetzelfde gewicht; het estimand verandert | [Handberekening](../fixtures/hand-calculated.json) |
| 5. Wat maakt een duplicaat anders dan een correctie? | Zelfde key/versie/hash is replay; hogere versie is update; dezelfde versie met andere inhoud is conflict | `events`, `revisions`, `audit`, `quarantine` |
| 6. Hoe behandel je teruggedateerde correcties? | Versie wint; watermark is monitoring en geen uitsluitfilter. Bronbestanden worden volledig gelezen | [Pipeline](PIPELINE.md), property tests |
| 7. Is dit echt incrementeel? | Writes/upserts wel; source reading en native snapshotrefresh niet als CDC/incremental partition pipeline | Noem beide niveaus expliciet |
| 8. Wat is atomair? | Events, revisionidentiteiten, materialized facts en watermarks; failed run apart vastgelegd | Geïnjecteerde fout laat vooraf gecommitteerde toestand intact |
| 9. Wat doet de publication gate? | Nul verschil, minimaal 99% departure coverage, maximaal 0,1% afkeur; slagen kan met waarschuwingen | Bij 99,9% dekkingseis blokkeert de volledige demo |
| 10. Waar komen 97/85/35%-doelen vandaan? | Oefenbeleid, geen bewezen industriestandaard. Operations/finance moeten echte doelen onderbouwen | 2.187 gewicht-/targetcombinaties, geen optimaliteitsclaim |

## Senior: verklaringen, investeringen en pilot

| Vraag | Wat een goed antwoord uitlegt | Controleerbaar bewijs |
|---|---|---|
| 11. Is personeel de oorzaak van minder vertraging? | Personeel kan reageren op volume/congestie; observationele associatie en synthetische generator identificeren geen behandelingseffect | Alternatieve Q4-specificaties; staffing toevoegen kan holdout verslechteren |
| 12. Wat bewijst de Q4-holdout niet? | Q4 bevat geen onderhoudsincident; predictive fit valideert de incidentwerking niet onafhankelijk | [Uitdagingen](ASSUMPTION-CHALLENGES.md) |
| 13. Waarom resample je blokken? | Gedeelde dagen/weken zijn afhankelijk; losse units resamplen geeft schijnprecisie | Week-bootstrap voor regressie, gekoppelde dagen voor pilot |
| 14. Is P10–P90 een 80%-betrouwbaarheidsinterval? | Nee: percentielen van fictieve inputtrekkingen, geen gekalibreerde statistische dekking | Oorspronkelijke Monte Carlo versus sensitivitygrid |
| 15. Wanneer is dispatch onverstandig? | Onder break-even, onbruikbare tijdwinst, onhaalbare uitvoering of onbetaalbare jaar-één-kasstroom | Bij EUR45/h: ongeveer 2,73% jaarlijkse, 4,85% jaar-één-fractie; gekozen centrale reductie |
| 16. Waarom telt benutbare fractie? | Vrijgekomen wachttijd moet werkelijk economisch inzetbaar zijn; niet elke voertuigwachtuur bespaart personeel | Verander 10% naar 0%: alle opties negatief, geen implementatie |
| 17. Wat als tijdwinst en kosten samenhangen? | Zelfde theoretische marginals kunnen bij andere dependence een andere netverdeling geven | 600 paired draws; coupling is een scenario, geen geschatte operationele relatie |
| 18. Wat als vooral slechte vertrekregistraties ontbreken? | Matched-only means kunnen te gunstig worden. Arrivaldelay blijft uit alle arrivals berekenbaar; ontbrekende dwell blijft onbekend | Selectieve-loss-simulatie en expliciete bounds |
| 19. Is de terminalrangorde objectief? | Afhankelijk van doelen, gewichten en aggregatie. Antwerpen blijft eerste binnen het grid; tweede/derde wisselen | Geen rangstabiliteit buiten het onderzochte grid claimen |
| 20. Is een significante pilot genoeg? | Scheid nul uitsluiten, minimaal nuttige verbetering, positief benutbaar net en guardrails | Precieze 1,5 minuut kan nuttigheidsgrens missen; 6 minuten met 1% usability kan verlies geven |
| 21. Waarom kan DiD afwijken van de geïnjecteerde -6? | Toeval in gesimuleerde steekproef plus estimator/ontwerp; geobserveerd circa -7,06 is geen echte prestatie | Bootstrapinterval en generatorparameters apart tonen |
| 22. Wat veranderen spillover/carryover? | Controlegroep wordt beïnvloed of eerdere behandeling werkt door; persistent cluster assignment kan nodig zijn | Echt ontwerp vereist operationele kennis en haalbaarheid |

## Senior: beheer, zekerheid en bewijs

| Vraag | Wat een goed antwoord uitlegt | Controleerbaar bewijs |
|---|---|---|
| 23. Wat bij publicatie gevolgd door foutieve verificatie? | Complete backup herstellen, originele modelbinding herstellen en read-back verifiëren; release blijft mislukt | Live geïsoleerde rollbackproef; productie niet gewijzigd |
| 24. Mag je create na een timeout herhalen? | Nee, server kan al gecreëerd hebben. Durable intent blokkeert een tweede create; inventory reconciliëren | Publishertests; geen distributed exactly-once claim |
| 25. Kan een failed refresh toch ‘fresh’ heten? | Last verified state blijft behouden; de ingestieklok schuift niet op door falen. Laatste failure en freshness apart inspecteren | Native-refreshtests voor auth, 429, time-outs, verkeerde totals/binding |
| 26. Zijn de RLS-rollen bewezen veilig? | Rollen bestaan; owner-roster en owner-interacties zijn apart bewezen. Viewerhandhaving blijft license-blocked | [Controlestatus](CONTROL-STATUS.md); eigenaarstest is geen viewer-RLS-test |
| 27. Wat bewijst de artifact-audit? | Versie/headlineconsistency, native totals, inventories en hashidentiteit; geen OCR van alle pixels of economische validiteit | Mutatietests: gewijzigde KPI/JSON/screenshot worden afgekeurd |
| 28. Wat bewijst hoge coverage niet? | Dat alle assertions juist zijn, iedere storing getest is of de bedrijfsvraag klopt | Scope en branches expliciet; kijk naar meaningful failure tests |
| 29. Kan een reviewer dit zelf installeren? | Nieuw git-archief, nieuwe locked omgeving, tests/demo/reportvalidatie zonder cloudcredentials | Schone-checkout-CI; downloadcache mag blijven bestaan |
| 30. Wat is de eerste productie-investering? | Afhankelijk van echte context: broncontracten, rechten, monitoring, eigenaarschap, herstel, retention en pilotontwerp beoordelen | Geen betaalde capacity of extra rechten als automatisch juiste oplossing voorstellen |

## Korte beoordelingsrubric

- **Nog onzeker:** noemt tools/termen, maar kan teller/noemer, foutpad of bewijs niet aanwijzen.
- **Werkbaar begrip:** legt de berekening en tradeoff uit, vindt de code en voert een lokale wijziging uit.
- **Sterk analytisch oordeel:** probeert de conclusie te weerleggen, onderscheidt aannames van bewijs,
  benoemt operationele gevolgen en begrenst wat de data toelaten.

Dit is een gespreksrubric, geen junior/medior/senior-certificering. Professionele senioriteit
vereist ook zelfstandig oordeel, samenwerken, verantwoordelijkheid en resultaten in echte context.
