[简体中文](usage.zh-CN.md) | [English](usage.en.md) | [日本語](usage.ja.md) | [Repository home](../README.md)

# ROKID AIUI Agent Skill — Usage Guide

<!-- usage:scope -->
## 1. What this skill is for

`rokid-aiui-agent` helps coding agents that support Agent Skills create, modify, review, debug, and validate ROKID AIUI agent projects. For creation and implementation work, its default deliverable is a complete, editable source directory that can be selected directly as an AIUI Studio import root—not a collection of snippets or an `.aix` archive by itself.

A typical creation or implementation task produces:

- an AIUI source project containing `AGENTS.md`, `app.json`, the application entry point, every declared Page, and all referenced assets;
- `aiui-audit-claims.json`, which closes the project's declared capability scope;
- a source fingerprint, capability inventory, strict structural validation, and business-logic test results tied to the exact import root;
- the mandatory `## Project UX evidence matrix` and `## Per-capability matrix`;
- preview, pack, and list results when the installed AIX CLI actually advertises those commands;
- the local path, or all three GitHub import coordinates: repository, ref, and project directory;
- any unexecuted AIUI Studio, physical-glasses, or signed-evidence gates explicitly marked `BLOCKED`.

If neither the project nor the host identifies a target version, the skill discloses that assumption and uses stable AIUI `0.17.0` as its baseline. It must generate `0.18` capabilities such as Widgets or Agent Workers only when the target explicitly supports them.

Every import root needs an `aiui-audit-claims.json` file. This minimal schema-1 document closes an empty product-claims universe; `scopeClosed: true` does not mean that runtime behavior has passed testing:

```json
{
  "schemaVersion": 1,
  "scopeClosed": true,
  "claims": []
}
```

Add a claim only for real product behavior that cannot be reliably derived from the source inventory. Every non-empty claim still needs its own capability gate and evidence; it cannot borrow proof from a similar source item.

<!-- usage:install -->
## 2. Install

In a coding environment that supports Agent Skills, use the general Skills CLI:

```bash
npx skills add BreezeLife/rokid-aiui-agent-skill --skill rokid-aiui-agent
```

If your GitHub CLI installation exposes the `gh skill` command, you can instead run:

```bash
gh skill install BreezeLife/rokid-aiui-agent-skill rokid-aiui-agent --agent codex --scope user
```

Before installing, review the repository's [`SKILL.md`](../skills/rokid-aiui-agent/SKILL.md) and scripts. To update the skill, repeat the installation method you chose and check the source and revision reported by that tool. Reinstalling the skill is not evidence that an AIUI project passed validation.

<!-- usage:invoke -->
## 3. Invoke the skill

Add `$rokid-aiui-agent` to a request in your coding-agent conversation to invoke the skill explicitly. Explicit invocation is the most reproducible option:

```text
Use $rokid-aiui-agent to create a complete ROKID AIUI project that is ready
for AIUI Studio import, then run local validation and the required UX and
capability review.
```

Hosts that support implicit discovery may also load the skill when you ask directly for AIUI development, review, debugging, AIX preview, or packaging. To avoid routing ambiguity, include `$rokid-aiui-agent` explicitly in release-related requests.

Whenever possible, provide the target directory or existing import root, AIUI runtime, glasses model, `_current` / `_blank` surfaces, input methods, permissions, UI language, and desired delivery location. If this information is missing, the skill should inspect the project first. Anything it still cannot establish must remain an assumption, `UNKNOWN`, or `BLOCKED`; it must not guess an API.

<!-- usage:prompts -->
## 4. Copyable prompt recipes

<!-- prompt:new-project -->
### Create an AIUI agent from scratch

```text
Use $rokid-aiui-agent to create a complete ROKID AIUI weather agent in the
standalone directory /absolute/path/to/weather-agent. Target AIUI 0.17.0 and
support both the conversation-embedded _current Page and the full-screen
_blank Page. Check version-matched official sources first; do not infer APIs
from browsers or WeChat Mini Programs. Deliver a complete source directory
that AIUI Studio can import directly. Add deterministic tests, strict project
validation, capability inventory, and AIX preview/pack/list only when the CLI
help confirms those commands. Produce the mandatory Project UX evidence matrix
and Per-capability matrix. Keep Studio and physical-device items BLOCKED unless
they were actually executed.
```

<!-- prompt:timer -->
### Build a timer

```text
Use $rokid-aiui-agent to create a focus timer for Rokid Glasses in the standalone
directory /absolute/path/to/my-focus-timer. Make it a Page-only AIUI 0.17.0 project whose source
directory can be imported directly into AIUI Studio. Accept an integer
durationSeconds from 1 to 3600 and an optional label, default to 600 seconds,
and implement idle, running, paused, finished, and error states. Calculate
remaining time from an absolute deadline, recalibrate on hide/show, and clear
the timer on unload. Design suitable information density for _current and
_blank while retaining button tap and focus paths. Add nod or hardware-key
input only after confirming the exact mechanism in version-matched sources,
and always provide a non-sensor fallback. Do not promise background timing,
system alarms, notifications, or persistent recovery.

Run deterministic logic tests, strict validation, capability inventory, and the
preview/pack/list flows supported by AIX. Produce the complete Project UX evidence matrix
and Per-capability matrix. Keep unexecuted Studio and physical-glasses gates BLOCKED,
then report the exact local import root or the GitHub Repository, Ref, and
Directory.
```

