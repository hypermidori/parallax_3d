import {createRequire} from 'node:module';
import {mkdir,writeFile} from 'node:fs/promises';
import assert from 'node:assert/strict';
const {chromium}=createRequire(import.meta.url)('playwright');
const browser=await chromium.launch({headless:true,executablePath:process.env.BROWSER_EXE||'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe'});
const origin=process.env.GAME_URL||'http://127.0.0.1:5180/',report={checks:[],models:{},errors:[]};
const check=(name,ok)=>{assert.ok(ok,name);report.checks.push(name);};
try{
  await mkdir('screenshots',{recursive:true});await mkdir('output/support-enemies',{recursive:true});
  const page=await browser.newPage({viewport:{width:1440,height:1000}});
  page.on('pageerror',e=>report.errors.push(e.message));page.on('response',r=>{if(r.status()>=400)report.errors.push(r.status()+' '+r.url());});
  await page.goto(origin+'enemy-lab.html');
  for(const type of ['scout','turret','interceptor','scout']){
    await page.locator('#model-select').selectOption(type);
    await page.waitForFunction(t=>window.__enemyLab?.ready&&__enemyLab.type===t,type);
    const info=await page.evaluate(()=>__enemyLab);report.models[type]=info;
    check(type+' has image textures on every mesh',info.meshes>0&&info.meshes===info.textured);
    check(type+' stays under 8000 triangles',info.triangles<8000);
    if(type!=='interceptor')check(type+' contains a projectile-origin anchor',info.hasShotOrigin);
    check(type+' reference image loaded',await page.locator('.reference img').evaluate(img=>img.complete&&img.naturalWidth>1000));
    for(const view of ['beauty','front','top','side']){
      await page.locator('[data-view="'+view+'"]').click();await page.waitForTimeout(120);
      await page.locator('#viewport').screenshot({path:'screenshots/'+type+'-'+view+'.png'});
    }
  }
  await page.goto(origin+'?debug=1&speed=4&invulnerable=1');
  await page.waitForFunction(()=>window.__nightVector);await page.click('#start');
  await page.waitForFunction(()=>__nightVector.inspect().stats.lastEnemyShot?.type==='scout',null,{timeout:15000});
  let shot=await page.evaluate(()=>__nightVector.inspect().stats.lastEnemyShot);report.scoutShot=shot;
  check('scout projectile is born at its optical core',shot.core&&shot.origin.every((v,i)=>Math.abs(v-shot.core[i])<1e-6));
  await page.waitForFunction(()=>__nightVector.inspect().stats.lastEnemyShot?.type==='turret',null,{timeout:20000});
  shot=await page.evaluate(()=>__nightVector.inspect().stats.lastEnemyShot);report.turretShot=shot;
  check('ground projectile is born at its energy core',shot.core&&shot.origin.every((v,i)=>Math.abs(v-shot.core[i])<1e-6));
  check('ground projectile height matches the modeled core',Math.abs(shot.origin[1]-1.48)<1e-5);
  const state=await page.evaluate(()=>{__nightVector.pause();return __nightVector.inspect();});
  check('new scout model is used in game',state.enemies.some(e=>e.type==='scout'&&e.design==='Amber Firefly'));
  check('new ground model is used in game',state.enemies.some(e=>e.type==='turret'&&e.design==='Iron Warden'));
  await page.addStyleTag({content:'#pause-panel{display:none!important}'});await page.screenshot({path:'screenshots/support-enemies-game.png'});
  check('no browser exceptions or missing assets',report.errors.length===0);
  await writeFile('output/support-enemies/browser-verification.json',JSON.stringify(report,null,2));console.log(JSON.stringify(report,null,2));
}finally{await browser.close();}

