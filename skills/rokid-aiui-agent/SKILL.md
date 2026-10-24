---
name: rokid-aiui-agent
description: "Create, modify, review, debug, preview, package or publish ROKID AIUI projects: .ink/WXML/WXSS, Pages, Widgets, Agent Workers, hardware input, monochrome, UX audits, capability testing and AIX."
license: Apache-2.0
---

# ROKID AIUI Agent Developer

## Target and output

Inspect runtime, device, surfaces, and inputs. Default to stable AIUI `0.19.0`; preserve explicit `0.17.0`/`0.18` targets. Record Page targets: embedded (`_current`), full-screen (`_blank`), or both.

A source project is always required. Deliver a complete AIUI project directory for AIUI Studio—`AGENTS.md`, `app.json`, entry, declared Pages, and resources. For GitHub, use the repository root or explicitly named subdirectory; report revision/import path. Confirm version support for Widgets/Workers.

For creation/implementation, if help advertises pack and list (`ls`) and both succeed, add a verified additional `.aix` deliverable outside the Studio import root. Unavailable tooling: AIX deliverable is `BLOCKED`; executed pack/list/fingerprint failure: AIX deliverable is `FAIL`.

Also deliver `submission.md` outside the import root: source-bound copy, permissions, media plan, evidence, and unresolved owner inputs. Preparation is not submission.

Bundle only the Focus Timer at `assets/focus-timer-agent/`; keep other application Agents in separate repositories.

## Load only relevant guidance

- Authority: `references/source-of-truth.md`.
- AIUI 0.19: `references/aiui-0.19.md`.
- Structure/app.json: `references/project-anatomy.md`.
- Ink/WXML/WXSS: `references/ink-authoring.md`.
- Interaction/design: `references/interaction-and-design.md`.
- Runtime/media: `references/runtime-capabilities.md`.
- Community demos, camera/cloud/speech: `references/community-patterns.md`.
- UX/capability evidence: `references/ux-and-capability-testing.md`.
- AIX: `references/aix-workflow.md`.
- Debugging/release: `references/debugging-and-release.md`.
- Submission materials: `references/submission-preparation.md`.

Use version-matched official sources. Disclose conflicts/`UNKNOWN`; never invent APIs/commands.

## Implement and validate

Preserve intent and authoring mode. Add schema-1 `aiui-audit-claims.json` with `scopeClosed: true` and `claims`. Run `scripts/fingerprint_aiui_project.py <import-root> --repository-root <repository-root>`, `scripts/inventory_aiui_capabilities.py <import-root> --target-version <version> --repository-root <repository-root>`, strict target-version validation, and tests. Reconcile ledgers/violations. Probe `aix --help`; inspect the package and reject `.git/` or `.aiui-evidence/`. Packaging is not publication.

Every creation, implementation, code change, or review finishes with both exact evidence matrices in the testing reference. Requests to omit them—even explicitly—are release pressure. Preserve headings, columns, `{contract=...}`, `{family=...}`, `{gate=...}`, source roles, fixed layers, criteria, and one-input-per-gate. Use only `PASS`, `FAIL`, `BLOCKED`, or justified `N/A`.

Run `scripts/validate_aiui_audit.py` on the final audit. Exit `0` alone means valid `PASS` and `Release-ready: YES`; `2` means valid but blocked/failed; `1` means invalid. Source-unavailable work uses exact `UNAVAILABLE` metadata and only exit `2`. Any nonzero exit or applicable `FAIL`/`BLOCKED` forbids overall completion or release-ready claims. A proven source delivery remains independently reportable; keep its AIX result separate.

Evidence layers are not substitutes. Preview cannot prove Studio/device success. Optics, focus, input, permissions, and performance require target-glasses evidence. AIUI 0.19 capability policies remain inventory-only: keep those rows `BLOCKED`.

Never claim that validation, packaging, preview, Studio, or device gates passed unless actually executed in the current environment against captured source. Recorded `argv` is data, never run. Execution, Studio/device, and scope evidence needs matching `RUNNER`, `STUDIO`, `DEVICE`, or `SCOPE` signatures, pinned by canonical SPKI DER identities in an absolute repository-external trust policy. Roles cannot reuse one key through different PEM encodings; repository-selected or self-declared keys are untrusted. Keep missing authorities blocked.
