# Next Step Agent Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build and publish a stable AIUI 0.17 Next Step Agent as a complete AIUI Studio-importable source project.

**Architecture:** Add one Page-only project at `examples/next-step-agent/`. Its `schema.data` receives `goal` and `nextStep`, a local state machine owns the ready/active/done loop, and target media queries change density without changing business state. Python contract tests execute the real `<script setup>` block through Node, while existing validation and published AIX tooling prove project and artifact integrity.

**Tech Stack:** AIUI 0.17 `.ink`, JavaScript, Python 3 standard-library `unittest`, Node.js 24 test harness, published `@yodaos-pkg/aix-cli@0.8.2`, GitHub Actions.

---

### Task 1: Correct the Page schema reference

**Files:**
- Modify: `tests/test_skill_structure.py`
- Modify: `skills/rokid-aiui-agent/references/ink-authoring.md`

- [ ] **Step 1: Write the failing reference regression**

Add `import json` and this test to `SkillStructureTests`:

```python
def test_page_definition_example_uses_schema_data_envelope(self):
    reference = (SKILL_ROOT / "references" / "ink-authoring.md").read_text(
        encoding="utf-8"
    )
    match = re.search(
        r"```html\s*<script def>\s*(\{.*?\})\s*</script>",
        reference,
        flags=re.DOTALL,
    )
    self.assertIsNotNone(match)
    definition = json.loads(match.group(1))
    schema = definition["schema"]
    self.assertNotIn("type", schema)
    self.assertNotIn("properties", schema)
    self.assertIn("data", schema)
    self.assertEqual(schema["data"]["type"], "object")
    self.assertIn("properties", schema["data"])
```

- [ ] **Step 2: Run the regression and verify RED**

Run:

```bash
python3 -m unittest \
  tests.test_skill_structure.SkillStructureTests.test_page_definition_example_uses_schema_data_envelope \
  -v
```

Expected: `FAIL` because the current example places `type` and `properties` directly under `schema`.

- [ ] **Step 3: Apply the official `schema.data` shape**

Replace the Page definition in `ink-authoring.md` with:

```html
<script def>
{
  "description": "Show the current task and allow confirmation",
  "schema": {
    "data": {
      "type": "object",
      "properties": {
        "title": { "type": "string" }
      }
    }
  }
}
</script>
```

- [ ] **Step 4: Verify GREEN and reference integrity**

Run:

```bash
python3 -m unittest \
  tests.test_skill_structure.SkillStructureTests.test_page_definition_example_uses_schema_data_envelope \
  -v
python3 skills/rokid-aiui-agent/scripts/verify_references.py .
```

Expected: one passing test and `OK: verified Markdown references`.

- [ ] **Step 5: Commit the isolated correction**

```bash
git add tests/test_skill_structure.py \
  skills/rokid-aiui-agent/references/ink-authoring.md
git commit -m "fix: use AIUI schema data envelope"
```

### Task 2: Capture the Next Step Agent contract in failing tests

**Files:**
- Create: `tests/test_next_step_agent_contract.py`

- [ ] **Step 1: Create the contract test file before the project exists**

Create `tests/test_next_step_agent_contract.py` with:

```python
from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EXAMPLE = ROOT / "examples" / "next-step-agent"
INK = EXAMPLE / "pages" / "index" / "index.ink"
VALIDATOR = ROOT / "skills" / "rokid-aiui-agent" / "scripts" / "validate_aiui_project.py"


def read_example(relative: str) -> str:
    path = EXAMPLE / relative
    if not path.is_file():
        raise AssertionError(f"missing Next Step Agent file: {relative}")
    return path.read_text(encoding="utf-8")


def extract_block(source: str, pattern: str, label: str) -> str:
    match = re.search(pattern, source, flags=re.DOTALL)
    if match is None:
        raise AssertionError(f"missing {label} block")
    return match.group(1).strip()


