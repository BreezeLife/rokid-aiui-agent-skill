# Post-Skill Forward Evaluation

Forward responses are preserved under `tests/evaluations/forward/`. Scenarios 05 and 06 were refreshed blind on 2026-09-10 from the current Skill, its routed references, and the scenario prompts, without opening their prior forward responses or any baseline response.

| Scenario | Baseline | Forward | Critical failures | Result |
|---|---:|---:|---:|---|
| Conversation weather card | 2/10 | 10/10 | 0 | Preserved the requested `_current` refresh interaction while disclosing the official-source conflict; delivered a complete 0.17 project, bounded network states, current green grammar, and layered verification. |
| Full-screen multimodal input | 5/10 | 10/10 | 0 | Rejected blanket keydown interception; implemented conditional keyup handling, bounded focus, feature-detected world awareness, voice/gesture events, cleanup, and device gates. |
| Released AIX workflow | 0/10 | 10/10 | 0 | Rejected four invented commands; used the official initializer, inspected scripts, probed the selected CLI, then separated preview, pack/list, platform upload, and physical-device evidence. |
| AIUI Studio import delivery | 1/10 | 10/10 | 0 | Made complete editable source the primary output, supplied exact import roots/coordinates, defaulted to 0.17, and treated AIX only as an additional verified artifact. |
| Mandatory UX/capability audit | 8/12 | 12/12 | 0 | The fresh 34-row source-unavailable audit closes every requested capability and input gate, separates host/element focus and CAMERA permission/runtime/lifecycle, and keeps every unproved layer `BLOCKED`. |
| Implementation/change completion gate | 2/7 | 7/7 | 0 | The fresh 22-row source-unavailable audit rejects stale pre-change evidence, retains both exact matrices, and keeps voice, fallback, migration, network, focus, target, route, and lifecycle bindings provisional. |
| **Total** | **18/59** | **59/59** | **0** | **Meets every scenario threshold with no critical failure.** |

## Scoring notes

### Conversation weather card

Awarded all invariants. The response names the stable runtime and target device assumption, keeps the compact interaction requested by the user, supplies every required project file, implements loading/success/empty/stale/failure and retry behavior with a finite timeout, avoids fabricated permissions, distinguishes runtime and optical coordinate systems, and preserves Studio/device uncertainty.

### Full-screen multimodal input

Awarded all invariants. Business actions occur once on owned `keyup` events; Backspace only closes the visible overlay and otherwise returns control to the host. Empty and boundary states are safe and visible. Voice uses `event.keyword`; gestures use `event.gesture` only after feature-detected Page world awareness is enabled. Preview and hardware evidence remain separate.

### Released AIX workflow

Awarded all invariants. The response does not emit executable `aix create`, `aix dev`, `aix build`, or `aix deploy` commands. It uses the official initializer, verifies Node and actual root help, conditionally previews, requires a non-empty archive and expected `list`/`ls` entries, distinguishes npm 0.8.2 from repository main, and leaves account/device work behind explicit gates.

### AIUI Studio import delivery

Awarded all invariants after rerunning this scenario against the final packaged Skill. The first capture exposed a verification-integrity risk, so the Skill was strengthened to forbid claiming a check passed unless it was executed in the current environment. The rerun materialized the complete 0.17 project in an isolated staging directory, then actually passed strict validation and AIX 0.8.2 `help`, `pack`, and `list`; it recorded the 4,064-byte artifact and SHA-256 while correctly leaving GitHub push, Studio account import, platform upload, and physical glasses unverified.

### Mandatory UX/capability audit

Awarded all invariants in the blind refresh. The report uses the exact seven metadata lines and both exact matrix schemas, splits all seven input paths, uses project-binding provisional rows with narrow commit-pinned 0.17 source policies, inventories route/target, host/element focus, button/binding, generic voice, gesture/fallback, CAMERA permission/runtime/lifecycle, and Page lifecycle separately, and contains no `PASS` or `N/A`. Source-unavailable validation returned the expected exit 2 with `Final status=BLOCKED` and `Release-ready=NO`.

### Implementation/change completion gate

Awarded all invariants in the blind refresh. The report treats the interaction change as invalidating older validator, unit, and AIX evidence, produces both exact schemas, separates the three scoped input gates, and inventories host focus, element focus, voice, fallback, migration, network, route, target, and lifecycle without adding an unclaimed voice declaration. The unresolved transport remains a provisional `network.unknown` row rather than inventing a concrete mechanism. Source-unavailable validation returned the expected exit 2 with `Final status=BLOCKED` and `Release-ready=NO`.

## Outcome

Across all six scenarios, the rubric score remains 59/59 with no critical failure, up 41 points from the recorded 18/59 baseline. The refreshed 05 and 06 reports were generated from zero without reading the old reports or baseline, then independently accepted by `validate_aiui_audit.py` in source-unavailable mode as structurally valid blocked audits. Six evaluation-specific contract and mutation tests passed. The full `tests.test_ux_capability_contract` module ran 41 tests: 40 passed, while `test_project_revision_is_resolvable_or_recomputed` failed because the shared worktree contains an uncommitted `tests/fixtures/valid-minimal/aiui-audit-claims.json`, so that fixture no longer byte-matches `HEAD`. This unrelated dirty-worktree failure is not counted as scenario evidence and remains unresolved rather than being hidden. These results are behavior-level evidence for the Skill contract, not a substitute for Studio account access or physical-glasses testing.
