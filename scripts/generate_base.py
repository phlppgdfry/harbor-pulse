"""Deterministic synthetic daily star model and disconnected scenario controls."""
import datetime as dt, json, math, pathlib, random
ROOT=pathlib.Path(__file__).resolve().parents[1]/"build"
ROOT.mkdir(exist_ok=True)
def save(name,data): (ROOT/name).write_text(json.dumps(data,ensure_ascii=False,indent=2))
terminals=[dict(TerminalKey=1,Terminal='Zeebrugge',Regio='West-Vlaanderen',DailyCapacity=630,YardSlots=470,Rate=30),
           dict(TerminalKey=2,Terminal='Antwerpen',Regio='Antwerpen',DailyCapacity=500,YardSlots=390,Rate=32),
           dict(TerminalKey=3,Terminal='Gent',Regio='Oost-Vlaanderen',DailyCapacity=330,YardSlots=260,Rate=28)]
dates=[];facts=[];rng=random.Random(20261010)
for day_no in range(365):
    day=dt.date(2026,1,1)+dt.timedelta(days=day_no);key=int(day.strftime('%Y%m%d'))
    week=day.isocalendar();weekday=day.weekday()
    dates.append(dict(DateKey=key,Datum=day.isoformat()+'T00:00:00',Maand=day.strftime('%Y-%m'),Maandnummer=day.month,
                      Week=f'{week.year}-W{week.week:02d}',Weekdag=['Maandag','Dinsdag','Woensdag','Donderdag','Vrijdag','Zaterdag','Zondag'][weekday],Weekdagnummer=weekday+1))
    for t in terminals:
        plan=round(t['DailyCapacity']*(.72 if weekday<5 else .48)*(1+.065*math.sin((day.month-2)*math.pi/6)+.012*(day.month-1)))
        incident=t['TerminalKey']==2 and dt.date(2026,4,6)<=day<=dt.date(2026,4,19)
        vehicles=max(1,round(plan*(rng.uniform(.93,1.055))*(.82 if incident else 1)))
        delay=round(max(3,17.5-day.month*.38+(4.5 if weekday==0 else 0)+rng.uniform(-4,6)+(31 if incident else 0)),1)
        dwell=round(15.0+delay*.13+(7.5 if incident else 0)+rng.uniform(-.8,1.2),1)
        available=max(1,round(t['YardSlots']*(.62 if incident else 1)))
        occupied=min(available,round(vehicles*dwell/24))
        ontime=max(0,min(vehicles,round(vehicles*(.989-delay*.001-(.055 if incident else 0)+rng.uniform(-.004,.004)))))
        revenue=vehicles*t['Rate'];cost=round(revenue*(rng.uniform(.63,.68)+(.10 if incident else 0)))
        facts.append(dict(DateKey=key,TerminalKey=t['TerminalKey'],Vehicles=vehicles,PlannedVehicles=plan,OnTimeVehicles=ontime,
                          Revenue=revenue,BudgetRevenue=plan*t['Rate'],HandlingCost=cost,DelayMinutes=delay,DwellHours=dwell,
                          AvailableSlots=available,OccupiedSlots=occupied,HandlingCapacity=t['DailyCapacity'],IncidentFlag=incident,
                          Incident='Onderhoudsknelpunt' if incident else 'Regulier',CO2Kg=round(vehicles*(2.0+delay*.016),1)))
