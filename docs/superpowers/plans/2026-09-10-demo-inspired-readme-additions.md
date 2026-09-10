# Demo-inspired README additions implementation plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a concise capability overview, Focus Timer operation map, and repository map to the prompt-first README.

**Architecture:** Extend only the root landing page and its semantic contract test. Borrow the external demo README's scannable presentation patterns while keeping all product claims bound to this repository and routing advanced audit detail to existing guides.

**Tech Stack:** Markdown, Python `unittest`, existing AIUI validators, pinned AIX CLI, GitHub Actions

---

### Task 1: Define the new README contract

**Files:**

- Modify: `tests/test_multilingual_usage_docs.py`

- [x] **Step 1: Add the new headings to reader-task order**

Require `## 这个 Skill 能做什么` after the opener and `## 仓库内容` before `## 深入指南`.

- [x] **Step 2: Add semantic capability checks**

Within the capability section, require creation of a complete AIUI project, modification of an existing project, AIUI-specific review or debugging, and verified Studio handoff without requiring exact paragraph wording.

- [x] **Step 3: Add Focus Timer operation checks**

Require these stable mappings inside the existing timer section:

```text
未开始 -> 开始
进行中 -> 暂停
已暂停 -> 继续
已完成 -> 重新开始
```

Keep the existing Studio, Rokid Glasses, voice, and `BLOCKED` checks. Require nod and touchpad to stay inside the same device-verification boundary.

- [x] **Step 4: Add repository-map link checks**

Require links to `SKILL.md`, `references/`, `scripts/`, `studio-importable-minimal/`, `focus-timer-agent/`, and all three localized guides. Require prose that distinguishes the minimal skeleton from the sole bundled product Agent.

- [x] **Step 5: Run the focused test and observe RED**

Run:

```bash
python3 -m unittest tests.test_multilingual_usage_docs.MultilingualUsageDocsTests.test_readme_is_a_prompt_first_quickstart -v
```

Expected: FAIL because the current README lacks the new sections and operation map.

### Task 2: Add the README content

**Files:**

- Modify: `README.md`

- [x] **Step 1: Add the capability overview**

Use four concise bullets for creating, modifying, reviewing/debugging, and validating/handoff. Each bullet names the developer outcome rather than listing APIs.

- [x] **Step 2: Add the Focus Timer operation table**

Use a two-column state-to-primary-action table. State that source and local callback tests cover the mapping, while nod, touchpad, voice, Studio, and physical-device behavior still require their matching evidence.

- [x] **Step 3: Add the repository map**

Use a compact path-and-purpose table. Keep Focus Timer as the only product Agent and describe the minimal project as a skeleton.

- [x] **Step 4: Run the focused documentation and timer tests**

Run:

```bash
python3 -m unittest tests.test_multilingual_usage_docs tests.test_focus_timer_agent_contract -v
```

Expected: all tests pass.

### Task 3: Review and verify

**Files:**

- Modify: `MEMORY.md`
- Modify: `WORKLOG.md`

- [x] **Step 1: Review against the current writing guidelines**

Check the opening summary, task-shaped headings, active voice, introduced lists, labeled code blocks, local links, paragraph length, and removal of unsupported external claims.

- [x] **Step 2: Request independent scope and accuracy review**

Reject copied private details, unsupported hardware/cloud claims, new product Agents, weakened output contracts, or false Studio/device conclusions.

- [x] **Step 3: Run the complete local gate**

Run the complete unit suite with the repository-approved Node.js runtime. Then run Skill validation, reference validation, four strict import-root validations, the release-ready audit black box, three AIX pack/list flows, the Focus Timer preview, and `git diff --check`.

Expected: every local gate passes.

### Task 4: Publish and verify

**Files:**

- Modify: `TASKS.md`
- Modify: `WORKLOG.md`

- [x] **Step 1: Commit the implementation**

Commit the README, test, plan, and continuity changes without rewriting published history.

- [x] **Step 2: Push to public `main`**

Confirm that public `main` still matches the local base, then fast-forward it over SSH.

- [x] **Step 3: Verify the public result**

Wait for both GitHub Actions jobs. Read the published README and Focus Timer path through the GitHub API, and confirm the public commit matches local `HEAD`.
