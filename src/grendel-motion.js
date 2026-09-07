// Hovering uses simulation time, so pause/retry and accelerated verification agree.
// The four legs stay folded. Only the hull attitude and attached exhausts move.
const jetsByModel=new WeakMap();
export const GRENDEL_HOVER_HEIGHT=1.8;
export function applyGrendelPose(model,time,height=GRENDEL_HOVER_HEIGHT){
  model.position.y=height+Math.sin(time*1.45)*.11+Math.sin(time*.63)*.045;
  model.rotation.order='YXZ';
  model.rotation.x=.018+Math.sin(time*1.1)*.009;
  model.rotation.z=Math.sin(time*.55)*.025;
  let jets=jetsByModel.get(model);
  if(!jets){jets=Array.from({length:4},(_,i)=>model.getObjectByName('HoverJet'+i));jetsByModel.set(model,jets);}
  jets.forEach((jet,i)=>{if(jet)jet.scale.y=1+Math.sin(time*6.5+i*.9)*.09;});
}
export function resetGrendelPose(model){
  model.position.y=0;model.rotation.x=0;model.rotation.z=0;
  for(let i=0;i<4;i++){const jet=model.getObjectByName('HoverJet'+i);if(jet)jet.scale.y=1;}
}
