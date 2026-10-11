"""Build an import model from a governed, embedded synthetic source snapshot.

No paid capacity or external datasource credentials. Native refresh reprocesses
versioned M-source data; real operational inputs still need an actual adapter.
"""
import argparse,base64,json,pathlib
ROOT=pathlib.Path(__file__).resolve().parents[1]

def build(push,tables):
    native={'name':'HarborPulseSecuredOperations2026','compatibilityLevel':1601,'model':{'culture':'en-US','defaultPowerBIDataSourceVersion':'powerBI_V3','defaultMode':'import','tables':[],'relationships':[],'roles':[]}}
    datatypes={'Int64':('int64','Int64.Type'),'Double':('double','type number'),'string':('string','type text'),'bool':('boolean','type logical'),'Boolean':('boolean','type logical'),'DateTime':('dateTime','type datetime')}
    for t in push['tables']:
        encoded=base64.b64encode(json.dumps(tables[t['name']],ensure_ascii=False).encode()).decode()
        columns=[];conversions=[]
        for c in t['columns']:
            dtype,mtype=datatypes[c['dataType']];column={**c,'dataType':dtype,'sourceColumn':c['name']};columns.append(column)
            conversions.append('{'+json.dumps(c['name'])+','+mtype+'}')
        expr='let Source=Json.Document(Binary.FromText("'+encoded+'",BinaryEncoding.Base64)), Records=Table.FromRecords(Source), Typed=Table.TransformColumnTypes(Records,{'+','.join(conversions)+'},"en-US") in Typed'
        native['model']['tables'].append({'name':t['name'],'columns':columns,'measures':t.get('measures',[]),'partitions':[{'name':t['name'],'mode':'import','source':{'type':'m','expression':expr}}]})
    for r in push['relationships']:
        native['model']['relationships'].append({**r,'crossFilteringBehavior':'oneDirection','fromCardinality':'many','toCardinality':'one','isActive':True})
    # Annual disconnected evidence contains all-terminal aggregates. Deny it
    # to terminal roles to prevent aggregate leakage across terminal boundaries.
    global_evidence=['DQRule','LoadRun','DecisionOption','PilotSummary','Association']
    for terminal,key in [('Zeebrugge',1),('Antwerpen',2),('Gent',3)]:
        permissions=[{'name':'DimTerminal','filterExpression':'[TerminalKey] = '+str(key)}]+[{'name':t,'filterExpression':'FALSE()'} for t in global_evidence]
        native['model']['roles'].append({'name':'Terminal_'+terminal,'modelPermission':'read','tablePermissions':permissions})
    return native

def definition(model):
    return {'parts':[{'path':name,'payload':base64.b64encode(json.dumps(value,ensure_ascii=False).encode()).decode(),'payloadType':'InlineBase64'} for name,value in [('model.bim',model),('definition.pbism',{'version':'1.0','settings':{}})]]}
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--run',type=pathlib.Path,default=ROOT/'build/run');a=p.parse_args()
    model=build(json.loads((a.run/'model.json').read_text()),json.loads((a.run/'tables.json').read_text()))
    (ROOT/'powerbi/native').mkdir(exist_ok=True);(ROOT/'powerbi/native/model.bim').write_text(json.dumps(model,ensure_ascii=False,indent=2))
    (ROOT/'build/native-model-definition.json').write_text(json.dumps(definition(model)))
    print('Built native model:',len(model['model']['tables']),'tables;',len(model['model']['roles']),'terminal roles; embedded synthetic snapshot')
