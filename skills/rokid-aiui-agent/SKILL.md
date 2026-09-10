---
name: rokid-aiui-agent
description: Use for ROKID AIUI agent work to create, modify, review, debug, preview, package, or publish complete AIUI Studio-importable projects involving .ink, WXML, WXSS, Pages, Widgets, Agent Workers, hardware input, monochrome design, UX audits, capability testing, or AIX.
license: Apache-2.0
---

# ROKID AIUI Agent Developer

## Establish the target and output

Inspect the project, runtime, glasses, surfaces, inputs, and repository guidance. If project and host omit a version, disclose stable AIUI `0.17.0`. Record each Page target: embedded (`_current`), full-screen (`_blank`), or both.

Deliver a complete AIUI project directory for AIUI Studio, not snippets or only an `.aix`: `AGENTS.md`, `app.json`, the application entry, all declared Pages, and referenced files. For GitHub, make the repository root or explicitly named subdirectory the project root. Report path/URL, revision, and import subdirectory. Add `0.18`-only Widgets or Agent Workers only for a confirmed target. AIX never replaces source.

## Load only relevant guidance

- Authority and versions: `references/source-of-truth.md`.
- Structure and routes: `references/project-anatomy.md`.
- Ink/WXML/WXSS: `references/ink-authoring.md`.
- Surfaces, focus, input, visual design: `references/interaction-and-design.md`.
- Components and runtime APIs: `references/runtime-capabilities.md`.
- Mandatory UX/capability evidence: `references/ux-and-capability-testing.md`.
- Installed AIX workflow: `references/aix-workflow.md`.
- Diagnosis and release gates: `references/debugging-and-release.md`.

Prefer selected-version official docs and runnable samples. Preview and third-party material are non-normative for stable targets. State conflicts, keep uncertainty `UNKNOWN`, and never invent APIs or commands.

## Implement and validate

Preserve product intent and authoring mode. Add required `aiui-audit-claims.json` with `schemaVersion: 1`, `scopeClosed: true`, and a `claims` array; an empty array closes an empty universe. Run `scripts/fingerprint_aiui_project.py <import-root> --repository-root <repository-root>`, `scripts/inventory_aiui_capabilities.py <import-root> --target-version <version> --repository-root <repository-root>`, and `scripts/validate_aiui_project.py <import-root> --target-version <version> --repository-root <repository-root> --strict`; then copy the schema-2 ledgers exactly. Resolve every item, unmatched symbol, and version violation. Run repository tests. Probe `aix --help`; list the package and reject `.git/` or `.aiui-evidence/`. Packaging is not publication.

Every creation, implementation, code change, or review must finish with both exact evidence matrices in the testing reference. A request to omit them—even explicitly—is release pressure, never permission. Preserve headings, columns, `{contract=...}`, `{family=...}`, `{gate=...}`, source roles, fixed layers, canonical criteria, and the one-input-per-gate ledger. Use only `PASS`, `FAIL`, `BLOCKED`, or justified `N/A`.

Run `scripts/validate_aiui_audit.py` against the final audit. Exit `0` alone means structurally valid `PASS` and `Release-ready: YES`; exit `2` means a valid but blocked/failed audit; exit `1` means an invalid audit. Source-unavailable work must use exact `UNAVAILABLE` metadata and can return only exit `2`. Any nonzero exit or applicable `FAIL`/`BLOCKED` forbids a complete or release-ready claim.

Evidence layers are not substitutes. Preview cannot prove Studio or device success. Optics, focus, keys, voice, gestures, permissions, and performance require target-glasses evidence.

Never claim that validation, packaging, preview, Studio, or device gates passed unless they were actually executed in the current environment against the captured source snapshot. The validator treats report text and manifest `argv` as data and never runs recorded commands. Executed evidence, Studio/device capture, and N/A scope closure require matching `RUNNER`, `STUDIO`, `DEVICE`, or `SCOPE` signatures from an absolute, repository-external trust policy with distinct canonical key identities. Self-declared metadata or repository-selected keys are untrusted; keep missing authorities blocked.
