# ROKID AIUI Agent Skill

## Vision

Build an open-source, source-traceable Agent Skill that helps coding agents and developers create, debug, validate, preview, and package ROKID AIUI agents without assuming browser behavior or inventing AIUI/AIX APIs.

## Users

- Developers starting a ROKID AIUI agent.
- Coding agents editing `.ink`, `app.json`, `app.js`, and `AGENTS.md` files.
- Maintainers diagnosing runtime, input, visual, preview, or packaging problems.

## Architecture

- `SKILL.md`: compact task router, invariants, and end-to-end workflow.
- `agents/openai.yaml`: UI-facing metadata for automatic discovery.
- `references/`: focused, on-demand guidance derived from authoritative sources.
- `scripts/validate_aiui_project.py`: dependency-free static project validator.
- `tests/`: validator fixtures, unit tests, behavioral scenarios, and recorded evaluations.
- `docs/superpowers/`: approved design and executable implementation plan.

## Principles

1. Current official AIUI and AIX sources outrank tutorials and third-party kits.
2. Preserve the distinction between non-interactive conversation-flow cards and interactive full-screen pages.
3. Treat AIUI as its own runtime: do not infer unsupported browser, WeChat, CSS, or AIX behavior.
4. Detect installed CLI capabilities before prescribing commands.
5. Prefer progressive disclosure over a monolithic reference dump.
6. Make generated work testable with deterministic checks and a real AIX pack/list smoke flow when available.

## Non-goals

- Mirroring every upstream AIUI document.
- Publishing agents to a live ROKID account or managing credentials.
- Treating unofficial projects as normative platform documentation.
- Guaranteeing on-device behavior without a physical-glasses test.

## Success criteria

- The Skill passes Codex skill validation.
- The local validator has positive and negative fixture coverage.
- Independent forward tests can create or review representative AIUI projects using the correct authoring mode, input model, design constraints, and AIX commands.
- A fixture packages and lists successfully with a supported published AIX CLI.
- The public GitHub installation URL resolves and the repository CI is green.

