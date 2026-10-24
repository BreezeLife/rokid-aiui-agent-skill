# Multimedia implementation and execution checks

Read this whenever implementing, changing, or testing an Agent's media feature. Apply it to each claimed feature and supported input path, not to every API in the platform. A manifest declaration, API availability check, constructor, registered callback, or source-code match does not prove that a media operation ran or produced a useful result.

## Versioned sources

The user's [0.18 media overview](https://js.rokid.com/AIUI/api/media/overview?version=0.18.0&lang=zh-CN) and [ordinary-photo guide](https://js.rokid.com/AIUI/api/media/media-capture?version=0.18.0&lang=zh-CN#拍摄普通照片) are navigation entrypoints. On 2026-10-25, checked the official [0.18 overview](https://github.com/yodaos-project/AIUI/blob/cfa902ba2732121808ddf07a4e71465545977742/documentation/3-api/media.md) and [0.19 overview](https://github.com/yodaos-project/AIUI/blob/7d62c2d9ac1cdc1389ba06ed0651b395903accff/documentation/3-api/media.md). New projects still default to 0.19; preserve explicit 0.18 targets.

| Contract | AIUI 0.18 source | AIUI 0.19 source |
| --- | --- | --- |
| Capture, photos, recording | [0.18](https://github.com/yodaos-project/AIUI/blob/cfa902ba2732121808ddf07a4e71465545977742/documentation/3-api/media/media-capture.md) | [0.19](https://github.com/yodaos-project/AIUI/blob/7d62c2d9ac1cdc1389ba06ed0651b395903accff/documentation/3-api/media/media-capture.md) |
| AudioPlayer | [0.18](https://github.com/yodaos-project/AIUI/blob/cfa902ba2732121808ddf07a4e71465545977742/documentation/3-api/media/audio-player.md) | [0.19](https://github.com/yodaos-project/AIUI/blob/7d62c2d9ac1cdc1389ba06ed0651b395903accff/documentation/3-api/media/audio-player.md) |
| Local short sounds | [0.18](https://github.com/yodaos-project/AIUI/blob/cfa902ba2732121808ddf07a4e71465545977742/documentation/3-api/media/sound.md) | [0.19](https://github.com/yodaos-project/AIUI/blob/7d62c2d9ac1cdc1389ba06ed0651b395903accff/documentation/3-api/media/sound.md) |
| Web Audio | [0.18](https://github.com/yodaos-project/AIUI/blob/cfa902ba2732121808ddf07a4e71465545977742/documentation/3-api/media/web-audio.md) | [0.19](https://github.com/yodaos-project/AIUI/blob/7d62c2d9ac1cdc1389ba06ed0651b395903accff/documentation/3-api/media/web-audio.md) |
| Video control and component events | [control](https://github.com/yodaos-project/AIUI/blob/cfa902ba2732121808ddf07a4e71465545977742/documentation/3-api/media/video.md), [events](https://github.com/yodaos-project/AIUI/blob/cfa902ba2732121808ddf07a4e71465545977742/documentation/2-components/video.md) | [control](https://github.com/yodaos-project/AIUI/blob/7d62c2d9ac1cdc1389ba06ed0651b395903accff/documentation/3-api/media/video.md), [events](https://github.com/yodaos-project/AIUI/blob/7d62c2d9ac1cdc1389ba06ed0651b395903accff/documentation/2-components/video.md) |
| WebRTC audio/data | Not a 0.18 contract | [0.19](https://github.com/yodaos-project/AIUI/blob/7d62c2d9ac1cdc1389ba06ed0651b395903accff/documentation/3-api/media/webrtc.md) |

## During implementation: trace the real operation

For each requested media behavior, record `Feature / User or Agent entry / Handler and source location / Start API or autoplay path / Useful output / Downstream use / Completion or stop / Cleanup`. Trace through wrappers and aliases to the platform call, and confirm that the intended button, voice intent, or Agent invocation actually reaches it. A helper that is never invoked is unfinished implementation.

Configure [app.json from the actual feature set](project-anatomy.md#configure-appjson-from-actual-features). Keep permission declarations, OS authorization, acquisition, operation start, useful output, and task completion separate. Register callbacks before starting operations that can complete quickly. Update UI success only from the corresponding result; catch failure and expose a usable retry or fallback.

| Selected feature | Actual execution path | Result and lifecycle checks |
| --- | --- | --- |
| Still photo, Web API | Video `getUserMedia()` → `new ImageCapture(videoTrack)` → **`await capture.takePhoto(settings)`** | Validate non-empty encoded `Blob` and its actual MIME; pass that same image to the intended consumer. Stop every acquired track in success/failure paths. |
| Still photo, wx API | Non-null `wx.media.createCameraContext()` → **`await camera.takePhoto(options)`** | Validate encoded `data.byteLength` and `mimeType`; build a Blob with the real MIME when needed. The context may be unavailable; do not invent a context `destroy()` method. |
| Current frame pixels | Video track → `ImageCapture.grabFrame()` | Consume the returned bitmap; close it and release tracks. Pixels are not JPEG/PNG bytes and this is not proof of the ordinary-photo path. |
| Web audio/video recording | Correct audio/video tracks → `MediaRecorder` → `start()` | Collect non-empty `dataavailable` chunks in order; call `stop()` and wait for final data and `stop` before assembling output. Check actual MIME and fixture playback/decoding; stop all tracks on failure and completion. `isTypeSupported()` and construction are not recording. |
| wx audio recording | Available `wx.media.getRecorderManager()` → register callbacks → `start(options)` | Consume `onFrameRecorded` data and finish on `onStop`; handle `onError` and interruption. For Opus, register `onHeader(format, headerBuffer)` before starting and process its header before ordered payloads; PCM has no header callback. The documented `tempFilePath` is empty and `isLastFrame` is not a completion signal. Stop the recorder and clear application-owned buffers/listeners as supported. |
| File/buffer audio playback | `new AudioPlayer()` → assign `src`/`setBuffer()` → `play()`, or explicitly configured, observed `player.autoplay` | File mode uses the no-argument constructor and properties; do not pass `{src, autoplay}` as constructor options, which select streaming mode and require `format`. Observe `onPlay` and advancing `onTimeUpdate`; for non-looping playback, `onEnded` is completion. `onCanplay` only means ready. Handle `onError`; stop/destroy and detach supported listeners. |
| Streaming audio playback | Explicit `pcm`/`ogg_opus` player → `play()` → actual `append(chunk)` → `finish()` when production ends | Verify format/order and playback progression. `finish()` closes input, not playback; wait for drained `onEnded`. Stop upstream production, reject stale chunks, and destroy the player on cancellation. |
| Local short sound | `new Sound(localPath)` → `play()` | Constructor alone is silent. Verify call and actual audible output; `Sound` has no event listener API, so never fabricate `onEnded`. Use `stop()`/`destroy()`; this API is not a remote-URL or streaming player. |
| Generated sound / PCM through Web Audio | Valid source/buffer → connected output graph → `resume()` as needed → source/oscillator `start()` | A running AudioContext is not a started source. Observe supported source completion and actual output. Buffer sources are single-use; replay creates a fresh source. Stop/disconnect owned nodes and close the context. |
| Microphone analysis | Audio `getUserMedia()` → media-stream source → analyser → running context → actual waveform/frequency reads | Assert samples change with a known input. Creating an analyser is not analysis. Do not require connection to the speaker destination for analysis. Stop the read loop/tracks, disconnect nodes, and close the context. |
| Video playback | Mounted `<video>` with stable ID and valid source → non-null `wx.createVideoContext(id)` → `play()`, or explicit component `autoplay` | `VideoContext` calls return void; `await play()` is not playback proof. Observe component `playing`/`timeupdate`, visible frame changes, `ended`/`error`. Pause/stop and respect unmount; do not invent `VideoContext.destroy()`. |
| WebRTC data, 0.19 | Real signaling/SDP/ICE → open data channel → actual `send()` | A connection or open channel is insufficient: verify matching peer `message` content/application acknowledgment, sizes and backpressure. Close channel/peer connection and stop signaling/retries. |
| WebRTC audio, 0.19 | Local audio track → `addTrack()` → negotiation; receiver `track` → connected Web Audio output, resumed when needed | A remote track does not play automatically. Verify useful audio and actual playback. Close connections/context and stop owned local tracks separately; `pc.close()` does not stop them. Receive-only audio does not require microphone capture. |

For continuous analysis, looping media, and real-time connections, verify explicit user stop and cleanup instead of requiring a natural `ended` event. WebRTC is audio/data only, requires device networking, and is unavailable to Agent Workers; do not infer video support or connectivity from an HTTPS request. Video format support must follow its own versioned contract. Speech/model APIs outside this overview follow the [camera/model/speech guidance](community-patterns.md), with the same call-to-result discipline.

## Camera emphasis: takePhoto must actually run

`capture` is the example variable holding an `ImageCapture`, not a global API name. For ordinary encoded photos, merely declaring `CAMERA`, granting permission, obtaining a stream, showing a preview, or constructing that object does **not** take a photo. Reach and await `capture.takePhoto()` and verify its result. The documented wx `CameraContext.takePhoto()` is an alternative; video streaming, recording and frame analysis have their own start/output contracts and must not be forced to contain this variable name or method.

The inspected capture contract requires `_blank` and excludes lifetime `cut`; it does not impose an additional user-gesture/focus prerequisite after entering `_blank`. Choose when to photograph from the product's explicit interaction. Ordinary photos use `mode: 'default'`; request only video when no microphone is needed.

This single-operation helper illustrates the call and encoded result contract, not a complete Page or lifecycle controller:

```javascript
async function captureOrdinaryPhoto() {
  const stream = await navigator.mediaDevices.getUserMedia({
    video: true,
    audio: false,
  });
  try {
    const [videoTrack] = stream.getVideoTracks();
    if (!videoTrack) throw new Error('Camera track unavailable');
    const capture = new ImageCapture(videoTrack);
    const photo = await capture.takePhoto({
      quality: 'high',
      mode: 'default',
      enableSystemPreview: true,
    });
    if (!(photo instanceof Blob) || photo.size === 0 ||
        !photo.type.startsWith('image/')) {
      throw new Error('No encoded photo returned');
    }
    return photo;
  } finally {
    for (const track of stream.getTracks()) track.stop();
  }
}
```

Wire the actual capture handler to this helper, await it, and pass its returned Blob to the implemented consumer; handle rejection visibly. Integrate [operation ownership](community-patterns.md#give-each-interaction-an-owner) for repeated input, cancellation/unload during acquisition or capture, and late results. Never launch image inference/upload with a missing photo or substitute sample text as a real-camera result. Keep captures out of UI state/logs when only phase or metadata is needed.

## During testing: execute the implementation, then verify the result

Use the working checklist in [UX/capability testing](ux-and-capability-testing.md#executable-functional-and-ux-checks); these checks supplement, not replace or rename, the two exact audit matrices. For each implemented media row and input mode:

1. **Real entry and call:** invoke the actual application handler through its intended interaction. Instrument the injected platform boundary to record call count, arguments, sequence, and operation identity. Assert the expected count for the selected mode: one capture for an accepted single-photo action, explicitly bounded repetition for burst/continuous capture, or real playback events for the declared autoplay path. Do not test only a stand-alone mock or an unused helper.
2. **Useful output:** return known image/audio/video data or controlled events to the actual code. Assert bytes/MIME, chunk ordering, sample changes, completion handling, and that the exact output reaches the correct consumer. A log saying “success” or a changed label is insufficient. Use real decoding/playback and target hardware to establish physical output.
3. **Failure and zero false success:** cover permission denial, unavailable context/device, start/capture failure, empty/corrupt output, downstream failure, and playback/recording error. Failed or empty capture must cause zero image-model/upload calls. Assert no false “captured”, “recorded” or “playing” state, and a recoverable UI.
4. **Duplicates and lifecycle:** repeated input starts one owned operation; stop/cancel/unload releases resources and invalidates late output. A late acquired stream is stopped, and old completion cannot mutate a new session. Test the chosen hide/show policy, reopen, and fresh-source requirements separately.
5. **Visible/audible UX:** inspect starting/active/stopped/completed/error states and retry controls. During capture, show progress without prematurely claiming success. During playback, reflect actual progress/error, not merely `play()` being called. Record runtime, source fingerprint, action, observed output, and environment limits.

A source search is a navigation aid only: comments, dead code and never-called functions are false positives; aliases, wrappers, wx variants and autoplay can be false negatives. Do not add a blanket rule that every `CAMERA` declaration requires the literal text `capture.takePhoto`.

Static validation proves structure; instrumented logic tests prove application calls/data handling; browser/Studio/device observations prove only their respective environments. A granted video stream satisfies acquisition, not still-photo completion. Existing camera policies cannot be broadened by prose, and this guide adds no new capability PASS policy. Keep unknown bindings and all current 0.19 capability audit rows `BLOCKED`, while reporting narrower executed logic results honestly. Missing hardware or trusted evidence remains blocked; do not fabricate a successful camera, microphone, speaker, or peer session.
