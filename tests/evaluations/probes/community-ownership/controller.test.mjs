import test from 'node:test';
import assert from 'node:assert/strict';
import { Controller } from './controller.mjs';

function deferred() {
  let resolve, reject;
  const promise = new Promise((a, b) => { resolve = a; reject = b; });
  return { promise, resolve, reject };
}
const flush = async () => { for (let i = 0; i < 15; i++) await Promise.resolve(); };
function fixture() {
  const calls = [];
  const scenarios = new Map();
  const timers = [];
  let configError = null;
  const get = id => {
    if (!scenarios.has(id)) {
      const s = Object.fromEntries(['acquire','capture','request','synthAcquire','synth','playerAcquire','play'].map(k => [k, deferred()]));
      s.count = { streamStop: 0, imageClose: 0, requestAbort: 0, speechAbort: 0, playerStop: 0, playerDestroy: 0, play: 0 };
      s.stream = { stop: () => s.count.streamStop++ };
      s.image = { mime: 'image/png', bytes: new Uint8Array([137,80,78,71]), width: 2, height: 2, close: () => s.count.imageClose++ };
      s.requestHandle = { result: s.request.promise, abort: () => s.count.requestAbort++ };
      s.speechHandle = { result: s.synth.promise, abort: () => s.count.speechAbort++ };
      s.player = {
        play: () => { s.count.play++; return s.play.promise; },
        stop: () => s.count.playerStop++,
        destroy: () => s.count.playerDestroy++
      };
      scenarios.set(id, s);
    }
    return scenarios.get(id);
  };
  const controller = new Controller({
    validateConfig: () => { if (configError) throw Error(configError); },
    acquire: id => { calls.push(['acquire',id]); return get(id).acquire.promise; },
    capture: (_,id) => { calls.push(['capture',id]); return get(id).capture.promise; },
    request: (image,id) => { calls.push(['request',id,image.mime,[...image.bytes]]); return get(id).requestHandle; },
    synthesize: (text,id) => { calls.push(['synthesize',id,text]); return get(id).synthAcquire.promise; },
    createPlayer: (_,id) => { calls.push(['createPlayer',id]); return get(id).playerAcquire.promise; },
    deadline: callback => { const t = { callback, cleared: false }; timers.push(t); return () => { t.cleared = true; }; },
    exit: () => calls.push(['exit'])
  });
  const start = id => controller.dispatch('start', { activationId: id });
  async function reach(id, stage) {
    const s = get(id);
    if (stage === 'acquire') return s;
    s.acquire.resolve(s.stream); await flush();
    if (stage === 'capture') return s;
    s.capture.resolve(s.image); await flush();
    if (stage === 'request') return s;
    s.request.resolve({ status: 200, summary: 'A blue sign.' }); await flush();
    if (stage === 'synthAcquire') return s;
    s.synthAcquire.resolve(s.speechHandle); await flush();
    if (stage === 'synth') return s;
    s.synth.resolve('FAKE_AUDIO'); await flush();
    if (stage === 'playerAcquire') return s;
    s.playerAcquire.resolve(s.player); await flush();
    if (stage === 'play') return s;
    s.play.resolve(); await flush();
    await controller.jobs.get(id);
    return s;
  }
  return { controller, get, calls, timers, start, reach, setConfigError: value => { configError = value; } };
}

test('normal PNG flow keeps bytes/MIME, releases camera before request, and cleans all handles', async () => {
  const f = fixture(), id = f.start('one');
  const s = await f.reach(id, 'request');
  assert.equal(s.count.streamStop, 1);
  assert.deepEqual(f.calls.find(c => c[0] === 'request').slice(2), ['image/png',[137,80,78,71]]);
  await f.reach(id, 'done');
  assert.equal(f.controller.phase, 'result');
  assert.equal(f.controller.text, 'A blue sign.');
  assert.deepEqual(s.count, { streamStop:1, imageClose:1, requestAbort:1, speechAbort:1, playerStop:1, playerDestroy:1, play:1 });
  assert.ok(f.timers[0].cleared);
});

