// Synthetic application-logic probe of the documented helper, not device evidence.
const fs = require('node:fs');
const vm = require('node:vm');
const assert = require('node:assert/strict');
const { createHash } = require('node:crypto');
const documentPath = process.argv[2];
const document = fs.readFileSync(documentPath, 'utf8');
const source = document.match(/```javascript\n(async function captureOrdinaryPhoto\(\)[\s\S]*?)\n```/)[1];
console.log('Reference SHA-256: ' + createHash('sha256').update(document).digest('hex'));

async function runCase(name, options = {}) {
  const calls = [];
  const track = { stop() { calls.push(['stop']); } };
  const stream = {
    getVideoTracks() { return options.noTrack ? [] : [track]; },
    getTracks() { return [track]; },
  };
  const photo = options.photo ?? new Blob(['encoded-fixture'], { type: 'image/png' });
  const context = vm.createContext({
    Blob,
    navigator: { mediaDevices: { async getUserMedia(constraints) {
      calls.push(['acquire', constraints]);
      if (options.acquireError) throw new Error('denied');
      return stream;
    } } },
    ImageCapture: class {
      constructor(value) {
        assert.equal(value, track);
        calls.push(['construct']);
        if (options.constructorError) throw new Error('unsupported');
      }
      async takePhoto(settings) {
        calls.push(['takePhoto', settings]);
        if (options.captureError) throw new Error('capture failed');
        return photo;
      }
    },
  });
  const capturePhoto = vm.runInContext(source + '\ncaptureOrdinaryPhoto', context);
  if (options.expectError) {
    await assert.rejects(capturePhoto(), options.expectError);
  } else {
    const result = await capturePhoto();
    assert.equal(result, photo, 'consumer receives the actual returned Blob');
    assert.equal(result.type, 'image/png', 'preserves actual MIME');
  }
  assert.deepEqual(JSON.parse(JSON.stringify(calls[0][1])), { video: true, audio: false });
  const shouldCapture = !options.acquireError && !options.noTrack && !options.constructorError;
  assert.equal(calls.filter(x => x[0] === 'construct').length,
    options.acquireError || options.noTrack ? 0 : 1);
  assert.equal(calls.filter(x => x[0] === 'takePhoto').length, shouldCapture ? 1 : 0);
  assert.equal(calls.filter(x => x[0] === 'stop').length, options.acquireError ? 0 : 1);
  if (shouldCapture) {
    const call = calls.find(x => x[0] === 'takePhoto');
    assert.deepEqual(JSON.parse(JSON.stringify(call[1])), {
      quality: 'high', mode: 'default', enableSystemPreview: true,
    });
    assert.equal(calls.at(-1)[0], 'stop', 'cleanup follows capture outcome');
  }
  console.log('PASS ' + name);
}

(async () => {
  await runCase('real helper reaches takePhoto once and returns the same PNG Blob');
  await runCase('denied acquisition never constructs or captures', { acquireError: true, expectError: /denied/ });
  await runCase('missing video track releases acquired resources', { noTrack: true, expectError: /track unavailable/ });
  await runCase('constructor failure releases acquired resources', { constructorError: true, expectError: /unsupported/ });
  await runCase('capture failure releases acquired resources', { captureError: true, expectError: /capture failed/ });
  await runCase('empty photo is rejected', { photo: new Blob([], { type: 'image/jpeg' }), expectError: /No encoded photo/ });
  await runCase('non-image MIME is rejected', { photo: new Blob(['x'], { type: 'text/plain' }), expectError: /No encoded photo/ });
  await runCase('non-Blob result is rejected', { photo: { size: 1, type: 'image/png' }, expectError: /No encoded photo/ });
  console.log('8/8 synthetic logic cases passed; no device or encoded-image decoding claim.');
})().catch(error => { console.error(error); process.exitCode = 1; });
