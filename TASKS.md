# Tasks

## In progress

- [ ] Complete RED/GREEN behavioral evaluation, full local verification, publication, and remote CI confirmation.

## Done

- [x] Confirmed repository name and public visibility with the user.
- [x] Initialized the empty local workspace as a Git repository.
- [x] Inspected the current canonical AIUI, AIX, Awesome AIUI, and third-party kit repositories.
- [x] Extracted and visually reviewed the official ROKID AIUI courseware PDF.
- [x] Finished the source audit and recorded authoritative URLs, pinned versions, conflicts, and third-party boundaries.
- [x] Captured and scored four independent pre-Skill behavioral baselines (8/40, six critical failures).
- [x] Implemented the discoverable `skills/rokid-aiui-agent/` package, metadata, seven routed references, and Studio-importable asset.
- [x] Implemented and tested the dependency-free AIUI project validator, including adversarial markup, entry, Widget, and version-gate cases.
- [x] Verified published AIX 0.8.2 capability detection, exact package listing, pack, static preview, and installed-Skill execution.
- [x] Ran four independent forward scenarios (40/40, zero critical failures) and closed the observed evidence-integrity gap.
- [x] Added CI, repository documentation, Apache-2.0 licensing, and source notices.
- [x] Completed independent Studio-contract and code/CI reviews with no remaining implementation P0/P1.
- [x] Created and pushed the public `BreezeLife/rokid-aiui-agent-skill` GitHub repository.
- [x] Verified the public default branch and files, both documented remote installation flows, and a green GitHub Actions run.
- [x] Corrected the discovered AIUI `schema.data` reference drift with a regression test.
- [x] Built the stable `examples/next-step-agent/` Studio-importable project through RED/GREEN tests.
- [x] Added strict validation, published-AIX package/preview coverage, documentation, and visual preview evidence.
- [x] Published the Next Step Agent to public `main` at `eb8204799b0cb13aae180e00a30283eb5367b35a` and confirmed GitHub Actions run `34158236017` passed both jobs.
- [x] Built and locally verified the Japanese `examples/focus-timer-agent/` stable AIUI 0.17 Page project with deterministic fake-clock coverage and AIX preview/pack/list evidence.
- [x] Added locally verified nod-driven primary actions to the Focus Timer Page without introducing eye tracking; retained physical-glasses gesture behavior as a manual gate.
- [x] Corrected voice-driven timer setup routing so valid new or changed durations require a fresh Page call, including the 25-minute-to-1500-second contract and reconfiguration regression.
- [x] Audited the Focus Timer against pinned AIUI 0.17 examples, hardened the World Awareness fallback, removed the error-state dead action, and visually inspected the generated AIX preview.
- [x] Published the complete Focus Timer history and audit fix to public `main`, verified the remote import directory, and observed a successful GitHub Actions run for the feature commit.
- [x] Added a tested 10-minute Focus Timer default for invocations without an explicit duration, while preserving errors for explicitly invalid values.
- [x] Built `examples/scenequest-agent/` as a stable-AIUI-0.17, Page-only Japanese Agent with exactly 12 source-traceable Osaka spots and no bundled anime screenshots.
- [x] Implemented and locally tested SceneQuest's bounded four-state contract, categorical confidence, one-retry uncertain flow, tolerant photo-guidance fallback, nearby selection, and prompt-injection/input-isolation boundaries.
- [x] Added SceneQuest strict validation, published-AIX pack/list smoke, blocking static-preview CI coverage, repository documentation, and locally recorded UX/capability evidence.
- [x] Reproduced and fixed Focus Timer touchpad single-click activation in the AIX simulator, including visible conditional action buttons and Page-level Enter/GlobalHook handling.
- [x] Published SceneQuest through GitHub pull request #1 to public `main` at `1b08da9fb8e39ab3e2e6bc4c3b7b894fb41f7583`, verified the remote import directory, and observed both GitHub Actions jobs succeed.
- [x] Added mandatory AIUI-standard UX and per-capability evidence matrices, six non-substitutable evidence layers, stable result semantics, and source-backed optical acceptance thresholds to the packaged Skill.
- [x] Ran two isolated RED/GREEN behavior gates: the audit improved from 8/12 to 12/12 and the implementation-change gate from 2/7 to 7/7; final post-hardening blind transcripts preserve exact matrix schemas, stable capability IDs, narrow version-pinned sources, and zero critical failures.

## External manual gates

- [ ] Import the example through an authenticated AIUI Studio account using the published GitHub coordinates.
- [ ] Verify product-specific agents on the target physical Rokid Glasses before making device-behavior or release-readiness claims.
- [ ] Import `examples/focus-timer-agent/` through an authenticated AIUI Studio account and verify both `_current` and `_blank` on physical Rokid Glasses.
- [ ] Verify World Awareness nod recognition and the start/pause/continue/restart mapping on physical Rokid Glasses.
- [ ] Verify that spoken timer setup and changes cause a new Page invocation in authenticated AIUI Studio and on physical Rokid Glasses.
- [x] Imported `examples/scenequest-agent/` through authenticated Craft by selecting the exact AIUI project root and ran the Web simulation in both 448×150 card and 480×352 interactive modes; Craft reported no project issues and logged a successful `pages/index/index` render.
- [ ] NOT TESTED: Verify SceneQuest Agent-host delivery of camera imagery and GPS/current-location context.
- [ ] NOT TESTED: Verify SceneQuest permission grant, denial, revocation, and unavailable-capability behavior for camera and location.
- [ ] NOT TESTED: Verify Japanese voice response and fresh Page invocation coordination for SceneQuest.
- [ ] NOT TESTED: Verify real `_current` / `_blank` targets, target transitions, host focus, element focus, and nearby scrolling.
- [ ] NOT TESTED: Verify SceneQuest hardware input and selection behavior on target Rokid Glasses.
- [ ] NOT TESTED: Verify physical-glasses readability over bright, dark, and cluttered real backgrounds, including optical clipping and contrast.
- [ ] NOT TESTED: Verify dynamic visual photo guidance under occlusion, viewpoint variation, and user motion.
- [ ] NOT TESTED: Measure SceneQuest cold-start latency, sustained performance, and thermal behavior on target hardware.
