# AIUI 0.19.0: authoring and verification

Use this for new AIUI work unless the project explicitly targets an older runtime. Sources were inspected on **2026-10-21**, pinned to official commit **`7d62c2d9ac1cdc1389ba06ed0651b395903accff`**. The `v0.19.x` branch and `main` resolved there; a `v0.19.0` tag did not exist. The [changelog](https://github.com/yodaos-project/AIUI/blob/7d62c2d9ac1cdc1389ba06ed0651b395903accff/documentation/8-changelog/latest.en-US.md) explicitly identifies v0.19.0. See [source-of-truth.md](source-of-truth.md) for mutable website selectors and explicit 0.17/0.18 targets.

## Find the exact contract

Open only the rows needed for the implementation. Every source below is official and commit-pinned; reading it establishes a documented contract, not evidence that the current project passed a test.

| Task | Narrow source |
| --- | --- |
| Create, import, preview, package, and review | [Studio quickstart](https://github.com/yodaos-project/AIUI/blob/7d62c2d9ac1cdc1389ba06ed0651b395903accff/documentation/0-guide/quickstart/quickstart.en-US.md) |
| Project files and manifest | [Structure](https://github.com/yodaos-project/AIUI/blob/7d62c2d9ac1cdc1389ba06ed0651b395903accff/documentation/0-guide/structure.en-US.md), [app.json](https://github.com/yodaos-project/AIUI/blob/7d62c2d9ac1cdc1389ba06ed0651b395903accff/documentation/1-framework/open-agent-format/app-json.en-US.md) |
| First frame, return, and cleanup | [Page lifecycle](https://github.com/yodaos-project/AIUI/blob/7d62c2d9ac1cdc1389ba06ed0651b395903accff/documentation/1-framework/open-agent-format/page-lifecycle.en-US.md), [component API](https://github.com/yodaos-project/AIUI/blob/7d62c2d9ac1cdc1389ba06ed0651b395903accff/documentation/3-api/framework/component.en-US.md) |
| Route success and failure | [Routing](https://github.com/yodaos-project/AIUI/blob/7d62c2d9ac1cdc1389ba06ed0651b395903accff/documentation/3-api/route.en-US.md) |
| Inline/full-screen, focus, input | [Target](https://github.com/yodaos-project/AIUI/blob/7d62c2d9ac1cdc1389ba06ed0651b395903accff/documentation/1-framework/open-agent-format/target.en-US.md), [focus](https://github.com/yodaos-project/AIUI/blob/7d62c2d9ac1cdc1389ba06ed0651b395903accff/documentation/1-framework/open-agent-format/focus.en-US.md), [events](https://github.com/yodaos-project/AIUI/blob/7d62c2d9ac1cdc1389ba06ed0651b395903accff/documentation/1-framework/open-agent-format/page-events.en-US.md) |
| Widget and Worker boundaries | [Widget](https://github.com/yodaos-project/AIUI/blob/7d62c2d9ac1cdc1389ba06ed0651b395903accff/documentation/1-framework/open-agent-format/widget.en-US.md), [Agent Worker](https://github.com/yodaos-project/AIUI/blob/7d62c2d9ac1cdc1389ba06ed0651b395903accff/documentation/1-framework/open-agent-format/agent-worker.en-US.md) |
| WebRTC | [Audio and data channels](https://github.com/yodaos-project/AIUI/blob/7d62c2d9ac1cdc1389ba06ed0651b395903accff/documentation/3-api/media/webrtc.en-US.md) |
| Connectivity and weak network | [Navigator](https://github.com/yodaos-project/AIUI/blob/7d62c2d9ac1cdc1389ba06ed0651b395903accff/documentation/3-api/navigator.en-US.md), [network UX](https://github.com/yodaos-project/AIUI/blob/7d62c2d9ac1cdc1389ba06ed0651b395903accff/documentation/0-guide/performance/network.en-US.md) |
| Streams and text chunks | [Streams](https://github.com/yodaos-project/AIUI/blob/7d62c2d9ac1cdc1389ba06ed0651b395903accff/documentation/3-api/network/streams.en-US.md), [encoding](https://github.com/yodaos-project/AIUI/blob/7d62c2d9ac1cdc1389ba06ed0651b395903accff/documentation/3-api/encoding.en-US.md) |
| Digests and HMAC | [Crypto](https://github.com/yodaos-project/AIUI/blob/7d62c2d9ac1cdc1389ba06ed0651b395903accff/documentation/3-api/crypto.en-US.md) |
| Image export and drawing | [Canvas](https://github.com/yodaos-project/AIUI/blob/7d62c2d9ac1cdc1389ba06ed0651b395903accff/documentation/3-api/canvas/index.en-US.md) |
| Speech and recorder checks | [Speech recognition](https://github.com/yodaos-project/AIUI/blob/7d62c2d9ac1cdc1389ba06ed0651b395903accff/documentation/3-api/ai/speech-recognition.en-US.md), [media capture](https://github.com/yodaos-project/AIUI/blob/7d62c2d9ac1cdc1389ba06ed0651b395903accff/documentation/3-api/media/media-capture.en-US.md) |
| Layout and animation | [WXSS functions](https://github.com/yodaos-project/AIUI/blob/7d62c2d9ac1cdc1389ba06ed0651b395903accff/documentation/1-framework/wxss/function.en-US.md), [animation](https://github.com/yodaos-project/AIUI/blob/7d62c2d9ac1cdc1389ba06ed0651b395903accff/documentation/1-framework/wxss/animation.en-US.md) |
| Simulator/device checks and performance | [Web self-test](https://github.com/yodaos-project/AIUI/blob/7d62c2d9ac1cdc1389ba06ed0651b395903accff/documentation/0-guide/debug/web_debug.en-US.md), [device CLI](https://github.com/yodaos-project/AIUI/blob/7d62c2d9ac1cdc1389ba06ed0651b395903accff/documentation/0-guide/debug/cli_device_debug.en-US.md), [metrics](https://github.com/yodaos-project/AIUI/blob/7d62c2d9ac1cdc1389ba06ed0651b395903accff/documentation/0-guide/performance/data.en-US.md) |

## Changes from 0.18

- **WebRTC** adds `RTCPeerConnection` and `RTCDataChannel` for audio, text, and binary data in Page/Widget Window environments. No video transport or Agent Worker support. Supply signaling, SDP/ICE exchange, STUN/TURN, and real device connectivity. HTTPS through the phone's Bluetooth link does not establish WebRTC connectivity. Queue candidates until the remote description exists; send only on open channels and bound queued bytes. `pc.close()` does not stop application-owned local tracks.
- **Network state** adds `navigator.onLine`, `navigator.connection`, Window `online`/`offline`, connection `change`, and App/Page `onNetworkStatus`. These are hints; handle actual request and peer failures separately.
- **Streams and encoding** add `tee()`, BYOB readers, `ReadableStream.from()`, async iteration, `TextEncoderStream`, `TextDecoderStream`, and `encodeInto()`. Await pipeline completion; handle backpressure, cancellation, errors, and split multibyte text. BYOB transfers supplied buffers: continue with the returned view.
- **Crypto** expands SHA digests and HMAC keys/sign/verify. Confirm supported algorithms and binary views from the exact API page; do not infer the full browser Web Crypto surface.
- **Canvas** adds PNG/JPEG encoding through `Canvas.convertToBlob()` and `createImageBlob()`. Distinguish encoded blobs from raw pixels, validate dimensions, and release bitmaps after use. Drawing a closed bitmap must fail visibly.
- **WXSS** adds `text-overflow: ellipsis`, constrained `calc()`, concurrent animations, animation lifecycle events, and text-triggered decorations. The current `calc()` subset uses two compatible operands with `+`/`-`. `random()` is experimental: use literal fallbacks and the documented numeric/length/percentage/time subset. Do not assume 3D transforms or `animation-play-state`.
- **Widgets** now receive `window.open('widgets/path/index?key=value', '_widget')` query strings in `onCreate(options)`. No query yields `{}`. Use defaults and validation; reopening an overlay may create a new instance.

Widgets and Agent Workers themselves were introduced in 0.18. Networking and CSS transitions already existed in 0.17; do not relabel entire families as new in 0.19.

## Compatibility checks before changing existing code

1. Page `onReady()` and component `lifetimes.ready()` run once per instance **after their own first presented frame**. Parsing/layout alone is insufficient; returning to a retained Page does not rerun ready. Restore visible work in `onShow()`/`onAttach()`.
2. `wx` route `success` runs after successful load, `fail` covers missing/failed targets and an unavailable back route, then `complete` runs. Check actual results instead of assuming a navigation request succeeded.
3. Remove the separate `SPEECH_RECOGNITION` permission. Microphone capture still needs `RECORD_AUDIO` and platform authorization; external-audio recognition does not open a microphone by itself. Use only documented `GEOLOCATION`, `CAMERA`, and `RECORD_AUDIO` declarations for those capabilities.
4. Call **static** `MediaRecorder.isTypeSupported(mimeType)`. Handle unsupported formats and capture denial.
5. `wx.canIUse()` checks registered runtime function paths; unknown paths, parameter options, and application-added functions return false. A true result proves neither device hardware nor permission.
6. Component directory entries must explicitly include `index`, such as `/components/card/index`. Resolve nested components from the real project paths.
7. Agent Workers still have no `window`, `document`, `fetch`, routing, rendering, capture, or WebRTC. `onOpen()` must synchronously register `event.waitUntil(promise)`; making the callback async does not extend lifetime. `agentWorkers` uses `instant`/`foreground`, one `open` trigger, and a safe relative `.js`/`.ts` script; `background` is reserved.

## Functional and UX scenarios

Run only applicable rows against the exact import-root fingerprint, runtime **0.19.0**, surface, and device. Write concrete fixture inputs, log/assertion locations, and capture IDs in the [required matrices](ux-and-capability-testing.md). Repeat core flows on `_current`, `_blank`, and declared Widget families where supported. These are test instructions, not pre-recorded `PASS` results.

| Flow | Positive action and expected result | Negative/recovery action and expected result | Lifecycle/UX observation |
| --- | --- | --- | --- |
| Core task and routes | Open with valid data; complete the main task; navigate back. Assert task state and route callbacks. | Open a missing route and go back without a previous page. Assert `fail` then `complete`, usable feedback, and an available return path. | Log `onLoad → onShow → first presented frame → onReady`; return to the retained Page and assert `onShow` without another ready. |
| Widget input | Open the declared overlay with `?city=hangzhou`; assert `options.city === 'hangzhou'`. | Open without query and with malformed values; assert `{}`/string input handling and a deliberate fallback. | Repeat attach/detach/close/reopen; check correct content, family-relative sizing, and no duplicated work or listeners. |
| Connectivity | Load data online and show completion; observe actual response. | Disconnect, delay, timeout, then reconnect. Assert bounded retries, clear loading/error/retry states, preserved useful content, and no stale result replacing newer data. | Hide/resume during a request; remove subscriptions on final cleanup. An online event alone must not show success. |
| WebRTC | Connect two peers with the chosen signaling/ICE services, send text/binary, and exchange audio if claimed. Assert channel state and received content/media stats. | Deny microphone, omit/expire TURN, lose the network, and try send-before-open/oversized data. Assert controlled errors and a usable retry/exit. | Close Page/destroy Widget: peer/channel closed, local tracks stopped, audio context closed, queue bounded, no phantom “connected” UI. Signaling success alone is insufficient. |
| Streaming text | Deliver UTF-8 text split across byte boundaries; assert exact final text through the decoder pipeline. | Fail/cancel midstream and apply a slow sink. Assert error/cancellation propagation and bounded buffering. | Leave and reopen during streaming; no late state write, duplicate reader, or invisible continued work. |
| Crypto and image export | Assert a known digest/HMAC vector and PNG/JPEG type, nonzero bytes, and decoded dimensions. | Verify altered data/signature and use invalid sizes or a closed bitmap. Assert verification failure or a handled error. | Repeat export and navigate away; track released references and memory trend. Show actionable save/upload failures. |
| Styles, input, and animation | Exercise long/empty text and complete input values (`event.detail.value`); run two animations and observe lifecycle events. | Remove an animated node, apply `display:none`, and exercise literal fallback where experimental styling is unavailable. Assert cancellation and readable fallback. | Unrelated updates preserve animation progress; cancellation precedes final cleanup. Focus, error, and selection remain legible without color-only cues. |
| Voice/camera/hardware | Invoke only claimed inputs and exact permissions; assert correct result and confirmation feedback. | Deny permission, provide unexpected speech/input, and interrupt capture. Assert a usable alternative input and recovery. | Stop acquired tracks/listeners; test actual temple controls and bright/dark/cluttered backgrounds on glasses. Simulator input is not device proof. |

Record startup-to-visible time, first useful interaction, request latency/retries, and memory trend for repeated navigation/continuous use. Establish a project baseline and acceptance budget; do not invent an official millisecond threshold.

## Completion boundary

Run strict project validation and executable behavior checks, probe and execute supported AIX pack/list operations, then separately capture Studio and physical-device evidence. New official CLI documentation does not prove that an installed CLI offers those commands; use [aix-workflow.md](aix-workflow.md).

The local audit's **0.19 capability policy is inventory-only**: every capability remains `BLOCKED` until a separately verified 0.19 policy and version-matched evidence exist. Preserve this even when individual tests pass; keep the distinct evidence layers and honest results in the matrices. Do not swap the 0.17 source commit for this SHA, relabel old signed captures, or claim `Release-ready: YES` from static validation, documentation lookup, preview, a package listing, or a launch-request acknowledgement.
