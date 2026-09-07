export const clamp=(x,a,b)=>Math.max(a,Math.min(b,x));
export const damp=(a,b,lambda,dt)=>a+(b-a)*(1-Math.exp(-lambda*dt));
export function segmentSphere(a,b,c,r){const dx=b.x-a.x,dy=b.y-a.y,dz=b.z-a.z;const n=dx*dx+dy*dy+dz*dz;const t=n?clamp(((c.x-a.x)*dx+(c.y-a.y)*dy+(c.z-a.z)*dz)/n,0,1):0;return (a.x+dx*t-c.x)**2+(a.y+dy*t-c.y)**2+(a.z+dz*t-c.z)**2<=r*r;}
export class LockSystem{
  constructor(max=8){this.max=max;this.targets=[];this.timer=0;this.cooldown=0;}
  clear(){this.targets=[];this.timer=0;}
  update(dt,held,candidate){this.cooldown=Math.max(0,this.cooldown-dt);this.targets=this.targets.filter(t=>t.hp>0&&!t.removed);if(!held){this.timer=0;return false;}if(this.cooldown>0||!candidate||candidate.hp<=0||this.targets.length>=this.max){this.timer=0;return false;}const count=this.targets.filter(t=>t===candidate).length;const cap=candidate.boss?8:Math.min(3,Math.ceil(candidate.hp/11));if(count>=cap){this.timer=0;return false;}this.timer+=dt;if(this.timer>=.12){this.targets.push(candidate);this.timer=0;return true;}return false;}
  release(){const result=this.targets.filter(t=>t.hp>0&&!t.removed);this.clear();if(result.length)this.cooldown=.48;return result;}
}
export function routeX(s){return 28*Math.sin(s/240)+10*Math.sin(s/90);}
export function routeSlope(s){return 28/240*Math.cos(s/240)+10/90*Math.cos(s/90);}
export function seeded(seed){let a=seed>>>0;return()=>{a+=0x6D2B79F5;let t=a;t=Math.imul(t^t>>>15,t|1);t^=t+Math.imul(t^t>>>7,t|61);return((t^t>>>14)>>>0)/4294967296;};}
export const WAVE_TIMES=[4,10,16,22,29,36,43,50,57,64,71,78,85,92,99,106,113];
