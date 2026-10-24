# App configuration and multimedia execution evaluation

Date: 2026-10-25. Evaluated the working Skill based on repository commit `4696d7e9450e28b1c79f0f531e33bbd74ea798cc`, with the manifest/media additions in this change. This is a Skill/excerpt evaluation and a synthetic helper probe, not a generated product, real media execution, or device acceptance.

## Independent review task

An isolated agent received the Skill path and [review input](../probes/media-execution/review-input.md), without expected answers or the maintainer's findings. It read relevant references and pinned official sources. The task supplied a proposed manifest and seven media handler/template excerpts; no complete source tree or runtime evidence existed.

The [retained review](../probes/media-execution/forward-review.md) identified:

- Missing `RECORD_AUDIO` for microphone capture, with no speculative library/playback permissions.
- Photo setup without `takePhoto`, fixed-text recognition instead of photo consumption, and missing track cleanup.
- Recorder construction without start/stop/final output; Sound construction without play; a running AudioContext without a started oscillator.
- The invalid AudioPlayer file constructor and readiness incorrectly labeled completion. This additional finding was checked against the official source and fed back into the guidance.
- The valid video autoplay path, while requiring actual playback events/frames instead of falsely insisting on a manual `play()` call.
- WebRTC channel creation without signaling/send/peer receipt; open is not delivery.
- Concrete actual-handler tests for output provenance, failures, duplicates, cancellation, late acquisitions, cleanup, and truthful UX.

The separate source-unavailable audit draft initially failed validation (exit 1): target tuples were not canonical, and its empty FAIL ledger omitted brackets. The maintainer normalized only those fields, without changing results or adding evidence. [Normalization record](../probes/media-execution/audit-normalization.json) retains original/normalized hashes and exact field changes. The [normalized audit](../probes/media-execution/forward-audit.md) validates with exit **2**, `BLOCKED` and `Release-ready: NO`; [validation log](../probes/media-execution/audit-validation.log). The review's draft warning describes the original output. This is not an untouched full audit pass, and formatting reliability remains a limit of the independent response.

## Executed photo-helper probe

The [probe](../probes/media-execution/photo-probe.cjs) extracts and executes the actual JavaScript helper from the packaged media reference with injected platform boundaries. Eight cases passed: valid output identity/MIME and one `takePhoto` call; denied acquisition; missing video track; constructor failure; capture rejection; empty Blob; non-image MIME; and non-Blob output. It checks video-only request arguments, capture settings, and track cleanup on all acquired-resource paths. The [log](../probes/media-execution/photo-probe.log) binds results to the reference SHA-256.

This probe uses dummy fixture bytes, not a real encoded photograph. It proves the helper's control flow and data handling only. It does not prove Page wiring, image decoding, authorization, photography, model inference, recording, audible playback, WebRTC transport, Studio, or physical-device behavior.

Replay from the repository root with a working Node runtime and Python:

```bash
node tests/evaluations/probes/media-execution/photo-probe.cjs \
  skills/rokid-aiui-agent/references/media-implementation-and-testing.md
python3 skills/rokid-aiui-agent/scripts/validate_aiui_audit.py \
  tests/evaluations/probes/media-execution/forward-audit.md \
  --repository-root . --import-root UNAVAILABLE \
  --request-prompt tests/evaluations/probes/media-execution/review-input.md
```

Expected exits: helper `0`; blocked audit `2`. No devices, media services, provider accounts, or live peers are needed or accessed. Existing 0.19 capability PASS policies remain unregistered.

## Repository verification

The complete local flow passed **323/323 unit tests and all 20 gates**: Skill/reference validation, five strict import roots, 0.19 inventory, signed release-audit black box, four real AIX pack/list flows, retained external archive delivery, HTML preview export, syntax, and whitespace. HTML export is not media playback or browser-render proof. This change does not claim new platform or physical-device acceptance.
