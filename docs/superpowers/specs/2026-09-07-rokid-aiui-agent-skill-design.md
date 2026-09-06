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

It begins by inspecting the target project and target surface. Conversation-embedded pages can support click, selection, input, and host-mediated expansion; full-screen pages provide more space and deeper flows. It then loads only the references relevant to the request. When platform facts are uncertain or version-sensitive, it checks the local project, installed CLI help, current official documentation, implementation, and samples rather than guessing.

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

`scripts/validate_aiui_project.py PROJECT_DIR` returns zero when no errors exist and nonzero when errors exist. Warnings describe maintainability or packaging risks without claiming the runtime rejects the project. `--strict` makes warnings fail CI. Diagnostics use stable severity/code/path messages suitable for humans and automation.

Initial checks:

- Required `app.json` exists and parses. Missing `AGENTS.md` or `app.js` is a warning because official project structure recommends them but the package reader does not establish both as hard requirements.
- `app.json` parses, has a non-empty string `pages` array, and does not contain duplicate routes.
- Every declared page route resolves to an `.ink` file or at least a `.wxml` entry for multi-file mode.
- A page `.ink` route contains exactly one `<page>` root and no `<widget>` root. Optional `<script def>`, `<script setup>`, and `<style>` blocks may occur at most once; a present definition block contains a JSON object.
- Declared Widgets resolve to `.ink`, use a documented `1x1` or `1x2` family, and contain exactly one `<widget>` root.
- Declared Agent Worker scripts exist and use a supported `.js` or `.ts` entry path.
- Mixed `.ink` and same-route multi-file definitions, missing manifest headings, reserved generated AIX paths, and target-sensitive design issues are warnings rather than invented runtime errors.

The validator deliberately avoids pretending to compile JavaScript, WXML, or WXSS. Runtime support remains the authority for those semantics. Its XML-like block checks are intentionally structural rather than a full `.ink` parser.

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
- correct `_current` versus `_blank` interaction, focus, and density model;
- no fabricated AIUI or AIX APIs;
- target-aware ROKID display and input decisions;
- successful static validation;
- successful AIX pack/list when the published CLI supports it.

The Skill is revised only for demonstrated gaps, then scenarios are rerun.

### CI

CI runs the unit tests, project fixtures, frontmatter/placeholder checks, Markdown link/path checks, and deterministic smoke checks that do not require credentials or physical glasses. Hardware validation stays an explicit manual gate.

## Failure handling

- If official sources conflict, prefer the current changelog and implementation-aligned documentation, corroborate with runtime/source and runnable samples, and state the conflict.
- If a command is absent from `--help`, stop prescribing it and offer the supported alternative.
- If packaging fails, preserve the first actionable diagnostic and do not proceed to upload claims.
- If device-only behavior cannot be verified, label it as an on-device validation step.

## GitHub delivery

After local verification, create the public `BreezeLife/rokid-aiui-agent-skill` repository, push `main`, confirm the remote files and default branch, and report the install URL. No live ROKID deployment is part of this delivery.