class NextStepAgentContractTests(unittest.TestCase):
    def test_import_root_manifest_and_route(self) -> None:
        self.assertTrue(EXAMPLE.is_dir(), f"missing import root: {EXAMPLE}")
        expected = {
            "AGENTS.md",
            "app.js",
            "app.json",
            "pages/index/index.ink",
        }
        actual = {
            path.relative_to(EXAMPLE).as_posix()
            for path in EXAMPLE.rglob("*")
            if path.is_file()
        }
        self.assertEqual(actual, expected)
        manifest = json.loads(read_example("app.json"))
        self.assertEqual(manifest["pages"], ["pages/index/index"])
        self.assertNotIn("widgets", manifest)
        self.assertNotIn("agentWorkers", manifest)

        result = subprocess.run(
            [
                sys.executable,
                str(VALIDATOR),
                str(EXAMPLE),
                "--target-version",
                "0.17.0",
                "--strict",
            ],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(result.stdout, "")
        self.assertEqual(result.stderr, "")

    def test_agents_declares_behavior_and_boundaries(self) -> None:
        agents = read_example("AGENTS.md")
        for fragment in (
            "# Agent: Next Step Agent",
            "## System Prompts",
            "## Capabilities",
            "## Configuration",
            "## Dependencies",
            "`goal`",
            "`nextStep`",
            "`empty`",
            "`error`",
            "`ready`",
            "`active`",
            "`done`",
            "`_current`",
            "`_blank`",
            "不使用网络、设备权限、持久化、计时器或后台任务",
        ):
            self.assertIn(fragment, agents)

    def test_ink_schema_and_bound_handlers(self) -> None:
        ink = read_example("pages/index/index.ink")
        self.assertEqual(len(re.findall(r"<script def>", ink)), 1)
        self.assertEqual(len(re.findall(r"<script setup>", ink)), 1)
        self.assertEqual(len(re.findall(r"<page\b", ink)), 1)
        self.assertEqual(len(re.findall(r"<style>", ink)), 1)
        self.assertNotIn("<widget", ink)

        definition = json.loads(
            extract_block(ink, r"<script def>\s*(.*?)\s*</script>", "definition")
        )
        schema = definition["schema"]
        self.assertEqual(set(schema), {"data"})
        data_schema = schema["data"]
        self.assertEqual(data_schema["type"], "object")
        self.assertEqual(set(data_schema["required"]), {"goal", "nextStep"})
        for name in ("goal", "nextStep"):
            self.assertEqual(data_schema["properties"][name]["type"], "string")
            self.assertEqual(data_schema["properties"][name]["minLength"], 1)

        setup = extract_block(
            ink, r"<script setup>\s*(.*?)\s*</script>", "setup"
        )
        page = extract_block(ink, r"<page\b[^>]*>\s*(.*?)\s*</page>", "page")
        handlers = set(re.findall(r'bindtap="([A-Za-z_$][\w$]*)"', page))
        self.assertEqual(handlers, {"startTask", "completeTask", "restartTask"})
        for handler in handlers:
            self.assertRegex(setup, rf"(?m)^\s{{2}}{handler}\(\)\s*\{{")
        for forbidden in (
            "fetch(",
            "wx.request",
            "setTimeout(",
            "setInterval(",
            "getStorage",
            "setStorage",
            "onKeyUp",
            "preventDefault",
        ):
            self.assertNotIn(forbidden, setup)

    def test_target_specific_design_hints(self) -> None:
        ink = read_example("pages/index/index.ink")
        setup = extract_block(
            ink, r"<script setup>\s*(.*?)\s*</script>", "setup"
        )
        style = extract_block(ink, r"<style>\s*(.*?)\s*</style>", "style")
        self.assertIn("@media (target: _current)", style)
        self.assertIn("@media (target: _blank)", style)
        current = style.split("@media (target: _current)", 1)[1].split(
            "@media (target: _blank)", 1
        )[0]
        blank = style.split("@media (target: _blank)", 1)[1]
        self.assertIn(".expanded-only", current)
        self.assertIn("display: none", current)
        self.assertIn(".expanded-only", blank)
        self.assertIn("display: flex", blank)
        self.assertIn("border: 1px solid", style)
        self.assertIn("border-radius: 4px", style)
        self.assertIn("border-radius: 6px", style)
        for forbidden in ("_current", "_blank", "onTargetChanged"):
            self.assertNotIn(forbidden, setup)

    def test_real_page_script_state_machine(self) -> None:
        node = shutil.which("node")
        self.assertIsNotNone(node, "Node.js is required for Page behavior tests")
        ink = read_example("pages/index/index.ink")
        setup = extract_block(
            ink, r"<script setup>\s*(.*?)\s*</script>", "setup"
        )
        harness = """
import definition from './page.mjs';

function mount() {
  const instance = {
    data: JSON.parse(JSON.stringify(definition.data)),
    setData(patch) { Object.assign(this.data, patch); }
  };
  for (const [name, value] of Object.entries(definition)) {
    if (typeof value === 'function') instance[name] = value;
  }
  return instance;
}

const valid = mount();
valid.onLoad({ goal: '  完成发布说明  ', nextStep: '  列出三个主要变化  ' });
const sequence = [valid.data.state];
valid.startTask(); sequence.push(valid.data.state);
valid.completeTask(); sequence.push(valid.data.state);
valid.restartTask(); sequence.push(valid.data.state);

const empty = mount(); empty.onLoad(null); empty.startTask();
const partial = mount(); partial.onLoad({ goal: '目标' });
const invalid = mount(); invalid.onLoad({ goal: '目标', nextStep: 7 });
const invalidRoot = mount(); invalidRoot.onLoad('bad');

console.log(JSON.stringify({
  sequence,
  trimmed: [valid.data.goal, valid.data.nextStep],
  empty: empty.data.state,
  partial: partial.data.state,
  invalid: invalid.data.state,
  invalidRoot: invalidRoot.data.state
}));
"""
        with tempfile.TemporaryDirectory(prefix="next-step-agent-") as directory:
            temp = Path(directory)
            (temp / "page.mjs").write_text(setup + "\n", encoding="utf-8")
            (temp / "harness.mjs").write_text(harness, encoding="utf-8")
            result = subprocess.run(
                [node, str(temp / "harness.mjs")],
                cwd=temp,
                text=True,
                capture_output=True,
                check=False,
            )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["sequence"], ["ready", "active", "done", "ready"])
        self.assertEqual(payload["trimmed"], ["完成发布说明", "列出三个主要变化"])
        self.assertEqual(payload["empty"], "empty")
        self.assertEqual(payload["partial"], "empty")
        self.assertEqual(payload["invalid"], "error")
        self.assertEqual(payload["invalidRoot"], "error")


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the new tests and verify RED**