<!-- prompt:review -->
### Review an existing project

```text
Use $rokid-aiui-agent to review /absolute/path/to/aiui-project without changing
its source. Establish the exact AIUI Studio import root, target version,
Page/Widget/Agent Worker surfaces, _current/_blank targets, inputs, and
permissions. Run the source fingerprint, capability inventory, and strict
validation, plus only the repository's existing safe tests. Report findings by
severity and produce the Project UX evidence matrix and Per-capability matrix.
Do not mark a row PASS without current-revision execution evidence. If Studio
access or physical glasses are unavailable, mark those gates BLOCKED rather
than N/A.
```

<!-- prompt:debug -->
### Fix or debug a project

```text
Use $rokid-aiui-agent to fix the current AIUI project's bug where a touchpad
single press does not invoke the primary action. Reproduce and isolate the Page
event, host focus, element focus, default-event, and fallback paths first, then
drive the smallest fix with a regression test. Preserve the current authoring
mode and target version, and do not invent event names. After the fix,
recompute the source fingerprint and capability inventory, run strict
validation and the available AIX flows, and refresh the Project UX evidence matrix
and Per-capability matrix. Do not reuse evidence from an older revision.
```

<!-- prompt:verify-package -->
### Validate, preview, and package

```text
Use $rokid-aiui-agent to validate skills/rokid-aiui-agent/assets/focus-timer-agent. Run
scripts/fingerprint_aiui_project.py, scripts/inventory_aiui_capabilities.py,
and strict project validation with scripts/validate_aiui_project.py first. Run
the deterministic tests before probing the CLI.
Then probe the current aix --help and use only the preview, pack, and list commands it actually
advertises. Do not upload or deploy anything. Confirm that the
.aix inventory excludes .git and .aiui-evidence, and report executed commands,
exit codes, artifact paths, and the current source revision. Also complete the
Project UX evidence matrix and Per-capability matrix, then run
scripts/validate_aiui_audit.py against the final audit. An AIX browser preview
does not replace AIUI Studio or physical-device evidence.
```

<!-- usage:verify -->
## 5. Check the delivered project

First confirm that the reported import root itself contains `app.json`; do not select a parent repository that contains the project only at a deeper path. The following commands use this repository's timer example as an executable reference. Replace `AIUI_IMPORT_ROOT` and the target version for your own project:

```bash
python3 -m pip install --only-binary=:all: -r requirements-dev.txt

AIUI_REPOSITORY_ROOT="$PWD"
AIUI_IMPORT_ROOT="skills/rokid-aiui-agent/assets/focus-timer-agent"

python3 skills/rokid-aiui-agent/scripts/fingerprint_aiui_project.py \
  "$AIUI_IMPORT_ROOT" --repository-root "$AIUI_REPOSITORY_ROOT"
python3 skills/rokid-aiui-agent/scripts/inventory_aiui_capabilities.py \
  "$AIUI_IMPORT_ROOT" --target-version 0.17.0 --repository-root "$AIUI_REPOSITORY_ROOT"
python3 skills/rokid-aiui-agent/scripts/validate_aiui_project.py \
  "$AIUI_IMPORT_ROOT" --target-version 0.17.0 --repository-root "$AIUI_REPOSITORY_ROOT" --strict
python3 -m unittest discover -s tests -v
```

The lockfile pins `@yodaos-pkg/aix-cli@0.8.2`, which requires Node.js `>=20`. Check the selected Node/npm runtimes before installing the locked dependency. Then probe `--help` and execute preview, pack, and list only when that installed CLI actually advertises them. The repository smoke flow exercises its supported pack-and-list path:

```bash
node --version
npm --version
npm ci --ignore-scripts --no-audit --no-fund

AIX_BIN="$PWD/node_modules/.bin/aix"
AIUI_PREVIEW_DIR="$(mktemp -d "${TMPDIR:-/tmp}/focus-timer-preview.XXXXXX")"
AIUI_PREVIEW_HTML="$AIUI_PREVIEW_DIR/index.html"
export AIX_BIN
"$AIX_BIN" --help
"$AIX_BIN" preview "$AIUI_IMPORT_ROOT" --html-out "$AIUI_PREVIEW_HTML"
test -s "$AIUI_PREVIEW_HTML"
bash skills/rokid-aiui-agent/scripts/smoke_aix.sh skills/rokid-aiui-agent/assets/focus-timer-agent
```

The audit validator checks the report and recorded `argv` as execution-provenance data; it never executes those recorded commands. Only results actually captured in the current environment and signed by the required authorities count as execution evidence.

Final audit validation requires an audit report for the current revision, content-addressed evidence, and an absolute trust policy stored outside the repository:

```bash
python3 skills/rokid-aiui-agent/scripts/validate_aiui_audit.py AUDIT.md \
  --repository-root /absolute/path/to/repository \
  --import-root skills/rokid-aiui-agent/assets/focus-timer-agent \
  --trust-policy /absolute/path/outside/repository/trust-policy.json
```

Audit exit codes have fixed meanings:

| Exit code | Contract | Meaning |
|---|---|---|
| `0` | `release-ready-pass` | Structurally valid with exactly `Final status: PASS` and `Release-ready: YES`. |
| `2` | `valid-not-release-ready` | Structurally valid, but the result remains `FAIL` or `BLOCKED`. |
| `1` | `invalid-or-untrusted` | Invalid, stale, tampered with, or untrusted. |

<!-- usage:audit -->
## 6. Mandatory UX and capability acceptance

Every creation, implementation, modification, or review must produce two separate tables. Use [`ux-and-capability-testing.md`](../skills/rokid-aiui-agent/references/ux-and-capability-testing.md) as the canonical format:

- `## Project UX evidence matrix` covers targets, states, boundary-length text, host and element focus, every input path, recovery, lifecycle, monochrome-green visuals, real optical conditions, motion, and performance;
- `## Per-capability matrix` covers every API, component, event, route, declaration, permission, fallback, and cleanup path, with commit-pinned official sources and the matching scanner gate.

Only these results are valid:

- `PASS`: every evidence layer required by that row was executed against the current source and supports the conclusion;
- `FAIL`: executed evidence contradicts the acceptance criterion;
- `BLOCKED`: a required environment, authority, or current-revision evidence is unavailable;
- `N/A`: allowed only when both the source scope and a closed product scope prove that the condition is inapplicable; missing hardware or time does not make a gate `N/A`.

The six evidence layers are not interchangeable. `SOURCE` establishes version-matched authority, `STATIC` establishes structure and bindings, `LOGIC` establishes deterministic behavior, `AIX` establishes the local CLI and basic browser rendering, `STUDIO` establishes authenticated import and Web simulation, and `DEVICE` establishes input, optics, and performance on the specified physical glasses. Execution evidence and AIX captures require a `RUNNER` authority; Studio, physical-glasses, and scope-exclusion evidence additionally require `STUDIO`, `DEVICE`, and `SCOPE` authorities respectively. Without the required signature, keep the gate `BLOCKED`.

<!-- usage:import -->
## 7. Import into AIUI Studio

For a local import, select the AIUI project directory that directly contains `app.json`. Do not select a parent repository when the project lives in a nested directory.

For a GitHub import, provide Repository, Ref, and Directory together. The timer example uses:

```text
Repository: https://github.com/BreezeLife/rokid-aiui-agent-skill
Ref: main
Directory: skills/rokid-aiui-agent/assets/focus-timer-agent
```

Importing through an authenticated AIUI Studio account is a separate execution step. Even if strict source validation, AIX preview, and pack all succeed, an unexecuted Studio import remains `BLOCKED` and may be described only as “source prepared for AIUI Studio import,” not “verified in Studio.”

<!-- usage:completion -->
## 8. What counts as complete

“Source delivery complete” means that the complete source project, import coordinates, and local validation results were provided. It does not automatically mean “release-ready.” You may write `Release-ready: YES` only when the audit validator returns `0` for the current fingerprint and trusted evidence, with no applicable `FAIL` or `BLOCKED` rows.

A typical accurate interim conclusion is: “Strict structural validation, logic tests, and AIX pack/list passed; AIUI Studio import and physical Rokid Glasses UX remain `BLOCKED`.”

<!-- usage:examples -->
## 9. Importable examples

- [`skills/rokid-aiui-agent/assets/studio-importable-minimal`](../skills/rokid-aiui-agent/assets/studio-importable-minimal/): minimal stable Page project;
- [`skills/rokid-aiui-agent/assets/focus-timer-agent`](../skills/rokid-aiui-agent/assets/focus-timer-agent/): Japanese focus timer;

Both directories are import roots; the timer is the repository's only product-shaped example Agent. Automated repository tests do not replace acceptance testing in your AIUI Studio account and on your target device.

<!-- usage:troubleshooting -->
## 10. Troubleshooting

- **The skill did not activate:** start the request with “Use `$rokid-aiui-agent`.”
- **Studio cannot see the project:** confirm that the selected directory directly contains `app.json` and every declared Page; do not select its parent directory.
- **An AIX command is missing:** run `--help` on the selected executable and use only commands listed by that installed version. Do not copy commands from another branch or an older website.
- **Preview works but the glasses do not:** preview supplies only `AIX`-layer evidence. It cannot prove Studio host behavior, sensors, hardware keys, focus, permissions, or optical presentation.
- **Can missing glasses be marked N/A?** No. Applicable physical-device gates remain `BLOCKED`.
- **Does pack mean published?** No. Pack only creates and inspects an `.aix` archive. Upload, platform review, deployment, and physical-device acceptance are later steps.
- **When can I use a Widget or Agent Worker?** Only when the target runtime explicitly supports the corresponding `0.18` capability and that version has an established source and evidence policy.