for (const reason of ['cancel','timeout','unload']) {
  test(`late camera acquisition after ${reason} stops once and never captures/uploads`, async () => {
    const f = fixture(), id = f.start('one'), s = f.get(id);
    if (reason === 'timeout') f.timers[0].callback();
    else if (reason === 'unload') f.controller.unload();
    else f.controller.dispatch('cancel');
    const before = JSON.stringify(f.controller.trace);
    s.acquire.resolve(s.stream); await f.controller.jobs.get(id);
    f.controller.cancel(reason);
    assert.equal(s.count.streamStop, 1);
    assert.deepEqual(f.calls, [['acquire',id]]);
    assert.equal(JSON.stringify(f.controller.trace), before);
  });
}

test('late photo after cancel is closed and never uploaded', async () => {
  const f = fixture(), id = f.start('one'), s = await f.reach(id,'capture');
  f.controller.cancel('cancel');
  s.capture.resolve(s.image); await f.controller.jobs.get(id);
  assert.equal(s.count.streamStop,1);
  assert.equal(s.count.imageClose,1);
  assert.equal(f.calls.filter(c => c[0] === 'request').length,0);
});

for (const settlement of ['success','failure']) {
  test(`A ${settlement}/finally after cancel and B retry cannot mutate B or its timer`, async () => {
    const f = fixture(), a = f.start('a'), sa = await f.reach(a,'request');
    f.controller.cancel('cancel');
    const b = f.controller.dispatch('retry',{ activationId:'b' });
    await f.reach(b,'request');
    const before = JSON.stringify(f.controller.trace);
    if (settlement === 'success') sa.request.resolve({ status:200, summary:'STALE' });
    else sa.request.reject(Error('old network rejection'));
    await f.controller.jobs.get(a);
    f.timers[0].callback(); // Even a queued callback from a cleared timer is stale.
    assert.equal(f.controller.current.id,b);
    assert.equal(f.controller.phase,'analyzing');
    assert.equal(JSON.stringify(f.controller.trace),before);
    assert.equal(f.timers[1].cleared,false);
    assert.equal(f.get(b).count.requestAbort,0);
    await f.reach(b,'done');
  });
}

for (const stage of ['synthAcquire','synth','playerAcquire','play']) {
  test(`cancel at ${stage} disposes late speech/player handles without replay or stale UI`, async () => {
    const f = fixture(), id = f.start('one'), s = await f.reach(id,stage);
    f.controller.dispatch('cancel');
    const before = JSON.stringify(f.controller.trace);
    if (stage === 'synthAcquire') s.synthAcquire.resolve(s.speechHandle);
    if (stage === 'synth') s.synth.resolve('LATE_AUDIO');
    if (stage === 'playerAcquire') s.playerAcquire.resolve(s.player);
    if (stage === 'play') s.play.resolve();
    await f.controller.jobs.get(id);
    assert.equal(JSON.stringify(f.controller.trace),before);
    assert.equal(f.controller.text,'A blue sign.');
    assert.equal(s.count.speechAbort,1);
    if (['playerAcquire','play'].includes(stage)) assert.equal(s.count.playerDestroy,1);
    if (stage === 'play') assert.equal(s.count.playerStop,1);
    if (stage !== 'play') assert.equal(s.count.play,0);
  });
}

test('observed capture-overlay hide holds upload until show; show never starts again', async () => {
  const f = fixture(), id = f.start('one'), s = await f.reach(id,'capture');
  f.controller.hide('observed-capture-overlay');
  s.capture.resolve(s.image); await flush();
  assert.equal(s.count.streamStop,1);
  assert.equal(f.calls.some(c => c[0] === 'request'),false);
  f.controller.show(); await flush();
  assert.equal(f.calls.filter(c => c[0] === 'request').length,1);
  await f.reach(id,'done');
  f.controller.show(); await flush();
  assert.equal(f.calls.filter(c => c[0] === 'acquire').length,1);
});

test('ordinary hide cancels; old rejection after show/retry cannot overwrite new turn', async () => {
  const f = fixture(), a = f.start('a'), sa = await f.reach(a,'request');
  f.controller.hide();
  assert.equal(sa.count.requestAbort,1);
  assert.equal(f.controller.dispatch('retry',{activationId:'hidden'}),null);
  f.controller.show();
  const b = f.controller.dispatch('retry',{activationId:'b'});
  sa.request.reject(Error('late hidden reject')); await f.controller.jobs.get(a);
  assert.equal(f.controller.current.id,b);
  await f.reach(b,'done');
});

