import {createRequire} from 'node:module';
import {mkdir,writeFile} from 'node:fs/promises';
import assert from 'node:assert/strict';
const {chromium}=createRequire(import.meta.url)('playwright');
const browser=await chromium.launch({headless:true,executablePath:process.env.BROWSER_EXE||'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe'});
const origin=process.env.GAME_URL||'http://127.0.0.1:5180/';
const report={checks:[],errors:[],samples:[]};
const check=(name,condition)=>{assert.ok(condition,name);report.checks.push(name);};
try{
  await mkdir('screenshots',{recursive:true});await mkdir('output/grendel-hover',{recursive:true});
  const page=await browser.newPage({viewport:{width:1440,height:1000}});
  page.on('pageerror',e=>report.errors.push(e.message));page.on('response',r=>{if(r.status()>=400)report.errors.push(r.status()+' '+r.url());});
  await page.goto(origin+'enemy-lab.html?model=boss');
  await page.waitForFunction(()=>window.__enemyLab?.ready&&__enemyLab.type==='boss');
  const model=await page.evaluate(()=>__enemyLab);report.model=model;
  check('boss uses images and UVs on every mesh',model.meshes>0&&model.meshes===model.textured);
  check('boss stays below 16000 triangles',model.triangles<16000);
  check('four separate hover jets and weapon/aim anchors exist',model.hoverJets===4&&model.hasShotOrigin&&model.hasAimTarget);
  await page.locator('#hover-motion').click();
  for(const view of ['beauty','front','top','side']){
    await page.locator('[data-view="'+view+'"]').click();await page.waitForTimeout(200);
    await page.locator('#viewport').screenshot({path:'screenshots/grendel-'+view+'.png'});
  }
  await page.locator('[data-view="beauty"]').click();await page.locator('#lighting').click();await page.waitForTimeout(100);
  await page.screenshot({path:'screenshots/grendel-comparison.png'});
  await page.locator('#model-select').selectOption('turret');await page.waitForFunction(()=>__enemyLab.ready&&__enemyLab.type==='turret');
  check('hover control is hidden for static enemies',await page.locator('#hover-motion').isHidden());
  await page.locator('#model-select').selectOption('boss');await page.waitForFunction(()=>__enemyLab.ready&&__enemyLab.type==='boss');
  check('boss can be reloaded after disposing its previous model',await page.locator('#hover-motion').isVisible());

  await page.goto(origin+'?debug=1&bossPreview=1&invulnerable=1&endlessBoss=1&speed=2');
  await page.waitForFunction(()=>window.__nightVector);await page.click('#start');
  await page.waitForFunction(()=>__nightVector.inspect().stats.lastEnemyShot?.type==='boss');
  let state=await page.evaluate(()=>__nightVector.inspect());
  check('GRENDEL replaces the old boss model',state.enemies.some(e=>e.type==='boss'&&e.design==='Grendel Hover'));
  const shot=state.stats.lastEnemyShot;report.shot=shot;
  check('boss fire starts at the modeled emitter',shot.core&&shot.origin.every((v,i)=>Math.abs(v-shot.core[i])<1e-6));
  const resources=state.renderMemory;
  for(let i=0;i<12;i++){
    state=await page.evaluate(()=>__nightVector.inspect());report.samples.push(state.bossPose);
    check('boss remains 68m ahead '+i,Math.abs(state.bossDistance-68)<1e-6);
    const pose=state.bossPose;
    check('hovering hull clears the road '+i,pose.position[1]>1.6&&pose.position[1]<2);
    check('weapon aim remains inside the vertical aim band '+i,state.enemies.find(e=>e.type==='boss').screen.y>-.4);
    check('all four exhausts pulse within their small range '+i,pose.jets.every(v=>v>=.9&&v<=1.1));
    await page.waitForTimeout(250);
  }
  check('hover motion changes altitude',Math.max(...report.samples.map(s=>s.position[1]))-Math.min(...report.samples.map(s=>s.position[1]))>.05);
  check('legs remain tucked instead of walking',report.samples.every(s=>JSON.stringify(s.legs)===JSON.stringify(report.samples[0].legs)));
  check('hover animation allocates no rendering resources',state.renderMemory.geometries===resources.geometries&&state.renderMemory.textures===resources.textures);
  const paused=await page.evaluate(()=>{__nightVector.pause();return __nightVector.inspect();});await page.waitForTimeout(250);
  check('pause freezes the boss pose',JSON.stringify((await page.evaluate(()=>__nightVector.inspect())).bossPose)===JSON.stringify(paused.bossPose));
  await page.addStyleTag({content:'#pause-panel{display:none!important}'});await page.screenshot({path:'screenshots/grendel-boss-game.png'});
  await page.setViewportSize({width:390,height:844});await page.waitForTimeout(150);await page.screenshot({path:'screenshots/grendel-boss-portrait.png'});
  state=await page.evaluate(()=>__nightVector.inspect());
  check('portrait boss target remains reachable',Math.abs(state.enemies.find(e=>e.type==='boss').screen.x)<.3&&state.enemies.find(e=>e.type==='boss').screen.y>-.4);
  await page.setViewportSize({width:1440,height:1000});
  await page.goto(origin+'?debug=1&bossPreview=1&invulnerable=1&autopilot=1&speed=8');await page.waitForFunction(()=>window.__nightVector);await page.click('#start');
  const phases=new Set();
  for(let i=0;i<120;i++){
    state=await page.evaluate(()=>__nightVector.inspect());
    if(state.bossHP>0)phases.add(state.bossHP/2200<.33?3:state.bossHP/2200<.66?2:1);
    if(state.state==='clear')break;
    await page.waitForTimeout(250);
  }
  check('all three phases still occur',phases.size===3);
  check('new boss can be defeated and stage cleared',state.state==='clear'&&state.bossHP<=0);
  report.clear={elapsed:state.elapsed,kills:state.kills,phases:[...phases]};
  await page.click('#retry');await page.waitForFunction(()=>__nightVector.inspect().bossHP>0);
  check('retry gets a fresh boss and clean state',(await page.evaluate(()=>__nightVector.inspect())).kills===0);
  check('no browser errors or missing assets',report.errors.length===0);
  report.note='Browser/headless checks; invulnerable accelerated autoplay verifies progression, not difficulty or real-device frame rate.';
  await writeFile('output/grendel-hover/browser-verification.json',JSON.stringify(report,null,2));
  console.log(JSON.stringify({checks:report.checks.length,model:report.model,clear:report.clear,errors:report.errors},null,2));
}finally{await browser.close();}
