"""Release an existing report definition with backup and structural read-back."""
import argparse,datetime as dt,json,pathlib
from cloud_operations import api,completion,definition,successful,ROOT
import base64
p=argparse.ArgumentParser();p.add_argument('--workspace',required=True);p.add_argument('--report',required=True);a=p.parse_args()
before=definition(a.workspace,a.report);(ROOT/'build/before-pixel-fix.private.json').write_text(json.dumps(before))
source=json.loads((ROOT/'build/update.json').read_text())
completion(api(f'workspaces/{a.workspace}/items/{a.report}/updateDefinition','post',source,'fabric'))
after=definition(a.workspace,a.report);(ROOT/'build/after-pixel-fix.private.json').write_text(json.dumps(after))
parts={part['path']:part for part in after['definition']['parts']}
matched=0
for part in source['definition']['parts']:
 if not part['path'].startswith('definition/pages/'):continue
 assert part['path'] in parts,part['path']
 assert json.loads(base64.b64decode(part['payload']))==json.loads(base64.b64decode(parts[part['path']]['payload'])),part['path']
 matched+=1
binding=successful(api('reports/'+a.report))['datasetId']
assert binding==json.loads((ROOT/'build/publication.private.json').read_text())['id']
result=dict(checked_at=dt.datetime.now(dt.timezone.utc).isoformat(),status='passed',matched_page_visual_files=matched,model_binding_preserved=True,backup_captured=True)
(ROOT/'evidence/pixel-fix-release.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
