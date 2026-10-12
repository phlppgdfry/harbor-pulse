/* Capture genuine Power BI rendered pages in an isolated headless CLI session.
 * CLI token stays in memory. No user browser profile, cookies, or tenant changes.
 */
const fs=require('fs'),path=require('path'),http=require('http'),cp=require('child_process');
const root=path.resolve(__dirname,'..');
(async()=>{
 const {chromium}=require(process.env.HARBOR_PLAYWRIGHT_MODULE||'@playwright/test');
 const launcher=fs.realpathSync(cp.execFileSync('which',['fab'],{encoding:'utf8'}).trim());
 const python=process.env.HARBOR_FAB_PYTHON||fs.readFileSync(launcher,'utf8').split('\n')[0].replace(/^#!/,'');
 const tokenCode='import contextlib,io\nfrom fabric_cli.core.fab_auth import FabAuth\nwith contextlib.redirect_stdout(io.StringIO()):\n token=FabAuth().get_access_token(["https://analysis.windows.net/powerbi/api/.default"],interactive_renew=False)\nif not token: raise SystemExit("CLI token unavailable")\nprint(token)';
 let token=cp.execFileSync(python,['-c',tokenCode],{encoding:'utf8',stdio:['ignore','pipe','pipe']}).trim();
 const report=JSON.parse(fs.readFileSync(process.env.HARBOR_CAPTURE_CONFIG||path.join(root,'build/report-embed.private.json'))).text;
 if(process.env.HARBOR_EMBED_TOKEN_FILE)token=JSON.parse(fs.readFileSync(process.env.HARBOR_EMBED_TOKEN_FILE)).text.token;
 const server=http.createServer((req,res)=>{res.setHeader('Content-Type','text/html');res.end('<!doctype html><html><head><meta charset="utf-8"><title>Private Power BI CLI capture</title><style>html,body,#report{margin:0;width:100%;height:100%;overflow:hidden;background:#fff}</style></head><body><div id="report"></div></body></html>')});
 await new Promise(resolve=>server.listen(0,'127.0.0.1',resolve));
 const browser=await chromium.launch({headless:true,...(process.env.HARBOR_CHROME?{executablePath:process.env.HARBOR_CHROME}:{})});
 try{
  const page=await browser.newPage({viewport:{width:1680,height:1050},deviceScaleFactor:1});
  await page.goto(`http://127.0.0.1:${server.address().port}`);
  await page.addScriptTag({path:require.resolve('powerbi-client/dist/powerbi.min.js')});
  await page.evaluate(({token,report,embedToken})=>{
   const models=window['powerbi-client'].models;window.captureState={loaded:false,rendered:false,errors:[]};
   window.report=window.powerbi.embed(document.getElementById('report'),{type:'report',id:report.id,embedUrl:report.embedUrl,accessToken:token,tokenType:embedToken?models.TokenType.Embed:models.TokenType.Aad,permissions:models.Permissions.Read,viewMode:models.ViewMode.View,settings:{panes:{filters:{visible:false},pageNavigation:{visible:false}},background:models.BackgroundType.Transparent}});
   window.report.on('loaded',()=>window.captureState.loaded=true);
   window.report.on('rendered',()=>window.captureState.rendered=true);
   window.report.on('error',event=>window.captureState.errors.push({message:event.detail.message,errorCode:event.detail.errorCode}));
  },{token,report,embedToken:!!process.env.HARBOR_EMBED_TOKEN_FILE});
  await page.waitForFunction(()=>window.captureState.rendered||window.captureState.errors.length,{timeout:150000});
  let state=await page.evaluate(()=>window.captureState);if(!state.rendered)throw Error(JSON.stringify(state));
  const pages=await page.evaluate(async()=> (await window.report.getPages()).map(p=>({name:p.name,displayName:p.displayName})));
  const out=path.join(root,process.env.HARBOR_CAPTURE_OUT||'docs/assets/powerbi');fs.mkdirSync(out,{recursive:true});const receipts=[];
  for(const item of (process.env.HARBOR_CAPTURE_FIRST_ONLY?pages.slice(0,1):pages)){
   await page.evaluate(async(name)=>{window.captureState.rendered=false;window.captureState.errors=[];await window.report.setPage(name);},item.name);
   await page.waitForFunction(()=>window.captureState.rendered,{timeout:90000});
   await page.waitForTimeout(2500);
   const visuals=await page.evaluate(async()=>{const p=await window.report.getActivePage();return (await p.getVisuals()).map(v=>({name:v.name,type:v.type,title:v.title}));});
   state=await page.evaluate(()=>window.captureState);
   if(process.env.HARBOR_CAPTURE_EXPORT){const data=await page.evaluate(async()=>{const p=await window.report.getActivePage();const v=(await p.getVisuals()).find(v=>v.type==='tableEx');return (await v.exportData(window['powerbi-client'].models.ExportDataType.Summarized,20)).data});fs.writeFileSync(path.join(out,'rows.private.csv'),data);}
   await page.locator('#report').screenshot({path:path.join(out,item.name+'.png')});
   receipts.push({...item,visuals:visuals.length,errors:state.errors,image:'docs/assets/powerbi/'+item.name+'.png'});
   console.log('Captured',item.displayName,visuals.length,'visuals',state.errors.length,'SDK errors');
  }
  if(process.env.HARBOR_CAPTURE_INTERACTIONS){
   const tables=JSON.parse(fs.readFileSync(path.join(root,process.env.HARBOR_RUN||'build/run','tables.json')));const facts=tables.FactOps;
   const basic=(table,column,values)=>({"$schema":"http://powerbi.com/product/schema#basic",target:{table,column},operator:'In',values,filterType:1});
   const checks=[];
   async function settle(action){await page.evaluate(()=>{window.captureState.rendered=false;window.captureState.errors=[]});await action();await page.waitForFunction(()=>window.captureState.rendered||window.captureState.errors.length,{timeout:90000});await page.waitForTimeout(1500);const errors=await page.evaluate(()=>window.captureState.errors);if(errors.length)throw Error(JSON.stringify(errors));}
   function visualFor(pageName,measure){const folder=path.join(root,'powerbi/report/definition/pages',pageName,'visuals');for(const dir of fs.readdirSync(folder)){const v=JSON.parse(fs.readFileSync(path.join(folder,dir,'visual.json')));if(['card','cardVisual'].includes(v.visual.visualType)&&Object.values(v.visual.query?.queryState||{}).some(r=>r.projections.some(p=>p.field?.Measure?.Property===measure)))return v.name;}throw Error('Card not found: '+measure);}
   async function exportNumber(name){const csv=await page.evaluate(async(name)=>{const p=await window.report.getActivePage();const v=(await p.getVisuals()).find(v=>v.name===name);return (await v.exportData(window['powerbi-client'].models.ExportDataType.Summarized,20)).data},name);fs.writeFileSync(path.join(root,'build/export-'+name+'.private.csv'),csv);const rows=csv.trim().split(/\r?\n/).slice(1);if(!rows.length)return null;const row=rows.at(-1);let cell=row.startsWith('"')?row.match(/^"((?:[^"]|"")*)"/)?.[1]:row.split(',')[0];if(!cell||/blank|blanco|leeg|n\/a/i.test(cell))return null;cell=cell.replace(/["\s€]/g,'').replace(/,/g,'');const value=Number(cell);if(!Number.isFinite(value))throw Error('Non-numeric export: '+JSON.stringify(row).slice(0,120));return value;}
   const management='b48bf8ced055e9f97bbc';
   await settle(()=>page.evaluate(name=>window.report.setPage(name),management));
   const card=visualFor(management,'Voertuigen');
   const cases=[{name:'empty-result',terminals:['No matching terminal'],keys:[],month:null},{name:'multiple-terminals',terminals:['Zeebrugge','Antwerpen'],keys:[1,2],month:null},...Array.from({length:12},(_,i)=>({name:'month-'+(i+1),month:`2026-${String(i+1).padStart(2,'0')}`,terminals:null,keys:[1,2,3]}))];
   for(const c of cases){const filters=[];if(c.terminals)filters.push(basic('DimTerminal','Terminal',c.terminals));if(c.month)filters.push(basic('DimDate','Maand',[c.month]));await settle(()=>page.evaluate(filters=>window.report.setFilters(filters),filters));const expected=facts.filter(f=>c.keys.includes(f.TerminalKey)&&(!c.month||String(f.DateKey).slice(0,6)===c.month.replace('-',''))).reduce((n,f)=>n+f.Vehicles,0);const actual=await exportNumber(card);if(expected===0?actual!==null&&actual!==0:actual!==expected)throw Error('Rendered interaction mismatch: '+c.name+' '+actual+' vs '+expected);checks.push({case:c.name,expected,actual,passed:true});console.log("Verified",c.name,actual);}
   await settle(()=>page.evaluate(()=>window.report.removeFilters()));
   const total=facts.reduce((n,f)=>n+f.Vehicles,0);const reset=await exportNumber(card);if(reset!==total)throw Error('Reset did not restore full total');checks.push({case:'reset-all',expected:total,actual:reset,passed:true});
   await settle(()=>page.evaluate(()=>window.report.setPage('hp_scenarios')));
   const savings=visualFor('hp_scenarios','Indicatieve besparing');
   for(const [minutes,value,fraction] of [[0,25,.05],[20,75,.15]]){
    for(const [table,column,selection] of [['ScenarioDelay','Minutes',minutes],['ScenarioCost','EUR',value],['ScenarioRealization','Fraction',fraction]]){
     const item=tables[table].find(r=>r[column]===selection);if(!item)throw Error('Scenario value absent: '+table+' '+selection);const filters=[basic(table,'Keuze',[item.Keuze])];
     await settle(()=>page.evaluate(async({table,filters})=>{const active=await window.report.getActivePage();const visuals=await active.getVisuals();for(const visual of visuals.filter(v=>v.type==='slicer')){const state=await visual.getSlicerState();if(state.targets?.some(t=>t.table===table)){await visual.setSlicerState({filters});return;}}throw Error('Slicer target not found: '+table)},{table,filters}));
    }
    const expected=facts.reduce((n,f)=>n+f.Vehicles*Math.min(f.DelayMinutes,minutes)/60,0)*value*fraction;const actual=await exportNumber(savings);if(actual===null||Math.abs(actual-expected)>.51+1e-9*Math.max(1,Math.abs(expected)))throw Error('Scenario export mismatch '+actual+' vs '+expected);checks.push({case:'scenario-'+minutes,expected,actual,passed:true});
   }
   await page.locator('#report').screenshot({path:path.join(out,'scenario-extreme.png')});
   fs.writeFileSync(path.join(root,'evidence/powerbi-expanded-interactions.json'),JSON.stringify({case_version:JSON.parse(fs.readFileSync(path.join(root,'contracts/case-release.json'))).case_version,checked_at:new Date().toISOString(),export_rounding:'Displayed whole-EUR values allowed 0.51 EUR rounding tolerance',status:'passed',scope:'Actual SDK filters, slicer states and rendered card exports; not mouse cross-highlighting or every visual',checks,filters_persisted:false,user_browser_controlled:false},null,2));
   console.log('PASS',checks.length,'actual report interactions');
  }
  fs.writeFileSync(path.join(root,process.env.HARBOR_CAPTURE_RECEIPT||'evidence/powerbi-render.json'),JSON.stringify({case_version:JSON.parse(fs.readFileSync(path.join(root,'contracts/case-release.json'))).case_version,checked_at:new Date().toISOString(),method:'Microsoft Power BI SDK, authenticated CLI token, isolated headless Chromium',user_browser_controlled:false,tenant_settings_changed:false,viewport:{width:1680,height:1050},pages:receipts},null,2));
 }finally{await browser.close();server.close()}
})().catch(e=>{console.error('Capture failed:',e.message);process.exit(1)});
