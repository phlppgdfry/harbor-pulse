"""Daily synthetic ingestion, guarded native refresh and a verifiable SLA.

Uses an existing model: no duplicate snapshots, tenant changes or user grants.
Source updates require an explicit model release when the content hash changes.
"""
import argparse,base64,datetime as dt,hashlib,json,pathlib,re,subprocess,sys,time
from cloud_operations import api,completion,successful,ROOT
sys.path.insert(0,str(ROOT))
from harbor_pulse.refresh_control import evaluate
p=argparse.ArgumentParser();p.add_argument('--model',required=True);p.add_argument('--report',required=True);p.add_argument('--workspace',required=True);p.add_argument('--baseline',type=pathlib.Path,default=ROOT/'build/run');a=p.parse_args()
now=dt.datetime.now(dt.timezone.utc);run=ROOT/'build/refresh-runs'/now.strftime('%Y%m%dT%H%M%S');run.mkdir(parents=True)
log={'started_at':now.isoformat(),'source_kind':'synthetic','model_mutations':False,'status':'running'}
state=ROOT/'build/refresh-state.private.json'
try:
 subprocess.run([sys.executable,'-m','harbor_pulse','demo','--output',str(run)],cwd=ROOT,check=True,stdout=subprocess.DEVNULL)
 summary=json.loads((run/'summary.json').read_text());gate=json.loads((run/'gate.json').read_text());tables=json.loads((run/'tables.json').read_text())
 if not all(gate['checks'].values()):raise RuntimeError('Publication gate failed')
 content=hashlib.sha256(json.dumps(tables,sort_keys=True,separators=(',',':')).encode()).hexdigest()
 baseline=json.loads((a.baseline/'tables.json').read_text())
 expected=hashlib.sha256(json.dumps(baseline,sort_keys=True,separators=(',',':')).encode()).hexdigest()
 if content!=expected:raise RuntimeError('Source content changed; explicit model release and revalidation required. Active model untouched.')
 native=completion(api(f'workspaces/{a.workspace}/semanticModels/{a.model}/getDefinition','post',None,'fabric'));embedded={}
 for part in native['definition']['parts']:
  if part['path'].startswith('definition/tables/'):
   expression=base64.b64decode(part['payload']).decode();match=re.search(r'Binary\.FromText\("([A-Za-z0-9+/=]+)"',expression)
   if not match:raise RuntimeError('Native source is not the approved embedded adapter')
   embedded[pathlib.Path(part['path']).stem]=json.loads(base64.b64decode(match.group(1)))
 native_hash=hashlib.sha256(json.dumps(embedded,sort_keys=True,separators=(',',':')).encode()).hexdigest()
 if native_hash!=content:raise RuntimeError('Native embedded source differs from newly validated ingestion; release required')
 log['native_source_hash_verified']=True
 accepted=api(f'datasets/{a.model}/refreshes','post',{'notifyOption':'NoNotification'});successful(accepted)
 deadline=time.monotonic()+300;refresh=None
 while time.monotonic()<deadline:
  history=successful(api(f'datasets/{a.model}/refreshes')).get('value',[])
  recent=[r for r in history if dt.datetime.fromisoformat(r['startTime'].replace('Z','+00:00'))>=now-dt.timedelta(seconds=5)]
  if recent:
   refresh=max(recent,key=lambda r:r['startTime'])
   if refresh['status']=='Completed':break
   if refresh['status']=='Failed':raise RuntimeError('Native refresh failed')
  time.sleep(5)
 else:raise RuntimeError('Native refresh timed out; inspect refresh history before retrying')
 d=successful(api(f'datasets/{a.model}/executeQueries','post',{'queries':[{'query':'EVALUATE ROW("Vehicles",[Voertuigen],"Coverage",[Vertrekdekking %],"Difference",[Bron fact verschil])'}]}))
 row=d['results'][0]['tables'][0]['rows'][0]
 if row['[Vehicles]']!=summary['vehicles'] or row['[Difference]']!=0 or row['[Coverage]']<.99:raise RuntimeError('Post-refresh cloud reconciliation failed')
 binding=successful(api('reports/'+a.report))['datasetId']
 if binding!=a.model:raise RuntimeError('Report binding drift')
 manifest={'ingested_at':dt.datetime.now(dt.timezone.utc).isoformat(),'source_kind':'synthetic','source_fact_difference':row['[Difference]'],'departure_coverage':row['[Coverage]'],'release_status':'verified','source_hash':content,'native_refresh_status':refresh['status'],'native_refresh_end':refresh['endTime']}
 policy=evaluate(manifest);assert policy['healthy'],policy
 log.update(status='passed',synthetic=True,source_fact_difference=0,vehicles=row['[Vehicles]'],departure_coverage=row['[Coverage]'],native_refresh_status=refresh['status'],native_refresh_start=refresh['startTime'],native_refresh_end=refresh['endTime'],source_hash=content,sla=policy)
 # Atomic state replaces only a successfully reconciled release state.
 temp=state.with_suffix('.tmp');temp.write_text(json.dumps(manifest,indent=2));temp.replace(state)
except Exception as e:
 log.update(status='failed',error=str(e));raise
finally:
 log['finished_at']=dt.datetime.now(dt.timezone.utc).isoformat();(ROOT/'build/native-refresh-last.private.json').write_text(json.dumps(log,indent=2));print(json.dumps(log,indent=2))
