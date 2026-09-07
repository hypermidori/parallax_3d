export class LandscapeMode {
  constructor(onPortrait) {
    this.onPortrait = onPortrait;
    this.touch = matchMedia('(pointer: coarse)');
    this.overlay = document.getElementById('rotate-screen');
    this.button = document.getElementById('landscape-button');
    this.pending = false;
    this.button.hidden = !document.getElementById('app').requestFullscreen && !screen.orientation?.lock;
    this.button.addEventListener('click', () => this.request());
    window.addEventListener('resize', () => this.update());
    this.touch.addEventListener('change', () => this.update());
    document.addEventListener('fullscreenchange', () => this.update());
    screen.orientation?.addEventListener('change', () => this.update());
    this.update();
  }

  get blocked() {
    return this.touch.matches && innerHeight > innerWidth;
  }

  update() {
    const blocked = this.blocked;
    this.overlay.classList.toggle('hidden', !blocked);
    // Prevent keyboard/accessibility activation of controls behind the gate.
    for (const id of ['menu', 'pause-panel', 'result', 'hud', 'telemetry']) {
      document.getElementById(id).inert = blocked;
    }
    if (blocked) this.onPortrait();
  }

  async request() {
    if (!this.touch.matches || this.pending) return;
    this.pending = true;
    this.button.disabled = true;
    try {
      const app = document.getElementById('app');
      // Request fullscreen while the tap still has user activation.
      if (!document.fullscreenElement && app.requestFullscreen) {
        try { await app.requestFullscreen(); } catch { /* Rotation remains manual. */ }
      }
      // Lock can also work without fullscreen in an installed web app.
      if (screen.orientation?.lock) {
        try { await screen.orientation.lock('landscape'); } catch { /* Keep the portrait gate. */ }
      }
    } finally {
      this.pending = false;
      this.button.disabled = false;
      this.update();
    }
  }
}
