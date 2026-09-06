# ROKID AIUI Agent Skill Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Deliver and publish a tested, source-traceable Agent Skill for developing ROKID AIUI agents.

**Architecture:** A compact root `SKILL.md` routes work to focused references. A dependency-free Python validator and fixtures turn important structural rules into executable checks, while behavioral scenarios verify that coding agents apply platform constraints and released AIX capabilities correctly.

**Tech Stack:** Markdown/YAML Agent Skill, Python 3 standard library, `unittest`, GitHub Actions, GitHub CLI, published AIX npm CLI.

---

### Task 1: Establish project truth and RED scenarios

**Files:**
- Create: `PROJECT.md`
- Create: `MEMORY.md`
- Create: `TASKS.md`
- Create: `WORKLOG.md`
- Create: `tests/scenarios/01-conversation-card.md`
- Create: `tests/scenarios/02-fullscreen-input.md`
- Create: `tests/scenarios/03-aix-workflow.md`
- Create: `tests/evaluations/baseline.md`

- [ ] Write three scenario prompts that separately test current conversation-embedded interaction/design, full-screen hardware input, and released AIX capability discovery.
- [ ] Dispatch fresh agents without access to the new Skill and save their responses verbatim under `tests/evaluations/baseline/`.
- [ ] Evaluate responses against explicit invariants and record observed failures in `tests/evaluations/baseline.md`.
- [ ] Run `git diff --check`; expect exit code 0.
- [ ] Commit with `test: capture AIUI skill baseline scenarios`.

### Task 2: Implement the minimal Skill router

**Files:**
- Create: `SKILL.md`
- Create: `agents/openai.yaml`

- [ ] Write a failing structure test that checks required frontmatter, discriminating trigger text, every routed reference path, and absence of scaffold placeholders.
- [ ] Run the structure test; expect failure because `SKILL.md` does not exist.
- [ ] Write the minimal root Skill with task classification, source precedence, surface/target discovery, implementation workflow, verification gates, and routed reference links.
- [ ] Add UI metadata with display name `ROKID AIUI Agent Developer`, a short description, and a default prompt that invokes the Skill for an AIUI development task.
- [ ] Run the structure test and the bundled `quick_validate.py`; expect both to pass.
- [ ] Commit with `feat: add ROKID AIUI skill router`.

### Task 3: Add focused, source-pinned references

**Files:**
- Create: `references/source-of-truth.md`
- Create: `references/project-anatomy.md`
- Create: `references/ink-authoring.md`
- Create: `references/interaction-and-design.md`
- Create: `references/runtime-capabilities.md`
- Create: `references/aix-workflow.md`
- Create: `references/debugging-and-release.md`

- [ ] Populate `source-of-truth.md` with canonical URLs, inspected commit hashes, source class, version caveats, and conflict rules.
- [ ] Synthesize project files, page data contracts, `.ink` authoring, routing, and authoring-mode invariants from current official AIUI docs.
- [ ] Synthesize interactive `_current`/`_blank` behavior, 480 by 352 green-display constraints, current low-mass 1px/4px/6px visual grammar, theme-token use, focus, keyup interception, voice, head gesture, and on-device gates.
- [ ] Build a capability index that directs agents to the narrow official component/API source and forbids inferred browser compatibility.
- [ ] Document released AIX install, help probing, pack/list/preview capability branches, and the separate platform publish flow.
- [ ] Document a symptom-led debugging and release checklist with evidence requirements.
- [ ] Run the structure/path test; expect every routed reference to resolve.
- [ ] Commit with `docs: add source-pinned AIUI development references`.

### Task 4: Build the AIUI project validator with TDD

**Files:**
- Create: `scripts/validate_aiui_project.py`
- Create: `tests/test_validate_aiui_project.py`
- Create: `tests/fixtures/valid-minimal/`
- Create: `tests/fixtures/invalid-missing-route/`
- Create: `tests/fixtures/warning-mixed-mode/`
- Create: `tests/fixtures/invalid-ink-blocks/`

- [ ] Write unit tests for missing/malformed/non-object `app.json`, empty/duplicate routes, unresolved routes, mixed page-mode warnings, wrong or duplicate `.ink` roots, duplicate optional blocks, invalid `<script def>` JSON, missing Widget and Agent Worker entries, and valid minimal projects.
- [ ] Run `python3 -m unittest discover -s tests -v`; expect failures because the validator is missing.
- [ ] Implement stable `ERROR`/`WARNING` diagnostics, normal/`--strict` exit behavior, and JSON output using only Python's standard library.
- [ ] Run the full unit test command; expect all tests to pass with no warnings from the test runner.
- [ ] Run the validator directly on every fixture and confirm valid exits 0 while invalid fixtures exit nonzero with the expected diagnostic code.
- [ ] Commit with `feat: add AIUI project validator`.

### Task 5: Verify the real AIX packaging flow

**Files:**
- Create: `scripts/smoke_aix.sh`
- Modify: `tests/fixtures/valid-minimal/` if packaging reveals a real missing requirement.
- Create: `tests/evaluations/aix-smoke.md`

- [ ] Query the npm registry for the current published `@yodaos-pkg/aix-cli` version and required Node range; record the observed values.
- [ ] Write the smoke script to use a temporary output directory, capture `--help`, require advertised `pack` and `list`/`ls`, package the valid fixture, list the artifact, and clean only its own temporary directory.
- [ ] Run the smoke script; expect a non-empty `.aix` artifact and a successful listing containing `app.json` and the page route.
- [ ] Record released-versus-main differences without documenting unreleased commands as generally available.
- [ ] Commit with `test: verify published AIX package flow`.

### Task 6: Add repository UX, provenance, and CI

**Files:**
- Create: `README.md`
- Create: `LICENSE`
- Create: `THIRD_PARTY_NOTICES.md`
- Create: `.github/workflows/ci.yml`
- Create: `tests/test_skill_structure.py`
- Create: `scripts/verify_references.py`

- [ ] Document install, invocation, supported workflows, source policy, local validation, AIX smoke test, and hardware-test limitations in the README.
- [ ] Add an Apache-2.0 license and notices for paraphrased or adapted official Apache-2.0 material; list unmodified links for non-vendored sources.
- [ ] Add a reference checker for local links, commit-pin syntax, and forbidden stale hostnames outside the historical-note allowlist.
- [ ] Add CI that checks out the repository and runs the Python tests, skill validation, fixture validation, reference checks, and `git diff --check`-equivalent whitespace checks without credentials.
- [ ] Run the complete CI command sequence locally; expect exit code 0 for every command.
- [ ] Commit with `ci: add repository verification workflow`.

### Task 7: GREEN forward tests and release

**Files:**
- Create: `tests/evaluations/forward.md`
- Modify: `SKILL.md` or relevant references only for observed scenario gaps.
- Modify: `TASKS.md`
- Modify: `WORKLOG.md`

- [ ] Dispatch fresh agents with the completed Skill for the same three scenarios and save their outputs under `tests/evaluations/forward/`.
- [ ] Score observable invariants, compare with baseline, and record the results in `tests/evaluations/forward.md`.
- [ ] Fix only demonstrated gaps, rerun affected scenarios, then rerun the entire local verification suite.
- [ ] Dispatch an independent spec-compliance review followed by a code-quality review; resolve every critical or important finding and re-review.
- [ ] Create the public GitHub repository `BreezeLife/rokid-aiui-agent-skill`, add it as `origin`, push `main`, and verify the remote default branch and files through the GitHub API.
- [ ] Confirm that the public install URL resolves, update `TASKS.md` and `WORKLOG.md`, and report the repository URL plus verification evidence.
