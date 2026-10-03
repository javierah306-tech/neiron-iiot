"use strict";
const $ = id => document.getElementById(id);
const zone = "America/Santiago";
const format = new Intl.DateTimeFormat("es-CL", {timeZone:zone, dateStyle:"short", timeStyle:"medium"});
const partsFormat = new Intl.DateTimeFormat("sv-SE", {timeZone:zone, year:"numeric",month:"2-digit",day:"2-digit",hour:"2-digit",minute:"2-digit",second:"2-digit",hourCycle:"h23"});
const states = {normal:["✓ Normal","good"],alarm:["△ Alarma","bad"],stopped:["■ Simulación detenida","neutral"],no_data:["○ Sin datos actuales","bad"],error:["! Error del sistema","bad"]};
const kinds = {temperature:"Temperatura elevada",vibration:"Vibración elevada",no_data:"Ausencia de datos"};
const scenarios = {normal:"operación normal",hot:"temperatura elevada",vibration:"vibración elevada",signal_loss:"pérdida de señal",recovery:"recuperación a condiciones normales"};
let activeView="monitor", state=null, lastSuccess=0, freshnessUntil=0, rulesLoaded=false, historyQuery="";
let chartRows=[], historyFilterEdited=false;
function date(value){return value ? format.format(new Date(value)) : "—";}
function localDate(value){const p=Object.fromEntries(partsFormat.formatToParts(new Date(value)).map(x=>[x.type,x.value]));return `${p.year}-${p.month}-${p.day}T${p.hour}:${p.minute}:${p.second}`;}
function toUTC(value){
  if(!/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}(:\d{2})?$/.test(value))throw Error("Completa una fecha y hora válidas.");
  const wanted=value.length===16?value+":00":value;
  const guess=Date.parse(wanted+"Z"), candidates=new Set();
  // Inferir los desplazamientos de la zona alrededor de la fecha, incluidos cambios de hora.
  for(let h=-36;h<=36;h+=6){const probe=guess+h*3600000;const offset=Date.parse(localDate(probe)+"Z")-probe;const candidate=guess-offset;if(localDate(candidate)===wanted)candidates.add(candidate);}
  if(candidates.size!==1)throw Error(candidates.size?"Hora ambigua por cambio de horario en Santiago; elige una hora fuera de ese cambio.":"Esa hora no existe en Santiago por cambio de horario; corrige la fecha.");
  return new Date([...candidates][0]).toISOString();
}
function node(tag, text, cls){const n=document.createElement(tag);if(text!==undefined)n.textContent=text;if(cls)n.className=cls;return n;}
function notify(text, error=false){$("message").textContent=text;$("message").className="message"+(error?" error":"");$("message").hidden=false;}
async function api(path, data){const ctrl=new AbortController(), timeout=setTimeout(()=>ctrl.abort(),4000);try{const r=await fetch(path,{signal:ctrl.signal,cache:"no-store",...(data===undefined?{}:{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(data)})});const payload=await r.json();if(!r.ok)throw Error(payload.error||"Solicitud rechazada.");return payload;}catch(e){if(e.name==="AbortError")throw Error("El servicio local no respondió a tiempo.");throw e;}finally{clearTimeout(timeout);}}
function clearCurrent(reason){$("temperature").textContent="—";$("vibration").textContent="—";$("freshness").textContent=reason;}
function renderStatus(s){
  state=s;lastSuccess=performance.now();
  document.querySelectorAll("[data-asset-name]").forEach(n=>n.textContent=s.asset.name);
  $("intervention-asset").value=s.asset.name;document.title="neiron · "+s.asset.name;
  const external=s.input_mode==="external";
  $("external-input").hidden=!external;$("external-simulator-link").href="http://127.0.0.1:"+(s.simulator_port||8766);$("internal-input").hidden=external;
  $("receiver-start").disabled=s.running;$("receiver-stop").disabled=!s.running;
  const remaining=s.current?Math.max(0,s.rules.no_data_s*1000-(Date.parse(s.server_time)-Date.parse(s.current.received_at))):0;
  freshnessUntil=lastSuccess+remaining;
  let [label,cls]=states[s.state]||states.error;if(external&&s.state==="stopped")label="■ Recepción suspendida";
  $("system-state").textContent=label;$("system-state").className="badge "+cls;
  $("last-received").textContent=s.last_received_at?date(s.last_received_at):"Sin datos guardados";
  if(s.current){$("temperature").textContent=s.current.temperature_c.toLocaleString("es-CL",{minimumFractionDigits:1,maximumFractionDigits:1});$("vibration").textContent=s.current.vibration_rms.toLocaleString("es-CL",{minimumFractionDigits:2,maximumFractionDigits:2});$("freshness").textContent="Recepción reciente · origen simulado / calidad sintética";}
  else clearCurrent(s.error||(s.running?"Esperando recepción válida. Las lecturas antiguas no son actuales.":(external?"Recepción suspendida. La fecha indicada corresponde al historial.":"Simulación detenida. La fecha indicada corresponde al historial.")));
  $("start").disabled=s.running;$("stop").disabled=!s.running;
  document.querySelectorAll("[data-scenario]").forEach(b=>{const selected=b.dataset.scenario===s.scenario;b.classList.toggle("selected",selected);b.setAttribute("aria-pressed",selected);});
  $("scenario-label").textContent="Escenario seleccionado: "+scenarios[s.scenario]+(s.running?" · en ejecución":" · simulación detenida");
  $("alarm-count").textContent=s.active_alarms.length;
  $("alarm-notice").hidden=!s.active_alarms.length;
  $("alarm-notice").textContent="△ Causas activas: "+s.active_alarms.map(a=>kinds[a.kind]+(a.acknowledged_at?" (reconocida)":" (sin reconocer)")).join(" · ")+". Consulta Alarmas para ver los eventos.";
  $("reception-events").replaceChildren(...s.reception_events.map(e=>{const n=node("div",undefined,"event-row");n.append(node("time",date(e.at)),node("span",e.code+" · "+e.detail));return n;}));
  if(!s.reception_events.length)$("reception-events").append(node("p","No hay eventos de recepción todavía.","small"));
  if(!rulesLoaded)fillRules(s.rules);
  chartRows=s.trend||[];drawCharts();
}
function fillRules(rules){for(const [k,v]of Object.entries(rules))$("rules-form").elements.namedItem(k).value=v;rulesLoaded=true;}
function drawChart(id,field,color,unit){
  const c=$(id),rect=c.getBoundingClientRect();if(rect.width<1)return;
  const ratio=window.devicePixelRatio||1;c.width=Math.round(rect.width*ratio);c.height=Math.round(rect.height*ratio);
  const x=c.getContext("2d");x.scale(ratio,ratio);const w=rect.width,h=rect.height,l=44,r=12,t=16,b=30;
  x.clearRect(0,0,w,h);x.font="10px Segoe UI";x.fillStyle="#7b8e99";
  if(!chartRows.length){x.textAlign="center";x.fillText("Inicia la simulación para construir el historial.",w/2,h/2);return;}
  const vals=chartRows.map(v=>v[field]);let low=Math.min(...vals),high=Math.max(...vals),padding=Math.max((high-low)*.15,field==="temperature_c"?1:.2);low=Math.max(0,low-padding);high+=padding;
  const first=Date.parse(chartRows[0].acquired_at),last=Date.parse(chartRows.at(-1).acquired_at),range=Math.max(1000,last-first);
  const px=v=>l+(Date.parse(v.acquired_at)-first)/range*(w-l-r),py=v=>t+(high-v[field])/(high-low)*(h-t-b);
  x.lineWidth=1;for(let i=0;i<4;i++){const y=t+i*(h-t-b)/3;x.strokeStyle="#edf2f4";x.beginPath();x.moveTo(l,y);x.lineTo(w-r,y);x.stroke();x.fillStyle="#7b8e99";x.textAlign="right";x.fillText((high-i*(high-low)/3).toFixed(1),l-8,y+3);}
  x.strokeStyle=color;x.lineWidth=2;x.beginPath();chartRows.forEach((v,i)=>{if(!i||Date.parse(v.acquired_at)-Date.parse(chartRows[i-1].acquired_at)>2500)x.moveTo(px(v),py(v));else x.lineTo(px(v),py(v));});x.stroke();
  const latest=chartRows.at(-1);x.beginPath();x.arc(px(latest),py(latest),3,0,2*Math.PI);x.fillStyle=color;x.fill();
  const tf=new Intl.DateTimeFormat("es-CL",{timeZone:zone,hour:"2-digit",minute:"2-digit",second:"2-digit"});x.fillStyle="#7b8e99";x.textAlign="left";x.fillText(tf.format(new Date(first)),l,h-8);x.textAlign="right";x.fillText(tf.format(new Date(last)),w-r,h-8);
  $(id+"-note").textContent=`Rango guardado: ${Math.min(...vals).toLocaleString("es-CL")}–${Math.max(...vals).toLocaleString("es-CL")} ${unit} · ${chartRows.length} paquetes. Los huecos indican interrupciones.`;
}
function drawCharts(){drawChart("temperature-chart","temperature_c","#2b807b","°C");drawChart("vibration-chart","vibration_rms","#547897","m/s²");}
function makeHistoryQuery(){const from=toUTC($("history-from").value),to=toUTC($("history-to").value);if(from>to)throw Error("La fecha inicial debe ser anterior a la fecha final.");return new URLSearchParams({from,to}).toString();}
async function loadHistory(){const q=makeHistoryQuery(),data=await api("/api/history?"+q);historyQuery=q;$("history-summary").textContent=`${data.total} mediciones en el intervalo · ${data.rows.length} visibles · horarios de America/Santiago`;
  const rows=data.rows.map(v=>{const tr=node("tr");[date(v.acquired_at),date(v.received_at),v.temperature_c.toLocaleString("es-CL"),v.vibration_rms.toLocaleString("es-CL"),v.source==="simulated"?"Simulado / sintético":"Real / "+v.quality,v.sequence].forEach(cell=>tr.append(node("td",cell)));return tr;});
  if(!rows.length){const tr=node("tr"),td=node("td","No hay mediciones en este intervalo. Ajusta las fechas o inicia la simulación.","empty");td.colSpan=6;tr.append(td);rows.push(tr);}$("history-rows").replaceChildren(...rows);
}
async function loadAlarms(){const data=await api("/api/alarms");if(!rulesLoaded)fillRules(data.rules);
  const rows=data.rows.map(a=>{const div=node("article",undefined,"card record"),head=node("div",undefined,"record-head");head.append(node("h3",`#${a.id} · ${kinds[a.kind]}`),node("span",a.recovered_at?"✓ Recuperada":"△ Causa activa","badge "+(a.recovered_at?"good":"bad")));div.append(head,node("p","Inicio: "+date(a.started_at)+" · Recuperación: "+date(a.recovered_at)),node("p",`Valor al inicio: ${a.start_value??"—"} · Umbral ilustrativo: ${a.start_limit??"—"}${a.kind==="temperature"?" °C":a.kind==="vibration"?" m/s²":" s"}`,"small"));
    if(a.acknowledged_at)div.append(node("p","Reconocida: "+date(a.acknowledged_at)+" · "+a.acknowledged_by,"small"));else{const b=node("button","Reconocer alarma");b.addEventListener("click",async()=>{b.disabled=true;try{await api(`/api/alarms/${a.id}/ack`,{author:$("ack-author").value});notify("Reconocimiento registrado. La causa y el historial se conservan.");await loadAlarms();}catch(e){notify(e.message,true);}finally{b.disabled=false;}});div.append(b);}return div;});
  $("alarm-list").replaceChildren(...(rows.length?rows:[node("p","No hay alarmas registradas. Prueba temperatura elevada, vibración elevada o pérdida de señal.","card small")]));
  const labels={started:"Inicio",recovered:"Recuperación",acknowledged:"Reconocimiento"};$("alarm-events").replaceChildren(...data.events.map(e=>{const n=node("div",undefined,"event-row");n.append(node("time",date(e.at)),node("span",`#${e.alarm_id} · ${labels[e.event]} · ${e.detail}`));return n;}));if(!data.events.length)$("alarm-events").append(node("p","Todavía no hay eventos.","small"));
}
async function loadInterventions(){const data=await api("/api/interventions");const rows=data.rows.map(v=>{const n=node("article",undefined,"card record"),head=node("div",undefined,"record-head");head.append(node("h3",`#${v.id} · ${v.work_type}`),node("span",state?.asset.name||"Activo","record-meta"));n.append(head,node("p","Intervención: "+date(v.intervention_at)+" · Autor: "+v.author),node("p","Registrada: "+date(v.recorded_at),"record-meta"),node("p",v.observations,"notes"));return n;});$("intervention-list").replaceChildren(...(rows.length?rows:[node("p","Todavía no hay intervenciones. Completa el formulario para guardar la primera.","card small")]));}
async function switchView(view){if(!["monitor","history","alarms","interventions"].includes(view))view="monitor";activeView=view;document.querySelectorAll(".view").forEach(s=>s.hidden=s.id!==view);document.querySelectorAll("[data-view]").forEach(b=>{b.classList.toggle("selected",b.dataset.view===view);b.setAttribute("aria-current",b.dataset.view===view?"page":"false");});$("page-title").textContent={monitor:"Monitoreo",history:"Historial",alarms:"Alarmas",interventions:"Intervenciones"}[view];location.hash=view;try{if(view==="history"){if(!historyFilterEdited)$("history-to").value=localDate(Date.now());await loadHistory();}if(view==="alarms")await loadAlarms();if(view==="interventions")await loadInterventions();if(view==="monitor")drawCharts();}catch(e){notify(e.message,true);}}
async function control(action){try{renderStatus(await api("/api/simulation",{action}));$("connection-error").hidden=true;}catch(e){notify(e.message,true);}}
$("receiver-start").addEventListener("click",()=>control("start"));$("receiver-stop").addEventListener("click",()=>control("stop"));
$("start").addEventListener("click",()=>control("start"));$("stop").addEventListener("click",()=>control("stop"));document.querySelectorAll("[data-scenario]").forEach(b=>b.addEventListener("click",()=>control(b.dataset.scenario)));document.querySelectorAll("[data-view]").forEach(b=>b.addEventListener("click",()=>switchView(b.dataset.view)));
for(const id of ["history-from","history-to"])$(id).addEventListener("input",()=>{historyFilterEdited=true;});
$("history-filter").addEventListener("submit",async e=>{e.preventDefault();try{await loadHistory();}catch(err){notify(err.message,true);}});
$("export").addEventListener("click",()=>{try{historyQuery=makeHistoryQuery();window.location.assign("/api/export.csv?"+historyQuery);}catch(e){notify(e.message,true);}});
$("rules-form").addEventListener("submit",async e=>{e.preventDefault();const raw=Object.fromEntries([...new FormData(e.target)].map(([k,v])=>[k,Number(v)]));try{await api("/api/rules",raw);notify("Umbrales ilustrativos guardados. Se reinicia la duración pendiente; las alarmas existentes se conservan.");}catch(err){notify(err.message,true);}});
$("intervention-form").addEventListener("submit",async e=>{e.preventDefault();const b=e.target.querySelector("button[type=submit]");b.disabled=true;try{const data=Object.fromEntries(new FormData(e.target));if(!state)throw Error("Espera la conexión al servicio antes de guardar.");data.asset_id=state.asset.id;data.intervention_at=toUTC($("intervention-at").value);const result=await api("/api/interventions",data);notify(`Intervención #${result.id} guardada.`);e.target.reset();$("intervention-at").value=localDate(Date.now());await loadInterventions();}catch(err){notify(err.message,true);}finally{b.disabled=false;}});
const now=Date.now();$("history-from").value=localDate(now-24*3600000);$("history-to").value=localDate(now);$("intervention-at").value=localDate(now);
window.addEventListener("resize",drawCharts);window.addEventListener("hashchange",()=>{if(location.hash.slice(1)!==activeView)switchView(location.hash.slice(1));});
let alarmPoll=0;
async function poll(){try{renderStatus(await api("/api/status"));$("connection-error").hidden=true;if(activeView==="alarms"&&++alarmPoll%2===0)await loadAlarms();}catch(e){$("connection-error").hidden=false;clearCurrent("Sin recepción verificable: conexión local interrumpida.");$("system-state").textContent="! Servicio no disponible";$("system-state").className="badge bad";}finally{setTimeout(poll,1000);}}
setInterval(()=>{if(state?.current&&performance.now()>=freshnessUntil){clearCurrent("La lectura venció. Esperando un paquete válido.");$("system-state").textContent="○ Sin datos actuales";$("system-state").className="badge bad";}},200);
switchView(location.hash.slice(1)||"monitor");poll();
