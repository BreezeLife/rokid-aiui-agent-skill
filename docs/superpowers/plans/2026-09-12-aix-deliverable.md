# AIX Deliverable Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Deliver a verified `.aix` archive alongside every complete editable AIUI source project when the installed AIX CLI supports and successfully executes packaging.

**Architecture:** Extend the existing `smoke_aix.sh` with an optional persistent mode that requires an explicit output path and repository root while preserving its one-argument temporary CI mode. Keep the compact Skill entrypoint declarative, place operational rules in the AIX reference, and enforce matching Chinese, English, and Japanese documentation through semantic tests.

**Tech Stack:** Bash, Python `unittest`, Markdown, `@yodaos-pkg/aix-cli@0.8.2`, GitHub Actions

---

### Task 1: Define the dual-output contract

**Files:**

- Add: `tests/test_aix_delivery_contract.py`
- Modify: `tests/test_smoke_aix.py`

- [ ] **Step 1: Add Skill and reference assertions**

Require creation/implementation work to always return a complete source root and to return a verified additional `.aix` when `pack` plus `list`/`ls` are advertised and succeed. Require an external destination, byte size, SHA-256, exact listing, no-overwrite behavior, and distinct `BLOCKED`/`FAIL` semantics.

- [ ] **Step 2: Add trilingual output assertions**

For each guide, parse the scope, prompt, verification, import, and completion sections. Require the archive to be described as additional, require the executable smoke command to carry an external `.aix` output argument, and keep Studio import pointed at the source directory.

- [ ] **Step 3: Add packaging-script behavior tests**

Use the existing fake AIX executable to request a persistent output. Assert that the exact bytes are preserved, the output metadata includes absolute path, size, a 64-character SHA-256, and an unchanged source fingerprint; existing destinations and destinations inside the source root fail, every declared Page is required, and list failure leaves no handed-off archive.

- [ ] **Step 4: Observe RED**

Run:

```bash
python3 -m unittest tests.test_aix_delivery_contract tests.test_skill_structure tests.test_multilingual_usage_docs tests.test_smoke_aix -v
```

Expected: the new assertions fail because the Skill does not yet promise the additional archive, the guide commands discard temporary packages, and the script accepts no delivery destination.

### Task 2: Implement verified archive delivery

**Files:**

- Add: `skills/rokid-aiui-agent/scripts/aix_delivery_guard.py`
- Modify: `skills/rokid-aiui-agent/scripts/smoke_aix.sh`

- [ ] **Step 1: Parse and validate the output path**

When argument two requests a persistent `.aix` destination, require argument three as the explicit repository root. Resolve all three roots through Python, require the import root to belong to that repository, reject a destination inside the import root, reject a missing lowercase `.aix` suffix, and refuse any existing file or symlink.

- [ ] **Step 2: Stage, inspect, and hand off**

Create the destination parent and a verified source snapshot in a unique hidden sibling directory. Require every declared Page plus the current package-entry and reserved-content checks. Only after all checks pass, publish the verified bytes through an exclusive no-clobber copy using a fixed parent-directory descriptor and list the exact destination once more. Recheck inode, size, and digest around the list operation; guarded cleanup removes only the current run's matching filesystem identity if the final recheck fails.

- [ ] **Step 3: Print content-addressed metadata**

Fingerprint the source before and after packaging and require equality. Print `AIUI source fingerprint`, `AIX artifact`, `AIX bytes`, and `AIX SHA-256` lines for a persistent output. Keep the existing smoke success line and temporary cleanup behavior when no output was requested. Document that AIX `0.8.2` embeds a random build ID, so the artifact SHA identifies delivered bytes rather than a reproducible source build.

- [ ] **Step 4: Observe GREEN for script tests**

Run:

```bash
python3 -m unittest tests.test_smoke_aix -v
```

Expected: every packaging-script test passes.

### Task 3: Teach the Skill and developers

**Files:**

- Modify: `skills/rokid-aiui-agent/SKILL.md`
- Modify: `skills/rokid-aiui-agent/references/aix-workflow.md`
- Modify: `README.md`
- Modify: `docs/usage.zh-CN.md`
- Modify: `docs/usage.en.md`
- Modify: `docs/usage.ja.md`

- [ ] **Step 1: Update the compact output contract**

State that source is mandatory and the verified archive is an additional default output when AIX capabilities and execution permit it. Route path, inspection, and failure detail to the AIX reference.

- [ ] **Step 2: Update the AIX reference**

Document source-validation order, external output location, the reusable command `bash skills/rokid-aiui-agent/scripts/smoke_aix.sh "$AIUI_IMPORT_ROOT" "$AIUI_AIX_OUTPUT" "$AIUI_REPOSITORY_ROOT"`, successful output fields, no-overwrite behavior, and separate `BLOCKED`/`FAIL` cases.

- [ ] **Step 3: Update README and three guides**

Make the Vibe Coding prompt request both outputs, add the archive to the result description, and update identical verification Bash blocks in all localized guides. Keep the README concise and keep the full audit mechanics routed out of it.

- [ ] **Step 4: Observe GREEN for contract tests**

Run:

```bash
python3 -m unittest tests.test_aix_delivery_contract tests.test_skill_structure tests.test_multilingual_usage_docs -v
```

Expected: all dual-output and existing documentation contracts pass.

### Task 4: Verify, review, and publish

**Files:**

- Modify: `PROJECT.md`
- Modify: `MEMORY.md`
- Modify: `TASKS.md`
- Modify: `WORKLOG.md`

- [ ] **Step 1: Record the durable decision**

Record that generated `.aix` archives are verified sibling/external deliverables, not tracked source or Studio import roots. Unavailable or unsupported packaging remains `BLOCKED`; an attempted pack/list, inventory, destination, or fingerprint failure is `FAIL`. Neither result invalidates an otherwise complete source delivery.

- [ ] **Step 2: Run independent contract and implementation reviews**

Review the diff for scope completeness, shell path safety, artifact cleanup, trilingual consistency, and evidence honesty. Resolve every critical or important finding.

- [ ] **Step 3: Run the complete local gate**

Run the full unit suite, OpenAI Skill validation, reference validation, four strict AIUI import-root validators, signed audit black-box test, Bash/Python/YAML syntax, real AIX smoke flows, one real persistent `.aix` handoff with list/hash checks, Focus Timer preview, and full-tree whitespace checks.

Expected: every automated local gate passes. Studio and device gates remain explicitly unexecuted.

- [ ] **Step 4: Commit and publish**

Commit the tested change, verify remote `main` still matches the base, push by fast-forward, wait for both CI jobs, and confirm public `main` exposes the updated Skill, script, and trilingual documentation.
