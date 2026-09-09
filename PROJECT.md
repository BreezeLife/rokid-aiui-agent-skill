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
- `skills/rokid-aiui-agent/scripts/validate_aiui_project.py`: dependency-free static project validator.
- `skills/rokid-aiui-agent/assets/studio-importable-minimal/`: complete stable-baseline AIUI source project and Studio import fixture.
- `examples/next-step-agent/`: first product-shaped project generated with the Skill; a stable-0.17, Page-only Studio import root.
- `examples/focus-timer-agent/`: Japanese stable-0.17 Page-only focus timer with deterministic absolute-deadline tests.
- `examples/scenequest-agent/`: Japanese SceneQuest / セイチ｜SEICHI stable-0.17 Page-only pilgrimage example with 12 curated Osaka spots and four bounded result states.
- `tests/`: validator fixtures, unit tests, behavioral scenarios, and recorded evaluations.
- `docs/superpowers/`: approved design and executable implementation plan.

## Principles

1. Official AIUI documentation for the selected target version and released AIX behavior outrank tutorials, newer preview-only material, and third-party kits.
2. Preserve the distinction between conversation-embedded (`_current`) and full-screen (`_blank`) surfaces. Current AIUI supports interaction in both; available space, focus, density, and flow depth differ.
3. Treat AIUI as its own runtime: do not infer unsupported browser, WeChat, CSS, or AIX behavior.
4. Detect installed CLI capabilities before prescribing commands.
5. When official repository artifacts conflict, prefer newer changelog/documentation plus implementation and runnable samples over a stale bundled Skill summary.
6. Prefer progressive disclosure over a monolithic reference dump.
7. Make generated work testable with deterministic checks and a real AIX pack/list smoke flow when available.
8. For implementation tasks, deliver an editable AIUI project directory. A local folder or a clearly identified GitHub repository subdirectory must be directly selectable for AIUI Studio import.
9. Default to the official `0.17.0` stable compatibility baseline when no target version is discoverable; gate `0.18` additions behind an explicit target or capability evidence.

## Non-goals

- Mirroring every upstream AIUI document.
- Publishing agents to a live ROKID account or managing credentials.
- Treating unofficial projects as normative platform documentation.
- Guaranteeing on-device behavior without a physical-glasses test.

## Success criteria

- The Skill passes Codex skill validation.
- GitHub and generic Skills CLIs discover and install `rokid-aiui-agent` from the standard package path.
- The local validator has positive and negative fixture coverage.
- A repository example is a complete `0.17.0`-compatible source directory that passes strict validation and real AIX pack/list.
- Independent forward tests can create or review representative AIUI projects using the correct authoring mode, input model, design constraints, and AIX commands.
- A fixture packages and lists successfully with a supported published AIX CLI.
- The public GitHub installation URL resolves and the repository CI is green.
