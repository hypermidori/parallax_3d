import config from '../config/city-route.json' with {type:'json'};
export const CITY_ROUTE=Object.freeze(config);
const originalX=s=>28*Math.sin(s/240)+10*Math.sin(s/90);
const originalSlope=s=>28/240*Math.cos(s/240)+10/90*Math.cos(s/90);
const {transitionStart,loopStart,chunkLength,poolSize}=CITY_ROUTE;
export const LOOP_X=originalX(loopStart);
// Smoothstep preserves position, tangent and curvature at both joins.
export function routeX(s){
  if(s<=transitionStart)return originalX(s);
  if(s>=loopStart)return LOOP_X;
  const t=(s-transitionStart)/(loopStart-transitionStart),w=t*t*t*(10+t*(-15+6*t));
  return originalX(s)*(1-w)+LOOP_X*w;
}
export function routeSlope(s){
  if(s<=transitionStart)return originalSlope(s);
  if(s>=loopStart)return 0;
  const length=loopStart-transitionStart,t=(s-transitionStart)/length;
  const w=t*t*t*(10+t*(-15+6*t)),dw=30*t*t*(1-t)*(1-t)/length;
  return originalSlope(s)*(1-w)+(LOOP_X-originalX(s))*dw;
}
// Each slot retains its geometry; relocation only happens behind the camera.
// poolSize is a multiple of loopVariants, keeping architecture deterministic.
export function loopChunkIndex(distance,slot){
  const first=Math.max(0,Math.floor((distance-180-loopStart)/chunkLength));
  return slot+poolSize*Math.ceil((first-slot)/poolSize);
}
