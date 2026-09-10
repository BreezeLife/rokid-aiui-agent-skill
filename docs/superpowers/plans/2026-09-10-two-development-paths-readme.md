# Two development paths README implementation plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Teach developers how to open an existing AIUI project in Studio or build one with Codex and other Agent Skills-compatible Vibe Coding tools.

**Architecture:** Keep `README.md` as a landing page. Add two distinct `###` route blocks inside the existing `快速开始` section, retain detailed output and Studio sections as single sources of truth, and protect the workflow with semantic Markdown tests.

**Tech Stack:** Markdown, Python `unittest`, existing AIUI validators, pinned AIX CLI, GitHub Actions

---

### Task 1: Define the two-route README contract

**Files:**

- Modify: `tests/test_multilingual_usage_docs.py`

- [x] **Step 1: Parse route subsections**

Add a small helper in `test_readme_is_a_prompt_first_quickstart` that splits the `快速开始` section at `###` headings. Require exactly two route blocks so a summary sentence cannot satisfy both routes.

- [x] **Step 2: Require the Studio route**

Require one route block to contain AIUI Studio, importing or opening an AIUI project, continued editing or development, and a Markdown link to `#导入-aiui-studio`.

- [x] **Step 3: Require the Vibe Coding route**

Require the other route to contain Codex, another Agent Skills-compatible coding tool, the primary and guarded alternative install commands, explicit `$rokid-aiui-agent` invocation, an independent output directory, a complete editable AIUI project, actual validation, and handoff to Studio.

- [x] **Step 4: Require ordered developer actions**

Within the Vibe Coding route, require numbered steps whose semantic order is install Skill, open a separate Agent workspace, invoke the Skill, inspect the delivered project and checks, then import it into AIUI Studio. Do not require exact prose beyond the action families.

- [x] **Step 5: Observe RED**

Run:

```bash
python3 -m unittest tests.test_multilingual_usage_docs.MultilingualUsageDocsTests.test_readme_is_a_prompt_first_quickstart -v
```

Expected: FAIL because the current `快速开始` section has no two route subsections or ordered Codex workflow.

### Task 2: Write the two development paths

**Files:**

- Modify: `README.md`

- [x] **Step 1: Add the route selector**

Open `快速开始` with one sentence that tells developers to choose by starting point. Add `路线 1：在 AIUI Studio 中打开项目` first and `路线 2：用 Codex 等 Vibe Coding 工具开发` second.

- [x] **Step 2: Add the Studio route summary**

Explain that an existing complete project or the bundled Focus Timer can be imported into AIUI Studio and edited there. Link to the existing Studio import and Focus Timer sections instead of repeating their coordinates or claims.

- [x] **Step 3: Turn the existing prompt into a Codex tutorial**

Wrap the existing install commands, output-path replacement instruction, and copyable timer prompt in a five-step numbered workflow. State that Codex is an example and the route also works in other coding tools that support Agent Skills and workspace file access.

- [x] **Step 4: Preserve the evidence boundary**

End the workflow by checking the complete editable source, executed validation, and remaining `BLOCKED` gates before importing the exact output directory into Studio. Do not claim unexecuted Studio, voice, gesture, touchpad, or device success.

- [x] **Step 5: Observe GREEN**

Run:

```bash
python3 -m unittest tests.test_multilingual_usage_docs tests.test_focus_timer_agent_contract -v
```

Expected: all tests pass.

### Task 3: Review and verify

**Files:**

- Modify: `MEMORY.md`
- Modify: `WORKLOG.md`

- [ ] **Step 1: Run two-stage review**

Request a scope/contract review, then a writing-quality review against the current Writing Guidelines. Fix every Critical or Important finding and repeat the matching review.

- [ ] **Step 2: Run the complete local gate**

Run the complete unit suite with the repository-approved Node.js runtime. Then run Skill validation, reference validation, four strict import-root validations, the release-ready audit black box, three AIX pack/list flows, the Focus Timer preview, and full-tree whitespace validation.

Expected: every local gate passes.

### Task 4: Publish and verify

**Files:**

- Modify: `TASKS.md`
- Modify: `WORKLOG.md`

- [ ] **Step 1: Commit the implementation**

Commit the test, README, plan, and continuity changes without rewriting published history.

- [ ] **Step 2: Push to public `main`**

Confirm that remote `main` still matches the local base, then fast-forward the verified commits over SSH.

- [ ] **Step 3: Verify the public result**

Wait for both GitHub Actions jobs, read the published README and Focus Timer import root through the GitHub API, and confirm that public `main` matches local `HEAD`.
