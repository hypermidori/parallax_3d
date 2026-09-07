import {createRequire} from 'node:module';
import {mkdir,writeFile} from 'node:fs/promises';
import assert from 'node:assert/strict';
const {chromium}=createRequire(import.meta.url)('playwright');
const browser=await chromium.launch({headless:true,executablePath:process.env.BROWSER_EXE||'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe'});
const report={checks:[],errors:[]},origin=process.env.GAME_URL||'http://127.0.0.1:5180/';
const check=(name,ok)=>{assert.ok(ok,name);report.checks.push(name);};
try{
  await mkdir('screenshots',{recursive:true});await mkdir('output/kestrel',{recursive:true});
  const page=await browser.newPage({viewport:{width:1440,height:940}});
  page.on('pageerror',e=>report.errors.push(e.message));
  page.on('response',r=>{if(r.status()>=400)report.errors.push(r.status()+' '+r.url());});
  await page.goto(origin+'enemy-lab.html');await page.waitForFunction(()=>window.__enemyLab?.ready);
  const stats=await page.evaluate(()=>__enemyLab);
  check('all model meshes have UV image textures',stats.meshes===stats.textured&&stats.meshes===7);
  check('model remains under 8000 triangles',stats.triangles>2000&&stats.triangles<8000);
  check('design reference loads',await page.locator('.reference img').evaluate(img=>img.complete&&img.naturalWidth>1000));
  report.model=stats;
  await page.screenshot({path:'screenshots/kestrel-lab.png'});
  for(const view of ['front','top','side','beauty']){
    await page.locator('[data-view="'+view+'"]').click();await page.waitForTimeout(250);
    await page.locator('#viewport').screenshot({path:'screenshots/kestrel-'+view+'.png'});
  }
  await page.locator('#lighting').click();await page.waitForTimeout(250);
  await page.locator('#viewport').screenshot({path:'screenshots/kestrel-night.png'});
  await page.locator('#spin').click();check('turntable can be enabled',await page.locator('#spin').evaluate(b=>b.classList.contains('active')));
  await page.goto(origin+'?debug=1&speed=4&invulnerable=1');
  await page.waitForFunction(()=>window.__nightVector);
  await page.click('#start');await page.waitForFunction(()=>__nightVector.inspect().elapsed>=19.6);
  const inGame=await page.evaluate(()=>{__nightVector.pause();return __nightVector.inspect();});
  const fighters=inGame.enemies.filter(e=>e.type==='interceptor');
  check('stage interceptor waves use the new design',fighters.length>0&&fighters.every(e=>e.design==='Azure Kestrel'));
  await page.addStyleTag({content:'#pause-panel{display:none!important}'});
  await page.screenshot({path:'screenshots/kestrel-game.png'});
  await page.evaluate(()=>__nightVector.retry());
  check('retry still starts the game',await page.evaluate(()=>__nightVector.inspect().state==='playing'));
  check('no browser errors or missing assets',report.errors.length===0);
  await writeFile('output/kestrel/browser-verification.json',JSON.stringify(report,null,2));console.log(JSON.stringify(report,null,2));
}finally{await browser.close();}

