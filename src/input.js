import {clamp} from './combat.js';

export const AIM_LIMITS = {left: -.3, right: .3, bottom: -.4, top: .2};

const AIM_SPEED = .85;

export function padDirection(dx, dy, radius) {
  const length = Math.hypot(dx, dy);
  const magnitude = clamp((length / radius - .12) / .88, 0, 1);
  return length ? {x: dx / length * magnitude, y: -dy / length * magnitude} : {x: 0, y: 0};
}

export function lockRadius(width, height) {
  return clamp(Math.min(width, height) * .13, 48, 76);
}

export class FlightInput {
  constructor(canvas, {pause, start}) {
    Object.assign(this, {
      aim: {x: 0, y: 0}, held: false, released: false, cancelled: false,
      keys: new Set(), pointer: null, source: 'mouse', enabled: false,
      padHeld: false, padPause: false, touchPad: null, canvas,
    });
    const locateMouse = event => {
      const rect = canvas.getBoundingClientRect();
      this.aim.x = clamp((event.clientX - rect.left) / rect.width * 2 - 1, AIM_LIMITS.left, AIM_LIMITS.right);
      this.aim.y = clamp(1 - (event.clientY - rect.top) / rect.height * 2, AIM_LIMITS.bottom, AIM_LIMITS.top);
    };
    canvas.addEventListener('pointerdown', event => {
      if (!this.enabled || this.pointer !== null || (event.pointerType === 'mouse' && event.button !== 0)) return;
      event.preventDefault();
      this.pointer = event.pointerId;
      this.source = event.pointerType;
      canvas.setPointerCapture(event.pointerId);
      if (event.pointerType === 'touch') {
        // A new touch anchors the joystick, never the aiming cursor.
        this.touchPad = {x: event.clientX, y: event.clientY, dx: 0, dy: 0,
          radius: clamp(Math.min(innerWidth, innerHeight) * .14, 44, 64)};
      } else locateMouse(event);
      this.held = true;
    });
    canvas.addEventListener('pointermove', event => {
      if (!this.enabled) return;
      if (event.pointerId === this.pointer && this.touchPad) {
        this.touchPad.dx = event.clientX - this.touchPad.x;
        this.touchPad.dy = event.clientY - this.touchPad.y;
      } else if (event.pointerType === 'mouse' && (this.pointer === null || event.pointerId === this.pointer)) {
        locateMouse(event);
        this.source = 'mouse';
      }
    });
    canvas.addEventListener('pointerup', event => {
      if (event.pointerId !== this.pointer) return;
      this.released = this.held;
      this.held = false;
      this.releasePointer();
    });
    const cancel = event => {
      if (event.pointerId !== this.pointer) return;
      this.held = false;
      this.released = false;
      this.cancelled = true;
      this.releasePointer();
    };
    canvas.addEventListener('pointercancel', cancel);
    canvas.addEventListener('lostpointercapture', cancel);
    canvas.addEventListener('contextmenu', event => event.preventDefault());
    window.addEventListener('keydown', event => {
      if (['Space','ArrowUp','ArrowDown','ArrowLeft','ArrowRight'].includes(event.code)) event.preventDefault();
      if (event.repeat) return;
      this.keys.add(event.code);
      if (event.code === 'Escape' || event.code === 'KeyP') pause();
      if (event.code === 'Enter') start();
      if (this.enabled && ['Space', 'KeyZ'].includes(event.code)) {
        this.source = 'keyboard';
        this.held = true;
      }
    });
    window.addEventListener('keyup', event => {
      this.keys.delete(event.code);
      if (['Space', 'KeyZ'].includes(event.code)) {
        this.released = this.held;
        this.held = false;
      }
    });
    window.addEventListener('blur', () => { this.reset(); pause(true); });
    window.addEventListener('resize', () => this.reset());
  }

  releasePointer() {
    const pointer = this.pointer;
    this.pointer = null;
    this.touchPad = null;
    if (pointer !== null && this.canvas.hasPointerCapture(pointer)) this.canvas.releasePointerCapture(pointer);
  }

  reset() {
    this.keys.clear();
    this.held = false;
    this.released = false;
    this.cancelled = true;
    this.padHeld = false;
    this.releasePointer();
  }

  update(dt) {
    if (!this.enabled) return;
    let x = (this.keys.has('KeyD') || this.keys.has('ArrowRight') ? 1 : 0) - (this.keys.has('KeyA') || this.keys.has('ArrowLeft') ? 1 : 0);
    let y = (this.keys.has('KeyW') || this.keys.has('ArrowUp') ? 1 : 0) - (this.keys.has('KeyS') || this.keys.has('ArrowDown') ? 1 : 0);
    const pad = [...(navigator.getGamepads?.() ?? [])].find(Boolean);
    if (pad) {
      const ax = pad.axes[0] ?? 0, ay = pad.axes[1] ?? 0;
      if (Math.abs(ax) > .15) x += ax;
      if (Math.abs(ay) > .15) y -= ay;
      const held = !!(pad.buttons[0]?.pressed || pad.buttons[7]?.pressed);
      if (held && !this.padHeld) { this.held = true; this.source = 'gamepad'; }
      if (!held && this.padHeld) { this.held = false; this.released = true; }
      this.padHeld = held;
      const ps = !!pad.buttons[9]?.pressed;
      if (ps && !this.padPause) window.dispatchEvent(new KeyboardEvent('keydown', {code: 'Escape'}));
      this.padPause = ps;
    }
    if (this.touchPad) {
      const stick = padDirection(this.touchPad.dx, this.touchPad.dy, this.touchPad.radius);
      x += stick.x;
      y += stick.y;
    }
    // Both axes share the same speed and a 30%-wide viewport travel band.
    this.aim.x = clamp(this.aim.x + clamp(x, -1, 1) * dt * AIM_SPEED, AIM_LIMITS.left, AIM_LIMITS.right);
    this.aim.y = clamp(this.aim.y + clamp(y, -1, 1) * dt * AIM_SPEED, AIM_LIMITS.bottom, AIM_LIMITS.top);
  }
}