Run:

```bash
python3 -m unittest tests.test_next_step_agent_contract -v
```

Expected: five assertion failures that identify the missing `examples/next-step-agent/` import root or files. No syntax or import error is acceptable.

- [ ] **Step 3: Commit the executable RED contract**

```bash
git add tests/test_next_step_agent_contract.py
git commit -m "test: define Next Step Agent contract"
```

### Task 3: Implement the minimal importable Agent

**Files:**
- Create: `examples/next-step-agent/AGENTS.md`
- Create: `examples/next-step-agent/app.json`
- Create: `examples/next-step-agent/app.js`
- Create: `examples/next-step-agent/pages/index/index.ink`

- [ ] **Step 1: Add the Agent instructions**

Create `AGENTS.md`:

```markdown
# Agent: Next Step Agent

- **Version**: 1.0.0
- **Description**: 把用户目标整理成一个可以立即开始的下一步
- **Author**: BreezeLife

## System Prompts

你是“下一步”行动助手。保留用户真正想达到的结果，再把它收敛成一个现在就能开始、一次只做一件事的动作。

- 将原始目标写入 `goal`，不要替用户改变最终目的。
- 将唯一的具体动作写入 `nextStep`，使用动词开头并控制在一句话内。
- `goal` 最多 120 个字符，`nextStep` 最多 48 个字符；长度按 Unicode 码点计算。
- 信息不足时先在对话中补齐，不要编造截止时间、资源或完成状态。
- 页面只能表示当前会话中的本地状态，不要承诺提醒、保存、同步或后台执行。

## Capabilities

- 接收 `goal` 与 `nextStep` 两个字符串并呈现本地 Page 状态。
- 支持 `empty`、`error`、`ready`、`active`、`done` 五种状态。
- 支持开始、完成和重新开始当前动作。
- `_current` 使用精简密度，`_blank` 显示完整目标；切换 target 不改变任务状态。
- 不使用网络、设备权限、持久化、计时器或后台任务。

## Configuration

无配置项。

## Dependencies

无外部服务依赖。
```

- [ ] **Step 2: Add the root manifest and application entry**

Create `app.json`:

```json
{
  "pages": ["pages/index/index"],
  "window": {
    "navigationBarTitleText": "下一步"
  }
}
```

Create `app.js`:

```javascript
export default {};
```

- [ ] **Step 3: Add the complete Page**

Create `pages/index/index.ink`:

