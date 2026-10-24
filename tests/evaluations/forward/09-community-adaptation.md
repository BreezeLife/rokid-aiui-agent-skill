# Community adaptation evaluation

Date: 2026-10-24 (Asia/Singapore). Scenario: [community adaptation](../../scenarios/09-community-adaptation.md). Pre-change repository base: `fc5f41b0f1738be1004240723d4ccfda6c82f597`.

## Research and baseline

Two independent read-only researchers inspected the user-selected repositories at goriri `b808fecbcf037e68da7db16eae33a8bdb7a1ae18` and sakai `6d30ed4367ee60be911d06c5d59f19df5cbde19d`. Their findings were checked against official AIUI 0.19 snapshot `7d62c2d9ac1cdc1389ba06ed0651b395903accff`. Third-party code was not executed or copied; upstream service/device success was not inherited. Sources and boundaries are maintained in the [packaged reference](../../../skills/rokid-aiui-agent/references/community-patterns.md).

A separate baseline agent received only the existing packaged Skill and the scenario, with no research findings or intended answer. It correctly rejected indiscriminate monorepo import, mock-as-runtime evidence, and automatic cancellation on hide. It also independently proposed operation IDs, late-stream disposal, old-finalizer isolation, input arbitration, and explicit backend configuration. Those are existing strengths, not new failures attributed to the old Skill.

The baseline identified a concrete retrieval gap: “It does not supply this application's request schema or a verified 0.19 speech-synthesis/cancellation contract; those remain implementation prerequisites.” The request schema correctly remains application-specific. The update supplies narrow official capture, vision-input, request-abort, and independent speech contracts, plus conditional import diagnosis and executable acceptance recipes. It makes previously inferred engineering decisions easier to apply without inventing platform APIs.

## Independent forward run

The fresh evaluator received the same scenario and updated packaged Skill, without the baseline, research notes, expected answer, or implementation diff. It selected `_blank` capture with the non-`cut` lifetime boundary, preserved encoded bytes/MIME, used the documented `AbortSignal` path, and selected `synthesize()` plus an independent player for controllable speech. It kept hide policy conditional on observed host transitions, protected new operations from old finalizers, preserved back/cancel, and separated portal parsing, mock evidence, and actual runtime verification. No unsupported generic browser cancellation API or inherited upstream PASS was proposed.

The evaluator also independently authored a pure JavaScript ownership model outside this repository, with fake capture/request/speech dependencies and controlled asynchronous completions. Its 26 cases passed on Node.js 24.19.0: zero failures, skips, cancellations, or TODOs. The primary agent inspected the model/tests and replayed the archived copy successfully, again 26/26. This is an application of the guidance to a synthetic model, not an AIUI adapter or a new product Agent.

The [retained probe](../probes/community-ownership/README.md) contains the controller, executable tests, original TAP output, and input/source hashes. Replay from that directory with `node --test --test-reporter=tap controller.test.mjs`. It covers byte/MIME preservation, late acquisition, old success/rejection/finalizer isolation, cancellation at speech stages, conditional hide/show, synthetic activation identity, denied/invalid payloads, service errors, timeout, and readable text after playback failure. Synthetic PNG bytes are not decoded, activation identity is not a claimed AIUI field, and fake resource counters do not prove hardware cleanup. Its unbounded diagnostic registries make it unsuitable as a production template.

All nine Skill-file hashes in the evaluator's metadata matched the final candidate. The full Skill-tree hash is `e696a225fbd55a5ed080f02da00ad4c2be1ddf0482b3690cbf6a4e17b5c7f3f5`; the exact hashing algorithm is recorded in [provenance.json](../probes/community-ownership/provenance.json). No Skill implementation changed after that capture.

## Repository verification and limits

The complete local flow passed 323/323 unit tests and 20/20 checks, including Skill/reference validation, five strict import roots, 0.19 inventory, the signed-audit black box, four real AIX pack/list flows, persistent archive delivery, HTML export, syntax, and whitespace. Independent source reviews found no blocking issue. The first focused run caught an over-budget Skill entrypoint and removal of an explicit import-directory phrase; both were corrected without weakening the tests.

This work does not validate a new production Agent, a live backend, authenticated Studio import, physical glasses, or platform submission. AIX HTML export is not rendered preview evidence. The existing 0.19 inventory-only capability policy and signed-evidence requirements remain unchanged.
