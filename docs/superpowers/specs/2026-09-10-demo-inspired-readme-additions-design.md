# Demo-inspired README additions design

## Overview

Add a small amount of product-oriented context to the prompt-first README. Borrow the user-provided demo repository's scannable information architecture, not its code, media, services, performance claims, credentials, or product capabilities.

## Goal

Help a Vibe Coding developer understand what the Skill can do, how the bundled Focus Timer behaves, and what the repository contains without reopening the low-level audit wall removed in the previous README revision.

## Audience

- Developers using natural-language coding agents to start or continue an AIUI project
- Developers deciding whether this Skill fits creation, modification, review, or Studio handoff work
- Maintainers locating the packaged Skill, references, validators, and the sole bundled product Agent

## Content plan

### Explain what the Skill can do

Add a short section after the opening paragraph. Cover four task families in plain language: create a complete project, modify an existing project, review and debug AIUI-specific behavior, and validate the handoff to AIUI Studio. Do not list unsupported platform APIs or imply that local checks prove device behavior.

### Show the Focus Timer controls

Add a compact operation table inside the existing Focus Timer section. Map the four implemented states to the primary nod or touchpad action: start, pause, continue, and restart. Keep voice, nod, touchpad, authenticated Studio, and physical-device behavior explicitly subject to their correct evidence gates.

### Add a repository map

Add a compact path-and-purpose table before the deeper guides. Link the Skill entry, focused references, validation scripts, minimal import template, Focus Timer project, and the three localized guides. State that the minimal asset is a skeleton and Focus Timer is the only bundled product Agent.

## Information boundary

The external README is a private, user-provided design reference. The public repository will not link to it or copy its screenshots, recordings, cloud endpoints, latency numbers, security architecture, brand claims, licenses, or unverified hardware capability statements. This change adds no Agent and changes no AIUI source project.

## Test design

Extend the existing prompt-first README contract before editing prose:

- require the new sections in reader-task order
- require the four supported task families without locking exact sentences
- require the four Focus Timer state-to-action mappings and the Studio/device verification boundary
- require repository-map links to the Skill, references, scripts, both assets, and localized guides
- preserve the existing complete-project, version, Studio import, low-level-term exclusion, and sole-product-Agent tests

Run the focused tests to observe RED, implement the minimum prose, then run the focused and complete suites plus reference, Skill, strict import, AIX, and publication checks.

## Open questions

None. The user requested a small README expansion and previously authorized continuous implementation without step-by-step confirmation. The minimal content-only approach is selected.