```html
<script def>
{
  "navigationBarTitleText": "下一步",
  "description": "把用户目标收敛为一个可以立即开始的下一步，并展示当前会话内的行动状态。",
  "schema": {
    "data": {
      "type": "object",
      "properties": {
        "goal": {
          "type": "string",
          "minLength": 1,
          "maxLength": 120,
          "description": "保留用户真实意图的目标。"
        },
        "nextStep": {
          "type": "string",
          "minLength": 1,
          "maxLength": 48,
          "description": "一个现在可以开始、以动词开头的具体动作。"
        }
      },
      "required": ["goal", "nextStep"]
    }
  }
}
</script>

<script setup>
const MAX_GOAL_LENGTH = 120;
const MAX_NEXT_STEP_LENGTH = 48;

function unicodeLength(value) {
  return Array.from(value).length;
}

const STATE_CONTENT = {
  empty: {
    statusLabel: '等待目标',
    statusTitle: '还没有下一步',
    statusDetail: '回到对话，告诉我你现在想推进什么。',
    primaryText: '先说出一个你想推进的目标'
  },
  error: {
    statusLabel: '需要重试',
    statusTitle: '暂时无法读取行动内容',
    statusDetail: '回到对话重新生成下一步。',
    primaryText: '行动内容格式不正确'
  },
  ready: {
    statusLabel: '准备开始',
    statusTitle: '只做这一件事',
    statusDetail: '开始后保持专注，完成时在这里确认。'
  },
  active: {
    statusLabel: '正在推进',
    statusTitle: '保持在下一步',
    statusDetail: '完成这个动作后再决定下一件事。'
  },
  done: {
    statusLabel: '已经完成',
    statusTitle: '这一步完成了',
    statusDetail: '回到对话告诉我下一件事，或重新开始这一动作。'
  }
};

function buildViewState(state, nextStep) {
  const content = STATE_CONTENT[state] || STATE_CONTENT.error;
  const actionable = state === 'ready' || state === 'active' || state === 'done';
  return {
    state,
    statusLabel: content.statusLabel,
    statusTitle: content.statusTitle,
    statusDetail: content.statusDetail,
    primaryText: actionable ? nextStep : content.primaryText,
    actionFocused: false
  };
}

function normalizeInput(query) {
  if (query === undefined || query === null) {
    return { state: 'empty', goal: '', nextStep: '' };
  }
  if (typeof query !== 'object' || Array.isArray(query)) {
    return { state: 'error', goal: '', nextStep: '' };
  }
  if (
    (query.goal !== undefined && typeof query.goal !== 'string') ||
    (query.nextStep !== undefined && typeof query.nextStep !== 'string')
  ) {
    return { state: 'error', goal: '', nextStep: '' };
  }
  const rawGoal = typeof query.goal === 'string' ? query.goal : '';
  const rawNextStep =
    typeof query.nextStep === 'string' ? query.nextStep : '';
  if (
    unicodeLength(rawGoal) > MAX_GOAL_LENGTH ||
    unicodeLength(rawNextStep) > MAX_NEXT_STEP_LENGTH
  ) {
    return { state: 'error', goal: '', nextStep: '' };
  }
  const goal = rawGoal.trim();
  const nextStep = rawNextStep.trim();
  if (!goal || !nextStep) {
    return { state: 'empty', goal: '', nextStep: '' };
  }
  return {
    state: 'ready',
    goal,
    nextStep
  };
}

export default {
  data: {
    state: 'empty',
    goal: '',
    nextStep: '',
    statusLabel: STATE_CONTENT.empty.statusLabel,
    statusTitle: STATE_CONTENT.empty.statusTitle,
    statusDetail: STATE_CONTENT.empty.statusDetail,
    primaryText: STATE_CONTENT.empty.primaryText,
    actionFocused: false
  },

  onLoad(query) {
    const input = normalizeInput(query);
    this.setData({
      goal: input.goal,
      nextStep: input.nextStep,
      ...buildViewState(input.state, input.nextStep)
    });
  },

  onActionFocus() {
    this.setData({ actionFocused: true });
  },

  onActionBlur() {
    this.setData({ actionFocused: false });
  },

  startTask() {
    if (this.data.state !== 'ready') return;
    this.setData(buildViewState('active', this.data.nextStep));
  },

  completeTask() {
    if (this.data.state !== 'active') return;
    this.setData(buildViewState('done', this.data.nextStep));
  },

  restartTask() {
    if (this.data.state !== 'done') return;
    this.setData(buildViewState('ready', this.data.nextStep));
  }
};
</script>

<page class="page-shell state-{{state}}">
  <view class="surface">
    <view class="topline">
      <text class="eyebrow">NEXT STEP</text>
      <text class="state-label">{{statusLabel}}</text>
    </view>
    <view class="divider"></view>
    <scroll-view class="content" scroll-y="true">
      <text class="status-title">{{statusTitle}}</text>
      <text class="primary-text">{{primaryText}}</text>
      <view class="goal-group expanded-only">
        <text class="section-label">目标</text>
        <text class="goal-text">{{goal}}</text>
      </view>
      <text class="guidance expanded-only">{{statusDetail}}</text>
    </scroll-view>
    <view class="actions">
      <button class="action action-start action-focused-{{actionFocused}}" bindtap="startTask" bindfocus="onActionFocus" bindblur="onActionBlur">开始行动</button>
      <button class="action action-complete action-focused-{{actionFocused}}" bindtap="completeTask" bindfocus="onActionFocus" bindblur="onActionBlur">标记完成</button>
      <button class="action action-restart action-focused-{{actionFocused}}" bindtap="restartTask" bindfocus="onActionFocus" bindblur="onActionBlur">重新开始</button>
    </view>
  </view>
</page>

<style>
.page-shell {
  width: 100%;
  height: 100%;
  padding: 18px;
  box-sizing: border-box;
  color: #40ff5e;
  background-color: rgba(0, 0, 0, 0.82);
}

.surface {
  display: flex;
  width: 100%;
  height: 100%;
  min-height: 0;
  flex-direction: column;
  padding: 16px;
  box-sizing: border-box;
  border: 1px solid rgba(64, 255, 94, 0.32);
  border-radius: 6px;
  overflow: hidden;
  opacity: 0.78;
}

.surface:host-focus { opacity: 1; }

.topline {
  display: flex;
  flex-direction: row;
  justify-content: space-between;
  align-items: center;
  flex-shrink: 0;
}

.eyebrow,
.section-label {
  font-size: 11px;
  line-height: 14px;
  color: rgba(64, 255, 94, 0.66);
}

.state-label {
  padding: 3px 6px;
  border: 1px solid rgba(64, 255, 94, 0.24);
  border-radius: 4px;
  font-size: 11px;
  line-height: 14px;
}

.divider {
  flex-shrink: 0;
  height: 1px;
  margin-top: 10px;
  background-color: rgba(64, 255, 94, 0.24);
}

.content,
.goal-group {
  display: flex;
  flex-direction: column;
}

.content {
  flex: 1 1 auto;
  min-height: 0;
  margin-top: 14px;
}
.status-title { font-size: 16px; line-height: 20px; }

.primary-text {
  margin-top: 8px;
  font-size: 22px;
  line-height: 28px;
  color: #b8ffc3;
}

.goal-group {
  margin-top: 18px;
  padding: 10px;
  border: 1px solid rgba(64, 255, 94, 0.18);
  border-radius: 6px;
  background-color: rgba(64, 255, 94, 0.06);
}

.goal-text {
  margin-top: 6px;
  font-size: 13px;
  line-height: 18px;
  color: rgba(184, 255, 195, 0.78);
}

.guidance {
  margin-top: 6px;
  font-size: 13px;
  line-height: 18px;
  color: rgba(184, 255, 195, 0.78);
}

.actions {
  display: flex;
  flex-direction: row;
  justify-content: space-between;
  align-items: center;
  flex-shrink: 0;
  margin-top: auto;
  padding-top: 16px;
}

.action {
  display: none;
  min-width: 112px;
  padding: 7px 12px;
  border: 1px solid rgba(64, 255, 94, 0.54);
  border-radius: 4px;
  box-sizing: border-box;
  color: #40ff5e;
  background-color: rgba(64, 255, 94, 0.08);
}

.action-focused-true {
  border: 2px solid #40ff5e;
  background-color: rgba(64, 255, 94, 0.12);
}

.state-ready .action-start,
.state-active .action-complete,
.state-done .action-restart { display: flex; }

.state-empty .goal-group,
.state-error .goal-group { display: none; }

@media (target: _current) {
  .page-shell { padding: 10px; }
  .surface { min-height: 0; padding: 12px; }
  .expanded-only { display: none; }
  .primary-text {
    max-height: 46px;
    font-size: 18px;
    line-height: 23px;
    overflow: hidden;
  }
}

@media (target: _blank) {
  .expanded-only { display: flex; }
}
</style>
```