test('synthetic activation identity suppresses key/tap/repeat/completion duplicate but permits deliberate retry/back', async () => {
  const f = fixture(), a = f.start('physical-1');
  assert.equal(f.start('physical-1'),null);
  assert.equal(f.controller.dispatch('start',{activationId:'repeat',repeat:true}),null);
  await f.reach(a,'done');
  assert.equal(f.start('physical-1'),null);
  const b = f.controller.dispatch('retry',{activationId:'physical-2'});
  assert.ok(b > a);
  f.controller.dispatch('back',{activationId:'physical-2',repeat:true});
  const sb = f.get(b); sb.acquire.resolve(sb.stream); await f.controller.jobs.get(b);
  assert.equal(sb.count.streamStop,1);
  assert.equal(f.calls.filter(c => c[0] === 'exit').length,1);
});

for (const invalid of ['empty','raw','oversized','denied']) {
  test(`${invalid} capture produces zero network requests and remains retryable`, async () => {
    const f = fixture(), id = f.start('one'), s = f.get(id);
    if (invalid === 'denied') s.acquire.reject(Error('permission denied'));
    else {
      await f.reach(id,'capture');
      if (invalid === 'empty') s.image.bytes = new Uint8Array();
      if (invalid === 'raw') s.image.mime = 'pixels/raw';
      if (invalid === 'oversized') s.image.bytes = new Uint8Array(1025);
      s.capture.resolve(s.image);
    }
    await f.controller.jobs.get(id);
    assert.equal(f.controller.phase,'error');
    assert.equal(f.calls.some(c => c[0] === 'request'),false);
    const retry = f.controller.dispatch('retry',{activationId:'retry'});
    assert.ok(retry > id);
    await f.reach(retry,'done');
  });
}

for (const failure of ['offline','unauthorized','partial','malformed']) {
  test(`${failure} response never becomes spoken live success`, async () => {
    const f = fixture(), id = f.start('one'), s = await f.reach(id,'request');
    if (failure === 'offline') s.request.reject(Error('offline'));
    else s.request.resolve(failure === 'unauthorized' ? {status:401,summary:'fake'} : failure === 'partial' ? {status:200} : {status:200,summary:{bad:true}});
    await f.controller.jobs.get(id);
    assert.equal(f.controller.phase,'error');
    assert.equal(f.calls.some(c => c[0] === 'synthesize'),false);
    assert.equal(s.count.requestAbort,1);
  });
}

test('missing backend configuration fails visibly before acquiring or uploading', async () => {
  const f = fixture(); f.setConfigError('missing endpoint/auth');
  const id = f.start('one'); await f.controller.jobs.get(id);
  assert.equal(f.controller.phase,'error');
  assert.deepEqual(f.calls,[]);
});

test('timeout during request invalidates owner and aborts; late success cannot speak', async () => {
  const f = fixture(), id = f.start('one'), s = await f.reach(id,'request');
  f.timers[0].callback();
  assert.equal(f.controller.phase,'error');
  assert.equal(s.count.requestAbort,1);
  s.request.resolve({status:200,summary:'too late'}); await f.controller.jobs.get(id);
  assert.equal(f.calls.some(c => c[0] === 'synthesize'),false);
});

test('playback failure preserves readable result and cleans player', async () => {
  const f = fixture(), id = f.start('one'), s = await f.reach(id,'play');
  s.play.reject(Error('speaker unavailable')); await f.controller.jobs.get(id);
  assert.equal(f.controller.phase,'error');
  assert.equal(f.controller.text,'A blue sign.');
  assert.equal(s.count.playerStop,1);
  assert.equal(s.count.playerDestroy,1);
});

test('unload while waiting for show releases resources and settles ownership', async () => {
  const f = fixture(), id = f.start('one'), s = await f.reach(id,'capture');
  f.controller.hide('observed-capture-overlay');
  s.capture.resolve(s.image); await flush();
  f.controller.unload(); await f.controller.jobs.get(id);
  assert.equal(s.count.imageClose,1);
  assert.equal(f.calls.some(c => c[0] === 'request'),false);
  assert.equal(f.controller.waiters.size,0);
});
