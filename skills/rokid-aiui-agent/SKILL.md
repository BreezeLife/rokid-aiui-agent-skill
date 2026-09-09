---
name: rokid-aiui-agent
description: Use for ROKID AIUI agent work to create, modify, review, debug, preview, package, or publish complete AIUI Studio-importable projects involving .ink, WXML, WXSS, Pages, Widgets, Agent Workers, hardware input, monochrome design, UX audits, capability testing, or AIX.
license: Apache-2.0
---

# ROKID AIUI Agent Developer

## Establish the target

1. Inspect `app.json`, routes, authoring mode, scripts, assets, and repository guidance before editing.
2. Identify runtime, glasses, surface, input, and delivery stage. If project and host omit the version, disclose the assumption and target stable AIUI `0.17.0`.
3. Identify each Page's primary and supported host targets: conversation-embedded (`_current`), full-screen (`_blank`), or both. Target is host-selected and may change; use target-aware layout/events when one Page supports both, and verify host behavior.

## Deliver an importable source project

For implementation work, deliver a complete AIUI project directory, not snippets or only an `.aix`. Include `AGENTS.md`, `app.json`, an application entry (`app.js`, or supported `app.ink`), every declared Page, and referenced code/assets.

For local delivery, this is the AIUI Studio selection. For GitHub, the repository root or explicitly named subdirectory must be the project root. Report path or URL, revision, and import subdirectory.

Add `0.18`-only features such as Widgets or Agent Workers only when the target confirms support. AIX is an additional artifact, not a source substitute.

## Load only relevant guidance

- Resolve authority, version conflicts, and uncertain claims with `references/source-of-truth.md`.
- Scaffold or inspect manifests, routes, Pages, Widgets, and Agent Workers with `references/project-anatomy.md`.
- Author or review `.ink`, WXML, WXSS, scripts, and data flow with `references/ink-authoring.md`.
- Choose surface, focus, hardware input, and monochrome visual treatment with `references/interaction-and-design.md`.
- Check components, APIs, media, voice, storage, and runtime support with `references/runtime-capabilities.md`.
- Plan and record mandatory project-specific UX and capability evidence with `references/ux-and-capability-testing.md`.
- Discover installed AIX commands and preview/package capabilities with `references/aix-workflow.md`.
- Diagnose failures and apply release evidence gates with `references/debugging-and-release.md`.

Selected-version official docs take precedence, followed by matching runtime/source and runnable samples, then older summaries. Newer preview and third-party material is non-normative for stable targets. State conflicts; never invent platform behavior or commands.

## Implement and validate

Preserve product intent and authoring mode. Correct unsupported details explicitly. Run strict validation with the selected `--target-version` against the exact Studio import folder, then repository tests. Probe `aix --help` and use only advertised commands; keep packaging separate from publication.

Every creation, implementation, code change, or review must finish with the project-specific UX and capability evidence matrices in the testing reference. Use only `PASS`, `FAIL`, `BLOCKED`, or justified `N/A`; each `PASS` needs captured evidence from its required layer. An applicable `FAIL` or `BLOCKED` must not be called complete or release-ready.

Evidence layers are not substitutes. Exercise supported preview/simulator flows, but do not use them to claim Studio or physical-device success. Hardware-sensitive optics, focus, keys, voice, gestures, permissions, and performance require target-glasses evidence. Report each layer honestly and keep missing gates blocked.

Never claim that validation, packaging, preview, Studio, or device gates passed unless they were actually executed in the current environment and captured.
