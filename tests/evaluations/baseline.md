# Pre-Skill Baseline Evaluation

Six fresh subagents answered isolated scenarios under the conditions recorded with each raw response. The first four had no AIUI-specific Skill; scenarios 05 and 06 used the pre-enhancement Skill to isolate the missing completion artifact. Raw responses are preserved under `tests/evaluations/baseline/`.

| Scenario | Score | Critical failures | High-signal misses |
|---|---:|---:|---|
| Conversation weather card | 2/10 | 2 | Removed the required refresh button by treating all conversation cards as display-only; supplied no AIUI project; used fabricated `aix dev/build/deploy`; omitted target, design, error, and device gates. |
| Full-screen multimodal input | 5/10 | 0 | Correctly noticed `keyup` host defaults, overlay back behavior, bounds, and head-gesture events, but still called `preventDefault()` throughout `onKeyDown`; did not name `_blank`, feature-detect world awareness, or provide layered static/AIX/preview testing. |
| Released AIX workflow | 0/10 | 2 | Repeated every requested imaginary subcommand, skipped help probing and artifact inspection, and claimed direct USB deployment without a platform flow or device evidence. |
| AIUI Studio import delivery | 1/10 | 2 | Invented `manifest.json`, scheduler/context APIs, permissions, and ZIP-renaming as AIX; omitted the required AIUI project root and exact GitHub revision/subdirectory. |
| Mandatory UX/capability audit | 8/12 | 1 | The pre-enhancement Skill blocked release and found the risks, but did not require separate project UX and per-capability matrices or consistent evidence states. |
| Implementation/change completion gate | 2/7 | 2 | Correctly rejected stale pre-change evidence, but brevity pressure caused it to omit both required matrices and their row-level network, voice, fallback, and evidence findings. |
| **Total** | **18/59** | **9** | The baseline is unsafe for release work even where isolated interaction logic is plausible. |

## Scoring notes

### Conversation weather card

Awarded only invariant 6 (no invented manifest permission) and invariant 7 (keeps the user in the conversation through a compact voice alternative). The response fails the user's key interaction requirement based on an obsolete universal restriction and compounds that error with unsupported AIX commands.

### Full-screen multimodal input

Awarded invariants 3, 4, 5, 8, and 9. The response correctly prevents the owned `keyup` default, keeps state changes single-shot, bounds focus, uses `event.gesture`, and avoids `GlobalHook` claims. It fails the stricter contract because it follows the requested blanket `onKeyDown.preventDefault()`, catches rather than feature-detects `enableWorldAwareness`, falls back to one wake word, and omits the full verification ladder.

### Released AIX workflow

No invariant is met. The currently published AIX CLI does not advertise `create`, `dev`, `build`, or `deploy`; the response never checks that fact and offers commands that fail before producing an artifact.

### AIUI Studio import delivery

Awarded only invariant 7 because it did not add Widget or Agent Worker declarations. It failed the primary source-delivery contract, replaced required `app.json` / `AGENTS.md` / Page structure with an invented manifest model, used unverified runtime APIs, and suggested renaming a ZIP instead of probing and using AIX. The named local folder therefore is not a valid AIUI Studio project root.

### Mandatory UX/capability audit

Awarded eight invariants because the pre-enhancement Skill still separated evidence layers, found the visible interaction and CAMERA defects, and rejected release. It incurred a critical artifact failure because neither exact project matrix was a mandatory output, so the response could not provide a stable row-level sign-off record.

### Implementation/change completion gate

Awarded invariants 1 and 5. The response correctly noticed that changing the primary interaction invalidated validator, unit, and preview evidence captured earlier, and it kept physical voice/focus checks unverified. It nevertheless omitted both exact matrices after the user requested a short answer, so the review had no inspectable per-risk or per-capability completion record.

## Required improvement

The finished Skill must earn full credit on the 7-point completion-gate scenario, raise each 10-point scenario to at least 9/10, produce no critical failure, and make uncertainty explicit where host/runtime or physical-device evidence is unavailable.

The first four baselines used no AIUI-specific Skill. Scenarios 05 and 06 instead test the existing pre-enhancement Skill so the RED results isolate both the missing mandatory matrix contract and its susceptibility to brevity/completion pressure.
