"""Append evidence and operating-model pages using the shared PBIR renderer."""

def add_pages(renderer):
    pages = renderer.pages
    save = renderer.save
    OUT = renderer.OUT
    obj = renderer.obj
    color = renderer.color
    PAPER = renderer.PAPER
    lit = renderer.lit
    text = renderer.text
    NAVY = renderer.NAVY
    cards = renderer.cards
    table = renderer.table
    d = renderer.d
    chart = renderer.chart
    m = renderer.m
    card = renderer.card

    extra_pages=[('hp_quality','08 · Datakwaliteit'),('hp_evidence','09 · Onderbouwing'),('hp_decision','10 · Investeringskeuze'),('hp_pilot','11 · Pilotmeting'),('hp_governance','12 · KPI & beheer')]
    pages.extend(extra_pages)
    for p,title in extra_pages:
     save(OUT/f'definition/pages/{p}/page.json',{'$schema':'https://developer.microsoft.com/json-schemas/fabric/item/report/definition/page/2.1.0/schema.json','name':p,'displayName':title,'displayOption':'FitToPage','width':1600,'height':1000,'objects':{'background':obj(color=color(PAPER),transparency=lit(0))}})
     text(p,'header',f'HARBOR PULSE  /  {title[5:].upper()}\nGecontroleerde verwerking · Onderbouwde beslissingen · Fictieve case',24,20,1552,80,19,NAVY,'#FFFFFF')
     text(p,'footer','BEWIJS EN BEHEER · Deze pagina gebruikt de volledige jaarsnapshot of afzonderlijke simulatie · Geen echte bedrijfsresultaten',24,950,1552,32,10,PAPER)

    p=extra_pages[0][0]
    cards(p,['Vertrekdekking %','Bron fact verschil','Datakwaliteit meldingen','Voertuigen'],120)
    text(p,'scope','PUBLICATIEGATE: reconciliatieverschil =0 · vertrekdekking ≥99% · afkeur ≤0,1% van inputregels. Waarschuwingen blijven zichtbaar; geen ontbrekende vertrekken als nulduur behandelen.',24,258,1552,70,13,'#E5F2F1')
    table(p,'rules','Gedetecteerde afwijkingen en afhandeling',[d('DQRule',k) for k in ['Regel','Aantal','Afhandeling','Ernst']],24,348,1552,245)
    table(p,'loads','Laadlog · initieel, replay en late correcties',[d('LoadRun',k) for k in ['Run','Status','Nieuw','Correcties','Duplicaten','Afgekeurd','FactRijen','BronVoertuigen','FactVoertuigen','Verschil']],24,613,1552,215)
    text(p,'explanation','INCREMENTEEL IN DE DATABASE\nBusiness key + versie bepalen de actuele bronrij. Identieke replay verandert niets. Auditlog bewaart oude en nieuwe hashes. De lokale bestandadapter scant snapshots volledig; watermarks zijn monitoringbewijs, geen riskante timestamp-only uitsluiting.',24,848,1552,80,12)

    p=extra_pages[1][0]
    text(p,'hypotheses','ALTERNATIEVE VERKLARINGEN\nOnderzoek onderhoud, volume/capaciteit, weekdag, terminalverschillen en personeelsuren per 100 voertuigen. Een descriptief OLS-model houdt deze factoren tegelijk in beeld. Coëfficiënten hebben verschillende eenheden en zijn geen feature-importance-ranking.',24,120,1552,125,14,'#E5F2F1')
    table(p,'coefficients','Descriptieve associaties met vertraging (minuten)',[d('Association','Factor'),d('Association','DelayAssociationMinutes')],24,265,760,325)
    chart(p,'weekday','clusteredColumnChart','Vertraging per weekdag',d('DimDate','Weekdag'),['Vertraging min'],804,265,772,325)
    chart(p,'maintenance','lineChart','Incidentdagen versus reguliere dagen',d('DimDate','Maand'),['Vertraging incident','Vertraging regulier'],24,610,970,318)
    text(p,'limitations','INTERPRETATIEGRENZEN\nDe synthetische data bevat bewust een incidentmechanisme. Personeelsuren hangen samen met gepland volume. Dit model levert associaties, geen causaal effect en geen gevalideerde operationele voorspelling. Een echte maatregel wordt apart in een pilot getoetst.',1014,610,562,318,14,'#FFF1DB')

    p=extra_pages[2][0]
    text(p,'scope','DRIE MAATREGELEN · VOLLEDIG JAAR, ALLE TERMINALS\n2.000 trekkingen per maatregel. Benutbare tijdwinst is 3–18% afhankelijk van de maatregel; tarief en tijdwinst zijn onzeker. Jaarlijkse netto waarde is na opex; de eenmalige investering is apart.',24,120,1552,110,14,'#E5F2F1')
    chart(p,'uncertainty','clusteredBarChart','Jaarlijkse netto waarde · P10, mediaan en P90',d('DecisionOption','Optie'),['Netto jaar P10','Netto jaar P50','Netto jaar P90'],24,250,970,340)
    table(p,'costs','Uitvoeringskosten en bandbreedte',[d('DecisionOption',k) for k in ['Optie','ImplementatieEUR','JaarlijkseOpexEUR','NettoP10','NettoP50','NettoP90','KansPositief']],24,610,970,318)
    text(p,'decision','VOORGESTELDE VOLGENDE STAP\nPilot dispatch/afspraakslots voordat geld wordt vastgelegd. Dit heeft onder de gekozen aannames de sterkste conservatieve netto waarde. Meer yardruimte is geen automatische volumegroei.\nP10/P90 zijn percentielen van aannames, geen statistische betrouwbaarheidsintervallen.',1014,250,562,340,14,'#FFF1DB')
    text(p,'payback','TERUGVERDIENTIJD\nAlleen berekend voor trekkingen met positieve jaarlijkse netto waarde. Een mediaan daarvan verbergt verlieskans: lees altijd ook KansPositief en het negatieve staartscenario. Jaar-één kasstroom trekt bovendien de implementatiekosten af.',1014,610,562,318,14)

    p=extra_pages[3][0]
    card(p,'effect','Pilot effect min',24,120,500)
    card(p,'low','Pilot interval laag',544,120,500)
    card(p,'high','Pilot interval hoog',1064,120,512)
    text(p,'design','GESIMULEERDE PROEFOPZET\n84 lane-dagsessies: 14 dagen vóór en 28 dagen na. Elke dag één gerandomiseerde interventie-lane en één controle-lane, met gelijk voertuigvolume. Difference-in-differences en een bootstrap op gepaarde dagen. Een negatief effect betekent minder vertraging.',24,258,1552,110,14,'#E5F2F1')
    chart(p,'beforeafter','clusteredColumnChart','Voor/na · interventie en controlegroep',d('PilotSummary','Groep'),['Pilot gemiddelde min'],24,388,970,320,d('PilotSummary','Periode'))
    table(p,'counts','Groepen en sessies',[d('PilotSummary',k) for k in ['Groep','Periode','Sessies','GemiddeldeVertraging']],24,728,970,200)
    text(p,'guardrails','GO/NO-GO VOOR EEN ECHTE PILOT\nVooraf vastleggen: minstens 3 minuten minder vertraging, geen slechtere veiligheid of punctualiteit, geen verschuiving van wachtrij naar andere lanes. Test personeelskosten en benutbaarheid.\nDe getoonde uitkomst is gesimuleerd, niet een gerealiseerde besparing.',1014,388,562,320,14,'#FFF1DB')
    text(p,'uncertainty','INTERVAL ≠ GARANTIE\nDe bootstrap kwantificeert variatie in deze simulatie. Een echte proef vereist voldoende onafhankelijke dagen en een controle op spillover tussen lanes.',1014,728,562,200,12)

    p=extra_pages[4][0]
    table(p,'contracts','KPI-contracten en fictieve roleigenaren',[d('KPIContract',k) for k in ['KPI','Definitie','Eigenaar','Doel','Controle']],24,120,1552,365)
    text(p,'permissions','TOEGANG EN VERANTWOORDELIJKHEID\nPersoonlijke Power BI-workspace; geen extra gebruikersrechten toegekend. Voor een gedeelde productieversie: viewers alleen lezen, builders apart, publicatie door een release-eigenaar. Drie terminalrollen staan in het native model. Admin-API toont alleen de eigenaar. Viewer-tests met effectieve rollen zijn nog licentiegeblokkeerd; geen handhavingstest als geslaagd claimen.',24,505,760,220,13,'#E5F2F1')
    text(p,'operations','MONITORING EN RELEASE\nSQLite-laadlog toont succes/falen, bronwatermarks, quarantaines en reconciliatie. GitHub CI reproduceert tests en demo wekelijks. Lokale dagelijkse ingestie + native refresh + cloudreconciliatie; uurmonitor bewaakt de 26-uurs SLA. Synthetische bron; Mac en CLI-aanmelding moeten beschikbaar blijven.',804,505,772,220,13)
    text(p,'recovery','HERSTELPROCEDURE\nVoor publicatie een rapportdefinitie back-uppen. Native importmodel eerst valideren: 66 queries, rollen en reconciliatie. Daarna rapport omkoppelen en vorige modellen archiveren. Bij fouten de vorige rapportdefinitie en modelkoppeling herstellen. Geen bronrecords of historische modellen automatisch verwijderen.',24,745,1552,183,14,'#FFF1DB')
