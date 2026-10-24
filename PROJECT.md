# ROKID AIUI Agent Skill

## Vision

Build an open-source, source-traceable Agent Skill that helps coding agents and developers create, debug, validate, preview, and package complete ROKID AIUI source projects that AIUI Studio can import, without assuming browser behavior or inventing AIUI/AIX APIs.

## Users

- Developers starting a ROKID AIUI agent.
- Coding agents editing `.ink`, `app.json`, `app.js`, and `AGENTS.md` files.
- Maintainers diagnosing runtime, input, visual, preview, or packaging problems.

## Architecture

- `skills/rokid-aiui-agent/`: installable Agent Skills package whose directory name matches its frontmatter name.
- `skills/rokid-aiui-agent/SKILL.md`: compact task router, invariants, and end-to-end workflow.
- `skills/rokid-aiui-agent/agents/openai.yaml`: UI-facing metadata for automatic discovery.
- `skills/rokid-aiui-agent/references/`: focused, on-demand guidance derived from authoritative sources.
- `skills/rokid-aiui-agent/references/aiui-0.19.md`: pinned 0.19 additions, migration boundaries, and functional/UX regression scenarios.
- `skills/rokid-aiui-agent/references/submission-preparation.md`: source-bound Agent listing drafts, permission/data-use explanations, review reproduction, media requirements, and unresolved platform inputs.
- `skills/rokid-aiui-agent/references/community-patterns.md`: attributed demo-adaptation patterns, official camera/model/speech contracts, async/input ownership, conditional Studio import diagnosis, and executable functional/UX case recipes.
- `skills/rokid-aiui-agent/references/media-implementation-and-testing.md`: versioned multimedia start/output/cleanup contracts and actual-call verification for photos, recording, audio, video, analysis, and 0.19 WebRTC; reached from runtime and testing guidance.
- `skills/rokid-aiui-agent/scripts/validate_aiui_project.py`: dependency-free static project validator.
- `skills/rokid-aiui-agent/scripts/fingerprint_aiui_project.py`: deterministic revision binding for the exact Studio import root.
- `skills/rokid-aiui-agent/scripts/inventory_aiui_capabilities.py`: schema-2 scanner that reconciles a closed claims ledger with exact declared surfaces and one-path-per-gate inputs.
- `skills/rokid-aiui-agent/scripts/validate_aiui_audit.py`: fail-closed UX/capability audit validator for source snapshots, signed evidence, scope exclusions, and release status.
- `skills/rokid-aiui-agent/scripts/aix_delivery_guard.py`: filesystem-identity path guard, verified source snapshotter, exclusive no-clobber publisher, and inode/digest verifier for persistent AIX delivery.
- `skills/rokid-aiui-agent/scripts/smoke_aix.sh`: capability-probed AIX pack/list gate with a temporary smoke mode and a source-bound, no-overwrite delivery mode for external `.aix` artifacts.
- `skills/rokid-aiui-agent/assets/studio-importable-minimal/`: complete stable-baseline AIUI source project and Studio import fixture.
- `skills/rokid-aiui-agent/assets/focus-timer-agent/`: the only bundled product-shaped Agent; a Japanese stable-0.17 Page-only focus timer with deterministic absolute-deadline tests.
- `README.md`, `README.en.md`, `README.ja.md`: parallel project homepages with a shared concept hero, language navigation, task-specific prerequisites, and two-route onboarding; keep commands, delivery requirements, and evidence boundaries aligned.
- `docs/usage.zh-CN.md`, `docs/usage.en.md`, `docs/usage.ja.md`: parallel developer guides for installation, invocation, validation, Studio import, and mandatory UX/capability acceptance.
- `docs/assets/focus-timer-user-journey.png` and `output/pdf/focus-timer-developer-reference.pdf`: reproducible developer visuals for the bundled Focus Timer; they are explanatory material, not Studio or device evidence.
- `tests/`: validator fixtures, unit tests, behavioral scenarios, and recorded evaluations.
- `docs/superpowers/`: approved design and executable implementation plan.

## Principles

