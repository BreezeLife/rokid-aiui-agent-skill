# ROKID AIUI Agent Skill Design

## Context

The official AIUI repository already contains a large `aiui-dev` reference Skill. The new project should add value by turning the scattered framework, design, sample, AIX, course, and third-party information into a reliable development workflow with source precedence and executable validation. It should not fork an unmaintainable copy of every upstream page.

## Approaches considered

### 1. Thin wrapper around the official `aiui-dev` Skill

This would contain only workflow instructions and require users to install the upstream Skill separately. Maintenance is low, but the result is fragile when the dependency is missing and it cannot validate projects on its own.

### 2. Curated standalone Skill with pinned sources — selected

The repository contains a concise root Skill, focused references, a static validator, fixtures, behavioral scenarios, and source pins. It covers common development locally and sends agents to the pinned canonical source for volatile or exhaustive API details. This balances reliability, context size, and maintenance.

### 3. Full upstream mirror plus extensions

This would vendor the entire AIUI Skill and documentation and add AIX guidance. It is the most comprehensive offline option, but duplicates fast-moving upstream content, expands context, complicates licensing notices, and is likely to drift.

## Product behavior

The Skill supports five request classes:

1. Scaffold or extend an AIUI agent project.
2. Author or review `.ink` pages and project manifests.
3. Design for the target ROKID display and input model.
4. Diagnose AIUI runtime, focus, hardware-key, voice, media, or API problems.
5. Preview, validate, package, and prepare an agent for the platform workflow.

It begins by inspecting the target project and target surface. Conversation-flow cards are display-only; full-screen pages may be interactive. It then loads only the references relevant to the request. When platform facts are uncertain or version-sensitive, it checks the local project, installed CLI help, and current official documentation rather than guessing.

## Repository layout

```text
.
├── SKILL.md
├── agents/openai.yaml
├── references/
│   ├── source-of-truth.md
│   ├── project-anatomy.md
│   ├── ink-authoring.md
│   ├── interaction-and-design.md
│   ├── runtime-capabilities.md
│   ├── aix-workflow.md
│   └── debugging-and-release.md
├── scripts/validate_aiui_project.py
├── tests/
│   ├── fixtures/
│   ├── scenarios/
│   ├── evaluations/
│   └── test_validate_aiui_project.py
├── .github/workflows/ci.yml
├── README.md
├── LICENSE
└── project continuity files
```

`SKILL.md` is the routing and decision layer, not an API encyclopedia. Each reference has one responsibility and states when it should be read. `source-of-truth.md` records canonical locations, inspected commits, official/third-party status, and conflict rules.

## Validator contract

`scripts/validate_aiui_project.py PROJECT_DIR` returns zero for a structurally valid project and nonzero when errors exist. It emits stable severity/code/path messages suitable for humans and CI.

Initial checks:

- Required `AGENTS.md`, `app.json`, `app.js`, and `pages/` exist.
- `app.json` parses, has a non-empty string `pages` array, and does not contain duplicate routes.
- Every declared route resolves to exactly one authoring mode: one `.ink` file, or the supported multi-file page set.
- An `.ink` route contains one `<script def>`, one `<script setup>`, one `<page>`, and one `<style>` block; the definition block contains a JSON object.
- A route does not mix `.ink` and same-route multi-file definitions.
- Missing `AGENTS.md` identity/capabilities headings and target-sensitive design issues are warnings, not invented hard runtime errors.

The validator deliberately avoids pretending to compile JavaScript, WXML, or WXSS. Runtime support remains the authority for those semantics.

## AIX workflow

The Skill never assumes a command from a repository branch exists in the user's installed release. It runs `aix --help` (or an equivalent `npx` invocation), chooses only advertised commands, uses `pack` for artifacts, `list`/`ls` for inspection, and `preview` only when available. Deployment/publishing remains a ROKID platform action, not an invented CLI command.

A smoke test packages the valid fixture to a temporary `.aix` file and lists it. It does not upload or publish anything.

## Source and licensing policy

- Paraphrase and synthesize rather than copy whole manuals.
- Link facts to official source files or pages, preferably commit-pinned GitHub URLs.
- Record the source date and distinguish released behavior from unreleased `main` behavior.
- Third-party kits can reveal developer needs but cannot establish platform guarantees.
- Include only third-party material whose license permits reuse; otherwise link and describe at a high level.

## Testing

### RED baseline

Independent agents receive representative tasks without the new Skill. Evaluations record wrong assumptions, missing constraints, unsupported commands, and incomplete verification.

### GREEN and refactor

The same tasks run with the Skill. Success is based on observable invariants, not matching prose:

- correct project and `.ink` structure;
- correct card versus page interaction model;
- no fabricated AIUI or AIX APIs;
- target-aware ROKID display and input decisions;
- successful static validation;
- successful AIX pack/list when the published CLI supports it.

The Skill is revised only for demonstrated gaps, then scenarios are rerun.

### CI

CI runs the unit tests, project fixtures, frontmatter/placeholder checks, Markdown link/path checks, and deterministic smoke checks that do not require credentials or physical glasses. Hardware validation stays an explicit manual gate.

## Failure handling

- If official sources conflict, prefer the current canonical repository and changelog, then state the conflict.
- If a command is absent from `--help`, stop prescribing it and offer the supported alternative.
- If packaging fails, preserve the first actionable diagnostic and do not proceed to upload claims.
- If device-only behavior cannot be verified, label it as an on-device validation step.

## GitHub delivery

After local verification, create the public `BreezeLife/rokid-aiui-agent-skill` repository, push `main`, confirm the remote files and default branch, and report the install URL. No live ROKID deployment is part of this delivery.

