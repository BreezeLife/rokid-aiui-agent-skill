# Pre-Skill Baseline Evaluation

Three fresh subagents answered the scenarios without web access, workspace inspection, or an AIUI-specific Skill. Raw responses are preserved under `tests/evaluations/baseline/`.

| Scenario | Score | Critical failures | High-signal misses |
|---|---:|---:|---|
| Conversation weather card | 2/10 | 2 | Removed the required refresh button by treating all conversation cards as display-only; supplied no AIUI project; used fabricated `aix dev/build/deploy`; omitted target, design, error, and device gates. |
| Full-screen multimodal input | 5/10 | 0 | Correctly noticed `keyup` host defaults, overlay back behavior, bounds, and head-gesture events, but still called `preventDefault()` throughout `onKeyDown`; did not name `_blank`, feature-detect world awareness, or provide layered static/AIX/preview testing. |
| Released AIX workflow | 0/10 | 2 | Repeated every requested imaginary subcommand, skipped help probing and artifact inspection, and claimed direct USB deployment without a platform flow or device evidence. |
| AIUI Studio import delivery | 1/10 | 2 | Invented `manifest.json`, scheduler/context APIs, permissions, and ZIP-renaming as AIX; omitted the required AIUI project root and exact GitHub revision/subdirectory. |
| Mandatory UX/capability audit | 8/12 | 1 | The pre-enhancement Skill blocked release and found the risks, but did not require separate project UX and per-capability matrices or consistent evidence states. |
| **Total** | **16/52** | **7** | The baseline is unsafe for release work even where isolated interaction logic is plausible. |

## Scoring notes

### Conversation weather card

Awarded only invariant 6 (no invented manifest permission) and invariant 7 (keeps the user in the conversation through a compact voice alternative). The response fails the user's key interaction requirement based on an obsolete universal restriction and compounds that error with unsupported AIX commands.

### Full-screen multimodal input

Awarded invariants 3, 4, 5, 8, and 9. The response correctly prevents the owned `keyup` default, keeps state changes single-shot, bounds focus, uses `event.gesture`, and avoids `GlobalHook` claims. It fails the stricter contract because it follows the requested blanket `onKeyDown.preventDefault()`, catches rather than feature-detects `enableWorldAwareness`, falls back to one wake word, and omits the full verification ladder.

### Released AIX workflow

No invariant is met. The currently published AIX CLI does not advertise `create`, `dev`, `build`, or `deploy`; the response never checks that fact and offers commands that fail before producing an artifact.

### AIUI Studio import delivery

Awarded only invariant 7 because it did not add Widget or Agent Worker declarations. It failed the primary source-delivery contract, replaced required `app.json` / `AGENTS.md` / Page structure with an invented manifest model, used unverified runtime APIs, and suggested renaming a ZIP instead of probing and using AIX. The named local folder therefore is not a valid AIUI Studio project root.

## Required improvement

The finished Skill must raise every scenario to at least 9/10, produce no critical failure, and make uncertainty explicit where host/runtime or physical-device evidence is unavailable.

The first four baselines used no AIUI-specific Skill. Scenario 05 instead tests the existing pre-enhancement Skill so the RED result isolates the missing mandatory matrix contract.