1. Official AIUI documentation for the selected target version and released AIX behavior outrank tutorials, newer preview-only material, and third-party kits.
2. Preserve the distinction between conversation-embedded (`_current`) and full-screen (`_blank`) surfaces. Current AIUI supports interaction in both; available space, focus, density, and flow depth differ.
3. Treat AIUI as its own runtime: do not infer unsupported browser, WeChat, CSS, or AIX behavior.
4. Detect installed CLI capabilities before prescribing commands.
5. When official repository artifacts conflict, prefer newer changelog/documentation plus implementation and runnable samples over a stale bundled Skill summary.
6. Prefer progressive disclosure over a monolithic reference dump.
7. Make generated work testable with deterministic checks and a real AIX pack/list flow when available.
8. For implementation tasks, always deliver an editable AIUI project directory directly selectable for Studio import. When supported pack/list operations execute successfully, also deliver a verified `.aix` outside that import root; the archive never replaces source.
9. Default new work to official stable AIUI `0.19.0`, pinned to a verified official source snapshot rather than mutable `latest`. Preserve explicitly selected 0.17/0.18 compatibility. The bundled 0.17 projects remain legacy compatibility fixtures.
10. Every AIUI project creation, implementation, change, or review must produce project-specific UX and per-capability evidence matrices. Bind them to an exact source fingerprint and a closed capability inventory whose claims, supported surfaces, and input gates reconcile exactly. Evidence layers are non-substitutable, and missing Studio or physical-device proof remains blocked.
11. Treat audit reports and repository evidence as untrusted input. The validator never executes recorded `argv`; execution, Studio, device, and scope evidence is accepted only when the required capture envelopes verify against distinct role-specific keys pinned by an absolute, repository-external trust policy using canonical SPKI DER identities.
12. Make the repository boundary explicit for fingerprints and inventories. Only the repository root's top-level `.git/` and `.aiui-evidence/` aliases are reserved, matched without ASCII case distinctions; nested same-named source remains in scope, reserved content cannot carry runtime code, and release-ready audit status also requires strict target-version Studio-import validation.

## Non-goals

- Mirroring every upstream AIUI document.
- Publishing agents to a live ROKID account or managing credentials.
- Treating unofficial projects as normative platform documentation.
- Guaranteeing on-device behavior without a physical-glasses test.

## Success criteria

- The Skill passes Codex skill validation.
- GitHub and generic Skills CLIs discover and install `rokid-aiui-agent` from the standard package path.
- Chinese, English, and Japanese usage entrypoints expose the same tested commands, prompt recipes, output contract, and evidence boundaries.
- The installed Skill contains the timer Agent as its sole product example; unrelated application Agents remain in separate repositories.
- The local validator has positive and negative fixture coverage.
- A repository example is a complete `0.17.0`-compatible source directory that passes strict validation and real AIX pack/list.
- Independent forward tests can create or review representative AIUI projects using the correct authoring mode, input model, design constraints, and AIX commands.
- 0.19 inventory and audit inputs use an explicit version profile and pinned sources; new platform-looking APIs cannot silently disappear from scope. Until separately registered 0.19 capability PASS policies exist, their rows remain `BLOCKED` while functional/UX evidence is still checked.
- Forward tests require consistent `PASS` / `FAIL` / `BLOCKED` / `N/A` evidence semantics and block release claims when an applicable UX or capability gate lacks its required evidence.
- The audit validator returns success only for a structurally valid `PASS` plus `Release-ready: YES`, distinguishes honest `FAIL` / `BLOCKED` reports from invalid or untrusted reports, and treats unavailable source and unsupported `N/A` claims fail-closed.
- CI explicitly exercises the complete signed-evidence black-box path that is allowed to return release-ready exit zero, in addition to the full negative unit suite.
- A fixture packages and lists successfully with a supported published AIX CLI.
- A supported real AIX flow can preserve a non-empty external archive without overwrite, bind it to an unchanged source fingerprint, and report its final path, size, SHA-256, command, and listing.
- A fresh independent generation run produces a complete external 0.19 project with executed functional checks, observed preview UX, reconciled capability/audit results, and a source-bound submission handoff; local success does not imply Studio/device or platform review success.
- The public GitHub installation URL resolves and the repository CI is green.
