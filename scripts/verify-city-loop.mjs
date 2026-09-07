import {createRequire} from 'node:module';
import {mkdir,writeFile} from 'node:fs/promises';
import assert from 'node:assert/strict';
const {chromium}=createRequire(import.meta.url)('playwright');
const browser=await chromium.launch({headless:true,executablePath:process.env.BROWSER_EXE||'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe'});
const page=await browser.newPage({viewport:{width:1280,height:720}});
const report={checks:[],samples:[],errors:[]};
const check=(name,ok)=>{assert.ok(ok,name);report.checks.push(name);};
page.on('pageerror',e=>report.errors.push(e.message));
page.on('response',r=>{if(r.status()>=400)report.errors.push(r.url()+' '+r.status());});
const read=()=>page.evaluate(()=>__nightVector.inspect());
try{
  await mkdir('screenshots',{recursive:true});await mkdir('output/night-city',{recursive:true});
  await page.goto((process.env.GAME_URL||'http://127.0.0.1:5180/')+'?debug=1&autopilot=1&speed=8&invulnerable=1&endlessBoss=1');
  await page.waitForFunction(()=>window.__nightVector);await page.click('#start');
  for(const target of [1685,1795,1810,2515,2530,3955,3970,7000,10200]){
    await page.waitForFunction(d=>__nightVector.inspect().distance>=d,target,{timeout:90000});
    const s=await read();
    check('boss remains 68 m ahead at '+target,Math.abs(s.bossDistance-68)<1e-6&&s.state==='playing');
    check('camera keeps advancing at '+target,Math.abs(s.camera.z+s.distance)<1e-5);
    const active=s.loopChunks.filter(c=>c.visible).sort((a,b)=>a.index-b.index);
    check('pool has eight fixed slots at '+target,s.loopChunks.length===8);
    check('visible loop sections are contiguous at '+target,active.every((c,i)=>i===0||c.index===active[i-1].index+1));
    if(target>1810)check('background covers camera and forward view at '+target,active[0].start<=s.distance&&active.at(-1).start+180>=s.distance+800);
    report.samples.push({distance:s.distance,elapsed:s.elapsed,bossDistance:s.bossDistance,loopIndices:active.map(c=>c.index),memory:s.renderMemory});
    if(target<4000)await page.screenshot({path:'screenshots/loop-'+target+'.png'});
    console.log('loop sample',target,'elapsed',s.elapsed.toFixed(1));
  }
  const start=report.samples[4],end=report.samples.at(-1);
  check('texture memory remains constant through repeated recycling',start.memory.textures===end.memory.textures);
  check('geometry memory stays bounded',end.memory.geometries<=start.memory.geometries+16);
  const before=await page.evaluate(()=>{__nightVector.pause();return __nightVector.inspect();});await page.waitForTimeout(250);
  check('pause freezes the moving city',(await read()).distance===before.distance);
  await page.evaluate(()=>__nightVector.retry());await page.waitForFunction(()=>__nightVector.inspect().distance<20);
  const reset=await read();check('retry resets the loop pool',reset.loopChunks.every(c=>c.index===c.slot)&&reset.bossDistance===null);
  check('no browser errors',report.errors.length===0);
  await writeFile('output/night-city/city-loop-verification.json',JSON.stringify(report,null,2));
  console.log(JSON.stringify({checks:report.checks.length,lastSample:end,errors:report.errors},null,2));
}finally{await browser.close();}