- [ ] **Step 4: Run the contract and full unit suite**

Run:

```bash
python3 -m unittest tests.test_next_step_agent_contract -v
python3 -m unittest discover -s tests -p "test_*.py" -v
```

Expected: the six new tests pass and the complete suite reports zero failures.

- [ ] **Step 5: Commit the working Agent**

```bash
git add examples/next-step-agent
git commit -m "feat: add Next Step AIUI agent"
```

### Task 4: Add CI package and preview gates

**Files:**
- Modify: `tests/test_next_step_agent_contract.py`
- Modify: `.github/workflows/ci.yml`
- Modify: `.gitignore`
- Modify: `README.md`
- Modify: `skills/rokid-aiui-agent/scripts/verify_references.py`
- Modify: `tests/test_verify_references.py`
- Create: `package.json`
- Create: `package-lock.json`
- Create: `requirements-dev.txt`

- [ ] **Step 1: Add a failing CI contract test**

Replace the original whole-file fragment checks with a structured contract in
`NextStepAgentContractTests`. Load the workflow with `yaml.safe_load`, select
`validate` and `aix-smoke` by job key, and select each step by its exact `name`.
Assert `needs`, the pinned `uses` values, exact `with` values, step `env`,
`shell`, and normalized `run` lines. Require both jobs and every verification
step to omit `if` and `continue-on-error`, and assert the dependency, unit,
strict-validation, reference, package, and preview order. Parse
`requirements-dev.txt` and require `PyYAML==6.0.3`; verify the README installs
that file before running tests and CI consumes the same source. Also parse
`package.json` and `package-lock.json` as JSON, require the private flag and
exact AIX `0.8.2` dev dependency without rejecting unrelated metadata,
lockfile version 3, an exact locked AIX version, and SHA-512 integrity for every
locked registry package.

