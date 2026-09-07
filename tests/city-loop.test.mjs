import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {CITY_ROUTE as C,LOOP_X,routeX,routeSlope,loopChunkIndex} from '../src/city-route.js';

test('approach joins the endless boulevard without position or tangent jumps',()=>{
  for(const s of [C.transitionStart,C.loopStart]){
    assert.ok(Math.abs(routeX(s-.0001)-routeX(s+.0001))<.0001);
    assert.ok(Math.abs(routeSlope(s-.0001)-routeSlope(s+.0001))<.00001);
  }
  assert.equal(routeX(C.loopStart+1e6),LOOP_X);
  assert.equal(routeSlope(C.loopStart+1e6),0);
});
test('pool covers the view for a full day and relocates only behind the camera',()=>{
  assert.equal(C.poolSize%C.loopVariants,0);
  let previous;
  for(let distance=0;distance<24*3600*C.flightSpeed;distance+=37){
    const indices=Array.from({length:C.poolSize},(_,i)=>loopChunkIndex(distance,i));
    const sorted=[...indices].sort((a,b)=>a-b);
    assert.equal(new Set(indices).size,C.poolSize);
    for(let i=1;i<sorted.length;i++)assert.equal(sorted[i]-sorted[i-1],1);
    if(distance>=C.loopStart)assert.ok(C.loopStart+sorted[0]*C.chunkLength<=distance);
    assert.ok(C.loopStart+(sorted.at(-1)+1)*C.chunkLength>distance+900);
    if(previous)indices.forEach((index,i)=>{
      assert.equal(index%C.loopVariants,i%C.loopVariants);
      if(index!==previous[i])assert.ok(C.loopStart+(previous[i]+1)*C.chunkLength<distance-170);
    });
    previous=indices;
  }
});
// Read the exported asset, not just the procedural source.
const bytes=readFileSync(new URL('../public/assets/night-city.glb',import.meta.url));
const jsonSize=bytes.readUInt32LE(12),gltf=JSON.parse(bytes.subarray(20,20+jsonSize).toString());
const bin=bytes.subarray(28+jsonSize);
function attribute(index,size){
  const a=gltf.accessors[index],v=gltf.bufferViews[a.bufferView],offset=(v.byteOffset||0)+(a.byteOffset||0),stride=v.byteStride||size*4;
  assert.equal(a.componentType,5126);
  return Array.from({length:a.count},(_,i)=>Array.from({length:size},(_,j)=>bin.readFloatLE(offset+i*stride+j*4)));
}
function road(name){
  const n=gltf.nodes.find(n=>n.name===name+'_Road asphalt'),p=gltf.meshes[n.mesh].primitives[0];
  return attribute(p.attributes.POSITION,3);
}
test('all four Blender loop roads meet edge to edge, including last to first',()=>{
  for(let i=0;i<C.loopVariants;i++){
    const points=road('boss_'+String(i).padStart(2,'0'));
    for(const z of [0,-C.chunkLength])for(const x of [-12,12]){
      assert.ok(points.some(p=>Math.abs(p[0]-x)<1e-5&&Math.abs(p[1]-.025)<1e-5&&Math.abs(p[2]-z)<1e-5));
    }
    assert.ok(points.every(p=>p[2]<=0&&p[2]>=-C.chunkLength));
  }
  const last=road('city_09');
  for(const side of [-12,12])assert.ok(last.some(p=>Math.abs(p[0]-(LOOP_X+side))<1e-4&&Math.abs(p[2]+C.loopStart)<1e-4));
});
test('every exported environment primitive has UVs and an embedded image texture',()=>{
  for(const m of gltf.meshes)for(const p of m.primitives){
    assert.ok(p.attributes.TEXCOORD_0!==undefined);
    const t=gltf.materials[p.material].pbrMetallicRoughness.baseColorTexture;
    assert.ok(t);
    assert.ok(gltf.images[gltf.textures[t.index].source].bufferView!==undefined);
  }
});
test('exported transition road centers follow the runtime flight route',()=>{
  for(const name of ['city_08','city_09']){
    const points=road(name);
    const start=Number(name.slice(-2))*180;
    for(let s=start;s<=start+180;s+=6)for(const side of [-12,12]){
      const slope=routeSlope(s),n=Math.hypot(1,slope);
      const x=routeX(s)+side/n,z=-s+side*slope/n;
      assert.ok(points.some(p=>Math.abs(p[0]-x)<1e-4&&Math.abs(p[2]-z)<2e-4),'exported ribbon at '+s);
    }
  }
});
