"use strict";
const $=id=>document.getElementById(id);
const browserEngine=new MotorBrowser.Engine();
let tickAt=performance.now();
setInterval(()=>{const now=performance.now();const dt=Math.min(1.5,(now-tickAt)/1000);tickAt=now;try{if(!document.hidden)browserEngine.tick(dt);}catch(error){toast(error.message,true);}},1000);
document.addEventListener("visibilitychange",()=>{tickAt=performance.now();if(document.hidden){browserEngine.current=null;}else{browserEngine.current=null;lastNewPacket=0;}});
let meta=null, snapshot=null, selected="de", lastSequence=null, lastNewPacket=0, pending={
}
, saveTimer=null, flushing=false, targetDirty=false;
const number=(v,d=1)=>Number.isFinite(v)?v.toLocaleString("es-CL",{
    minimumFractionDigits:d,maximumFractionDigits:d
}
):"—";
const dateFormat=new Intl.DateTimeFormat("es-CL",{
    timeZone:"America/Santiago",day:"2-digit",month:"2-digit",year:"numeric",hour:"2-digit",minute:"2-digit",second:"2-digit",hourCycle:"h23"
}
);
const formatDate=v=>v?dateFormat.format(new Date(v))+" · Santiago":"Esperando adquisición";
function toast(message,error=false){
    const el=$("toast");
    el.textContent=message;
    el.classList.toggle("error",error);
    el.hidden=false;
    clearTimeout(el.timer);
    el.timer=setTimeout(()=>el.hidden=true,5500);
}
async function api(path,payload){
    if(path==="/api/meta")return browserEngine.metadata();
    if(path==="/api/parameters")browserEngine.configure(payload);
    if(path==="/api/control")browserEngine.command(payload.action);
    return browserEngine.status();
}
async function action(path,payload){
    try{
        const data=await api(path,payload);
        snapshot=data;
        render();
        return data;
    }
    catch(error){
        toast(error.message,true);
        return null;
    }
}
function makeParameters(){
    const bearings=["lubrication_pct","contamination_pct","misalignment_mm","imbalance_gmm","looseness_pct","bearing_defect_pct"];
    for(const [key,item] of Object.entries(meta.parameters)){
        if(key==="time_scale")continue;
        const row=document.createElement("div");
        row.className="parameter-row";
        const top=document.createElement("div");
        top.className="parameter-label";
        const label=document.createElement("label");
        label.htmlFor=key;
        label.textContent=item.label;
        const output=document.createElement("output");
        output.id=key+"-value";
        output.className="parameter-value";
        output.htmlFor=key;
        top.append(label,output);
        const input=document.createElement("input");
        Object.assign(input,{
            type:"range",id:key,min:item.min,max:item.max,step:key==="misalignment_mm"?.05:key==="suction_margin_m"?.1:1
        }
        );
        input.setAttribute("aria-describedby",key+"-help");
        const help=document.createElement("p");
        help.id=key+"-help";
        help.className="parameter-help";
        help.textContent=item.help;
        row.append(top,input,help);
        $(bearings.includes(key)?"bearing-parameters":"water-parameters").append(row);
        input.addEventListener("input",()=>{
            pending[key]=Number(input.value);
            displayParameter(key,pending[key]);
            clearTimeout(saveTimer);
            saveTimer=setTimeout(flushParameters,250);
        }
        );
        input.addEventListener("change",()=>{
            clearTimeout(saveTimer);
            flushParameters();
        }
        );
    }
    $("preset").replaceChildren();
    for(const [key,label] of Object.entries(meta.presets)){
        const option=document.createElement("option");
        option.value=key;
        option.textContent=label;
        $("preset").append(option);
    }
    let n=0;
    for(const [key,label] of Object.entries(meta.zones)){
        const card=document.createElement("button");
        card.type="button";
        card.className="zone-card";
        card.dataset.zone=key;
        card.setAttribute("aria-label","Seleccionar "+label);
        card.innerHTML='<div class="zone-top"><span>'+String(++n).padStart(2,"0")+" / "+key.toUpperCase()+'</span><span>◎</span></div><div class="values">— °C</div><small class="rms">— m/s²</small><div class="condition">◌ Esperando</div>';
        $("zone-cards").append(card);
        card.onclick=()=>selectZone(key);
    }
    document.querySelectorAll(".zone-hotspot").forEach(el=>{
        el.onclick=()=>selectZone(el.dataset.zone);
        el.onkeydown=event=>{
            if(event.key==="Enter"||event.key===" "){
                event.preventDefault();
                selectZone(el.dataset.zone);
            }
        }
        ;
    }
    );
}
function displayParameter(key,value){
    const item=meta.parameters[key];
    $(key+"-value").textContent=number(value,["misalignment_mm","suction_margin_m"].includes(key)?2:0)+" "+item.unit;
}
async function flushParameters(){
    if(flushing||!Object.keys(pending).length)return;
    flushing=true;
    const changes=pending;
    pending={
    }
    ;
    await action("/api/parameters",changes);
    flushing=false;
    if(Object.keys(pending).length)await flushParameters();
    else if(snapshot)render();
}
function selectZone(key){
    selected=key;
    MotorMechanics.select(key);
    render();
}
function condition(z){
    if(!z)return ["◌ Sin lectura actual",false];
    if(z.quality==="saturated")return ["! Sensor sintético saturado",true];
    const t=z.temperature_c>=75,v=z.vibration_rms_m_s2>=3;
    return [t&&v?"! Calor y vibración elevados":t?"! Calor elevado":v?"≋ Vibración elevada":"✓ Referencia normal",t||v];
}
function clearReadings(message="Sin lectura actual"){
    $("temperature").textContent="—";
    $("vibration").textContent="—";
    $("zone-condition").textContent="◌ "+message;
    $("stage").classList.add("stale");
    $("stage").classList.remove("running");
    for(const key of Object.keys(meta?.zones||{
    }
    )){
        $("svg-"+key).textContent="Sin lectura";
        const card=document.querySelector(`.zone-card[data-zone="${key}"]`);
        card.querySelector(".values").textContent="— °C";
        card.querySelector(".rms").textContent="— m/s²";
        card.querySelector(".condition").textContent="◌ "+message;
        card.querySelector(".condition").classList.remove("hot");
        $("visual-"+key).classList.remove("shaking");
    }
    $("visual-coupling").classList.remove("shaking");
    MotorMechanics.invalidate();
    $("packet").textContent="Sin paquete actual. El historial conserva las lecturas anteriores.";
}
function render(){
    if(!snapshot||!meta)return;
    const s=snapshot,p=s.current,params=s.settings;
    for(const key of Object.keys(meta.parameters)){
        if(key==="time_scale")continue;
        if(!(key in pending)&&!flushing&&document.activeElement!==$(key)){
            $(key).value=params[key];
            displayParameter(key,params[key]);
        }
    }
    if(document.activeElement!==$("time-scale"))$("time-scale").value=params.time_scale;
    const descriptions={
        live:s.motor_on?"● Simulación activa":"○ Motor apagado · enfriando",paused:"Ⅱ Simulación pausada",signal_loss:"⌁ Sin telemetría",waiting:"◌ Esperando datos nuevos",error:"! Error de adquisición"
    }
    ;
    $("system-state").textContent=descriptions[s.state]||s.state;
    $("system-state").className="state"+(["paused","signal_loss","waiting"].includes(s.state)?" warn":s.state==="error"?" error":"");
    $("pause").textContent=s.running?"Ⅱ Pausar":"▷ Reanudar";
    $("motor-toggle").textContent=s.motor_on?"○ Apagar motor":"▷ Encender motor";
    $("signal-toggle").textContent=s.signal?"⌁ Perder señal":"⌁ Restaurar señal";
    const context=s.plant.context;
    for(const [id,key,digits] of [["rpm","rpm",0],["flow","flow_m3h",1],["head","head_m",1],["load","motor_load_pct",0]])$(id).textContent=number(context[key],digits);
    const seconds=Math.floor(s.elapsed_s),hour=Math.floor(seconds/3600),minute=Math.floor(seconds/60)%60;
    $("physical-time").textContent="T+ "+[hour,minute,seconds%60].map(v=>String(v).padStart(2,"0")).join(":")+" · "+params.time_scale+"×";
    $("valve-caption").textContent="VÁLVULA "+number(params.valve_pct,0)+" %";
    $("stage").classList.toggle("misaligned",params.misalignment_mm>.15);
    $("visual-coupling").style.translate="0 "+(params.misalignment_mm*3)+"px";
    for(const el of document.querySelectorAll("[data-zone]")){
        el.classList.toggle("selected",el.dataset.zone===selected);
        if(el.classList.contains("zone-card"))el.setAttribute("aria-pressed",String(el.dataset.zone===selected));
    }
    $("selected-title").textContent=meta.zones[selected];
    $("received").textContent=p?formatDate(p.acquired_at):s.last_received_at?"Última: "+formatDate(s.last_received_at):"Esperando la primera adquisición";
    if(p){
        if(p.sequence!==lastSequence){
            lastSequence=p.sequence;
            lastNewPacket=performance.now();
        }
        $("stage").classList.remove("stale");
        $("stage").classList.toggle("running",s.running&&context.rpm>100);
        for(const [key,z] of Object.entries(p.zones)){
            const [text,hot]=condition(z);
            const visual=$("visual-"+key);
            visual.style.setProperty("--heat",Math.max(0,Math.min(1,(z.temperature_c-55)/35)));
            const shaking=z.vibration_rms_m_s2>=3;
            visual.classList.toggle("shaking",shaking);
            visual.style.setProperty("--shake",Math.min(5,.7+(z.vibration_rms_m_s2-3)*.55)+"px");
            $("svg-"+key).textContent=number(z.temperature_c,1)+" °C · "+number(z.vibration_rms_m_s2,2)+" m/s²";
            const card=document.querySelector(`.zone-card[data-zone="${key}"]`);
            card.querySelector(".values").textContent=number(z.temperature_c,1)+" °C";
            card.querySelector(".rms").textContent=number(z.vibration_rms_m_s2,2)+" m/s²";
            card.querySelector(".condition").textContent=text;
            card.querySelector(".condition").classList.toggle("hot",hot);
        }
        const z=p.zones[selected];
        $("temperature").textContent=number(z.temperature_c,1);
        $("vibration").textContent=number(z.vibration_rms_m_s2,2);
        $("zone-condition").textContent=condition(z)[0];
        $("threshold-note").textContent=z.quality==="saturated"?"Sensor virtual saturado a 125 °C: el valor está limitado; no representa la temperatura interna del modelo.":"Referencias visuales: 75 °C y 3 m/s². Ilustrativas; sin clasificación normativa.";
        $("packet").textContent=JSON.stringify(p,null,2);
        const coupling=p.zones.de.vibration_rms_m_s2;
        $("visual-coupling").classList.toggle("shaking",coupling>=3);
        $("visual-coupling").style.setProperty("--shake",Math.min(4,coupling*.3)+"px");
    }
    else clearReadings(s.state==="paused"?"Pausada":s.state==="signal_loss"?"Sin señal":"Sin lectura actual");
    const effects=[];
    if(params.lubrication_pct<80)effects.push("Lubricación reducida: mayor fricción y ruido en DE y NDE.");
    if(params.contamination_pct>10)effects.push("Contaminación del lubricante: ruido de rodamiento; el circuito sigue usando agua limpia.");
    if(params.misalignment_mm>.15)effects.push("Desalineación: aumenta 2× giro, sobre todo cerca del acoplamiento.");
    if(params.imbalance_gmm>30)effects.push("Desequilibrio: aumenta 1× giro en el motor.");
    if(params.looseness_pct>10)effects.push("Fijación suelta: armónicos y movimiento de la base.");
    if(params.bearing_defect_pct>10)effects.push("Defecto impuesto: impulsos en los rodamientos; no mide daño acumulado.");
    if(params.cooling_pct<70)effects.push("Ventilación limitada: el calor se acumula gradualmente.");
    if(context.cavitation_index>.05)effects.push("NPSH bajo: caudal reducido y ruido intenso en la bomba.");
    if(!s.motor_on)effects.push("Motor apagado: desaceleración y enfriamiento, con sensores virtuales activos.");
    $("effects-text").textContent=effects.join(" ")||"Operación normal con agua limpia. Las temperaturas suben desde el arranque hasta su equilibrio térmico supuesto.";
    $("storage-info").textContent=s.stored_packets+" paquetes en esta pestaña · máximo 3.600 · descarga antes de cerrar";
    MotorMechanics.update(s);
    drawCharts();
}
function drawChart(id,series,options={
}
){
    const canvas=$(id),rect=canvas.getBoundingClientRect(),ratio=window.devicePixelRatio||1;
    if(!rect.width)return;
    canvas.width=Math.round(rect.width*ratio);
    canvas.height=Math.round(rect.height*ratio);
    const ctx=canvas.getContext("2d");
    ctx.scale(ratio,ratio);
    const w=rect.width,h=rect.height,left=43,right=w-13,top=15,bottom=h-27;
    const points=series.flatMap(s=>s.data).filter(p=>Number.isFinite(p.y));
    let low=options.low??Math.min(0,...points.map(p=>p.y)),high=options.high??Math.max(options.floor||1,...points.map(p=>p.y));
    if(options.symmetric){
        high=Math.max(1,...points.map(p=>Math.abs(p.y)));
        low=-high;
    }
    else high+=Math.max(1,(high-low)*.12);
    if(high===low)high=low+1;
    const xs=points.map(p=>p.x);
    let xmin=xs.length?Math.min(...xs):0,xmax=xs.length?Math.max(...xs):1;
    if(xmax===xmin)xmax=xmin+1;
    const X=x=>left+(x-xmin)/(xmax-xmin)*(right-left),Y=y=>bottom-(y-low)/(high-low)*(bottom-top);
    ctx.font='9px "Segoe UI",Arial';
    for(let i=0;i<4;i++){
        const val=low+(high-low)*i/3,y=Y(val);
        ctx.strokeStyle="#1b3644";
        ctx.lineWidth=.7;
        ctx.beginPath();
        ctx.moveTo(left,y);
        ctx.lineTo(right,y);
        ctx.stroke();
        ctx.fillStyle="#628799";
        ctx.fillText(number(val,Math.abs(high)>15?0:1),3,y+3);
    }
    if(options.threshold&&options.threshold<high){
        ctx.strokeStyle="#865b41";
        ctx.setLineDash([4,5]);
        ctx.beginPath();
        ctx.moveTo(left,Y(options.threshold));
        ctx.lineTo(right,Y(options.threshold));
        ctx.stroke();
        ctx.setLineDash([]);
    }
    for(const s of series){
        ctx.strokeStyle=s.color;
        ctx.lineWidth=1.5;
        ctx.beginPath();
        let previous=null;
        for(const p of s.data){
            if(!Number.isFinite(p.y)){
                previous=null;
                continue;
            }
            if(previous===null||(options.time&&p.x-previous>2500))ctx.moveTo(X(p.x),Y(p.y));
            else ctx.lineTo(X(p.x),Y(p.y));
            previous=p.x;
        }
        ctx.stroke();
        if(s.data.length===1){
            ctx.beginPath();
            ctx.arc(X(s.data[0].x),Y(s.data[0].y),2,0,Math.PI*2);
            ctx.fillStyle=s.color;
            ctx.fill();
        }
    }
    ctx.fillStyle="#60899a";
    const label=x=>options.time?new Intl.DateTimeFormat("es-CL",{
        timeZone:"America/Santiago",hour:"2-digit",minute:"2-digit",second:"2-digit",hourCycle:"h23"
    }
    ).format(new Date(x)):number(x,0)+" ms";
    if(points.length){
        ctx.fillText(label(xmin),left,bottom+20);
        const text=label(xmax);
        ctx.fillText(text,right-ctx.measureText(text).width,bottom+20);
    }
    else{
        ctx.textAlign="center";
        ctx.fillText("Esperando datos simulados",w/2,h/2);
    }
}
function drawCharts(){
    if(!snapshot)return;
    const trend=snapshot.trend;
    drawChart("temperature-chart",[{
        color:"#68ddc8",data:trend.map(p=>({
            x:Date.parse(p.acquired_at),y:p.zones[selected].temperature_c
        }
        ))
    }
    ],{
        floor:40,threshold:75,time:true
    }
    );
    drawChart("vibration-chart",[{
        color:"#77b9ef",data:trend.map(p=>({
            x:Date.parse(p.acquired_at),y:p.zones[selected].vibration_rms_m_s2
        }
        ))
    }
    ],{
        floor:3.5,threshold:3,time:true
    }
    );
    const wave=snapshot.current?snapshot.waveforms[selected]||[]:[];
    drawChart("wave-chart",["x","y","z"].map((axis,i)=>({
        color:["#75e8d3","#72b4e7","#c4a5e8"][i],data:wave.map(p=>({
            x:p.t_ms,y:p[axis]
        }
        ))
    }
    )),{
        symmetric:true
    }
    );
}
async function poll(){
    try{
        snapshot=await api("/api/status");
        render();
    }
    catch(error){
        if(meta){
            clearReadings("Servidor sin respuesta");
            $("system-state").textContent="! Servidor sin respuesta";
            $("system-state").className="state error";
            for(const id of ["rpm","flow","head","load"])$(id).textContent="—";
            $("received").textContent="No hay recepción actual. Vuelve a cargar la página si el problema persiste.";
        }
    }
    finally{
        setTimeout(poll,700);
    }
}
async function init(){
    try{
        meta=await api("/api/meta");
        MotorMechanics.init(selectZone);
        makeParameters();
        $("pause").onclick=()=>action("/api/control",{
            action:snapshot.running?"pause":"resume"
        }
        );
        $("motor-toggle").onclick=()=>action("/api/control",{
            action:snapshot.motor_on?"motor_off":"motor_on"
        }
        );
        $("signal-toggle").onclick=()=>action("/api/control",{
            action:snapshot.signal?"signal_loss":"signal_restore"
        }
        );
        $("apply-preset").onclick=async()=>{
            await flushParameters();
            await action("/api/control",{
                action:$("preset").value
            }
            );
            toast("Escenario aplicado. La temperatura evoluciona gradualmente.");
        }
        ;
        $("time-scale").onchange=()=>action("/api/parameters",{
            time_scale:Number($("time-scale").value)
        }
        );
        function download(content,type,name){
            const url=URL.createObjectURL(new Blob([content],{type}));
            const a=document.createElement("a");a.href=url;a.download=name;a.click();
            setTimeout(()=>URL.revokeObjectURL(url),1000);
        }
        $("export-csv").onclick=()=>download(browserEngine.csv(),"text/csv;charset=utf-8","motor-lab-"+browserEngine.instance_id+".csv");
        $("export-json").onclick=()=>download(JSON.stringify({model_version:"1.1.0-web",source:"simulated",session_id:browserEngine.instance_id,exported_at:new Date().toISOString(),retention_limit:3600,events:browserEngine.events,packets:browserEngine.history},null,2),"application/json","motor-lab-"+browserEngine.instance_id+".json");
        $("new-session").onclick=()=>{
            if(browserEngine.history.length&&!confirm("Se borrarán los datos de esta pestaña. Descarga CSV o JSON antes de iniciar otro ensayo. ¿Continuar?"))return;
            location.reload();
        };
        browserEngine.tick(1);
        window.addEventListener("resize",drawCharts);
        setInterval(()=>{
            if(snapshot?.current&&lastNewPacket&&performance.now()-lastNewPacket>4000){
                clearReadings("Lectura vencida");
                $("system-state").textContent="⌁ Sin datos nuevos";
                $("system-state").className="state warn";
            }
        }
        ,300);
        poll();
    }
    catch(error){
        $("system-state").textContent="! No se pudo abrir el simulador";
        toast("Vuelve a cargar la página. "+error.message,true);
    }
}
init();
