# Two development paths README design

## Overview

The root README remains a Chinese-first landing page for developers who want to build ROKID AIUI Agents. It must teach two distinct starting paths without duplicating the detailed Studio import coordinates or implying that local automation replaces Studio and physical-device verification.

## Goal

Help a new developer choose either AIUI Studio or an AI Vibe Coding tool, then complete the first actionable steps without needing to infer how the Skill is invoked.

## Audience

- Developers who already have a complete AIUI project or want to open the bundled Focus Timer in AIUI Studio
- Developers starting from a natural-language idea or an existing AIUI codebase in Codex or another Agent Skills-compatible coding tool

## Approaches considered

### Add a route selector and keep detailed sections

Add two route subsections inside `快速开始`. Keep the existing complete-project and Studio sections as the detailed destinations. This keeps the README scannable, preserves one source for GitHub import coordinates, and allows the Codex route to contain a copyable tutorial.

### Merge all setup and Studio material into one branched tutorial

This would put every step in one place, but it would make the landing page longer and repeat concepts that belong to the output and verification sections.

### Add a separate Codex-only section

This would require fewer edits, but it would duplicate the existing coding-agent prompt and could imply that the Skill only works with Codex.

The first approach is selected. It preserves the current prompt-first flow while making both routes explicit.

## Content design

`快速开始` opens with a short route-selection summary. It then contains exactly two task-oriented subsections in this order:

1. `路线 1：在 AIUI Studio 中打开项目` serves developers who already have a Studio-importable project or want to inspect the bundled example. It links to the detailed Studio import section and Focus Timer section instead of repeating coordinates.
2. `路线 2：用 Codex 等 Vibe Coding 工具开发` serves developers who want an AI coding agent to create, modify, review, or debug an AIUI project. It teaches a numbered workflow: install the Skill, open a separate Agent workspace, invoke `$rokid-aiui-agent` with a copyable prompt, inspect the complete output and executed checks, then import the delivered directory into Studio.

The route selector must describe Codex as one compatible tool, not the only supported host. The existing `npx skills add` command remains the primary install path; the guarded `gh skill install` command remains the alternative.

## Output and evidence boundaries

Both routes converge on the same editable AIUI project contract. The output root contains `AGENTS.md`, `app.json`, an application entry, every page declared by `app.json.pages`, and every referenced resource. An `.aix` package alone is insufficient.

The Vibe Coding route tells developers to create work outside this Skill repository and replace the sample absolute path. It must not imply that a coding agent can complete authenticated Studio or Rokid Glasses checks without those environments. Studio import and physical-device behavior remain `BLOCKED` until executed.

The Focus Timer remains the only bundled product Agent. No new example Agent, cloud service, screenshot, or external product claim is added.

## Test design

Extend the README semantic contract before editing prose. Tests identify two distinct `###` route blocks inside `快速开始` without requiring exact sentence wording.

- The Studio route requires AIUI Studio, importing or opening a project, continued editing or development, and a link to the detailed import section.
- The Vibe Coding route requires Codex plus other compatible coding tools, Skill installation, explicit `$rokid-aiui-agent` invocation, an independent output directory, a complete editable project, executed validation, and Studio handoff.
- The Vibe Coding workflow must preserve the order install, invoke, validate, Studio handoff.
- The existing complete-project, output-path, version, Focus Timer, Studio/device, language, and sole-product-Agent checks remain intact.

Run the focused test once before the README change and require it to fail only because the two routes are absent. After implementation, run the focused documentation and timer tests, the full unit suite, strict project checks, Skill and reference validation, AIX pack/list and preview flows, full-tree whitespace validation, and GitHub Actions.

## Open questions

None. The user explicitly requested both AIUI Studio and Codex-style Vibe Coding instructions and previously authorized continuous implementation without intermediate approval prompts.
