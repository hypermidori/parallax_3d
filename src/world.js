import * as THREE from 'three';
import {GLTFLoader} from 'three/addons/loaders/GLTFLoader.js';
import {EffectComposer} from 'three/addons/postprocessing/EffectComposer.js';
import {RenderPass} from 'three/addons/postprocessing/RenderPass.js';
import {UnrealBloomPass} from 'three/addons/postprocessing/UnrealBloomPass.js';
import {OutputPass} from 'three/addons/postprocessing/OutputPass.js';
import {routeX,routeSlope,CITY_ROUTE,LOOP_X,loopChunkIndex} from './city-route.js';
import {applyHeroFrame,installHeroAnimation} from './hero-frames.js';
const UP=new THREE.Vector3(0,1,0);
export function trackPoint(s,side=0,height=0){const slope=routeSlope(s),n=Math.sqrt(1+slope*slope);return new THREE.Vector3(routeX(s)+side/n,height,-s+side*slope/n);}
export class GameWorld{
  constructor(canvas){
    this.renderer=new THREE.WebGLRenderer({canvas,antialias:true,powerPreference:'high-performance'});this.renderer.setPixelRatio(Math.min(devicePixelRatio,1.5));this.renderer.outputColorSpace=THREE.SRGBColorSpace;this.renderer.toneMapping=THREE.ACESFilmicToneMapping;this.renderer.toneMappingExposure=1.1;
    this.scene=new THREE.Scene;this.scene.fog=new THREE.FogExp2(0x071b34,.0032);this.camera=new THREE.PerspectiveCamera(59,1,.15,1500);
    this.scene.add(new THREE.HemisphereLight(0x93c5f5,0x111e30,1.6));const sun=new THREE.DirectionalLight(0x77a9ff,2);sun.position.set(-60,120,30);this.scene.add(sun);const fill=new THREE.DirectionalLight(0x9dc2e0,.5);fill.position.set(40,10,-20);this.scene.add(fill);
    this.composer=new EffectComposer(this.renderer);this.composer.addPass(new RenderPass(this.scene,this.camera));this.bloom=new UnrealBloomPass(new THREE.Vector2(1280,720),.35,.35,.8);this.composer.addPass(this.bloom);this.composer.addPass(new OutputPass);
    this.dynamic=new THREE.Group;this.scene.add(this.dynamic);this.kit={};this.chunks=[];this.loopChunks=[];
    const skyGeo=new THREE.SphereGeometry(1200,32,18);const skyMat=new THREE.ShaderMaterial({side:THREE.BackSide,depthWrite:false,fog:false,uniforms:{},vertexShader:'varying vec3 vDirection; void main(){vDirection=position;gl_Position=projectionMatrix*modelViewMatrix*vec4(position,1.);}',fragmentShader:`varying vec3 vDirection;float hash(vec2 p){return fract(sin(dot(p,vec2(12.9898,78.233)))*43758.5453);}void main(){vec3 d=normalize(vDirection);float y=clamp(d.y,0.,1.);vec3 col=mix(vec3(.008,.027,.067),vec3(.001,.004,.013),pow(y,.45));vec2 uv=vec2(atan(d.z,d.x),asin(d.y))*160.;float h=hash(floor(uv));float star=step(.997,h)*pow(max(0.,1.-length(fract(uv)-.5)*3.),8.)*smoothstep(.08,.4,y);col+=vec3(.22,.32,.45)*star;float mist=sin(d.x*30.+d.z*15.)*sin(d.z*40.-d.y*34.);col+=vec3(.001,.004,.009)*smoothstep(.1,.8,mist)*smoothstep(0.,.2,y);gl_FragColor=vec4(col,1.);}`});this.sky=new THREE.Mesh(skyGeo,skyMat);this.scene.add(this.sky);
    this.sharedGeometry={shot:new THREE.SphereGeometry(.10,6,4),bullet:new THREE.IcosahedronGeometry(.22,1),spark:new THREE.IcosahedronGeometry(.13,0)};
    this.sharedMaterial={shot:new THREE.MeshBasicMaterial({color:0x9affef,toneMapped:false}),bullet:new THREE.MeshBasicMaterial({color:new THREE.Color(3,.11,.45),toneMapped:false}),spark:new THREE.MeshBasicMaterial({color:0x9df4ff,toneMapped:false})};
  }
  async load(onProgress){const loader=new GLTFLoader;let count=0;const done=()=>onProgress(++count/3);
    const [city,enemies,hero]=await Promise.all([loader.loadAsync('/assets/night-city.glb').then(x=>{done();return x}),loader.loadAsync('/assets/enemy-kit.glb').then(x=>{done();return x}),new THREE.TextureLoader().loadAsync('/assets/player-flight-keyed.png').then(x=>{done();return x})]);
    this.city=city.scene;this.scene.add(this.city);this.city.traverse(o=>{if(o.isMesh){o.frustumCulled=true;if(o.material.map)o.material.map.anisotropy=Math.min(8,this.renderer.capabilities.getMaxAnisotropy());if(o.material.name==='Office windows')o.material.emissiveIntensity=.65;if(o.material.name==='Concrete facade')o.material.emissiveIntensity=.14;}});
    this.chunks=this.city.children.filter(o=>/^city_\d/.test(o.name));for(const ch of this.chunks)ch.userData.index=Number(ch.name.match(/\d+/)[0]);
    const templates=this.city.children.filter(o=>/^boss_\d/.test(o.name)).sort((a,b)=>a.name.localeCompare(b.name));
    if(templates.length!==CITY_ROUTE.loopVariants)throw new Error('City loop asset needs rebuilding');
    this.loopChunks=Array.from({length:CITY_ROUTE.poolSize},(_,slot)=>{
      const source=templates[slot%templates.length],ch=slot<templates.length?source:source.clone(true);
      ch.name='loop_slot_'+slot;ch.userData.slot=slot;this.city.add(ch);return ch;
    });

    enemies.scene.traverse(o=>{if(o.isMesh){o.material.side=THREE.DoubleSide;if(o.material.map)o.material.map.anisotropy=4;if(o.material.name!=='Illuminated details'){o.material.emissive.set(0xffffff);o.material.emissiveMap=o.material.map;o.material.emissiveIntensity=o.material.name==='Painted details'?1.3:.45;o.material.metalness=.15;}}});for(const ob of enemies.scene.children)this.kit[ob.name]=ob;
    hero.colorSpace=THREE.SRGBColorSpace;hero.magFilter=THREE.NearestFilter;hero.minFilter=THREE.NearestFilter;hero.generateMipmaps=false;this.heroTexture=hero;
    const material=new THREE.SpriteMaterial({map:hero,transparent:true,depthWrite:false,alphaTest:.4,fog:false,toneMapped:false});installHeroAnimation(material);
    this.hero=new THREE.Sprite(material);this.hero.scale.set(2.45,3.65,1);this.hero.visible=false;this.scene.add(this.hero);this.setHeroFrame(0,0);this.resize();
  }
  setHeroFrame(row,col){applyHeroFrame(this.hero,this.heroTexture,row,col);}
  cloneEnemy(type){if(type==='boss'){const group=new THREE.Group;for(const name of ['sentinel_body','sentinel_leg_0','sentinel_leg_1','sentinel_leg_2','sentinel_leg_3']){const ob=this.kit[name]?.clone(true);if(ob)group.add(ob);}group.scale.setScalar(1.1);return group;}const model=this.kit[type];if(!model)throw new Error('Missing enemy model: '+type);return model.clone(true);}
  resize(){const w=innerWidth,h=innerHeight;this.renderer.setSize(w,h,false);this.composer.setSize(w,h);this.camera.aspect=w/h;this.camera.fov=w<h?67:59;this.camera.updateProjectionMatrix();}
  setCamera(distance,bank=0,title=false){const h=title?8:9.5+Math.sin(distance/200)*.9;this.camera.position.copy(trackPoint(distance,0,h));const look=trackPoint(distance+110,0,h+1.2);this.camera.up.set(bank*.06,1,0).normalize();this.camera.lookAt(look);this.sky.position.copy(this.camera.position);
    for(const ch of this.chunks){const center=ch.userData.index*CITY_ROUTE.chunkLength+CITY_ROUTE.chunkLength/2;ch.visible=center>distance-180&&center<distance+900;}
    for(const ch of this.loopChunks){
      const index=loopChunkIndex(distance,ch.userData.slot),start=CITY_ROUTE.loopStart+index*CITY_ROUTE.chunkLength;
      ch.userData.loopIndex=index;ch.userData.start=start;
      ch.position.set(LOOP_X,0,-start);
      const center=start+CITY_ROUTE.chunkLength/2;ch.visible=center>distance-180&&center<distance+900;
    }}
  render(){this.renderer.info.autoReset=false;this.renderer.info.reset();this.composer.render();}
  project(point){const p=point.clone().project(this.camera);return{x:p.x,y:p.y,z:p.z};}
  aimPoint(aim,distance=100){const p=new THREE.Vector3(aim.x,aim.y,.5).unproject(this.camera);return p.sub(this.camera.position).normalize().multiplyScalar(distance).add(this.camera.position);}
  orientToFlight(ob,s){ob.rotation.y=-Math.atan(routeSlope(s));}
  clearDynamic(){for(const ob of [...this.dynamic.children]){this.dynamic.remove(ob);if(ob.userData.disposableGeometry)ob.geometry.dispose();if(ob.userData.ownMaterial)ob.material.dispose();}}
}
