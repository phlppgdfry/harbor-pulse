/* Capture genuine Power BI rendered pages in an isolated headless CLI session.
 * CLI token stays in memory. No user browser profile, cookies, or tenant changes.
 */
const fs=require('fs'),path=require('path'),http=require('http'),cp=require('child_process');
const root=path.resolve(__dirname,'..');
(async()=>{
 const {chromium}=require(process.env.HARBOR_PLAYWRIGHT_MODULE||'playwright');
 const launcher=fs.realpathSync(cp.execFileSync('which',['fab'],{encoding:'utf8'}).trim());
 const python=process.env.HARBOR_FAB_PYTHON||fs.readFileSync(launcher,'utf8').split('\n')[0].replace(/^#!/,'');
 const tokenCode='import contextlib,io\nfrom fabric_cli.core.fab_auth import FabAuth\nwith contextlib.redirect_stdout(io.StringIO()):\n token=FabAuth().get_access_token(["https://analysis.windows.net/powerbi/api/.default"],interactive_renew=False)\nif not token: raise SystemExit("CLI token unavailable")\nprint(token)';
 let token=cp.execFileSync(python,['-c',tokenCode],{encoding:'utf8',stdio:['ignore','pipe','pipe']}).trim();
 const report=JSON.parse(fs.readFileSync(process.env.HARBOR_CAPTURE_CONFIG||path.join(root,'build/report-embed.private.json'))).text;
 if(process.env.HARBOR_EMBED_TOKEN_FILE)token=JSON.parse(fs.readFileSync(process.env.HARBOR_EMBED_TOKEN_FILE)).text.token;
 const server=http.createServer((req,res)=>{res.setHeader('Content-Type','text/html');res.end('<!doctype html><html><head><meta charset="utf-8"><title>Private Power BI CLI capture</title><style>html,body,#report{margin:0;width:100%;height:100%;overflow:hidden;background:#fff}</style></head><body><div id="report"></div></body></html>')});
 await new Promise(resolve=>server.listen(0,'127.0.0.1',resolve));
 const browser=await chromium.launch({headless:true,executablePath:process.env.HARBOR_CHROME||'/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'});
 try{
  const page=await browser.newPage({viewport:{width:1680,height:1050},deviceScaleFactor:1});
  await page.goto(`http://127.0.0.1:${server.address().port}`);
  await page.addScriptTag({url:'https://cdn.jsdelivr.net/npm/powerbi-client@2.23.1/dist/powerbi.min.js'});
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
   await page.evaluate(async()=>{window.captureState.rendered=false;await window.report.setPage('b48bf8ced055e9f97bbc');await window.report.setFilters([{"$schema":"http://powerbi.com/product/schema#basic",target:{table:'DimTerminal',column:'Terminal'},operator:'In',values:['Antwerpen'],filterType:1},{"$schema":"http://powerbi.com/product/schema#basic",target:{table:'DimDate',column:'Maand'},operator:'In',values:['2026-04'],filterType:1}]);});
   await page.waitForFunction(()=>window.captureState.rendered,{timeout:60000});await page.waitForTimeout(2000);
   const folder=path.join(root,'powerbi/report/definition/pages/b48bf8ced055e9f97bbc/visuals');let visualName;
   for(const dir of fs.readdirSync(folder)){const v=JSON.parse(fs.readFileSync(path.join(folder,dir,'visual.json')));const p=v.visual.query?.queryState?.Data?.projections?.[0];if(p?.field?.Measure?.Property==='Voertuigen')visualName=v.name;}
   const csv=await page.evaluate(async(name)=>{const p=await window.report.getActivePage();const v=(await p.getVisuals()).find(v=>v.name===name);return (await v.exportData(window['powerbi-client'].models.ExportDataType.Summarized,20)).data},visualName);
   const expected=JSON.parse(fs.readFileSync(path.join(root,'build/release-v1/tables.json'))).FactOps.filter(f=>f.TerminalKey===2&&f.DateKey>=20260401&&f.DateKey<=20260430).reduce((n,f)=>n+f.Vehicles,0);
   const actual=Number(csv.trim().split(/\r?\n/).at(-1).replace(/[^0-9]/g,''));if(actual!==expected)throw Error('Rendered filter mismatch: '+actual+' vs '+expected);
   await page.locator('#report').screenshot({path:path.join(root,'docs/assets/powerbi/filtered-antwerpen-april.png')});
   fs.writeFileSync(path.join(root,'evidence/powerbi-interaction.json'),JSON.stringify({terminal:'Antwerpen',month:'2026-04',rendered_vehicles:actual,expected_source_vehicles:expected,passed:true,filters_persisted:false,user_browser_controlled:false},null,2));console.log('PASS rendered terminal/month filter',actual,'vehicles');
  }
  fs.writeFileSync(path.join(root,process.env.HARBOR_CAPTURE_RECEIPT||'evidence/powerbi-render.json'),JSON.stringify({method:'Microsoft Power BI SDK, authenticated CLI token, isolated headless Chromium',user_browser_controlled:false,tenant_settings_changed:false,viewport:{width:1680,height:1050},pages:receipts},null,2));
 }finally{await browser.close();server.close()}
})().catch(e=>{console.error('Capture failed:',e.message);process.exit(1)});
