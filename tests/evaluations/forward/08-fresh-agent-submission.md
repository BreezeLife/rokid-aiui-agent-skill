# Fresh AIUI 0.19 generation evaluation

Date: 2026-10-23 (Asia/Shanghai). Brief: [fresh generation scenario](../../scenarios/08-fresh-agent-submission.md).

An independent agent generated the Chinese timer **一刻专注** in the sibling delivery directory `AIUI019-FocusTimer-Verification-20261023`, without consulting or copying the bundled timer implementation. Only its `app/` directory is the Studio import root. Product source, tests, packages, raw captures, and listing drafts remain outside this Skill repository.

## Method and provenance

The generation used repository base `4d139890d0a9e54f93d05c38e3c867db0901a772` plus the in-progress functional/UX and submission guidance. The external `evidence/skill-provenance.json` records hashes of the exact Skill files read; the base commit alone does not identify those working files. Official AIUI requirements were pinned to `7d62c2d9ac1cdc1389ba06ed0651b395903accff`.

An independent reviewer replayed the logic tests and inspected the source against the selected API contract. The main agent separately opened the actual preview in a browser and operated its rendered controls. Unit tests load the generated `.ink` setup logic with a controlled clock; they do not stand in for browser, Studio, or device execution.

## Findings and corrections

1. Strict validation, deterministic tests, AIX pack/list, and HTML export initially succeeded. Opening that HTML failed before application loading: `Cannot read properties of null (reading 'length')` in the Ink constructor. The published `@yodaos-pkg/ink@0.19.0` JavaScript wrapper supplied 15 arguments to a 17-argument generated binding, shifting a null value into a required string. The original failure screenshot, stack, upstream package, hashes, and minimal diff are preserved in the external evidence directory.
2. A separate diagnostic runtime adds only the missing constructor arguments. Its pages carry a visible compatibility-patch warning; the import source does not contain this patch. Diagnostic observations cannot become an unmodified AIX, Studio, or device PASS. The original AIX 0.8.2 preview imports an unversioned network module, so its CLI lockfile alone does not pin rendering behavior.
3. Source review found that resetting cleared the visual focus flag on a retained reset button. A regression reproduced the retained-focus case, and state updates now preserve that flag until an actual blur. Browser clicking subsequently showed the reset outline remaining visible.
4. Actual rendering exposed implicit column layout where the author intended horizontal groups. The generated source was corrected to specify its layout direction explicitly. This is why source review and a successful HTML export do not replace visual inspection.

## Evidence boundaries

Final source fingerprint: `WORKTREE:272e826dc5685cc77263c6728ee06847aa66df271f66784d266e9558bdb12093`. Archive: `submission/focus-timer-v3.aix`, 14,430 bytes, SHA-256 `f894a6d2ae31c9245e4f6a34b5fd080c453978d1d80feba90881b342b46dcb4a`. Earlier packages and captures remain identified as superseded snapshots.

| Check | Actual outcome |
| --- | --- |
| Strict AIUI 0.19 import-root validation | Exit 0, zero errors/warnings |
| Deterministic application tests | 17/17 passed |
| Fresh inventory/fingerprint and real AIX pack/list | Passed for the final source; archive identity above |
| Unmodified AIX browser startup | FAIL before bundle loading; HTML export alone passed |
| Explicit diagnostic preview | Click start/pause/resume/reset, retained reset focus, five-second completion, invalid-input recovery, and long mixed Unicode label rendered and operated successfully; horizontal layout fits the observed 480×352 canvas |
| Diagnostic keys | Enter and ArrowDown had no visible effect through the panel or direct SDK input, even with reported interactive focus; event-delivery root cause unresolved |
| Audit structure | Exit 2, 18 UX rows and 39 capability rows, BLOCKED; missing trusted authorities and 0.19 policies preserved |
| Submission preparation | Filled copy and permission/reviewer drafts, custom icon, two warning-labeled diagnostic PNGs and a 17.36-second sampled interaction MP4; formal platform media and owner inputs still blocked |

The MP4 preserves the timing of 254 actual browser screenshots; it is sampled diagnostic capture, not a claim of continuous device recording. The external capture manifest records hashes, source identity, runtime, viewport, and timestamps. The audit's blocked AIX reasons explicitly disclose the observed failures: unsigned local captures cannot satisfy its signed FAIL evidence contract, and its admitted-evidence ledger must not be read as an assertion that no local failure occurred.

The application implements a Page-local timer, explicit start/pause/continue/reset, completion, input validation, and recovery to the ten-minute default. Tests exercise absolute deadlines, elapsed hidden time, unload cleanup, stale callbacks, repeated actions, range boundaries, Unicode labels, and host-default delegation. New voice requests require a fresh Page invocation; background alarms, persistence, and in-place conversational mutation are not promised.

The diagnostic preview permits inspection of application rendering and click behavior. AIX panel keyboard behavior is investigated separately and must not be inferred from passing callbacks. Both `_current` and `_blank` remain subject to real host testing. No physical glasses were attached, and no authenticated Studio run or platform submission occurred.

Submission preparation includes listing copy, concrete call examples, permission/data-use explanations, source/package identity, a custom draft icon, capture provenance and plans, reviewer steps, and missing owner/platform fields. Any diagnostic media retains its warning and must not be presented as unmodified platform or device evidence.

The exact UX and capability matrices retain missing authorities and unregistered AIUI 0.19 PASS policies as blockers. A structurally valid audit returning exit `2` is an honest blocked assessment, not evidence that release readiness passed. This evaluation establishes the tested coverage of one generated sample, not universal correctness of AIUI agents.
