# Post-Skill Forward Evaluation

Four fresh subagents loaded the completed Skill and only the references routed for their scenario. Raw responses are preserved under `tests/evaluations/forward/`.

| Scenario | Baseline | Forward | Critical failures | Result |
|---|---:|---:|---:|---|
| Conversation weather card | 2/10 | 10/10 | 0 | Preserved the requested `_current` refresh interaction while disclosing the official-source conflict; delivered a complete 0.17 project, bounded network states, current green grammar, and layered verification. |
| Full-screen multimodal input | 5/10 | 10/10 | 0 | Rejected blanket keydown interception; implemented conditional keyup handling, bounded focus, feature-detected world awareness, voice/gesture events, cleanup, and device gates. |
| Released AIX workflow | 0/10 | 10/10 | 0 | Rejected four invented commands; used the official initializer, inspected scripts, probed the selected CLI, then separated preview, pack/list, platform upload, and physical-device evidence. |
| AIUI Studio import delivery | 1/10 | 10/10 | 0 | Made complete editable source the primary output, supplied exact import roots/coordinates, defaulted to 0.17, and treated AIX only as an additional verified artifact. |
| **Total** | **8/40** | **40/40** | **0** | **Meets the release threshold of at least 9/10 per scenario with no critical failure.** |

## Scoring notes

### Conversation weather card

Awarded all invariants. The response names the stable runtime and target device assumption, keeps the compact interaction requested by the user, supplies every required project file, implements loading/success/empty/stale/failure and retry behavior with a finite timeout, avoids fabricated permissions, distinguishes runtime and optical coordinate systems, and preserves Studio/device uncertainty.

### Full-screen multimodal input

Awarded all invariants. Business actions occur once on owned `keyup` events; Backspace only closes the visible overlay and otherwise returns control to the host. Empty and boundary states are safe and visible. Voice uses `event.keyword`; gestures use `event.gesture` only after feature-detected Page world awareness is enabled. Preview and hardware evidence remain separate.

### Released AIX workflow

Awarded all invariants. The response does not emit executable `aix create`, `aix dev`, `aix build`, or `aix deploy` commands. It uses the official initializer, verifies Node and actual root help, conditionally previews, requires a non-empty archive and expected `list`/`ls` entries, distinguishes npm 0.8.2 from repository main, and leaves account/device work behind explicit gates.

### AIUI Studio import delivery

Awarded all invariants after rerunning this scenario against the final packaged Skill. The first capture exposed a verification-integrity risk, so the Skill was strengthened to forbid claiming a check passed unless it was executed in the current environment. The rerun materialized the complete 0.17 project in an isolated staging directory, then actually passed strict validation and AIX 0.8.2 `help`, `pack`, and `list`; it recorded the 4,064-byte artifact and SHA-256 while correctly leaving GitHub push, Studio account import, platform upload, and physical glasses unverified.

## Outcome

The forward suite improved by 32 points, from 8/40 with six critical failures to 40/40 with none. This is behavior-level evidence that the Skill corrects the targeted failure modes; it is not a substitute for CI, Studio account access, or physical-glasses testing.
