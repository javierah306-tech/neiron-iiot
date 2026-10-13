/* Motor / Lab Web 1.1.0. Port del modelo reducido twin/model.py 1.0.0.
 * Las constantes son ilustrativas. RNG propio: no reproduce el ruido de Python. */
(function(root) {
  'use strict';
  const ZONES = {nde:'Rodamiento posterior · NDE',casing:'Carcasa del motor',de:'Rodamiento del acoplamiento · DE',pump:'Bomba de agua'};
  const DEFAULTS = {ambient_c:22,water_c:20,valve_pct:100,cooling_pct:100,lubrication_pct:100,contamination_pct:0,misalignment_mm:0,imbalance_gmm:0,looseness_pct:0,bearing_defect_pct:0,suction_margin_m:3.5,time_scale:1};
  const FIELDS = {
    ambient_c:[0,45,'°C','Temperatura ambiente','Afecta la disipación de todas las zonas.'],
    water_c:[5,40,'°C','Temperatura del agua','Agua limpia, sin sólidos; enfría la bomba.'],
    valve_pct:[25,120,'%','Apertura relativa de válvula','100 % es el punto nominal supuesto; cambia caudal y carga.'],
    cooling_pct:[5,100,'%','Ventilación disponible','Menos refrigeración eleva gradualmente la temperatura.'],
    lubrication_pct:[0,100,'%','Lubricación efectiva','Índice ilustrativo: reducirlo añade fricción y ruido.'],
    contamination_pct:[0,100,'%','Contaminación del lubricante','Índice de escenario en rodamientos; el agua sigue limpia.'],
    misalignment_mm:[0,1.5,'mm','Desalineación paralela','Desplazamiento supuesto del acoplamiento.'],
    imbalance_gmm:[0,400,'g·mm','Desequilibrio del rotor','Masa excéntrica × radio; refuerza 1× giro.'],
    looseness_pct:[0,100,'%','Holgura de la fijación','Índice ilustrativo; añade armónicos.'],
    bearing_defect_pct:[0,100,'%','Defecto de rodamiento','Impulsos sintéticos; no representa vida consumida.'],
    suction_margin_m:[0.2,5,'m','NPSH disponible supuesto','Bajo 2,5 m aparece cavitación ilustrativa.'],
    time_scale:[1,60,'×','Velocidad del tiempo físico','Acelera la física, conserva aproximadamente un paquete por segundo.']
  };
  const PRESETS = {normal:['Agua · operación normal',{...DEFAULTS}],lubrication:['Lubricación insuficiente',{lubrication_pct:10}],alignment:['Desalineación',{misalignment_mm:1.1}],imbalance:['Desequilibrio',{imbalance_gmm:320}],cooling:['Refrigeración deficiente',{cooling_pct:10}],bearing:['Defecto de rodamiento',{bearing_defect_pct:85}],cavitation:['Cavitación',{suction_margin_m:0.6}]};
  const clamp=(v,a,b)=>Math.max(a,Math.min(b,v));
  class Random {
    constructor(seed){this.seed=seed>>>0;}
    uniform(){this.seed=(1664525*this.seed+1013904223)>>>0;return (this.seed+.5)/4294967296;}
    gauss(){return Math.sqrt(-2*Math.log(this.uniform()))*Math.cos(2*Math.PI*this.uniform());}
  }
  class Plant {
    constructor(seed=512){this.seed=seed;this.settings={...DEFAULTS};this.motor_on=true;this.elapsed_s=0;this.rpm=0;this.temperatures={nde:22,casing:22,de:22,pump:20};this.probes={...this.temperatures};this.phase=0;this.zones={};this.waveforms={};this.context={};}
    configure(raw){
      if(!raw||typeof raw!=='object'||Array.isArray(raw)||!Object.keys(raw).length)throw Error('Envíe parámetros conocidos.');
      for(const [k,v] of Object.entries(raw)){
        if(!FIELDS[k]||!Number.isFinite(v)||v<FIELDS[k][0]||v>FIELDS[k][1]||(k==='time_scale'&&![1,10,60].includes(v)))throw Error('Parámetro fuera de rango: '+k);
      }
      this.settings={...this.settings,...raw};
    }
    hydraulics(rpm){
      const s=this.settings,r=Math.max(0,rpm/2910),valve=s.valve_pct/100;
      const qratio=r*Math.sqrt(65/(20+45/valve**2)),cav=clamp((2.5-s.suction_margin_m)/2.5,0,1);
      const flow=18*qratio*(1-.25*cav),head=45/valve**2*qratio**2*(1-.2*cav);
      const eta=Math.max(.38,.64*Math.exp(-.7*(qratio/Math.max(r,.001)-1)**2));
      const hydraulic=1000*9.80665*flow/3600*head,shaft=hydraulic/eta+120*r**3;
      return {flow_m3h:flow,head_m:head,pressure_bar:head*.0980665,hydraulic_power_w:hydraulic,pump_shaft_w:shaft,pump_efficiency:eta,cavitation_index:cav,pump_load:shaft/3700};
    }
    step(dt){
      if(!Number.isFinite(dt)||dt<0||dt>5)throw Error('Paso real inválido.');
      const s=this.settings;let remaining=dt*s.time_scale;
      while(remaining>1e-8){
        const h=Math.min(remaining,1),hyd=this.hydraulics(this.rpm);
        const friction=140*(1-s.lubrication_pct/100)**2+75*s.contamination_pct/100+85*(s.misalignment_mm/1.5)**2+65*s.bearing_defect_pct/100;
        const target=this.motor_on?Math.max(0,2970-60*(hyd.pump_load+friction/3700)):0;
        this.rpm+=(target-this.rpm)*(1-Math.exp(-h/(this.motor_on?1.1:1.8)));
        const ratio=Math.min(1.15,this.rpm/2910),p=this.hydraulics(this.rpm),bearing=friction*ratio;
        const losses=this.motor_on?180+(3700/.85-3700-180)*p.pump_load**2:0;
        const g=this.motor_on?18.18*(.35+.65*ratio)*s.cooling_pct/100:5.5;
        const old={...this.temperatures},t=this.temperatures,heat=Math.max(0,losses-(this.motor_on?32*ratio:0));
        t.casing+=(heat-g*(old.casing-s.ambient_c)+2*(old.de-old.casing)+2*(old.nde-old.casing))*h/16000;
        for(const [key,weight,cap] of [['de',.65,2400],['nde',.35,1800]])t[key]+=((this.motor_on?16*ratio:0)+weight*bearing+2*(old.casing-old[key])-2.5*(old[key]-s.ambient_c))*h/cap;
        t.pump+=(p.pump_shaft_w-p.hydraulic_power_w-(35+18*p.flow_m3h)*(old.pump-s.water_c))*h/6000;
        for(const key of Object.keys(ZONES))this.probes[key]+=(t[key]-this.probes[key])*(1-Math.exp(-h/8));
        this.elapsed_s+=h;remaining-=h;
        this.context={...p,rpm:this.rpm,bearing_friction_w:bearing,motor_losses_w:losses,electrical_power_w:this.motor_on?p.pump_shaft_w+bearing+losses:0,motor_load_pct:100*(p.pump_shaft_w+bearing)/3700,synchronous_rpm:3000};
      }
    }
    acquire(sequence){
      const s=this.settings,r=Math.min(1.15,this.rpm/2910),f=this.rpm/60,p=this.hydraulics(this.rpm),rng=new Random(this.seed+sequence);
      const a1=(.55+.2*p.pump_load+s.imbalance_gmm*.010)*r**2,a2=(.14+s.misalignment_mm*4.1)*r**2;
      const loose=s.looseness_pct/100*1.6*r**2,noise=(.03+1.4*(1-s.lubrication_pct/100)**2+.8*s.contamination_pct/100)*r+.01;
      const defect=s.bearing_defect_pct/100*8*r,cav=p.cavitation_index*3.4*r;
      const weights={nde:[.78,.4,.7,.35],casing:[.7,.45,.35,.3],de:[1,1,1,1],pump:[.55,.6,.15,1.7]};
      for(const [zone,[w1,w2,wn,wc]] of Object.entries(weights)){
        const axes=[[],[],[]];
        for(let i=0;i<1000;i++){
          const angle=this.phase+2*Math.PI*f*i/1000,first=a1*w1*Math.sin(angle),second=a2*w2*Math.sin(2*angle+.2),blade=.2*r**2*Math.sin(6*angle+.7);
          const rough=rng.gauss()*(noise*wn+cav*wc),impact=defect*wn*Math.max(0,Math.sin(4.7*angle))**20*(.85+.3*rng.uniform());
          const harmonic=loose*Math.sin(3*angle+.4),electrical=this.motor_on?.2*r*Math.sin(2*Math.PI*100*i/1000):0;
          axes[0].push(first+second+.5*blade+harmonic+.45*rough+impact);
          axes[1].push(.8*a1*w1*Math.cos(angle)+.35*second+rough+electrical+.6*impact);
          axes[2].push(.35*first+.7*second+.45*blade+.5*rough+.4*harmonic+.35*impact);
        }
        const centered=axes.map(axis=>{const mean=axis.reduce((a,b)=>a+b,0)/1000;return axis.map(v=>v-mean);});
        const rmsAxes=centered.map(axis=>Math.sqrt(axis.reduce((a,v)=>a+v*v,0)/1000));
        const measured=Math.round((this.probes[zone]+rng.gauss()*.012)*16)/16;
        this.zones[zone]={name:ZONES[zone],temperature_c:clamp(measured,-55,125),vibration_rms_m_s2:+Math.hypot(...rmsAxes).toFixed(6),rms_axes_m_s2:rmsAxes.map(v=>+v.toFixed(6)),quality:measured>125||measured< -55?'saturated':'synthetic'};
        this.waveforms[zone]=Array.from({length:120},(_,i)=>({t_ms:i,x:+centered[0][i].toFixed(4),y:+centered[1][i].toFixed(4),z:+centered[2][i].toFixed(4)}));
      }
      this.phase=(this.phase+2*Math.PI*f)%(2*Math.PI);return this.zones;
    }
  }
  class Engine {
    constructor(){this.plant=new Plant();this.sequence=0;this.revision=1;this.running=true;this.signal=true;this.current=null;this.history=[];this.events=[];this.lastAt=0;this.instance_id=root.crypto?.randomUUID?.()||'web-'+Date.now()+'-'+Math.random().toString(16).slice(2);this.record('session_started',{model:'1.1.0-web',seed:512});}
    record(event,detail){this.events.push({recorded_at:new Date().toISOString(),event,detail});if(this.events.length>3600)this.events.shift();}
    tick(dt=1){
      if(!this.running)return;this.plant.step(dt);const z=this.plant.acquire(this.sequence+1);
      if(!this.signal)return;
      const p=this.plant;this.current={schema:'motor-pump-twin.telemetry',schema_version:1,instance_id:this.instance_id,device_id:'virtual-sensors-01',asset_id:'motor-pump-5hp',sequence:++this.sequence,acquired_at:new Date().toISOString(),source:'simulated',quality:Object.values(z).some(v=>v.quality==='saturated')?'saturated':'synthetic',config_revision:this.revision,simulation_time_s:+p.elapsed_s.toFixed(3),time_scale:p.settings.time_scale,temperature:{value:z.de.temperature_c,unit:'degC',location:'de',method:'synthetic_contact_probe_12bit'},vibration:{value:z.de.vibration_rms_m_s2,unit:'m/s2',location:'de',method:'synthetic_vector_acceleration_rms_dc_removed',sample_rate_hz:1000,window_s:1,samples_per_axis:1000},zones:JSON.parse(JSON.stringify(z)),context:Object.fromEntries(Object.entries(p.context).map(([k,v])=>[k,+v.toFixed(5)])),settings:{...p.settings},model_version:'1.1.0-web',seed:p.seed};
      this.lastAt=Date.now();this.history.push(this.current);if(this.history.length>3600)this.history.shift();
    }
    configure(raw){this.plant.configure(raw);this.revision++;this.record('parameters_changed',{revision:this.revision,changes:{...raw}});}
    command(action){
      if(PRESETS[action]){const values={...PRESETS[action][1]};if(action==='normal')values.time_scale=this.plant.settings.time_scale;this.configure(values);}
      else if(action==='pause')this.running=false;
      else if(action==='resume')this.running=true;
      else if(action==='motor_on')this.plant.motor_on=true;
      else if(action==='motor_off')this.plant.motor_on=false;
      else if(action==='signal_loss')this.signal=false;
      else if(action==='signal_restore')this.signal=true;
      else throw Error('Control desconocido.');
      if(['pause','resume','signal_loss','signal_restore'].includes(action))this.current=null;
      this.record('command',{action});
    }
    status(){const fresh=this.running&&this.signal&&this.current&&Date.now()-this.lastAt<4000;
      return {version:'1.1.0-web',state:!this.running?'paused':!this.signal?'signal_loss':fresh?'live':'waiting',running:this.running,motor_on:this.plant.motor_on,signal:this.signal,sequence:this.sequence,instance_id:this.instance_id,elapsed_s:this.plant.elapsed_s,settings:{...this.plant.settings},config_revision:this.revision,current:fresh?this.current:null,last_received_at:this.history.at(-1)?.acquired_at||null,plant:{context:this.plant.context,zones:this.plant.zones},waveforms:fresh?this.plant.waveforms:{},trend:this.history.slice(-240),stored_packets:this.history.length,ai_enabled:false,hardware_connected:false};
    }
    metadata(){return {parameters:Object.fromEntries(Object.entries(FIELDS).map(([k,[min,max,unit,label,help]])=>[k,{min,max,unit,label,help}])),presets:Object.fromEntries(Object.entries(PRESETS).map(([k,v])=>[k,v[0]])),zones:ZONES};}
    csv(){
      const keys=Object.keys(DEFAULTS),header=['instance_id','model_version','seed','sequence','acquired_at','source','quality','config_revision','simulation_time_s','zone','temperature_c','vibration_rms_m_s2','rms_x_m_s2','rms_y_m_s2','rms_z_m_s2','rpm','flow_m3h','head_m','motor_load_pct',...keys];
      const lines=[header];for(const p of this.history)for(const [zone,z] of Object.entries(p.zones))lines.push([p.instance_id,p.model_version,p.seed,p.sequence,p.acquired_at,p.source,z.quality,p.config_revision,p.simulation_time_s,zone,z.temperature_c,z.vibration_rms_m_s2,...z.rms_axes_m_s2,p.context.rpm,p.context.flow_m3h,p.context.head_m,p.context.motor_load_pct,...keys.map(k=>p.settings[k])]);
      return '\ufeff'+lines.map(row=>row.join(',')).join('\r\n');
    }
  }
  root.MotorBrowser={Plant,Engine,DEFAULTS,FIELDS,PRESETS,ZONES};
  if(typeof module!=='undefined')module.exports=root.MotorBrowser;
})(globalThis);
