"""Prepare a disposable shared-workspace model/report for real RLS tests."""
import base64,copy,json
from cloud_operations import api,completion,ROOT
workspace=json.loads((ROOT/'build/security-workspace.private.json').read_text());ws=workspace['id']
p=ROOT/'build/security-validation-model.private.json'
if p.exists():model=json.loads(p.read_text())
else:
 model=completion(api(f'workspaces/{ws}/semanticModels','post',{'displayName':'Harbor Pulse — Security Validation Model','definition':json.loads((ROOT/'build/native-model-definition.json').read_text())},'fabric'));p.write_text(json.dumps(model))
r=ROOT/'build/security-validation-report.private.json'
if r.exists():report=json.loads(r.read_text())
else:
 request=json.loads((ROOT/'build/update.json').read_text())
 part=next(p for p in request['definition']['parts'] if p['path']=='definition.pbir');payload=json.loads(base64.b64decode(part['payload']))
 payload['datasetReference']['byConnection']['connectionString']=f'Data Source="powerbi://api.powerbi.com/v1.0/myorg/{workspace["name"]}";initial catalog="{model["displayName"]}";integrated security=ClaimsToken;semanticmodelid={model["id"]}'
 part['payload']=base64.b64encode(json.dumps(payload).encode()).decode()
 report=completion(api(f'workspaces/{ws}/reports','post',{'displayName':'Harbor Pulse — RLS Validation','definition':request['definition']},'fabric'));r.write_text(json.dumps(report))
refresh=api(f'groups/{ws}/datasets/{model["id"]}/refreshes','post',{'notifyOption':'NoNotification'});(ROOT/'build/security-validation-refresh.private.json').write_text(json.dumps(refresh))
metadata=api(f'groups/{ws}/reports/{report["id"]}');(ROOT/'build/security-validation-embed.private.json').write_text(json.dumps(metadata))
for role in ['Terminal_Zeebrugge','Terminal_Antwerpen','Terminal_Gent']:
 d=api('GenerateToken','post',{'datasets':[{'id':model['id']}],'reports':[{'id':report['id']}],'identities':[{'username':'synthetic-rls-auditor','roles':[role],'datasets':[model['id']]}],'lifetimeInMinutes':30})
 (ROOT/'build'/('rls-token-'+role+'.private.json')).write_text(json.dumps(d));print(role,'token HTTP',d['status_code'],'issued' if isinstance(d.get('text'),dict) and 'token' in d['text'] else d.get('text'))
print('Isolated real RLS validation prepared')
