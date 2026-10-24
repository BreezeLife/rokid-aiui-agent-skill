// Pure ownership model. These dependency names are NOT AIUI APIs.
const stale = Symbol('stale');

export class Controller {
  constructor(deps) {
    this.deps = deps;
    this.current = null;
    this.visible = true;
    this.mounted = true;
    this.seq = 0;
    this.phase = 'idle';
    this.text = '';
    this.jobs = new Map();
    this.seen = new Set();
    this.waiters = new Set();
    this.trace = [];
    this.cleanupErrors = [];
  }
  owns(op) { return this.current === op && this.mounted; }
  assert(op) { if (!this.owns(op)) throw stale; }
  state(op, phase, text = this.text) {
    this.assert(op);
    this.phase = phase;
    this.text = text;
    this.trace.push({ id: op.id, phase, text });
  }
  retain(op, dispose) {
    let released = false;
    const release = () => {
      if (released) return;
      released = true;
      op.resources.delete(release);
      try { dispose(); } catch (error) { this.cleanupErrors.push(error.message); }
    };
    if (!this.owns(op)) { release(); throw stale; }
    op.resources.add(release);
    return release;
  }
  cleanup(op) { for (const release of [...op.resources]) release(); }
  wake() { for (const resolve of this.waiters) resolve(); this.waiters.clear(); }
  async visibleGate(op) {
    while (!this.visible && this.owns(op)) {
      await new Promise(resolve => this.waiters.add(resolve));
    }
    this.assert(op);
  }
  dispatch(action, { activationId, repeat = false } = {}) {
    // IDs must come from an observed host adapter, not an assumed AIUI field.
    if (action === 'cancel' || action === 'back') {
      this.cancel(action);
      if (action === 'back') this.deps.exit();
      return null;
    }
    if (repeat || (activationId !== undefined && this.seen.has(activationId))) return null;
    if (activationId !== undefined) this.seen.add(activationId);
    if (!this.mounted || !this.visible) return null;
    if (action === 'retry') this.cancel('superseded');
    if (this.current || !['start', 'retry'].includes(action)) return null;
    return this.start();
  }
  start() {
    const op = { id: ++this.seq, resources: new Set() };
    this.current = op;
    this.state(op, 'acquiring', '');
    const clear = this.deps.deadline(() => {
      if (this.owns(op)) this.cancel('timeout');
    });
    this.retain(op, clear);
    const done = this.run(op);
    this.jobs.set(op.id, done);
    return op.id;
  }
  cancel(reason) {
    const op = this.current;
    if (!op) return;
    this.current = null; // Invalidate BEFORE abort/dispose callbacks run.
    this.phase = reason === 'timeout' ? 'error' : 'cancelled';
    this.trace.push({ id: op.id, phase: this.phase, reason, text: this.text });
    this.cleanup(op);
    this.wake();
  }
  hide(reason = 'external') {
    this.visible = false;
    // Engineering policy to be enabled only after actual capture UI observation.
    const observedOverlay = reason === 'observed-capture-overlay' &&
      ['acquiring', 'capturing'].includes(this.phase);
    if (!observedOverlay) this.cancel('hide');
  }
  show() { this.visible = true; this.wake(); } // Does not start a new turn.
  unload() { this.cancel('unload'); this.mounted = false; this.wake(); }
  async run(op) {
    try {
      this.deps.validateConfig();
      const stream = await this.deps.acquire(op.id);
      const releaseStream = this.retain(op, () => stream.stop());
      this.state(op, 'capturing');
      const image = await this.deps.capture(stream, op.id);
      const releaseImage = this.retain(op, () => image?.close?.());
      releaseStream();
      if (!image || !/^image\/(png|jpeg)$/.test(image.mime) ||
          !(image.bytes instanceof Uint8Array) || !image.bytes.length ||
          image.bytes.length > 1024 || image.width <= 0 || image.height <= 0) {
        throw new Error('invalid image');
      }
      await this.visibleGate(op);
      this.state(op, 'analyzing');
      const request = this.deps.request(image, op.id);
      const releaseRequest = this.retain(op, () => request.abort());
      const result = await request.result;
      this.assert(op);
      releaseRequest();
      releaseImage();
      if (result.status !== 200 || typeof result.summary !== 'string' ||
          !result.summary.trim() || result.summary.length > 120) {
        throw new Error('invalid response');
      }
      this.state(op, 'generating', result.summary);
      const speech = await this.deps.synthesize(result.summary, op.id);
      const releaseSpeech = this.retain(op, () => speech.abort());
      const audio = await speech.result;
      this.assert(op);
      releaseSpeech();
      const player = await this.deps.createPlayer(audio, op.id);
      this.retain(op, () => {
        try { player.stop(); } finally { player.destroy(); }
      });
      await this.visibleGate(op);
      this.state(op, 'playing');
      await player.play();
      this.assert(op);
      this.state(op, 'result');
    } catch (error) {
      if (error !== stale && this.owns(op)) this.state(op, 'error');
    } finally {
      this.cleanup(op);
      if (this.owns(op)) this.current = null;
    }
  }
}