capacity=[dict(Pct=p,Keuze='Basis · 0%' if p==0 else f'+{int(p*100)}% ruimte') for p in [0,.05,.10,.15,.20,.25]]
delay=[dict(Minutes=m,Keuze='Basis · 0 min' if m==0 else f'{m} min minder') for m in [0,5,10,15,20]]
rate=[dict(EUR=r,Keuze=f'€{r} per wachtuur') for r in [25,35,45,60,75]]
rows={'DimDate':dates,'DimTerminal':terminals,'FactOps':facts,'ScenarioCapacity':capacity,'ScenarioDelay':delay,'ScenarioCost':rate}
currency='€ #,0;€ -#,0';percent='0.0%';delta='+0.0%;-0.0%;0.0%'
measures=[
 ('Voertuigen','SUM(FactOps[Vehicles])','#,0'),('Planning','SUM(FactOps[PlannedVehicles])','#,0'),
 ('Volumeverschil','[Voertuigen]-[Planning]','+#,0;-#,0;0'),('Volume vs planning','DIVIDE([Volumeverschil],[Planning])',delta),
 ('Omzet','SUM(FactOps[Revenue])',currency),('Omzetbudget','SUM(FactOps[BudgetRevenue])',currency),
 ('Kosten','SUM(FactOps[HandlingCost])',currency),('Brutomarge','[Omzet]-[Kosten]',currency),('Marge %','DIVIDE([Brutomarge],[Omzet])',percent),
 ('Omzet vs budget','DIVIDE([Omzet]-[Omzetbudget],[Omzetbudget])',delta),('Op tijd %','DIVIDE(SUM(FactOps[OnTimeVehicles]),[Voertuigen])',percent),
 ('Doel op tijd','IF([Voertuigen]>0,0.97)',percent),('Doel marge','IF([Voertuigen]>0,0.35)',percent),
 ('Punctualiteit afwijking','[Op tijd %]-[Doel op tijd]','+0.0 pp;-0.0 pp;0.0 pp'),
 ('Vertraging min','DIVIDE(SUMX(FactOps,FactOps[DelayMinutes]*FactOps[Vehicles]),[Voertuigen])','0.0'),
 ('Verblijftijd uur','DIVIDE(SUMX(FactOps,FactOps[DwellHours]*FactOps[Vehicles]),[Voertuigen])','0.0'),
 ('Bezetting %','DIVIDE(SUM(FactOps[OccupiedSlots]),SUM(FactOps[AvailableSlots]))',percent),
 ('Doel bezetting','IF([Voertuigen]>0,0.85)',percent),
 ('Omzet per voertuig','DIVIDE([Omzet],[Voertuigen])','€ 0.00'),('CO2 kg per voertuig','DIVIDE(SUM(FactOps[CO2Kg]),[Voertuigen])','0.00'),
 ('Terminaldagen','COUNTROWS(FactOps)','#,0'),
 ('Dagen boven bezettingsdoel','COUNTROWS(FILTER(FactOps,DIVIDE(FactOps[OccupiedSlots],FactOps[AvailableSlots])>0.85))','#,0'),
 ('Incidentdagen','COUNTROWS(FILTER(FactOps,FactOps[IncidentFlag]=TRUE()))','#,0'),
 ('Incidentvoertuigen','CALCULATE([Voertuigen],FactOps[IncidentFlag]=TRUE())','#,0'),
 ('Incident volumeverschil','CALCULATE([Volumeverschil],FactOps[IncidentFlag]=TRUE())','+#,0;-#,0;0'),
 ('Incident extra kosten','SUMX(FILTER(FactOps,FactOps[IncidentFlag]=TRUE()),FactOps[Revenue]*0.10)',currency),
 ('Vertraging regulier','CALCULATE([Vertraging min],FactOps[IncidentFlag]=FALSE())','0.0'),
 ('Vertraging incident','CALCULATE([Vertraging min],FactOps[IncidentFlag]=TRUE())','0.0'),
 ('Volume per terminaldag','DIVIDE([Voertuigen],[Terminaldagen])','#,0'),
 ('Status punctualiteit','IF([Voertuigen]=0,BLANK(),IF([Op tijd %]>=0.97,"Op doel",IF([Op tijd %]>=0.95,"Aandacht","Actie nodig")))',None),
 ('Status bezetting','IF([Voertuigen]=0,BLANK(),IF([Bezetting %]>0.85,"Actie nodig",IF([Bezetting %]>0.75,"Aandacht","Binnen doel")))',None),
 ('Status marge','IF([Voertuigen]=0,BLANK(),IF([Marge %]>=0.35,"Op doel","Onder doel"))',None),
 ('Aandachtscore','IF([Voertuigen]>0,MAX(0,0.97-[Op tijd %])*100+MAX(0,[Bezetting %]-0.85)*100+MAX(0,-[Volume vs planning])*100+MAX(0,0.35-[Marge %])*100)','0.0'),
 ('Prioriteit','IF([Voertuigen]>0,RANKX(ALLSELECTED(DimTerminal[Terminal]),[Aandachtscore],,DESC,Dense))','0'),
 ('Verbeterpunt','IF([Voertuigen]=0,BLANK(),IF([Op tijd %]<0.95,"Onderzoek wachtrij en verstoringen",IF([Bezetting %]>0.85,"Onderzoek beschikbare yardruimte",IF([Marge %]<0.35,"Onderzoek handlingkosten","Volg afwijking versus planning"))))',None),
 ('Extra capaciteit %','SELECTEDVALUE(ScenarioCapacity[Pct],0)',percent),
 ('Minder vertraging min','SELECTEDVALUE(ScenarioDelay[Minutes],0)','0'),
 ('Tarief wachtuur','SELECTEDVALUE(ScenarioCost[EUR],45)','€ 0'),
 ('Scenario bezetting %','DIVIDE([Bezetting %],1+[Extra capaciteit %])',percent),
 ('Bespaarde wachturen','SUMX(FactOps,FactOps[Vehicles]*MIN(FactOps[DelayMinutes],[Minder vertraging min])/60)','#,0.0'),
 ('Indicatieve besparing','[Bespaarde wachturen]*[Tarief wachtuur]',currency),
 ('Scenario vertraging min','DIVIDE(SUMX(FactOps,FactOps[Vehicles]*MAX(0,FactOps[DelayMinutes]-[Minder vertraging min])),[Voertuigen])','0.0'),
 ('Scenario voordeel per voertuig','DIVIDE([Indicatieve besparing],[Voertuigen])','€ 0.00'),
 ('Gekozen terminal','SELECTEDVALUE(DimTerminal[Terminal],"Selecteer één terminal voor detail")',None),
]
# Percentage-point deltas are multiplied by 100 before displaying the pp suffix.
measures=[(n,'([Op tijd %]-[Doel op tijd])*100' if n=='Punctualiteit afwijking' else e,f) for n,e,f in measures]
tables=[]
for name,data in rows.items():
    cols=[]
    for key,value in data[0].items():
        dtype='bool' if isinstance(value,bool) else 'string' if isinstance(value,str) else 'Int64' if isinstance(value,int) else 'Double'
        if key=='Datum':dtype='DateTime'
        if key=='Pct':dtype='Double'
        c={'name':key,'dataType':dtype}
        if key in ['Revenue','BudgetRevenue','HandlingCost','EUR']:c['formatString']=currency
        if key=='Pct':c['formatString']=percent
        if key=='Weekdag':c['sortByColumn']='Weekdagnummer'
        cols.append(c)
    table={'name':name,'columns':cols}
    if name=='FactOps':table['measures']=[dict(name=n,expression=e,**({'formatString':f} if f else {})) for n,e,f in measures]
    tables.append(table)
