---
name: rokid-aiui-agent
description: Use for ROKID AIUI agent work to create, modify, review, debug, preview, package, or publish complete AIUI Studio-importable projects involving .ink, WXML, WXSS, Pages, Widgets, Agent Workers, hardware input, monochrome design, or AIX.
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
- Discover installed AIX commands and preview/package capabilities with `references/aix-workflow.md`.
- Diagnose failures and apply release evidence gates with `references/debugging-and-release.md`.

Selected-version official docs take precedence, followed by matching runtime/source and runnable samples, then older summaries. Newer preview and third-party material is non-normative for stable targets. State conflicts; never invent platform behavior or commands.

## Implement and validate

Preserve product intent, structure, and authoring mode. Correct unsupported details explicitly and make the smallest maintainable change.

Run strict validation with the selected `--target-version` against the exact Studio import folder, then run repository tests. Before giving AIX instructions, run `aix --help` (or the project's equivalent invocation) and use only capabilities advertised by the installed release; do not assume create, dev, build, deploy, upload, or publish commands. Keep local packaging separate from platform publication.

Never claim that validation, packaging, preview, Studio import, platform upload, or device testing passed unless it was actually executed in the current environment and its evidence was captured. Otherwise provide the command and mark the gate unverified.

Exercise the flow in the supported simulator/preview path and record the result. Hardware-sensitive interaction, optics, focus, keys, gestures, and release readiness also require physical-glasses evidence. Report both simulator and device evidence, or label the missing gate and avoid claiming completion.
