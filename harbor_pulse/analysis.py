"""Descriptive associations, bounded decision assumptions, and a simulated pilot."""
import math,random,statistics

def percentile(values,p):
    values=sorted(values);position=(len(values)-1)*p;low=int(position);high=min(low+1,len(values)-1)
    return values[low]+(values[high]-values[low])*(position-low)

def solve(matrix,vector):
    a=[list(row)+[value] for row,value in zip(matrix,vector)];n=len(a)
    for col in range(n):
        pivot=max(range(col,n),key=lambda row:abs(a[row][col]));a[col],a[pivot]=a[pivot],a[col]
        if abs(a[col][col])<1e-10:raise ValueError('singular_design')
        factor=a[col][col];a[col]=[v/factor for v in a[col]]
        for row in range(n):
            if row!=col:
                factor=a[row][col];a[row]=[v-factor*w for v,w in zip(a[row],a[col])]
    return [row[-1] for row in a]

def associations(facts):
    import datetime as dt
    # Terminal fixed effects plus operational candidates. This is an association
    # model over generated data, not a causal estimate or an operational forecast.
    names=['Intercept','Onderhoudsincident','Volume/capaciteit','Maandag','Personeelsuren per 100 voertuigen','Antwerpen','Gent']
    x=[];y=[]
    for f in facts:
        weekday=dt.datetime.strptime(str(f['DateKey']),'%Y%m%d').weekday()
        x.append([1,int(f['IncidentFlag']),f['Vehicles']/f['HandlingCapacity'],int(weekday==0),f['StaffHours']/f['Vehicles']*100,int(f['TerminalKey']==2),int(f['TerminalKey']==3)])
        y.append(f['DelayMinutes'])
    coefficients=solve([[sum(row[i]*row[j] for row in x) for j in range(7)] for i in range(7)],
                       [sum(row[i]*v for row,v in zip(x,y)) for i in range(7)])
    predicted=[sum(a*b for a,b in zip(row,coefficients)) for row in x]
    ss=sum((v-statistics.mean(y))**2 for v in y);residual=sum((v-p)**2 for v,p in zip(y,predicted))
    return dict(method='OLS descriptive association; terminal fixed effects; no causal interpretation',
                observations=len(facts),r_squared=1-residual/ss,
                coefficients=[dict(Factor=name,DelayAssociationMinutes=round(value,3)) for name,value in zip(names,coefficients)],
                limitations=['Synthetic data encodes the incident mechanism.','Staffing is correlated with planned volume.','No causal identification; no out-of-sample production validation.','Coefficient units differ; magnitudes are not feature importance.'])

def decisions(facts,draws=2000):
    rng=random.Random(505);vehicles=sum(f['Vehicles'] for f in facts)
    options=[('Dispatch en afspraakslots',35000,45000,(5,6,8),(.05,.10,.15)),
             ('Extra yardruimte +15%',90000,12000,(0,.7,2),(.03,.05,.08)),
             ('Extra inzet personeel',8000,131400,(3,4.5,6),(.08,.12,.18))]
    result=[]
    for name,investment,opex,time,realization in options:
        gross=[];net=[];payback=[]
        for _ in range(draws):
            reduction=rng.triangular(time[0],time[2],time[1]);fraction=rng.triangular(realization[0],realization[2],realization[1]);hourvalue=rng.triangular(25,60,45)
            hours=sum(f['Vehicles']*min(f['DelayMinutes'],reduction)/60 for f in facts)
            value=hours*hourvalue*fraction;annual=value-opex;gross.append(value);net.append(annual)
            if annual>0:payback.append(12*investment/annual)
        result.append(dict(Optie=name,ImplementatieEUR=investment,JaarlijkseOpexEUR=opex,
                           TijdwinstLaagMin=time[0],TijdwinstHoogMin=time[2],BenutbaarLaag=realization[0],BenutbaarHoog=realization[2],
                           BrutoP50=round(percentile(gross,.5)),NettoP10=round(percentile(net,.1)),NettoP50=round(percentile(net,.5)),NettoP90=round(percentile(net,.9)),
                           KansPositief=sum(n>0 for n in net)/draws,TerugverdientijdMaanden=round(percentile(payback,.5),1) if payback else None,
                           PaybackCondition='Median among positive annual net-benefit draws only'))
    return dict(draws=draws,scope='Full-year 2026, all terminals; annual benefit excluding one-off implementation cost',
                interpretation='Assumption-based Monte Carlo distribution; P10/P90 are not statistical confidence bounds',options=result,
                limitations=['Savings require real resource redeployment; waiting hours are not automatically payroll savings.','Parameter ranges are invented and independent.','Investment must be deducted separately for year-one cash flow.','No claimed improvement in throughput or on-time rate.'])

def pilot():
    rng=random.Random(606);rows=[]
    import datetime as dt
    for day in range(42):
        date=dt.date(2026,5,1)+dt.timedelta(days=day);post=day>=14;shared=rng.gauss(0,1.5)
        treatment_lane=rng.choice(['A','B'])
        for lane in ['A','B']:
            treatment=lane==treatment_lane
            delay=max(0,20+shared+rng.gauss(0,1.6)-(6 if post and treatment else 0))
            rows.append(dict(Dag=date.isoformat(),Lane=lane,Groep='Interventie' if treatment else 'Controle',Periode='Na' if post else 'Voor',VertragingMin=round(delay,2),Vehicles=180))
    means={(g,p):statistics.mean(r['VertragingMin'] for r in rows if r['Groep']==g and r['Periode']==p) for g in ['Interventie','Controle'] for p in ['Voor','Na']}
    did=(means['Interventie','Na']-means['Interventie','Voor'])-(means['Controle','Na']-means['Controle','Voor'])
    pre=[];post=[]
    for date in sorted({r['Dag'] for r in rows}):
        d=[r for r in rows if r['Dag']==date];difference=next(r['VertragingMin'] for r in d if r['Groep']=='Interventie')-next(r['VertragingMin'] for r in d if r['Groep']=='Controle')
        (pre if d[0]['Periode']=='Voor' else post).append(difference)
    bootstrap=[statistics.mean(rng.choices(post,k=len(post)))-statistics.mean(rng.choices(pre,k=len(pre))) for _ in range(2000)]
    summary=[dict(Groep=g,Periode=p,Sessies=sum(r['Groep']==g and r['Periode']==p for r in rows),GemiddeldeVertraging=mean) for (g,p),mean in means.items()]
    return dict(synthetic=True,design='Day-blocked randomized lane-day demonstration; 14 baseline days + 28 intervention days',
                known_generated_effect_minutes=-6,observed_did_minutes=did,paired_day_bootstrap_95=[percentile(bootstrap,.025),percentile(bootstrap,.975)],
                sessions=rows,summary=summary,limitations=['This is a simulated experiment, not evidence of an actual business effect.','Assumes no cross-lane spillover.','A real pilot needs pre-registration, agreed minimum effect and operational guardrails.'])
