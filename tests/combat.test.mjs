import test from 'node:test';
import assert from 'node:assert/strict';
import {LockSystem,segmentSphere,routeX,routeSlope} from '../src/combat.js';

test('fast projectiles hit across a sphere even when endpoints miss',()=>{
  assert.equal(segmentSphere({x:-20,y:0,z:0},{x:20,y:0,z:0},{x:0,y:0,z:0},1),true);
  assert.equal(segmentSphere({x:-20,y:2,z:0},{x:20,y:2,z:0},{x:0,y:0,z:0},1),false);
  assert.equal(segmentSphere({x:2,y:0,z:0},{x:3,y:0,z:0},{x:0,y:0,z:0},1),false);
  assert.equal(segmentSphere({x:0,y:0,z:0},{x:0,y:0,z:0},{x:0,y:0,z:0},1),true);
});
test('multi-lock accumulates up to eight and consumes targets exactly once',()=>{
  const system=new LockSystem(),boss={hp:1000,boss:true};
  for(let i=0;i<20;i++)system.update(.13,true,boss);
  assert.equal(system.targets.length,8);
  assert.equal(system.release().length,8);
  assert.equal(system.release().length,0);
  assert.equal(system.update(.1,true,boss),false);
  assert.equal(system.update(.5,true,boss),true);
});
test('destroyed targets are removed and ordinary enemies cannot consume all locks',()=>{
  const system=new LockSystem(),small={hp:12},other={hp:20};
  for(let i=0;i<8;i++)system.update(.13,true,small);
  assert.equal(system.targets.length,2);
  system.update(.13,true,other);small.hp=0;system.update(.01,true,null);
  assert.deepEqual(system.targets,[other]);other.removed=true;
  assert.deepEqual(system.release(),[]);
});
test('cancel clears partial lock charge as well as accumulated targets',()=>{
  const system=new LockSystem(),target={hp:30};
  system.update(.13,true,target);system.update(.1,true,target);system.clear();
  assert.equal(system.targets.length,0);assert.equal(system.update(.03,true,target),false);
});
test('route tangent agrees with the curved city path',()=>{
  for(let s=0;s<2160;s+=17){const derivative=(routeX(s+.001)-routeX(s-.001))/.002;assert.ok(Math.abs(derivative-routeSlope(s))<1e-7);}
});
