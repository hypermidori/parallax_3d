import './enemy-lab.css';
import {applyGrendelPose,resetGrendelPose} from './grendel-motion.js';
import {ENEMY_DESIGNS} from './enemy-designs.js';
import * as THREE from 'three';
import {GLTFLoader} from 'three/addons/loaders/GLTFLoader.js';
import {OrbitControls} from 'three/addons/controls/OrbitControls.js';
const canvas=document.getElementById('model-canvas'),viewport=document.getElementById('viewport');
const renderer=new THREE.WebGLRenderer({canvas,antialias:true});renderer.setPixelRatio(Math.min(devicePixelRatio,2));renderer.outputColorSpace=THREE.SRGBColorSpace;renderer.toneMapping=THREE.ACESFilmicToneMapping;renderer.toneMappingExposure=1.2;
const scene=new THREE.Scene();scene.background=new THREE.Color('#182431');
const camera=new THREE.OrthographicCamera(-6,6,6,-6,.1,100);camera.position.set(9,7,-11);camera.zoom=1.22;
const controls=new OrbitControls(camera,canvas);controls.enableDamping=true;controls.target.set(0,.4,0);controls.autoRotateSpeed=1.4;controls.minZoom=.5;controls.maxZoom=3;
const hemi=new THREE.HemisphereLight(0xddecff,0x384657,2.3);scene.add(hemi);
const key=new THREE.DirectionalLight(0xffefdb,3);key.position.set(-4,8,-6);scene.add(key);
const rim=new THREE.DirectionalLight(0x82c9ff,2);rim.position.set(5,3,6);scene.add(rim);
function resize(){const w=viewport.clientWidth,h=viewport.clientHeight,a=w/h;renderer.setSize(w,h,false);camera.left=-5.5*a;camera.right=5.5*a;camera.top=5.5;camera.bottom=-5.5;camera.updateProjectionMatrix();}
new ResizeObserver(resize).observe(viewport);resize();
let modelTarget=new THREE.Vector3(0,.4,0),fitScale=1;
const views={beauty:[9,7,-11],top:[0,15,0],front:[0,0,-15],side:[-15,0,0]};
for(const button of document.querySelectorAll('[data-view]'))button.onclick=()=>{controls.autoRotate=false;document.getElementById('spin').classList.remove('active');camera.up.set(0,button.dataset.view==='top'?0:1,button.dataset.view==='top'?1:0);camera.position.copy(modelTarget).add(new THREE.Vector3(...views[button.dataset.view]));camera.zoom=fitScale*{beauty:1.22,top:1.03,front:1.35,side:1.1}[button.dataset.view];camera.updateProjectionMatrix();controls.target.copy(modelTarget);controls.update();document.querySelectorAll('[data-view]').forEach(b=>b.classList.toggle('active',b===button));};
document.getElementById('spin').onclick=event=>{controls.autoRotate=!controls.autoRotate;event.target.classList.toggle('active',controls.autoRotate);};
let night=false;document.getElementById('lighting').onclick=event=>{night=!night;hemi.intensity=night?1.2:2.3;key.intensity=night?.7:3;key.color.set(night?0x77a9ff:0xffefdb);scene.background.set(night?'#071322':'#182431');event.target.classList.toggle('active',night);};
const selector=document.getElementById('model-select'),params=new URLSearchParams(location.search);
let currentModel=null,requestVersion=0,currentType=null,hoverEnabled=true,hoverTime=0;
const motionButton=document.getElementById('hover-motion');
motionButton.onclick=()=>{hoverEnabled=!hoverEnabled;motionButton.classList.toggle('active',hoverEnabled);if(currentModel&&!hoverEnabled)resetGrendelPose(currentModel);};
selector.value=ENEMY_DESIGNS[params.get('model')]?params.get('model'):'interceptor';
async function loadModel(){
  const version=++requestVersion,type=selector.value,spec=ENEMY_DESIGNS[type];
  window.__enemyLab={ready:false};
  document.getElementById('loading').hidden=false;
  document.querySelector('h1').textContent=spec.title;document.title=spec.title+' / MODEL STUDY';
  document.querySelector('.reference img').src='/assets/'+spec.reference;
  document.querySelector('.reference img').alt=spec.title+' の２Dデザイン画';
  document.getElementById('reference-source').textContent=spec.source;
  try{
    const asset=await new GLTFLoader().loadAsync('/assets/'+spec.slug+'.glb');
    const dispose=model=>{const maps=new Set();model.traverse(o=>{if(o.isMesh){o.geometry.dispose();for(const value of Object.values(o.material))if(value?.isTexture)maps.add(value);o.material.dispose();}});maps.forEach(t=>t.dispose());};
    if(version!==requestVersion){dispose(asset.scene);return;}
    if(currentModel){scene.remove(currentModel);dispose(currentModel);}
    currentModel=asset.scene;currentType=type;hoverTime=0;hoverEnabled=true;motionButton.hidden=type!=='boss';motionButton.classList.toggle('active',hoverEnabled);scene.add(currentModel);
    let triangles=0,meshes=0,textured=0;
    currentModel.traverse(o=>{if(o.isMesh){meshes++;triangles+=(o.geometry.index?.count??o.geometry.attributes.position.count)/3;if(o.material.map&&o.geometry.attributes.uv)textured++;if(o.material.map)o.material.map.anisotropy=8;}});
    const box=new THREE.Box3().setFromObject(currentModel),size=box.getSize(new THREE.Vector3);
    modelTarget=box.getCenter(new THREE.Vector3);fitScale=8.72/Math.max(size.x,size.y,size.z);controls.minZoom=fitScale*.5;controls.maxZoom=fitScale*3;
    document.querySelector('[data-view="beauty"]').click();
    document.getElementById('loading').hidden=true;
    document.getElementById('model-stats').textContent=triangles.toLocaleString()+' triangles / '+textured+' textured meshes / GLB';
    window.__enemyLab={ready:true,type,triangles,meshes,textured,hasShotOrigin:!!currentModel.getObjectByName('ShotOrigin'),hasAimTarget:!!currentModel.getObjectByName('AimTarget'),hoverJets:Array.from({length:4},(_,i)=>currentModel.getObjectByName('HoverJet'+i)).filter(Boolean).length};
  }catch(e){document.getElementById('loading').textContent=e.message;console.error(e);}
}
selector.onchange=()=>{history.replaceState(null,'','?model='+selector.value);loadModel();};
loadModel();
let previousTime=performance.now();
renderer.setAnimationLoop(now=>{const dt=Math.min(.05,(now-previousTime)/1000);previousTime=now;if(currentType==='boss'&&currentModel&&hoverEnabled){hoverTime+=dt;applyGrendelPose(currentModel,hoverTime,0);}controls.update();renderer.render(scene,camera);});
