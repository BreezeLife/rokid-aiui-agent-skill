# Focus Timer Agent Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Deliver a Japanese stable-AIUI-0.17 focus timer as a complete Studio-importable Page project with deterministic timer tests and recorded AIX evidence.

**Architecture:** Add one single-file Page project modeled on `examples/next-step-agent`. Execute its real Page definition in Node with a fake clock and fake interval registry so elapsed time, transitions, duplicate actions, and lifecycle cleanup are verified without wall-clock waits.

**Tech Stack:** AIUI 0.17 `.ink`, JavaScript, Python `unittest`, Node.js 24, repository validator, `@yodaos-pkg/aix-cli@0.8.2`.

---

### Task 1: Capture the import, UI, and behavior contract

**Files:**
- Create: `tests/test_focus_timer_agent_contract.py`

- [ ] Write contract assertions for the four-file Page-only import root, `schema.data`, Japanese Agent/UI copy, both target media queries, five action bindings, and focus handlers.
- [ ] Add a Node harness that replaces `Date.now`, `setInterval`, and `clearInterval`, mounts the real Page object, and emits snapshots for input boundaries, transitions, duplicate actions, pause/continue, completion, hide/show, and unload.
- [ ] Run `python3 -m unittest tests.test_focus_timer_agent_contract -v`; expect failure because `examples/focus-timer-agent/` does not exist.

### Task 2: Implement the minimal Japanese Page project

**Files:**
- Create: `examples/focus-timer-agent/AGENTS.md`
- Create: `examples/focus-timer-agent/app.js`
- Create: `examples/focus-timer-agent/app.json`
- Create: `examples/focus-timer-agent/pages/index/index.ink`

- [ ] Define Japanese extraction instructions and explicit non-goals in `AGENTS.md`.
- [ ] Declare only `pages/index/index` in `app.json` and keep `app.js` dependency-free.
- [ ] Implement validation, absolute-deadline state, derived display/progress, guarded action handlers, per-action focus, and lifecycle cleanup in the Page.
- [ ] Implement `_current` compact and `_blank` complete black/green layouts, with every button using `bindtap`, `bindfocus`, and `bindblur`.
- [ ] Run the focused contract test until GREEN, then run strict validation.

### Task 3: Add repository verification coverage

**Files:**
- Modify: `.github/workflows/ci.yml`
- Modify: `README.md`

- [ ] Add the focus timer to strict validation, AIX pack/list smoke coverage, and a non-empty static preview gate containing `pages/index/index.ink`.
- [ ] Document local verification, scope, limitations, and GitHub Studio import coordinates.
- [ ] Run the focused test and complete unit suite after the integration edits.

### Task 4: Capture fresh local evidence and continuity

**Files:**
- Modify: `MEMORY.md`
- Modify: `TASKS.md`
- Modify: `WORKLOG.md`

- [ ] Run `aix --help` from the lockfile-resolved binary and confirm `preview`, `pack`, and `list` are advertised.
- [ ] Run strict validation, static preview, pack, and list against the exact focus-timer import directory; record command results, artifact size, and listing.
- [ ] Inspect the generated preview in a browser and report only what that layer proves.
- [ ] Run the full repository verification flow fresh, update continuity files with exact evidence, and keep Studio login/import plus physical-glasses checks as manual gates.