- [ ] **Step 2: Run the method and verify RED**

Run:

```bash
python3 -m unittest \
  tests.test_next_step_agent_contract.NextStepAgentContractTests.test_ci_validates_packages_and_previews_example \
  -v
```

Expected: `FAIL` because the required Python dependency file and documented
installation are absent, CI still embeds PyYAML as a second version source, the
package files do not exist, Node is only pinned to the major version, the AIX
install step is absent, and AIX still resolves dynamically.

- [ ] **Step 3: Add deterministic CI coverage**

Add to `Validate importable AIUI projects strictly`:

```yaml
python skills/rokid-aiui-agent/scripts/validate_aiui_project.py examples/next-step-agent --target-version 0.17.0 --strict
```

Create one pinned Python development dependency source:

```text
PyYAML==6.0.3
```

Use it in CI and at the start of the README local verification block:

```yaml
- name: Install validator dependency
  run: 'python -m pip install --only-binary=:all: -r requirements-dev.txt'
```

```bash
python3 -m pip install --only-binary=:all: -r requirements-dev.txt
```

Create the minimal private package manifest and generate its lockfile with Node
`24.19.0` and npm:

```json
{
  "name": "rokid-aiui-agent-skill",
  "private": true,
  "devDependencies": {
    "@yodaos-pkg/aix-cli": "0.8.2"
  }
}
```

```bash
npm install --package-lock-only --ignore-scripts --no-audit --no-fund
```

Ignore `node_modules/`. Add a RED/GREEN reference-verifier regression containing
a broken Markdown link under `node_modules/vendor/README.md`, then prune
`.git`, `.worktrees`, and `node_modules` directories while walking the repository. This keeps
the documented validation sequence repeatable when dependencies are already
installed. Pin both jobs to the same exact Node release:

```yaml
- name: Set up Node.js
  uses: actions/setup-node@820762786026740c76f36085b0efc47a31fe5020 # v7.0.0
  with:
    node-version: "24.19.0"
```

Install the lockfile before any AIX command:

```yaml
- name: Install locked AIX CLI
  run: npm ci --ignore-scripts --no-audit --no-fund
```

Configure `Pack and inspect stable AIUI projects` to use the workspace-absolute
locked executable, and include the generated example:

