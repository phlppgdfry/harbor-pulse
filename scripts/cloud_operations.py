"""Authenticated API health checks and an isolated report rollback drill.

No credentials in source. Private response receipts stay in ignored build/.
Only the clone created by this invocation may be modified or deleted.
"""
import argparse,base64,copy,datetime as dt,hashlib,json,pathlib,subprocess,tempfile,time,uuid
ROOT=pathlib.Path(__file__).resolve().parents[1]

def api(endpoint,method='get',body=None,audience='powerbi'):
    ROOT.joinpath('build').mkdir(exist_ok=True);request=None
    cmd=['fab','api',endpoint,'-X',method,'-A',audience,'--output_format','json','--show_headers']
    if body is not None:
        with tempfile.NamedTemporaryFile(mode='w',suffix='.private.json',dir=ROOT/'build',delete=False) as f:
            json.dump(body,f);request=pathlib.Path(f.name)
        cmd+=['-i',str(request)]
    try:
        for attempt in range(3):
            response=subprocess.run(cmd,text=True,capture_output=True,timeout=150)
            if response.returncode:raise RuntimeError(response.stderr[-1000:])
            data=json.loads(response.stdout)['result']['data'][0]
            safe_retry=method=='get' or endpoint.endswith(('/getDefinition','/updateDefinition','/executeQueries'))
            if not safe_retry or data['status_code'] not in (429,500,502,503,504) or attempt==2:return data
            time.sleep(min(20,int(data.get('headers',{}).get('Retry-After',5))))
    finally:
        if request:request.unlink(missing_ok=True)

def successful(data):
    if data['status_code'] not in (200,201,202,204):raise RuntimeError(str(data['status_code'])+' '+json.dumps(data.get('text')))
    return data.get('text')

def completion(data):
    successful(data)
    if data['status_code']!=202:return data.get('text')
    operation=data['headers']['x-ms-operation-id']; deadline=time.monotonic()+240
    while time.monotonic()<deadline:
        time.sleep(5);state=successful(api('operations/'+operation,audience='fabric'))
        if state['status']=='Succeeded':
            result=api('operations/'+operation+'/result',audience='fabric')
            if result['status_code']==400 and isinstance(result.get('text'),dict) and result['text'].get('errorCode')=='OperationHasNoResult':return None
            return successful(result)
        if state['status']=='Failed':raise RuntimeError(str(state))
    raise RuntimeError('operation polling timed out; private receipts retain drill identity')

def definition(workspace,item):
    return completion(api(f'workspaces/{workspace}/items/{item}/getDefinition','post',{'format':'PBIR'},'fabric'))

def fingerprints(definition):
    return {p['path']:hashlib.sha256(base64.b64decode(p['payload'])).hexdigest() for p in definition['definition']['parts']}

def health(report,model,workspace):
    result=dict(checked_at=dt.datetime.now(dt.timezone.utc).isoformat(),browser_used=False,synthetic_model=True,checks={})
    for name,url in [('report','reports/'+report),('totals','datasets/'+model+'/executeQueries'),('refresh_history','datasets/'+model+'/refreshes'),('report_access','groups/'+workspace+'/reports/'+report+'/users')]:
        body={'queries':[{'query':'EVALUATE ROW("Vehicles",[Voertuigen],"Difference",[Bron fact verschil],"Coverage",[Vertrekdekking %])'}]} if name=='totals' else None
        data=api(url,'post' if body else 'get',body)
        (ROOT/'build'/f'health-{name}.private.json').write_text(json.dumps(data,indent=2))
        entry=dict(http_status=data['status_code'])
        if name=='report' and data['status_code']==200:entry['expected_model_binding']=data['text'].get('datasetId')==model
        if name=='refresh_history' and data['status_code']==200:
            entries=data['text'].get('value',[]);entry['entry_count']=len(entries);entry['failed_entries']=sum(r.get('status')=='Failed' for r in entries)
        if name=='totals' and data['status_code']==200:
            rows=data['text'].get('results',[{}])[0].get('tables',[{}])[0].get('rows',[])
            entry['totals']=rows;entry['reconciled']=bool(rows) and rows[0].get('[Difference]')==0 and rows[0].get('[Vehicles]')==366910 and rows[0].get('[Coverage]',0)>=.99
        if data['status_code']>=400:entry['error']=data.get('text',{}).get('error',{})
        result['checks'][name]=entry
    result['healthy']=result['checks']['report'].get('expected_model_binding',False) and result['checks']['totals'].get('reconciled',False)
    result['limits']=['Push snapshot health is checked; no conventional source refresh is performed.','Access API denial is a capability limit, not evidence that no other user has access.','Local scheduler depends on this computer and authenticated CLI.']
    return result

def drill(report,workspace):
    original=definition(workspace,report)
    created=completion(api(f'workspaces/{workspace}/items','post',{'displayName':'Harbor Pulse - isolated recovery drill '+uuid.uuid4().hex[:8],'type':'Report','definition':original['definition']},'fabric'));clone=created['id']
    (ROOT/'build/recovery-clone.private.json').write_text(json.dumps(created))
    result=dict(checked_at=dt.datetime.now(dt.timezone.utc).isoformat(),isolated_clone=True,production_report_modified=False,browser_used=False)
    # Clone report definitions may normalize references; use its own backup.
    backup=definition(workspace,clone);(ROOT/'build/recovery-backup.private.json').write_text(json.dumps(backup))
    changed=copy.deepcopy(backup);page=next(p for p in changed['definition']['parts'] if p['path'].endswith('/page.json'))
    payload=json.loads(base64.b64decode(page['payload']));payload['displayName']='RECOVERY DRILL - temporary'
    page['payload']=base64.b64encode(json.dumps(payload).encode()).decode()
    try:
        completion(api(f'workspaces/{workspace}/items/{clone}/updateDefinition','post',changed,'fabric'))
        edited=definition(workspace,clone);result['change_observed']=fingerprints(edited)!=fingerprints(backup)
        completion(api(f'workspaces/{workspace}/items/{clone}/updateDefinition','post',backup,'fabric'))
        restored=definition(workspace,clone);result['all_definition_parts_restored']=fingerprints(restored)==fingerprints(backup)
        result['production_unchanged']=fingerprints(definition(workspace,report))==fingerprints(original)
        restored_report=successful(api('reports/'+clone));result['binding_restored']=restored_report['datasetId']==successful(api('reports/'+report))['datasetId']
        result['passed']=all(result.get(k,False) for k in ['change_observed','all_definition_parts_restored','production_unchanged','binding_restored'])
    finally:
        result['temporary_clone_deleted']=api('reports/'+clone,'delete')['status_code'] in (200,204)
        (ROOT/'evidence/recovery-drill.json').write_text(json.dumps(result,indent=2))
    return result

def main():
    p=argparse.ArgumentParser();p.add_argument('command',choices=['health','drill']);p.add_argument('--report',required=True);p.add_argument('--workspace',required=True);p.add_argument('--model');args=p.parse_args()
    if args.command=='health' and not args.model:p.error('--model is required for health')
    result=health(args.report,args.model,args.workspace) if args.command=='health' else drill(args.report,args.workspace)
    target=ROOT/'build/cloud-health.private.json' if args.command=='health' else ROOT/'evidence/recovery-drill.json'
    target.write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
    if not result.get('healthy',result.get('passed',False)):raise SystemExit(1)
if __name__=='__main__':main()
