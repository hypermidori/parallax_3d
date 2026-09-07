import {clamp} from './combat.js';
export class FlightInput{
  constructor(canvas,{pause,start}){this.aim={x:0,y:0};this.held=false;this.released=false;this.cancelled=false;this.keys=new Set;this.pointer=null;this.source='mouse';this.enabled=false;this.padHeld=false;this.padPause=false;this.canvas=canvas;
    const locate=e=>{const r=canvas.getBoundingClientRect();this.aim.x=clamp((e.clientX-r.left)/r.width*2-1,-.92,.92);this.aim.y=clamp(1-(e.clientY-r.top-(e.pointerType==='touch'?48:0))/r.height*2,-.82,.82);};
    canvas.addEventListener('pointerdown',e=>{if(!this.enabled||this.pointer!==null)return;e.preventDefault();this.pointer=e.pointerId;this.source=e.pointerType;canvas.setPointerCapture(e.pointerId);locate(e);this.held=true;});
    canvas.addEventListener('pointermove',e=>{if(!this.enabled)return;if(e.pointerType==='mouse'||e.pointerId===this.pointer){locate(e);this.source=e.pointerType;}});
    canvas.addEventListener('pointerup',e=>{if(e.pointerId!==this.pointer)return;this.pointer=null;this.released=this.held;this.held=false;});
    canvas.addEventListener('pointercancel',()=>{this.pointer=null;this.held=false;this.cancelled=true;});canvas.addEventListener('contextmenu',e=>e.preventDefault());
    window.addEventListener('keydown',e=>{if(['Space','ArrowUp','ArrowDown','ArrowLeft','ArrowRight'].includes(e.code))e.preventDefault();if(e.repeat)return;this.keys.add(e.code);if(e.code==='Escape'||e.code==='KeyP')pause();if(e.code==='Enter')start();if(this.enabled&&['Space','KeyZ'].includes(e.code)){this.source='keyboard';this.held=true;}});
    window.addEventListener('keyup',e=>{this.keys.delete(e.code);if(['Space','KeyZ'].includes(e.code)){this.released=this.held;this.held=false;}});
    window.addEventListener('blur',()=>{this.reset();pause(true);});}
  reset(){this.keys.clear();this.held=false;this.released=false;this.cancelled=true;this.pointer=null;this.padHeld=false;}
  update(dt){if(!this.enabled)return;let x=(this.keys.has('KeyD')||this.keys.has('ArrowRight')?1:0)-(this.keys.has('KeyA')||this.keys.has('ArrowLeft')?1:0);let y=(this.keys.has('KeyW')||this.keys.has('ArrowUp')?1:0)-(this.keys.has('KeyS')||this.keys.has('ArrowDown')?1:0);
    const pad=[...(navigator.getGamepads?.()??[])].find(Boolean);if(pad){const ax=pad.axes[0]??0,ay=pad.axes[1]??0;if(Math.abs(ax)>.15)x+=ax;if(Math.abs(ay)>.15)y-=ay;const held=!!(pad.buttons[0]?.pressed||pad.buttons[7]?.pressed);if(held&&!this.padHeld){this.held=true;this.source='gamepad';}if(!held&&this.padHeld){this.held=false;this.released=true;}this.padHeld=held;const ps=!!pad.buttons[9]?.pressed;if(ps&&!this.padPause)window.dispatchEvent(new KeyboardEvent('keydown',{code:'Escape'}));this.padPause=ps;}
    if(x||y){this.aim.x=clamp(this.aim.x+x*dt*1.7,-.92,.92);this.aim.y=clamp(this.aim.y+y*dt*1.7,-.82,.82);}}
}
