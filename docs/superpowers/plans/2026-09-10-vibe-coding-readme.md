# Vibe Coding README implementation plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the root README with a prompt-first quickstart for Vibe Coding developers while preserving tested AIUI delivery and evidence boundaries.

**Architecture:** Keep the root README as a landing page and short how-to. Route complete validation, audit, and maintainer detail to the existing localized guides and Skill references. Protect the new information hierarchy with focused document-contract tests.

**Tech Stack:** Markdown, Python `unittest`, GitHub Actions, existing AIUI validation and AIX smoke scripts

---

### Task 1: Define the README contract

**Files:**

- Modify: `tests/test_multilingual_usage_docs.py`
- Modify: `tests/test_focus_timer_agent_contract.py`

- [x] **Step 1: Add a failing prompt-first README test**

Assert that the README keeps both install commands, an explicit Chinese `$rokid-aiui-agent` prompt, complete-project language, local and GitHub Studio import guidance, the timer path, AIUI `0.17.0` and `0.18` boundaries, and links to advanced guidance. Assert that headings appear in reader-task order and that low-level trust-schema terms are absent.

- [x] **Step 2: Remove timer implementation details from the README contract**

Keep the Focus Timer path and Studio import coordinate assertions. Stop requiring `Date.now()` or other Page implementation internals in the landing page.

- [x] **Step 3: Run the document tests and confirm RED**

Run:

```bash
python3 -m unittest tests.test_multilingual_usage_docs tests.test_focus_timer_agent_contract -v
```

Expected: the new prompt-first contract fails against the old README.

### Task 2: Rewrite the root README

**Files:**

- Modify: `README.md`

- [x] **Step 1: Replace the technical opening with the quickstart**

Put language links, both install commands, and a copyable Chinese timer prompt before architecture or validation detail.

- [x] **Step 2: Describe outputs and Studio import in plain language**

Show the expected editable project tree. Explain local folder import and GitHub repository, ref, and directory coordinates.

- [x] **Step 3: Keep the timer example concise**

Retain the Focus Timer link, default 10-minute behavior, supported inputs, and exact GitHub import directory. State that it is the only bundled product Agent.

- [x] **Step 4: Route advanced detail out of the main flow**

Summarize automated checks in user language. Link audit mechanics, complete commands, source policy, and localized guides instead of reproducing schemas, signatures, and validator internals.

- [x] **Step 5: Run the focused tests and confirm GREEN**

Run the Task 1 command. Expected: all focused tests pass.

### Task 3: Review writing and project continuity

**Files:**

- Modify: `MEMORY.md`
- Modify: `TASKS.md`
- Modify: `WORKLOG.md`

- [x] **Step 1: Review the README against current writing guidelines**

Check task-based headings, opening summary, active voice, short paragraphs, introduced lists, labeled code blocks, resolved links, and removal of low-level onboarding noise.

- [x] **Step 2: Record the durable README role**

Document that the root README is the prompt-first Vibe Coding landing page, while the three localized guides and routed references own advanced validation detail.

- [x] **Step 3: Run reference and whitespace checks**

Run:

```bash
python3 skills/rokid-aiui-agent/scripts/verify_references.py
git diff --check
```

Expected: both commands pass.

### Task 4: Verify and publish

**Files:**

- Verify: entire repository

- [x] **Step 1: Run the complete test suite**

Run with the repository-approved healthy Node.js runtime on `PATH`:

```bash
python3 -m unittest discover -s tests -v
```

Expected: all tests pass.

- [x] **Step 2: Validate the Skill and import roots**

Run OpenAI Skill validation, reference validation, strict validation for all four CI import roots, and the existing AIX pack/list and Focus Timer preview flows.

- [x] **Step 3: Request an independent final review**

Reject any release-blocking finding, fix it with a regression, and rerun affected gates.

- [ ] **Step 4: Commit and push without rewriting history**

Confirm public `main` has not advanced, push the verified commits, wait for GitHub Actions, and verify the public README and timer paths.
