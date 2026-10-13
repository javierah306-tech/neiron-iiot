const assert=require('node:assert/strict');
const {Plant,Engine}=require('./browser-model.js');
const fs=require('node:fs');
let checks=0;
function check(name,fn){fn();checks++;console.log('PASS '+name);}
const normal=new Plant();for(let i=0;i<60;i++)normal.step(1);normal.acquire(60);
check('nominal speed and finite telemetry',()=>{assert(normal.rpm>2800&&normal.rpm<3000);for(const z of Object.values(normal.zones)){assert(Number.isFinite(z.temperature_c));assert(z.vibration_rms_m_s2>0);assert.equal(z.quality,'synthetic');}});
for(const [field,value,zone] of [['imbalance_gmm',320,'de'],['misalignment_mm',1.1,'de'],['lubrication_pct',10,'de'],['bearing_defect_pct',85,'de'],['contamination_pct',90,'nde'],['looseness_pct',90,'de'],['suction_margin_m',.6,'pump']]){
  check('increased vibration '+field,()=>{const p=new Plant();p.configure({[field]:value});for(let i=0;i<60;i++)p.step(1);p.acquire(60);assert(p.zones[zone].vibration_rms_m_s2>normal.zones[zone].vibration_rms_m_s2);});
}
check('gradual heating with low ventilation',()=>{const a=new Plant(),b=new Plant();a.configure({time_scale:60});b.configure({time_scale:60,cooling_pct:10});for(let i=0;i<100;i++){a.step(1);b.step(1);}assert(b.temperatures.casing>a.temperatures.casing+20);});
check('motor off slows rotation and power becomes zero',()=>{normal.motor_on=false;normal.step(5);assert(normal.rpm<300);assert.equal(normal.context.electrical_power_w,0);});
check('invalid input is atomic',()=>{const p=new Plant();for(const v of [NaN,Infinity,true,'10',-1,200])assert.throws(()=>p.configure({cooling_pct:v}));assert.throws(()=>p.configure({ambient_c:30,time_scale:2}));assert.equal(p.settings.ambient_c,22);});
check('pause invalidates readings and freezes physical clock',()=>{const e=new Engine();e.tick();e.command('pause');const t=e.plant.elapsed_s;e.tick();assert.equal(e.plant.elapsed_s,t);assert.equal(e.status().current,null);e.command('resume');assert.equal(e.status().current,null);e.tick();assert(e.status().current);});
check('signal loss evolves plant without repeating telemetry',()=>{const e=new Engine();e.tick();e.command('signal_loss');const seq=e.sequence,t=e.plant.elapsed_s;e.tick();assert.equal(e.sequence,seq);assert(e.plant.elapsed_s>t);assert.equal(e.status().current,null);e.command('signal_restore');e.tick();assert.equal(e.sequence,seq+1);});
check('normal preset preserves temperature and selected time scale',()=>{const e=new Engine();e.configure({time_scale:60,cooling_pct:10});for(let i=0;i<20;i++)e.tick();const t=e.plant.temperatures.casing;e.command('normal');assert.equal(e.plant.temperatures.casing,t);assert.equal(e.plant.settings.time_scale,60);assert.equal(e.plant.settings.cooling_pct,100);});
check('CSV contains all zones and scenario metadata',()=>{const e=new Engine();e.configure({imbalance_gmm:100});e.tick();const csv=e.csv().replace(/^\ufeff/,'').split('\r\n');assert.equal(csv.length,5);const headers=csv[0].split(',');assert(headers.includes('imbalance_gmm'));for(const row of csv.slice(1))assert.equal(row.split(',').length,headers.length);assert.equal(e.current.source,'simulated');assert.equal(e.current.vibration.sample_rate_hz,1000);assert.equal(e.plant.waveforms.de.length,120);});
check('retention cap preserves latest packets',()=>{const e=new Engine();e.history=Array.from({length:3600},(_,i)=>({sequence:i}));e.tick();assert.equal(e.history.length,3600);assert.equal(e.history.at(-1).sequence,1);});
// Compartir referencias deterministas con la prueba del Python original.
const a=new Plant();const reference=[];for(let i=0;i<90;i++){if(i===30)a.configure({time_scale:10,cooling_pct:10,misalignment_mm:1.1});if(i===60)a.motor_on=false;a.step(1);if([29,59,89].includes(i))reference.push({step:i+1,rpm:a.rpm,elapsed_s:a.elapsed_s,temperatures:a.temperatures,context:a.context});reference[reference.length-1]=reference[reference.length-1]?JSON.parse(JSON.stringify(reference[reference.length-1])):undefined;if(reference.at(-1)===undefined)reference.pop();}
fs.writeFileSync('model-reference.json',JSON.stringify(reference));
console.log(checks+' model checks passed');
