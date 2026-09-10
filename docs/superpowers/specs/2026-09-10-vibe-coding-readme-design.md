# Vibe Coding README design

## Goal

Turn the root README into a task-oriented landing page for developers who use natural-language coding agents. A reader should be able to install the Skill, invoke it, understand the deliverable, and locate the AIUI Studio import root without learning the audit implementation first.

## Audience

- Developers starting a ROKID AIUI Agent through Codex, Claude Code, Cursor, or another Agent Skills host
- Developers who prefer to describe an outcome and let the coding agent handle project structure and validation
- Evaluators who need a tested example before building their own Agent

## Information architecture

Use a prompt-first flow:

1. State the outcome in one sentence and keep all three language links near the top.
2. Put installation and one copyable Chinese prompt in the first major section.
3. Explain the generated project and AIUI Studio import handoff in plain language.
4. Show the Focus Timer as the sole bundled product Agent.
5. Summarize automated quality checks without exposing their internal schemas.
6. Link to the three complete guides, advanced audit reference, source policy, and maintainer commands.

## Progressive disclosure

The README keeps these public guarantees:

- Creation work returns a complete, editable AIUI project directory rather than snippets or only an `.aix` archive.
- The default is stable AIUI `0.17.0`; `0.18` features require an explicit compatible target.
- The coding agent reports local checks separately from authenticated AIUI Studio and physical-device checks.
- Focus Timer remains the only bundled product Agent; other application Agents belong in separate repositories.

The README does not explain claims schemas, inventory reconciliation, evidence signatures, trust-policy keys, validator exit codes, or every maintainer command. Those details remain available in the localized guides and `ux-and-capability-testing.md`.

## README sections

1. Product statement and language navigation
2. Three-step quickstart
3. Copyable prompts for a new Agent and an existing project
4. Expected project output
5. Local and GitHub AIUI Studio import
6. Bundled Focus Timer
7. Automated checks and evidence boundary
8. AIUI version policy
9. Deeper guides, repository map, sources, and license

## Acceptance checks

- The README stays concise and follows the reader's task flow from installation and prompting through project handoff, Studio import, verification boundaries, and deeper guides.
- Language links remain in the first 15 lines.
- Both supported installation commands and an explicit `$rokid-aiui-agent` prompt are copyable.
- Low-level audit terms such as `publicKeySha256`, `claimsLedger`, `SPKI DER`, `attestations`, and `trust-policy` are absent.
- The timer path and Studio GitHub coordinates are accurate.
- Local Markdown links resolve.
- Existing Skill, AIUI project, AIX, and audit behavior remains unchanged.