model={'name':'Harbor Pulse — Dagelijkse Intelligence 2026','defaultMode':'Push','tables':tables,
       'relationships':[dict(name='Date_to_Ops',fromTable='FactOps',fromColumn='DateKey',toTable='DimDate',toColumn='DateKey',crossFilteringBehavior='OneDirection'),
                        dict(name='Terminal_to_Ops',fromTable='FactOps',fromColumn='TerminalKey',toTable='DimTerminal',toColumn='TerminalKey',crossFilteringBehavior='OneDirection')]}
save('model-v3.json',model);save('rows-v3.json',rows)
vehicles=sum(r['Vehicles'] for r in facts);revenue=sum(r['Revenue'] for r in facts);cost=sum(r['HandlingCost'] for r in facts)
expected=dict(vehicles=vehicles,revenue=revenue,cost=cost,ontime=sum(r['OnTimeVehicles'] for r in facts)/vehicles,
              margin=(revenue-cost)/revenue,occupancy=sum(r['OccupiedSlots'] for r in facts)/sum(r['AvailableSlots'] for r in facts),
              delay=sum(r['Vehicles']*r['DelayMinutes'] for r in facts)/vehicles)
save('expected-v3.json',expected)
print(json.dumps(dict(tables=len(tables),relationships=2,measures=len(measures),dailyFacts=len(facts),totalRows=sum(map(len,rows.values())),**expected),indent=2))
