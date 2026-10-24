# Adapt community demos into reliable AIUI Agents

Read this when adapting a third-party demo, building camera → model → speech flows, diagnosing monorepo imports, or testing asynchronous input and recovery. These are independently written engineering patterns, not additional platform requirements. Keep the user's product scope and explicit runtime; new work defaults to 0.19.0.

## What the examples contribute

Inspected on **2026-10-24**. Both repositories were publicly readable. Pin observations to these revisions; do not inherit their device results, service credentials, media, or release claims.

| Community source | Useful observation | Adaptation boundary |
| --- | --- | --- |
| [goriri multimodal Page](https://github.com/goriri/rokid-aiui-demos/blob/b808fecbcf037e68da7db16eae33a8bdb7a1ae18/demos/02-rokid-gcp-multimodal-agent/pages/index/index.ink) | Visible phases, per-turn ownership, centralized cleanup, and a no-photo gate connect capture, inference, and speech. | Its demos declare `>=0.18.0`; that is not a verified 0.19 runtime. Rebuild the API/data contracts for the selected target. |
| [goriri delivery workflow](https://github.com/goriri/rokid-aiui-demos/blob/b808fecbcf037e68da7db16eae33a8bdb7a1ae18/.agent/skills/rokid-aiui-lifecycle/SKILL.md) | Media inspection belongs beside source, packaging, and reviewer reproduction. | Local workflow conventions, endpoints, thresholds, and submission automation are not official rules or authorization. |
| [sakai sample/real-input boundary](https://github.com/sakai55/rokid/blob/6d30ed4367ee60be911d06c5d59f19df5cbde19d/gaze-translate/README.md), [isolated demo state](https://github.com/sakai55/rokid/blob/6d30ed4367ee60be911d06c5d59f19df5cbde19d/breath-pace/pages/index/index.ink) | Listing copy must match where results actually come from; demonstration state should not overwrite an active user task. | A camera permission or captured photo alone does not establish photo-derived recognition. Keep sample content visibly separate. |
| [sakai benchmark](https://github.com/sakai55/rokid/blob/6d30ed4367ee60be911d06c5d59f19df5cbde19d/glasses-benchmark/pages/index/index.ink), [preview workflow](https://github.com/sakai55/rokid/blob/6d30ed4367ee60be911d06c5d59f19df5cbde19d/skills/rokid-preview-screenshots/SKILL.md) | Device probes, input traces, and screenshots of distinct states help expose runtime differences. | API presence, any nonempty response, one passing mode, and screenshot existence do not prove the full task. Re-run your own assertions. |

No upstream code, prose, or media is bundled. At inspection, goriri's metadata/README declared MIT but no root license text was found; sakai had no identified license grant. Link and synthesize observations; verify permission before redistributing third-party material. Keep the existing Focus Timer as the sole bundled product example.

## Select the smallest useful architecture

- An offline task needs local state and appropriate persistence only if requested. Retain the timer's absolute-deadline approach; a demo's per-second counter does not establish background correctness.
- A one-shot vision task can be a Page with `idle → capturing → analyzing → result`, optional playback, and recoverable error/cancel states. Show the current phase, one primary action, and a usable exit. Choose compact text over exposing protocol details to the wearer.
- Use the built-in model when it supports the requested input; use a separately configured backend when the product needs an external provider. Do not introduce a relay merely because a demo has one. A backend, test harness, preview, and submission folder stay outside the Studio import root.
- Add continuous audio only when required. Define capture and playback encoding, sample rate, channels, frame boundaries, queue limits, and termination independently. A socket opening does not establish intelligible speech. Do not assume every WAV has a 44-byte header; parse its chunks or use a documented raw-audio contract.

## Bind camera, model, and speech to official 0.19 contracts

Use official snapshot `7d62c2d9ac1cdc1389ba06ed0651b395903accff` below, not community API lists.

| Stage | Contract and implementation decision |
| --- | --- |
| [Capture](https://github.com/yodaos-project/AIUI/blob/7d62c2d9ac1cdc1389ba06ed0651b395903accff/documentation/3-api/media/media-capture.en-US.md) | Capture requires `_blank`, is unavailable with lifetime `cut`, and needs the exact manifest permission plus authorization. `ImageCapture.takePhoto()` returns an encoded `Blob`; `CameraContext.takePhoto()` returns encoded `{ data, mimeType }`. Preserve actual MIME and bytes together; `grabFrame()` pixels are not an encoded JPEG. Stop acquired tracks; close temporary bitmaps. |
| Capture quality | Prefer documented `telephoto`/high quality for reading detail, `wide` for codes; inspect actual dimensions and payload size. Measure recognition quality and latency before resizing/compressing. A smaller payload that destroys small text is not a successful optimization. |
| [Vision input](https://github.com/yodaos-project/AIUI/blob/7d62c2d9ac1cdc1389ba06ed0651b395903accff/documentation/3-api/ai/language-model.en-US.md) | A vision-capable selected model can receive `image_url` content built from an encoded image's Data URL or accessible HTTPS URL. Check availability and model input support. No image/failed capture means no vision request; sample text must never silently substitute for a photo-derived answer. |
| [HTTPS](https://github.com/yodaos-project/AIUI/blob/7d62c2d9ac1cdc1389ba06ed0651b395903accff/documentation/3-api/network/https.en-US.md) | Check status and response schema before consuming a result. For this snapshot, the documented cancellation path is `new AbortSignal()` passed to `fetch`, then `signal.abort()`; `wx.request` returns a task with `abort()`. Do not substitute browser `AbortController` without target support evidence. A timeout alone is not cancellation. |
| [Speech](https://github.com/yodaos-project/AIUI/blob/7d62c2d9ac1cdc1389ba06ed0651b395903accff/documentation/3-api/ai/speech-synthesis.en-US.md) | `speak()` shares a player and returns no task. Generic `speechSynthesis.cancel/pause/resume` are not exposed. If the product promises independent stop/cancel, use `synthesize()` with its abortable task and `SpeechAudioPlayer` with `stop()`/`destroy()`. Do not call both speech paths for the same reply. Keep text readable if playback fails; do not infer completion from an unsupported utterance event. |

Keep camera, model, and playback handles outside reactive UI data; render only the phase, short result, and action labels. Bound input and output sizes. Use known pictures/phrases to test content, not merely “response received.” For an external backend, record the configured URL, request/response format, authentication mode, and data retention evidence. Provider keys stay server-side; a copied demo endpoint or localhost is not a device deployment. Missing configuration/authentication must fail visibly. A labeled sample mode may remain usable, but it never supplies live capability evidence or replaces a user's real session.

## Give each interaction an owner

The [Page contract](https://github.com/yodaos-project/AIUI/blob/7d62c2d9ac1cdc1389ba06ed0651b395903accff/documentation/3-api/framework/page.en-US.md) separates hide/show from unload. It does not promise that hiding automatically cancels promises or releases all devices. Choose a product-specific hide policy and observe transitions around system capture UI before assuming every hide means the user cancelled.

For a cancellable capture/request/playback flow:

1. Allocate a new operation ID and an operation-local resource set before starting. Route supported tap/key/voice actions through one state-aware dispatcher.
2. On explicit cancel, timeout, superseding retry, or unload, invalidate ownership first; then abort supported tasks and release owned resources. Cleanup must be safe to repeat. Apply the chosen hide policy explicitly; `onShow` reconciles state without implicitly repeating capture or upload.
3. After **every** asynchronous boundary, check that the operation is still current before uploading, changing UI, or starting speech. If acquisition completes late, immediately release the newly returned stream/task/player even when the UI has already left the operation.
4. A `Promise.race` deadline leaves the original promise alive. Retain a late-result disposal path and a rejection handler. Old `catch`/`finally` callbacks must not clear a new operation's busy state, timer, or resources.
5. Release media after its last needed stage, rather than holding a camera through a long model request. Cancelling a client request does not prove the server stopped processing or deleted data.

Record actual host input sequences. If a host delivers overlapping key/tap events or repeated keys, assert one intended action per physical activation. Do not assume `Enter`/`GlobalHook` pairing on every host or copy a fixed global debounce delay. A busy guard may suppress duplicate starts; it must preserve cancel/back and intentional subsequent actions. See [focus and input guidance](interaction-and-design.md).

## Import one demo, diagnose the portal separately

Use the [official import coordinates](project-anatomy.md): repository, ref, and project directory. In a monorepo, select the directory that directly contains `app.json`, not the collection root or backend. Confirm the remote ref contains all source/resources; passing against unpushed local files is insufficient.

The [sakai README](https://github.com/sakai55/rokid/blob/6d30ed4367ee60be911d06c5d59f19df5cbde19d/README.md) reports a Global Studio URL-parser problem with combined `/tree/<ref>/<subdirectory>` URLs on 2026-10-24. This is a third-party observation, not a universal restriction. On a matching failure, record portal/region/date, entered URL/ref/directory, resolved revision, and exact error. Try separate import fields if the portal provides them, or the complete local project folder, to distinguish parsing from source failure. If the affected portal still requires a branch-root layout, prepare a separate clean branch/repository proposal; do not overwrite main, infer publication authorization, or claim an untested workaround passed. An `.aix` remains an additional artifact, not a replacement for source.

## Turn these patterns into executable checks

Keep the harness, fixtures, and reproduction commands with the generated application's tests outside its import root; a README pass count or vanished `/tmp` script cannot be replayed. These cases extend the existing [UX/capability matrices](ux-and-capability-testing.md); they do not change their schemas, evidence layers, result vocabulary, or inventory gates.

| Case | Concrete assertion |
| --- | --- |
| Known image and non-JPEG payload | Correct bytes/MIME reach the selected model/backend; the result corresponds to that fixture. Empty/denied capture produces zero model calls and a usable retry. |
| Late acquisition | Resolve camera permission or speech-task creation after cancel/timeout/unload. Every late handle is released; no upload, playback, or stale UI write occurs. |
| Retry race | Start A, cancel, start B, then deliver A's success, failure, and finalizer. B's state/resources survive; A has no effects. Repeat while hidden and after return. |
| Input arbitration | Replay observed key/tap duplicates, repeat events, and a completion-time late event. Exactly one intended action occurs; no accidental restart, blocked back, or lost deliberate retry. |
| Service and sample isolation | Missing config, invalid/expired auth, offline, malformed response, and failed health check never become live success. Sample mode is visible, isolated, and cannot overwrite a real session. |
| Speech and streaming | Stop during generation/playback, close during acquisition, lose a connection, and saturate queues. Resources and pending audio are cleared; final text remains usable. Inspect intelligibility and content on the target host. |
| Capability granularity | Test every claimed camera mode/input path separately. Presence probes and connection checks stay distinct from actual capture, recognition, inference, and playback results. One passing mode cannot cover a failed or untested mode. |
| Rendered state | Operate idle, busy, result, error, denied, and retry states. Verify labels, visible focus, long text, and reachable actions; re-identify controls after layout changes instead of reusing stale click coordinates. |

An independently recreated HTML mock is design evidence only. Actual AIX preview must load the project's source in the identified Ink runtime; HTML export alone proves neither rendering nor interaction. Preserve bootstrap failures and label any diagnostic runtime patch separately. For submission media, inspect representative frames and listen to relevant speech; check state transitions, blank/frozen frames, clipping, and A/V timing. Container metadata alone is insufficient. Disclose mock data, re-voicing, or compositing and follow [submission preparation](submission-preparation.md).

Report measured capture, upload, inference, first audio, and total latency separately when those stages exist; compare against a project budget, not a copied demo threshold. These are test recipes, not pre-recorded passes. Studio/device gates and the current 0.19 capability PASS-policy limitation remain `BLOCKED` until their own evidence requirements are met.
