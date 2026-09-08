from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import yaml


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


def extract_media_region(style: str, target: str) -> str:
    header = re.compile(
        rf"@media\s*\(\s*target\s*:\s*{re.escape(target)}\s*\)\s*\{{"
    )
    matches = list(header.finditer(style))
    if len(matches) != 1:
        raise AssertionError(
            f"expected exactly one @media region for {target}, found {len(matches)}"
        )

    opening_brace = matches[0].end() - 1
    depth = 0
    for index in range(opening_brace, len(style)):
        if style[index] == "{":
            depth += 1
        elif style[index] == "}":
            depth -= 1
            if depth == 0:
                return style[opening_brace + 1 : index]
    raise AssertionError(f"unclosed @media region for {target}")


class NextStepAgentContractTests(unittest.TestCase):
    def test_ci_validates_packages_and_previews_example(self) -> None:
        package_path = ROOT / "package.json"
        with self.subTest(contract="package manifest"):
            self.assertTrue(package_path.is_file(), "missing package.json")
            package = json.loads(package_path.read_text(encoding="utf-8"))
            self.assertEqual(package.get("name"), "rokid-aiui-agent-skill")
            self.assertIs(package.get("private"), True)
            self.assertEqual(
                package.get("devDependencies", {}).get(
                    "@yodaos-pkg/aix-cli"
                ),
                "0.8.2",
            )

        requirements_path = ROOT / "requirements-dev.txt"
        with self.subTest(contract="Python development dependencies"):
            self.assertTrue(
                requirements_path.is_file(), "missing requirements-dev.txt"
            )
            requirements = {
                line.strip()
                for line in requirements_path.read_text(
                    encoding="utf-8"
                ).splitlines()
                if line.strip() and not line.lstrip().startswith("#")
            }
            self.assertIn("PyYAML==6.0.3", requirements)

        with self.subTest(contract="documented Python dependency install"):
            readme = (ROOT / "README.md").read_text(encoding="utf-8")
            local_verification = extract_block(
                readme,
                r"(?ms)^## 本地验证\s+(.*?)(?=^## |\Z)",
                "README local verification",
            )
            install_command = (
                "python3 -m pip install --only-binary=:all: "
                "-r requirements-dev.txt"
            )
            self.assertIn(install_command, local_verification)
            self.assertLess(
                local_verification.index(install_command),
                local_verification.index("python3 -m unittest"),
            )

        lock_path = ROOT / "package-lock.json"
        with self.subTest(contract="package lock"):
            self.assertTrue(lock_path.is_file(), "missing package-lock.json")
            lock = json.loads(lock_path.read_text(encoding="utf-8"))
            self.assertEqual(lock["name"], "rokid-aiui-agent-skill")
            self.assertEqual(lock["lockfileVersion"], 3)
            self.assertEqual(
                lock["packages"][""]["devDependencies"],
                {"@yodaos-pkg/aix-cli": "0.8.2"},
            )
            locked_packages = {
                path: metadata
                for path, metadata in lock["packages"].items()
                if path.startswith("node_modules/")
            }
            self.assertGreater(len(locked_packages), 1)
            self.assertEqual(
                locked_packages["node_modules/@yodaos-pkg/aix-cli"]["version"],
                "0.8.2",
            )
            for path, metadata in locked_packages.items():
                self.assertRegex(
                    metadata.get("version", ""),
                    r"^\d+\.\d+\.\d+(?:[-+][0-9A-Za-z.-]+)*$",
                    path,
                )
                self.assertRegex(
                    metadata.get("integrity", ""), r"^sha512-", path
                )

        workflow = yaml.safe_load(
            (ROOT / ".github" / "workflows" / "ci.yml").read_text(
                encoding="utf-8"
            )
        )
        self.assertIsInstance(workflow, dict)
        jobs = workflow["jobs"]
        validate_job = jobs["validate"]
        aix_job = jobs["aix-smoke"]
        self.assertEqual(aix_job["needs"], "validate")

        for job_name, job in (
            ("validate", validate_job),
            ("aix-smoke", aix_job),
        ):
            with self.subTest(contract="blocking job", job=job_name):
                self.assertNotIn("if", job)
                self.assertNotIn("continue-on-error", job)

        def step_named(job: dict, name: str) -> dict:
            matches = [
                step for step in job["steps"] if step.get("name") == name
            ]
            self.assertEqual(len(matches), 1, f"expected one CI step named {name}")
            return matches[0]

        node_action = (
            "actions/setup-node@"
            "820762786026740c76f36085b0efc47a31fe5020"
        )
        for job_name, job in (
            ("validate", validate_job),
            ("aix-smoke", aix_job),
        ):
            with self.subTest(contract="Node setup", job=job_name):
                setup_node = step_named(job, "Set up Node.js")
                self.assertEqual(setup_node["uses"], node_action)
                self.assertEqual(
                    setup_node["with"], {"node-version": "24.19.0"}
                )

        validate_step = step_named(
            validate_job, "Validate importable AIUI projects strictly"
        )
        self.assertIn(
            "python skills/rokid-aiui-agent/scripts/validate_aiui_project.py "
            "examples/next-step-agent --target-version 0.17.0 --strict",
            validate_step["run"].splitlines(),
        )

        dependency_step = step_named(
            validate_job, "Install validator dependency"
        )
        with self.subTest(contract="shared Python dependency source"):
            self.assertEqual(
                dependency_step["run"],
                "python -m pip install --only-binary=:all: "
                "-r requirements-dev.txt",
            )

        with self.subTest(contract="locked dependency install"):
            install_step = step_named(aix_job, "Install locked AIX CLI")
            self.assertEqual(
                install_step["run"],
                "npm ci --ignore-scripts --no-audit --no-fund",
            )
            step_names = [step.get("name") for step in aix_job["steps"]]
            self.assertLess(
                step_names.index("Install locked AIX CLI"),
                step_names.index("Pack and inspect stable AIUI projects"),
            )
            self.assertLess(
                step_names.index("Pack and inspect stable AIUI projects"),
                step_names.index("Generate the Next Step Agent static preview"),
            )

        aix_bin = "${{ github.workspace }}/node_modules/.bin/aix"
        pack_step = step_named(aix_job, "Pack and inspect stable AIUI projects")
        with self.subTest(contract="locked pack and list"):
            self.assertEqual(pack_step["env"], {"AIX_BIN": aix_bin})
            self.assertEqual(
                tuple(line.strip() for line in pack_step["run"].splitlines()),
                (
                    "bash skills/rokid-aiui-agent/scripts/smoke_aix.sh "
                    "tests/fixtures/valid-minimal",
                    "bash skills/rokid-aiui-agent/scripts/smoke_aix.sh "
                    "skills/rokid-aiui-agent/assets/studio-importable-minimal",
                    "bash skills/rokid-aiui-agent/scripts/smoke_aix.sh "
                    "examples/next-step-agent",
                    "bash skills/rokid-aiui-agent/scripts/smoke_aix.sh "
                    "examples/focus-timer-agent",
                ),
            )

        preview_step = step_named(
            aix_job, "Generate the Next Step Agent static preview"
        )
        with self.subTest(contract="preview shell"):
            self.assertEqual(preview_step.get("shell"), "bash")
        with self.subTest(contract="locked preview binary"):
            self.assertEqual(preview_step["env"], {"AIX_BIN": aix_bin})
        with self.subTest(contract="preview failure and artifact gates"):
            self.assertEqual(
                tuple(line.strip() for line in preview_step["run"].splitlines()),
                (
                    "set -euo pipefail",
                    'preview_html="$RUNNER_TEMP/next-step-agent-preview.html"',
                    '"$AIX_BIN" --help | grep -Eq '
                    "'(^|[[:space:]])preview([[:space:]<]|$)'",
                    '"$AIX_BIN" preview examples/next-step-agent '
                    '--html-out "$preview_html"',
                    'test -s "$preview_html"',
                    "grep -Fq 'pages/index/index.ink' \"$preview_html\"",
                ),
            )

        validate_step_names = [
            step.get("name") for step in validate_job["steps"]
        ]
        self.assertLess(
            validate_step_names.index("Install validator dependency"),
            validate_step_names.index(
                "Run unit suite including offline AIX smoke tests"
            ),
        )
        self.assertLess(
            validate_step_names.index(
                "Run unit suite including offline AIX smoke tests"
            ),
            validate_step_names.index(
                "Validate importable AIUI projects strictly"
            ),
        )
        self.assertLess(
            validate_step_names.index(
                "Validate importable AIUI projects strictly"
            ),
            validate_step_names.index("Verify references"),
        )

        critical_steps = (
            (validate_job, "Install validator dependency"),
            (
                validate_job,
                "Run unit suite including offline AIX smoke tests",
            ),
            (validate_job, "Validate importable AIUI projects strictly"),
            (validate_job, "Verify references"),
            (aix_job, "Install locked AIX CLI"),
            (aix_job, "Pack and inspect stable AIUI projects"),
            (aix_job, "Generate the Next Step Agent static preview"),
        )
        for job, step_name in critical_steps:
            with self.subTest(contract="blocking CI step", step=step_name):
                critical_step = step_named(job, step_name)
                self.assertNotIn("if", critical_step)
                self.assertNotIn("continue-on-error", critical_step)

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
            "`goal` 最多 120 个字符",
            "`nextStep` 最多 48 个字符",
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
        limits = {"goal": 120, "nextStep": 48}
        for name, max_length in limits.items():
            self.assertEqual(data_schema["properties"][name]["type"], "string")
            self.assertEqual(data_schema["properties"][name]["minLength"], 1)
            self.assertEqual(
                data_schema["properties"][name].get("maxLength"), max_length
            )

        setup = extract_block(
            ink, r"<script setup>\s*(.*?)\s*</script>", "setup"
        )
        page = extract_block(ink, r"<page\b[^>]*>\s*(.*?)\s*</page>", "page")
        scroll_tags = re.findall(r"<scroll-view\b[^>]*>", page, flags=re.DOTALL)
        self.assertEqual(len(scroll_tags), 1)
        scroll_tag = scroll_tags[0]
        self.assertRegex(scroll_tag, r"\bclass\s*=\s*([\"'])[^\"']*\bcontent\b[^\"']*\1")
        self.assertRegex(scroll_tag, r"\bscroll-y\s*=\s*([\"'])true\1")
        self.assertEqual(page.count("</scroll-view>"), 1)
        scroll_start = page.index(scroll_tag)
        scroll_end = page.index("</scroll-view>")
        actions_match = re.search(
            r"<view\b[^>]*class\s*=\s*([\"'])[^\"']*\bactions\b[^\"']*\1",
            page,
        )
        self.assertIsNotNone(actions_match)
        self.assertGreater(actions_match.start(), scroll_end)
        for class_name in ("primary-text", "goal-text", "guidance"):
            content_match = re.search(
                rf"<[^>]+\bclass\s*=\s*([\"'])[^\"']*\b{class_name}\b[^\"']*\1",
                page,
            )
            self.assertIsNotNone(content_match, class_name)
            self.assertGreater(content_match.start(), scroll_start)
            self.assertLess(content_match.start(), scroll_end)

        bindtap_pattern = re.compile(
            r"""\bbindtap\s*=\s*(["'])([A-Za-z_$][\w$]*)\1"""
        )
        bindfocus_pattern = re.compile(
            r"""\bbindfocus\s*=\s*(["'])([A-Za-z_$][\w$]*)\1"""
        )
        bindblur_pattern = re.compile(
            r"""\bbindblur\s*=\s*(["'])([A-Za-z_$][\w$]*)\1"""
        )
        buttons = re.findall(r"<button\b[^>]*>", page, flags=re.DOTALL)
        self.assertEqual(len(buttons), 3)
        button_handlers = []
        for button in buttons:
            bindings = [
                handler for _, handler in bindtap_pattern.findall(button)
            ]
            self.assertEqual(len(bindings), 1, button)
            button_handlers.extend(bindings)
            self.assertEqual(
                [handler for _, handler in bindfocus_pattern.findall(button)],
                ["onActionFocus"],
                button,
            )
            self.assertEqual(
                [handler for _, handler in bindblur_pattern.findall(button)],
                ["onActionBlur"],
                button,
            )
            self.assertIn("action-focused-{{actionFocused}}", button)

        expected_handlers = ["startTask", "completeTask", "restartTask"]
        self.assertEqual(len(button_handlers), 3)
        self.assertCountEqual(button_handlers, expected_handlers)
        for handler in expected_handlers:
            self.assertEqual(button_handlers.count(handler), 1)

        all_bindtap_handlers = [
            handler for _, handler in bindtap_pattern.findall(page)
        ]
        self.assertEqual(len(re.findall(r"\bbindtap\b", page)), 3)
        self.assertEqual(len(re.findall(r"\bbindfocus\b", page)), 3)
        self.assertEqual(len(re.findall(r"\bbindblur\b", page)), 3)
        self.assertEqual(len(all_bindtap_handlers), 3)
        self.assertCountEqual(all_bindtap_handlers, expected_handlers)
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
        current = extract_media_region(style, "_current")
        blank = extract_media_region(style, "_blank")
        self.assertRegex(
            current,
            r"(?s)\.expanded-only\s*\{[^{}]*\bdisplay\s*:\s*none\s*;?[^{}]*\}",
        )
        self.assertRegex(
            blank,
            r"(?s)\.expanded-only\s*\{[^{}]*\bdisplay\s*:\s*flex\s*;?[^{}]*\}",
        )
        self.assertIn("border: 1px solid", style)
        self.assertIn("border-radius: 4px", style)
        self.assertIn("border-radius: 6px", style)

        def rules(region: str, selector: str) -> list[str]:
            return re.findall(
                rf"(?m)^[ \t]*{re.escape(selector)}[ \t]*\{{([^{{}}]*)\}}",
                region,
            )

        def rule(region: str, selector: str) -> str:
            matches = rules(region, selector)
            self.assertGreaterEqual(
                len(matches), 1, f"missing {selector} style rule"
            )
            return matches[0]

        content_rule = rule(style, ".content")
        self.assertRegex(content_rule, r"\bflex\s*:\s*1\s+1\s+auto\s*;?")
        self.assertRegex(content_rule, r"\bmin-height\s*:\s*0\s*;?")
        actions_rule = rule(style, ".actions")
        self.assertRegex(actions_rule, r"\bflex-shrink\s*:\s*0\s*;?")

        current_header = re.search(
            r"@media\s*\(\s*target\s*:\s*_current\s*\)", style
        )
        self.assertIsNotNone(current_header)
        base = style[: current_header.start()]
        for region_name, region in (("base", base), ("_blank", blank)):
            for selector in (".primary-text", ".goal-text", ".guidance"):
                for text_rule in rules(region, selector):
                    self.assertNotRegex(
                        text_rule,
                        r"\bmax-height\s*:",
                        f"{region_name} {selector} must remain complete",
                    )
                    self.assertNotRegex(
                        text_rule,
                        r"\boverflow\s*:\s*hidden\b",
                        f"{region_name} {selector} must remain complete",
                    )

        current_primary_rule = rule(current, ".primary-text")
        self.assertRegex(
            current_primary_rule, r"\bmax-height\s*:\s*46px\s*;?"
        )
        self.assertRegex(
            current_primary_rule, r"\boverflow\s*:\s*hidden\s*;?"
        )

        focus_rule = rule(style, ".action-focused-true")
        self.assertIn("border: 2px solid", focus_rule)
        focus_fill = re.search(
            r"background-color\s*:\s*rgba\(\s*64\s*,\s*255\s*,\s*94\s*,\s*([0-9.]+)\s*\)",
            focus_rule,
        )
        self.assertIsNotNone(focus_fill)
        self.assertLessEqual(float(focus_fill.group(1)), 0.12)
        for forbidden in ("_current", "_blank", "onTargetChanged"):
            self.assertNotIn(forbidden, setup)

    def test_real_page_script_state_machine(self) -> None:
        node = shutil.which("node")
        self.assertIsNotNone(node, "Node.js is required for Page behavior tests")
        ink = read_example("pages/index/index.ink")
        setup = extract_block(
            ink, r"<script setup>\s*(.*?)\s*</script>", "setup"
        )
        self.assertNotRegex(
            setup,
            r"""\bthis\.data(?:\.[A-Za-z_$][\w$]*|\[\s*["'][^"']+["']\s*\])\s*=(?!=)""",
        )
        harness = """
import definition from './page.mjs';

const VIEW_KEYS = [
  'state',
  'statusLabel',
  'statusTitle',
  'statusDetail',
  'primaryText',
  'actionFocused'
];

function snapshot(instance) {
  return Object.fromEntries(
    VIEW_KEYS.map((key) => [key, instance.data[key]])
  );
}

function mount() {
  const instance = {
    data: JSON.parse(JSON.stringify(definition.data)),
    setDataCalls: [],
    setData(patch) {
      this.setDataCalls.push(JSON.parse(JSON.stringify(patch)));
      Object.assign(this.data, patch);
    }
  };
  for (const [name, value] of Object.entries(definition)) {
    if (typeof value === 'function') instance[name] = value;
  }
  return instance;
}

function loaded(query) {
  const instance = mount();
  instance.onLoad(query);
  return instance;
}

function captureInput(query) {
  const instance = mount();
  const beforeCalls = instance.setDataCalls.length;
  instance.onLoad(query);
  return {
    view: snapshot(instance),
    stored: [instance.data.goal, instance.data.nextStep],
    setDataCallDelta: instance.setDataCalls.length - beforeCalls
  };
}

function exerciseLegalTransition(instance, method) {
  if (typeof instance.onActionFocus === 'function') instance.onActionFocus();
  const beforeCalls = instance.setDataCalls.length;
  instance[method]();
  return {
    view: snapshot(instance),
    setDataCallDelta: instance.setDataCalls.length - beforeCalls
  };
}

function exerciseFocusHandler(method, initialFocused) {
  const instance = loaded({ goal: '目标', nextStep: '行动' });
  instance.data.actionFocused = initialFocused;
  const beforeCalls = instance.setDataCalls.length;
  if (typeof instance[method] !== 'function') {
    return {
      exists: false,
      before: initialFocused,
      after: instance.data.actionFocused,
      setDataCallDelta: 0,
      lastPatch: null
    };
  }
  instance[method]();
  return {
    exists: true,
    before: initialFocused,
    after: instance.data.actionFocused,
    setDataCallDelta: instance.setDataCalls.length - beforeCalls,
    lastPatch: instance.setDataCalls[instance.setDataCalls.length - 1]
  };
}

function exerciseInvalidTransition(query, preparationMethods, method) {
  const instance = loaded(query);
  for (const preparationMethod of preparationMethods) {
    instance[preparationMethod]();
  }
  const before = snapshot(instance);
  instance[method]();
  return {
    state: before.state,
    method,
    before,
    after: snapshot(instance)
  };
}

const valid = mount();
const beforeLoadCalls = valid.setDataCalls.length;
valid.onLoad({ goal: '  完成发布说明  ', nextStep: '  列出三个主要变化  ' });
const legalTransitions = [{
  view: snapshot(valid),
  setDataCallDelta: valid.setDataCalls.length - beforeLoadCalls
}];
legalTransitions.push(exerciseLegalTransition(valid, 'startTask'));
legalTransitions.push(exerciseLegalTransition(valid, 'completeTask'));
legalTransitions.push(exerciseLegalTransition(valid, 'restartTask'));

const invalidTransitions = [
  exerciseInvalidTransition(null, [], 'startTask'),
  exerciseInvalidTransition(null, [], 'completeTask'),
  exerciseInvalidTransition(null, [], 'restartTask'),
  exerciseInvalidTransition(
    { goal: 7, nextStep: '行动' }, [], 'startTask'
  ),
  exerciseInvalidTransition(
    { goal: 7, nextStep: '行动' }, [], 'completeTask'
  ),
  exerciseInvalidTransition(
    { goal: 7, nextStep: '行动' }, [], 'restartTask'
  ),
  exerciseInvalidTransition(
    { goal: '目标', nextStep: '行动' }, [], 'completeTask'
  ),
  exerciseInvalidTransition(
    { goal: '目标', nextStep: '行动' }, [], 'restartTask'
  ),
  exerciseInvalidTransition(
    { goal: '目标', nextStep: '行动' }, ['startTask'], 'startTask'
  ),
  exerciseInvalidTransition(
    { goal: '目标', nextStep: '行动' }, ['startTask'], 'restartTask'
  ),
  exerciseInvalidTransition(
    { goal: '目标', nextStep: '行动' },
    ['startTask', 'completeTask'],
    'startTask'
  ),
  exerciseInvalidTransition(
    { goal: '目标', nextStep: '行动' },
    ['startTask', 'completeTask'],
    'completeTask'
  )
];

const inputs = {
  undefinedRoot: captureInput(),
  nullRoot: captureInput(null),
  whitespace: captureInput({ goal: '   ', nextStep: ' \t ' }),
  blankGoal: captureInput({ goal: '   ', nextStep: '行动' }),
  blankNextStep: captureInput({ goal: '目标', nextStep: '   ' }),
  missingGoal: captureInput({ nextStep: '行动' }),
  missingNextStep: captureInput({ goal: '目标' }),
  invalidGoal: captureInput({ goal: 7, nextStep: '行动' }),
  invalidNextStep: captureInput({ goal: '目标', nextStep: 7 }),
  stringRoot: captureInput('bad'),
  arrayRoot: captureInput(['目标', '行动']),
  atLimits: captureInput({
    goal: '目'.repeat(120),
    nextStep: '行'.repeat(48)
  }),
  overlongGoal: captureInput({
    goal: '目'.repeat(121),
    nextStep: '行动'
  }),
  overlongNextStep: captureInput({
    goal: '目标',
    nextStep: '行'.repeat(49)
  }),
  paddedGoalOverLimit: captureInput({
    goal: ' ' + '目'.repeat(120),
    nextStep: '行动'
  }),
  paddedNextStepOverLimit: captureInput({
    goal: '目标',
    nextStep: '行'.repeat(48) + ' '
  }),
  emojiNextAtLimit: captureInput({
    goal: '目标',
    nextStep: '😀'.repeat(48)
  }),
  emojiNextOverLimit: captureInput({
    goal: '目标',
    nextStep: '😀'.repeat(49)
  }),
  extendedGoalAtLimit: captureInput({
    goal: '𠮷'.repeat(120),
    nextStep: '行动'
  }),
  extendedGoalOverLimit: captureInput({
    goal: '𠮷'.repeat(121),
    nextStep: '行动'
  })
};

console.log(JSON.stringify({
  legalTransitions,
  trimmed: [valid.data.goal, valid.data.nextStep],
  invalidTransitions,
  focusHandlers: {
    focus: exerciseFocusHandler('onActionFocus', false),
    blur: exerciseFocusHandler('onActionBlur', true)
  },
  inputs
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
        empty = {
            "state": "empty",
            "statusLabel": "等待目标",
            "statusTitle": "还没有下一步",
            "statusDetail": "回到对话，告诉我你现在想推进什么。",
            "primaryText": "先说出一个你想推进的目标",
            "actionFocused": False,
        }
        error = {
            "state": "error",
            "statusLabel": "需要重试",
            "statusTitle": "暂时无法读取行动内容",
            "statusDetail": "回到对话重新生成下一步。",
            "primaryText": "行动内容格式不正确",
            "actionFocused": False,
        }
        ready = {
            "state": "ready",
            "statusLabel": "准备开始",
            "statusTitle": "只做这一件事",
            "statusDetail": "开始后保持专注，完成时在这里确认。",
            "primaryText": "列出三个主要变化",
            "actionFocused": False,
        }
        active = {
            "state": "active",
            "statusLabel": "正在推进",
            "statusTitle": "保持在下一步",
            "statusDetail": "完成这个动作后再决定下一件事。",
            "primaryText": "列出三个主要变化",
            "actionFocused": False,
        }
        done = {
            "state": "done",
            "statusLabel": "已经完成",
            "statusTitle": "这一步完成了",
            "statusDetail": "回到对话告诉我下一件事，或重新开始这一动作。",
            "primaryText": "列出三个主要变化",
            "actionFocused": False,
        }
        self.assertEqual(
            [item["view"] for item in payload["legalTransitions"]],
            [ready, active, done, ready],
        )
        for item in payload["legalTransitions"]:
            self.assertGreaterEqual(item["setDataCallDelta"], 1)
            self.assertFalse(item["view"]["actionFocused"])
        self.assertEqual(payload["trimmed"], ["完成发布说明", "列出三个主要变化"])
        self.assertEqual(
            payload["focusHandlers"],
            {
                "focus": {
                    "exists": True,
                    "before": False,
                    "after": True,
                    "setDataCallDelta": 1,
                    "lastPatch": {"actionFocused": True},
                },
                "blur": {
                    "exists": True,
                    "before": True,
                    "after": False,
                    "setDataCallDelta": 1,
                    "lastPatch": {"actionFocused": False},
                },
            },
        )
        self.assertEqual(
            [
                (item["state"], item["method"])
                for item in payload["invalidTransitions"]
            ],
            [
                ("empty", "startTask"),
                ("empty", "completeTask"),
                ("empty", "restartTask"),
                ("error", "startTask"),
                ("error", "completeTask"),
                ("error", "restartTask"),
                ("ready", "completeTask"),
                ("ready", "restartTask"),
                ("active", "startTask"),
                ("active", "restartTask"),
                ("done", "startTask"),
                ("done", "completeTask"),
            ],
        )
        for item in payload["invalidTransitions"]:
            self.assertEqual(item["after"], item["before"])
            if item["state"] == "error":
                self.assertEqual(item["before"], error)
        self.assertEqual(
            {
                name: result["view"]
                for name, result in payload["inputs"].items()
            },
            {
                "undefinedRoot": empty,
                "nullRoot": empty,
                "whitespace": empty,
                "blankGoal": empty,
                "blankNextStep": empty,
                "missingGoal": empty,
                "missingNextStep": empty,
                "invalidGoal": error,
                "invalidNextStep": error,
                "stringRoot": error,
                "arrayRoot": error,
                "atLimits": {
                    **ready,
                    "primaryText": "行" * 48,
                },
                "overlongGoal": error,
                "overlongNextStep": error,
                "paddedGoalOverLimit": error,
                "paddedNextStepOverLimit": error,
                "emojiNextAtLimit": {
                    **ready,
                    "primaryText": "😀" * 48,
                },
                "emojiNextOverLimit": error,
                "extendedGoalAtLimit": {
                    **ready,
                    "primaryText": "行动",
                },
                "extendedGoalOverLimit": error,
            },
        )
        self.assertEqual(
            payload["inputs"]["atLimits"]["stored"],
            ["目" * 120, "行" * 48],
        )
        self.assertEqual(
            payload["inputs"]["emojiNextAtLimit"]["stored"],
            ["目标", "😀" * 48],
        )
        self.assertEqual(
            payload["inputs"]["extendedGoalAtLimit"]["stored"],
            ["𠮷" * 120, "行动"],
        )
        for name in (
            "overlongGoal",
            "overlongNextStep",
            "paddedGoalOverLimit",
            "paddedNextStepOverLimit",
            "emojiNextOverLimit",
            "extendedGoalOverLimit",
        ):
            self.assertEqual(payload["inputs"][name]["view"], error)
            self.assertEqual(payload["inputs"][name]["stored"], ["", ""])
        for name in (
            "invalidGoal",
            "invalidNextStep",
            "stringRoot",
            "arrayRoot",
            "overlongGoal",
            "overlongNextStep",
            "paddedGoalOverLimit",
            "paddedNextStepOverLimit",
            "emojiNextOverLimit",
            "extendedGoalOverLimit",
        ):
            self.assertGreaterEqual(
                payload["inputs"][name]["setDataCallDelta"], 1
            )


if __name__ == "__main__":
    unittest.main()
