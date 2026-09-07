export class GameAudio{
 constructor(){this.muted=localStorage.getItem('nv-muted')==='1';this.ready=false;this.ctx=null;this.music=null;this.loaded=new Map;}
 async unlock(){if(!this.ctx)this.ctx=new (window.AudioContext||window.webkitAudioContext)();await this.ctx.resume();this.ready=true;}
 setMuted(value){this.muted=value;localStorage.setItem('nv-muted',value?'1':'0');if(this.music)this.music.muted=value;}
 bgm(boss=false){const src='/assets/'+(boss?'city-approach-boss-bgm.mp3':'city-approach-bgm.mp3');if(this.music?.getAttribute('src')===src){this.music.play().catch(()=>{});return;}this.music?.pause();this.music=new Audio(src);this.music.loop=true;this.music.volume=.27;this.music.muted=this.muted;this.music.play().catch(()=>{});}
 pause(){this.music?.pause();}
 resume(){this.music?.play().catch(()=>{});}
 tone(freq=600,duration=.05,type='sine',gain=.025,end=300){if(!this.ctx||this.muted||!this.ready)return;const o=this.ctx.createOscillator(),g=this.ctx.createGain(),t=this.ctx.currentTime;o.type=type;o.frequency.setValueAtTime(freq,t);o.frequency.exponentialRampToValueAtTime(Math.max(20,end),t+duration);g.gain.setValueAtTime(gain,t);g.gain.exponentialRampToValueAtTime(.0001,t+duration);o.connect(g);g.connect(this.ctx.destination);o.start(t);o.stop(t+duration);}
 lock(count){this.tone(650+count*120,.08,'sine',.055,1000+count*100);}
 laser(){this.tone(1500,.23,'sawtooth',.024,180);}
 explosion(big=false){this.tone(big?90:160,big?.55:.22,'sawtooth',big?.08:.035,25);}
 hit(){this.tone(110,.3,'square',.04,40);}
}