```yaml
- name: Pack and inspect stable AIUI projects
  env:
    AIX_BIN: ${{ github.workspace }}/node_modules/.bin/aix
  run: |
    bash skills/rokid-aiui-agent/scripts/smoke_aix.sh tests/fixtures/valid-minimal
    bash skills/rokid-aiui-agent/scripts/smoke_aix.sh skills/rokid-aiui-agent/assets/studio-importable-minimal
    bash skills/rokid-aiui-agent/scripts/smoke_aix.sh examples/next-step-agent
```

Add this step to the `aix-smoke` job:

```yaml
- name: Generate the Next Step Agent static preview
  shell: bash
  env:
    AIX_BIN: ${{ github.workspace }}/node_modules/.bin/aix
  run: |
    set -euo pipefail
    preview_html="$RUNNER_TEMP/next-step-agent-preview.html"
    "$AIX_BIN" --help | grep -Eq '(^|[[:space:]])preview([[:space:]<]|$)'
    "$AIX_BIN" preview examples/next-step-agent --html-out "$preview_html"
    test -s "$preview_html"
    grep -Fq 'pages/index/index.ink' "$preview_html"
```

The explicit Bash shell and `pipefail` make a failed `aix --help` capability
probe fail the job instead of being hidden by a successful `grep` process.

- [ ] **Step 4: Verify CI contract and local AIX commands**

Run:

```bash
python3 -m pip install --only-binary=:all: -r requirements-dev.txt
python3 -m unittest \
  tests.test_next_step_agent_contract.NextStepAgentContractTests.test_ci_validates_packages_and_previews_example \
  -v
python3 skills/rokid-aiui-agent/scripts/validate_aiui_project.py \
  examples/next-step-agent --target-version 0.17.0 --strict
npm ci --ignore-scripts --no-audit --no-fund
python3 skills/rokid-aiui-agent/scripts/verify_references.py .
AIX_BIN="$PWD/node_modules/.bin/aix" \
  bash skills/rokid-aiui-agent/scripts/smoke_aix.sh examples/next-step-agent
```

Generate the preview with the same locked executable into a fresh temporary
path, then require a non-empty file and the declared route string. Expected:
every command exits 0.

- [ ] **Step 5: Commit the CI gates**

```bash
git add .github/workflows/ci.yml tests/test_next_step_agent_contract.py \
  .gitignore README.md package.json package-lock.json requirements-dev.txt \
  skills/rokid-aiui-agent/scripts/verify_references.py \
  tests/test_verify_references.py \
  docs/superpowers/plans/2026-09-08-next-step-agent.md
git commit -m "ci: enforce blocking verification gates"
```

### Task 5: Publish exact usage and continuity records

**Files:**
- Modify: `README.md`
- Modify: `PROJECT.md`
- Modify: `MEMORY.md`
- Modify: `TASKS.md`
- Modify: `WORKLOG.md`

- [ ] **Step 1: Document the project and Studio coordinates**

Add a README section that states:

````markdown
## 使用 Skill 生成的 Agent

`examples/next-step-agent` 是使用本 Skill 生成的完整 AIUI `0.17.0` 项目。它把一个目标收敛成一个立即可执行的下一步，并在当前 Page 内支持开始、完成和重新开始。目录创建后，README 将该代码路径改为可点击的相对链接。

AIUI Studio GitHub 导入坐标：

```text
Repository: https://github.com/BreezeLife/rokid-aiui-agent-skill
Ref: main
Directory: examples/next-step-agent
```

该项目不使用网络、权限、存储、计时器、Widget 或 Agent Worker。自动验证不能替代账号侧 Studio 导入和 Rokid Glasses 真机验收。
````

- [ ] **Step 2: Record durable architecture and evidence boundaries**

Add these durable lines after their matching headings:

```markdown
- `examples/next-step-agent/`: first product-shaped project generated with the Skill; a stable-0.17, Page-only Studio import root.
```

```markdown
- 2026-09-08: The first generated product example is `examples/next-step-agent/`. It uses the official `schema.data` Page input envelope, local Page state, no permissions, and target-specific density without target-specific business state.
```

Move completed implementation tasks from `TASKS.md` to Done only after fresh command evidence exists. Append the exact observed test count, AIX archive size/listing, preview byte size, visual observation, pushed commit, and Actions run to `WORKLOG.md`; never prewrite an unexecuted success.

- [ ] **Step 3: Verify documentation and commit**

