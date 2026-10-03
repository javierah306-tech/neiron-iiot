// Verificación opcional de desarrollo. La aplicación no depende de Node ni Playwright.
const {chromium}=require(process.env.NEIRON_PLAYWRIGHT_MODULE||"playwright");
const {spawn}=require("node:child_process");
const fs=require("node:fs"),path=require("node:path"),os=require("node:os"),net=require("node:net"),assert=require("node:assert/strict");
const root=path.resolve(__dirname,".."),artifacts=path.join(root,".test-artifacts");
fs.mkdirSync(artifacts,{recursive:true});
const temp=fs.mkdtempSync(path.join(os.tmpdir(),"neiron-browser-"));
const report={started:new Date().toISOString(),checks:[],requests:[],temporaryDatabase:temp};
let server,browser,url;
const delay=ms=>new Promise(r=>setTimeout(r,ms));
async function until(fn,description,timeout=12000){const start=Date.now();while(Date.now()-start<timeout){try{if(await fn())return;}catch{}await delay(200);}throw Error("Tiempo agotado: "+description);}
async function availablePort(){const s=net.createServer();await new Promise(r=>s.listen(0,"127.0.0.1",r));const p=s.address().port;await new Promise(r=>s.close(r));return p;}
async function start(port){url=`http://127.0.0.1:${port}`;server=spawn(path.join(root,".venv","Scripts","python.exe"),["-m","neiron.server","--port",String(port),"--data-dir",temp],{cwd:root,windowsHide:true,stdio:["ignore","pipe","pipe"]});server.stdout.on("data",d=>fs.appendFileSync(path.join(artifacts,"server-test.log"),d));server.stderr.on("data",d=>fs.appendFileSync(path.join(artifacts,"server-test.log"),d));await until(async()=>{const r=await fetch(url+"/api/status");return r.ok;},"inicio local");}
async function stop(){if(server&&server.exitCode===null){const exit=new Promise(r=>server.once("exit",r));server.kill();await exit;}server=null;}
async function status(){return (await fetch(url+"/api/status")).json();}
function check(text){report.checks.push(text);console.log("OK:",text);}
(async()=>{
 try{
  const port=await availablePort();await start(port);
  browser=await chromium.launch({executablePath:"C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe",headless:true});
  const context=await browser.newContext({viewport:{width:1440,height:1000},acceptDownloads:true});
  const errors=[];context.on("page",p=>p.on("pageerror",e=>errors.push(e.message)));
  await context.route("**/*",async route=>{const requestURL=route.request().url();report.requests.push(requestURL);if(!requestURL.startsWith(url+"/"))await route.abort();else await route.continue();});
  const page=await context.newPage();await page.goto(url);await page.waitForSelector("#start:not([disabled])");
  assert.equal(await page.locator("#temperature").textContent(),"—");assert.equal(await page.locator(".simulation-label").textContent(),"◇ DATOS SIMULADOS");check("Inicio en loopback, marca de simulación y estado detenido sin lectura antigua");
  await page.click("#start");await until(async()=>await page.locator("#temperature").textContent()!=="—","datos en monitoreo");
  assert.equal((await status()).source,"simulated");assert.equal((await status()).ai,"disabled");
  await page.screenshot({path:path.join(artifacts,"01-monitoreo.png"),fullPage:true});check("Recepción cada segundo y visualización de ambos indicadores y gráficos");
  await page.click('[data-scenario="normal"]');assert.equal((await status()).scenario,"normal");
  await page.click('[data-scenario="hot"]');await until(async()=>(await status()).active_alarms.some(a=>a.kind==="temperature"),"alarma temperatura");
  await page.click('[data-view="alarms"]');await until(async()=>await page.locator("#alarm-list button").count()>0,"vista alarmas");
  await page.locator("#alarm-list button").first().click();await until(async()=>(await status()).active_alarms.some(a=>a.kind==="temperature"&&a.acknowledged_at),"reconocimiento sin borrar causa");
  await page.locator('[name="temperature_limit"]').fill("46");await page.click('#rules-form button[type="submit"]');await until(async()=>(await status()).rules.temperature_limit===46,"persistencia reglas");
  await page.screenshot({path:path.join(artifacts,"02-alarmas.png"),fullPage:true});check("Temperatura elevada, duración mínima, reconocimiento con causa activa y configuración de reglas");
  await page.click('[data-view="monitor"]');await page.click('[data-scenario="recovery"]');await until(async()=>!(await status()).active_alarms.some(a=>a.kind==="temperature"),"recuperación temperatura");
  await page.click('[data-scenario="vibration"]');await until(async()=>(await status()).active_alarms.some(a=>a.kind==="vibration"),"alarma vibración");
  await page.click('[data-scenario="recovery"]');await until(async()=>!(await status()).active_alarms.some(a=>a.kind==="vibration"),"recuperación vibración");check("Vibración elevada y recuperación normal con eventos conservados");
  await page.click('[data-scenario="signal_loss"]');await until(async()=>(await status()).state==="no_data","pérdida de señal");await until(async()=>await page.locator("#temperature").textContent()==="—","ocultar lectura vencida");
  assert.equal(await page.locator("#vibration").textContent(),"—");assert((await status()).active_alarms.some(a=>a.kind==="no_data"));
  await page.click('[data-scenario="recovery"]');await until(async()=>(await status()).state==="normal","recuperación señal");check("Ausencia de señal sin valores antiguos y recuperación al recibir un paquete válido");
  await page.click('[data-view="interventions"]');await page.locator('#intervention-form [name="author"]').fill("Prueba automática");await page.locator('#intervention-form [name="work_type"]').selectOption({label:"Inspección"});await page.locator('#intervention-form [name="observations"]').fill("Inspección del prototipo con datos simulados. No hay hardware conectado.");await page.click('#intervention-form button[type="submit"]');await until(async()=>await page.locator("#intervention-list .record").count()===1,"guardar intervención");
  await page.screenshot({path:path.join(artifacts,"03-intervenciones.png"),fullPage:true});check("Formulario separado, intervención guardada y dos fechas visibles en Santiago");
  await page.click('[data-view="history"]');await page.locator("#history-to").fill(await page.evaluate(()=>localDate(Date.now()+24*3600000)));await page.click('#history-filter button[type="submit"]');await until(async()=>await page.locator("#history-rows tr").count()>3,"historial filtrado");
  const downloadPromise=page.waitForEvent("download");await page.click("#export");const download=await downloadPromise;const csvPath=path.join(artifacts,"export-prueba.csv");await download.saveAs(csvPath);const csv=fs.readFileSync(csvPath,"utf8");assert(csv.includes("temperatura_superficial_C"));assert(csv.includes("simulated"));assert(csv.includes("synthetic_rms_acceleration"));
  await page.screenshot({path:path.join(artifacts,"04-historial.png"),fullPage:true});check("Filtro de fechas y descarga CSV con origen, unidades, método y UTC");
  const before=(await (await fetch(url+"/api/history?from=2020-01-01T00:00:00Z&to=2030-01-01T00:00:00Z")).json()).total;
  await page.click('[data-view="monitor"]');await page.click("#stop");await until(async()=>await page.locator("#temperature").textContent()==="—","detener simulación");await stop();
  await until(async()=>await page.locator("#connection-error").isVisible(),"desconexión del servicio");assert.equal(await page.locator("#temperature").textContent(),"—");check("Detener simulación y cerrar servicio elimina valores actuales en pantalla");
  await start(port);await page.reload();await page.waitForSelector("#start:not([disabled])");assert.equal(await page.locator("#temperature").textContent(),"—");
  const after=(await (await fetch(url+"/api/history?from=2020-01-01T00:00:00Z&to=2030-01-01T00:00:00Z")).json()).total;assert(after>=before);
  assert.equal((await (await fetch(url+"/api/interventions")).json()).rows.length,1);assert.equal((await status()).rules.temperature_limit,46);const alarms=await (await fetch(url+"/api/alarms")).json();assert(alarms.events.some(x=>x.event==="acknowledged"));assert(alarms.events.some(x=>x.event==="recovered"));
  check("Reinicio del proceso conserva mediciones, intervenciones, configuración y eventos; inicia detenido");
  await page.setViewportSize({width:390,height:844});await page.screenshot({path:path.join(artifacts,"05-monitoreo-movil.png"),fullPage:true});assert(await page.locator('[data-view="interventions"]').isVisible());assert(await page.evaluate(()=>document.documentElement.scrollWidth<=window.innerWidth));check("Diseño usable a 390 px sin desbordamiento horizontal");
  assert.deepEqual(errors,[]);assert(report.requests.every(r=>r.startsWith(url+"/")));check("Sin errores JavaScript ni solicitudes externas; IA desactivada");
  report.result="passed";
 }catch(error){report.result="failed";report.error=error.stack;console.error(error);process.exitCode=1;}
 finally{if(browser)await browser.close();await stop();report.finished=new Date().toISOString();fs.writeFileSync(path.join(artifacts,"browser-report.json"),JSON.stringify(report,null,2));const resolved=path.resolve(temp);assert(resolved.startsWith(path.resolve(os.tmpdir())+path.sep)&&path.basename(resolved).startsWith("neiron-browser-"));try{fs.rmSync(resolved,{recursive:true,force:true,maxRetries:3,retryDelay:200});}catch(e){report.cleanupWarning="No se pudo borrar la base temporal: "+e.message;fs.writeFileSync(path.join(artifacts,"browser-report.json"),JSON.stringify(report,null,2));console.log("Base temporal conservada:",resolved);}}
})();
