import * as THREE from 'C:/workspace/codex_sample/node_modules/three/build/three.module.js';
import { OrbitControls } from 'C:/workspace/codex_sample/node_modules/three/examples/jsm/controls/OrbitControls.js';
import { GLTFLoader } from 'C:/workspace/codex_sample/node_modules/three/examples/jsm/loaders/GLTFLoader.js';

const scene=new THREE.Scene();scene.background=new THREE.Color('#171c29');
const camera=new THREE.PerspectiveCamera(32,1,.01,100);camera.position.set(2.25,1.4,3.7);
const renderer=new THREE.WebGLRenderer({antialias:true});renderer.setPixelRatio(Math.min(devicePixelRatio,2));
renderer.outputColorSpace=THREE.SRGBColorSpace;renderer.toneMapping=THREE.ACESFilmicToneMapping;renderer.toneMappingExposure=1.05;
document.querySelector('#viewport').append(renderer.domElement);
const controls=new OrbitControls(camera,renderer.domElement);controls.target.set(0,.94,0);controls.enableDamping=true;
controls.minDistance=.5;controls.maxDistance=6;controls.maxPolarAngle=Math.PI*.92;
scene.add(new THREE.HemisphereLight(0xe8eaff,0x555062,2.2));
for(const [pos,color,power] of [[[2,4,3],0xfff0df,2.7],[[-3,2,1],0x94baff,1.3],[[0,3,-3],0xc9a7ff,2]]){
 const l=new THREE.DirectionalLight(color,power);l.position.set(...pos);scene.add(l);
}
const grid=new THREE.GridHelper(3,15,0x45445a,0x2a3040);scene.add(grid);
let model,mixer,clip,rotating=false,wire=false;
const clock=new THREE.Clock();
function angle(which){
 controls.target.set(0,.94,0);
 const positions={front:[0,1,3.9],back:[0,1,-3.9],side:[3.9,1,0],perspective:[2.25,1.4,3.7]};
 camera.position.set(...positions[which]);controls.update();
 document.querySelectorAll('[data-view]').forEach(b=>b.classList.toggle('active',b.dataset.view===which));
}
document.querySelectorAll('[data-view]').forEach(b=>b.onclick=()=>angle(b.dataset.view));
document.querySelector('#rotate').onclick=e=>{rotating=!rotating;controls.autoRotate=rotating;e.target.classList.toggle('active',rotating);};
document.querySelector('#wire').onclick=e=>{wire=!wire;model?.traverse(o=>{if(o.isMesh)o.material.wireframe=wire;});e.target.classList.toggle('active',wire);};
document.querySelector('#motion').onclick=e=>{
 if(!clip)return;
 const running=e.target.classList.toggle('active');
 if(running){clip.reset().play();}else{mixer.stopAllAction();model.traverse(o=>{if(o.isSkinnedMesh)o.skeleton.pose();});}
 e.target.textContent=running?'ホバー停止':'ホバー再生';
};
document.querySelector('#grid').onclick=e=>{grid.visible=!grid.visible;e.target.classList.toggle('active',grid.visible);};
const bytes=Uint8Array.from(atob(window.PLAYER_GLB),c=>c.charCodeAt(0));
new GLTFLoader().parse(bytes.buffer,'',gltf=>{
 model=gltf.scene;scene.add(model);
 mixer=new THREE.AnimationMixer(model);if(gltf.animations[0])clip=mixer.clipAction(gltf.animations[0]);
 model.traverse(o=>{if(o.isSkinnedMesh)o.skeleton.pose();});
 document.querySelector('#status').textContent='ドラッグで回転 · ホイールで拡大';
 document.body.dataset.loaded='true';
},error=>{document.querySelector('#status').textContent='モデルを読み込めませんでした: '+error.message;console.error(error);});
function resize(){const v=document.querySelector('#viewport');renderer.setSize(v.clientWidth,v.clientHeight);camera.aspect=v.clientWidth/v.clientHeight;camera.updateProjectionMatrix();}
new ResizeObserver(resize).observe(document.querySelector('#viewport'));resize();
renderer.setAnimationLoop(()=>{const dt=Math.min(clock.getDelta(),.1);mixer?.update(dt);controls.update();renderer.render(scene,camera);});