Run:

```bash
python3 skills/rokid-aiui-agent/scripts/verify_references.py .
git diff --check
```

Expected: reference verification prints `OK` and whitespace checking exits 0.

Commit:

```bash
git add README.md PROJECT.md MEMORY.md TASKS.md WORKLOG.md
git commit -m "docs: publish Next Step Agent workflow"
```

### Task 6: Run final evidence gates and publish

**Files:**
- Modify: `TASKS.md`
- Modify: `WORKLOG.md`

- [ ] **Step 1: Run the complete local verification flow**

Run:

```bash
python3 -m pip install --only-binary=:all: -r requirements-dev.txt
python3 -m unittest discover -s tests -p "test_*.py" -v
python3 skills/rokid-aiui-agent/scripts/validate_aiui_project.py \
  tests/fixtures/valid-minimal --target-version 0.17.0 --strict
python3 skills/rokid-aiui-agent/scripts/validate_aiui_project.py \
  tests/fixtures/valid-widget-worker --target-version 0.18.0 --strict
python3 skills/rokid-aiui-agent/scripts/validate_aiui_project.py \
  skills/rokid-aiui-agent/assets/studio-importable-minimal \
  --target-version 0.17.0 --strict
python3 skills/rokid-aiui-agent/scripts/validate_aiui_project.py \
  examples/next-step-agent --target-version 0.17.0 --strict
python3 skills/rokid-aiui-agent/scripts/verify_references.py .
python3 /Users/weiqi/.codex/skills/.system/skill-creator/scripts/quick_validate.py \
  skills/rokid-aiui-agent
bash -n skills/rokid-aiui-agent/scripts/smoke_aix.sh
ruby -ryaml -e 'ARGV.each { |path| YAML.safe_load(File.read(path)); puts path }' \
  .github/workflows/ci.yml skills/rokid-aiui-agent/agents/openai.yaml
git diff --check
```

Run every stable AIX package gate with the lockfile-resolved release:

```bash
npm ci --ignore-scripts --no-audit --no-fund
AIX_BIN="$PWD/node_modules/.bin/aix"
export AIX_BIN
bash skills/rokid-aiui-agent/scripts/smoke_aix.sh tests/fixtures/valid-minimal
bash skills/rokid-aiui-agent/scripts/smoke_aix.sh \
  skills/rokid-aiui-agent/assets/studio-importable-minimal
bash skills/rokid-aiui-agent/scripts/smoke_aix.sh examples/next-step-agent
```

Generate and inspect the exact static preview artifact:

```bash
set -euo pipefail
preview_dir=$(mktemp -d "${TMPDIR:-/tmp}/next-step-preview.XXXXXX")
preview_html="$preview_dir/next-step-agent.html"
AIX_BIN="$PWD/node_modules/.bin/aix"
"$AIX_BIN" --help | grep -Eq '(^|[[:space:]])preview([[:space:]<]|$)'
"$AIX_BIN" preview \
  examples/next-step-agent --html-out "$preview_html"
test -s "$preview_html"
grep -Fq 'pages/index/index.ink' "$preview_html"
wc -c "$preview_html"
```

Every command must exit 0. The unit runner must report zero failures or errors.

- [ ] **Step 2: Inspect the browser preview**

Serve the exact generated HTML through a local HTTP server. Inspect the default empty state at the rendered preview size, confirm the key text and layout are visible, and exercise the available Page controls if the preview host supplies valid input. Record static generation separately from visual evidence.

- [ ] **Step 3: Complete independent reviews**

Run a spec-compliance review and a code-quality review. Resolve P0/P1 findings with a failing regression first, then repeat the relevant verification.

- [ ] **Step 4: Update the final ledger and commit**

Record exact evidence in `TASKS.md` and `WORKLOG.md`, run `git diff --check`, and commit only those ledger changes:

```bash
git add TASKS.md WORKLOG.md
git commit -m "docs: record Next Step Agent verification"
```

- [ ] **Step 5: Push and wait for GitHub Actions**

```bash
git push origin main
gh run list --repo BreezeLife/rokid-aiui-agent-skill --limit 3
```

Wait for the run at the pushed commit and require both `Validate skill and examples` and `Package importable projects with published AIX` to finish with `success`. Re-read the public files through the GitHub API and report the final repository, ref, Studio subdirectory, local/CI evidence, and the two remaining external manual gates.
