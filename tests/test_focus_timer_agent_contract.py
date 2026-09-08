from __future__ import annotations

import json
import re
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
EXAMPLE = ROOT / "examples" / "focus-timer-agent"
INK = EXAMPLE / "pages" / "index" / "index.ink"


def read_example(relative: str) -> str:
    path = EXAMPLE / relative
    if not path.is_file():
        raise AssertionError(f"missing Focus Timer Agent file: {relative}")
    return path.read_text(encoding="utf-8")


def extract_block(source: str, pattern: str, label: str) -> str:
    match = re.search(pattern, source, flags=re.DOTALL)
    if match is None:
        raise AssertionError(f"missing {label} block")
    return match.group(1).strip()


class FocusTimerAgentContractTests(unittest.TestCase):
    def test_readme_and_ci_cover_delivery_flow(self) -> None:
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        for fragment in (
            "examples/focus-timer-agent",
            "Japanese Focus Timer Agent",
            "durationSeconds",
            "Date.now()",
            "Directory: examples/focus-timer-agent",
        ):
            self.assertIn(fragment, readme)

        workflow = yaml.safe_load(
            (ROOT / ".github" / "workflows" / "ci.yml").read_text(
                encoding="utf-8"
            )
        )
        validate_run = next(
            step["run"]
            for step in workflow["jobs"]["validate"]["steps"]
            if step.get("name") == "Validate importable AIUI projects strictly"
        )
        self.assertIn(
            "examples/focus-timer-agent --target-version 0.17.0 --strict",
            validate_run,
        )
        aix_steps = workflow["jobs"]["aix-smoke"]["steps"]
        pack_run = next(
            step["run"]
            for step in aix_steps
            if step.get("name") == "Pack and inspect stable AIUI projects"
        )
        self.assertIn(
            "smoke_aix.sh examples/focus-timer-agent", pack_run
        )
        preview = next(
            step
            for step in aix_steps
            if step.get("name") == "Generate the Focus Timer Agent static preview"
        )
        self.assertEqual(
            preview["env"],
            {"AIX_BIN": "${{ github.workspace }}/node_modules/.bin/aix"},
        )
        self.assertIn(
            '"$AIX_BIN" --help', preview["run"]
        )
        self.assertIn(
            '"$AIX_BIN" preview examples/focus-timer-agent', preview["run"]
        )
        self.assertIn("test -s", preview["run"])

    def test_import_root_is_page_only_aiui_017_project(self) -> None:
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

    def test_japanese_agent_contract_declares_inputs_states_and_limits(self) -> None:
        agents = read_example("AGENTS.md")
        for fragment in (
            "# Agent: フォーカスタイマー",
            "## System Prompts",
            "## Capabilities",
            "## Configuration",
            "## Dependencies",
            "`durationSeconds`",
            "1～3600",
            "`label`",
            "`idle`",
            "`running`",
            "`paused`",
            "`finished`",
            "`error`",
            "`_current`",
            "`_blank`",
            "バックグラウンド",
            "通知",
            "永続化",
        ):
            self.assertIn(fragment, agents)

    def test_schema_targets_visuals_and_action_bindings(self) -> None:
        ink = read_example("pages/index/index.ink")
        self.assertEqual(ink.count("<script def>"), 1)
        self.assertEqual(ink.count("<script setup>"), 1)
        self.assertEqual(len(re.findall(r"<page\b", ink)), 1)
        self.assertNotIn("<widget", ink)

        definition = json.loads(
            extract_block(ink, r"<script def>\s*(.*?)\s*</script>", "definition")
        )
        schema = definition["schema"]
        self.assertEqual(set(schema), {"data"})
        data_schema = schema["data"]
        self.assertEqual(data_schema["type"], "object")
        self.assertEqual(data_schema["required"], ["durationSeconds"])
        duration = data_schema["properties"]["durationSeconds"]
        self.assertEqual(
            duration,
            {
                "type": "integer",
                "minimum": 1,
                "maximum": 3600,
                "description": "集中する時間（秒）。",
            },
        )
        label = data_schema["properties"]["label"]
        self.assertEqual(label["type"], "string")
        self.assertEqual(label["maxLength"], 48)

        page = extract_block(ink, r"<page\b[^>]*>(.*?)</page>", "page")
        setup = extract_block(
            ink, r"<script setup>\s*(.*?)\s*</script>", "setup"
        )
        style = extract_block(ink, r"<style>\s*(.*?)\s*</style>", "style")
        self.assertIn("@media (target: _current)", style)
        self.assertIn("@media (target: _blank)", style)
        self.assertIn("background-color: #000000", style)
        self.assertIn("border: 1px solid", style)
        self.assertIn("border-radius: 4px", style)
        self.assertIn("border-radius: 6px", style)
        for text in (
            "フォーカスタイマー",
            "開始",
            "一時停止",
            "再開",
            "最初から",
            "リセット",
        ):
            self.assertIn(text, ink)

        buttons = re.findall(r"<button\b[^>]*>", page, flags=re.DOTALL)
        self.assertEqual(len(buttons), 5)
        handlers = []
        for button in buttons:
            tap = re.findall(r'\bbindtap="([A-Za-z_$][\w$]*)"', button)
            self.assertEqual(len(tap), 1, button)
            handlers.extend(tap)
            self.assertIn('bindfocus="onActionFocus"', button)
            self.assertIn('bindblur="onActionBlur"', button)
        self.assertCountEqual(
            handlers,
            ["startTimer", "pauseTimer", "continueTimer", "restartTimer", "resetTimer"],
        )
        for handler in handlers + ["onActionFocus", "onActionBlur"]:
            self.assertRegex(setup, rf"(?m)^\s{{2}}{handler}\([^)]*\)\s*\{{")

        current = style[style.index("@media (target: _current)") :]
        blank = style[style.index("@media (target: _blank)") :]
        self.assertIn(".expanded-only { display: none; }", current)
        self.assertIn(".expanded-only { display: flex; }", blank)
        self.assertIn("Date.now()", setup)
        self.assertIn("setInterval", setup)
        self.assertIn("clearInterval", setup)
        for lifecycle in ("onShow", "onHide", "onUnload"):
            self.assertRegex(setup, rf"(?m)^\s{{2}}{lifecycle}\(\)\s*\{{")
        for forbidden in ("fetch(", "wx.request", "getStorage", "setStorage"):
            self.assertNotIn(forbidden, setup)

    def test_real_page_uses_absolute_deadline_and_fake_clock(self) -> None:
        node = shutil.which("node")
        self.assertIsNotNone(node, "Node.js is required for Page behavior tests")
        setup = extract_block(
            read_example("pages/index/index.ink"),
            r"<script setup>\s*(.*?)\s*</script>",
            "setup",
        )
        harness = r"""
import definition from './page.mjs';

let nowMs = 100000;
let nextTimerId = 1;
const intervals = new Map();
Date.now = () => nowMs;
globalThis.setInterval = (callback, delay) => {
  const id = nextTimerId++;
  intervals.set(id, { callback, delay });
  return id;
};
globalThis.clearInterval = (id) => intervals.delete(id);

function mount(query) {
  const page = {
    data: JSON.parse(JSON.stringify(definition.data)),
    patches: [],
    setData(patch) {
      this.patches.push(JSON.parse(JSON.stringify(patch)));
      Object.assign(this.data, patch);
    }
  };
  for (const [name, value] of Object.entries(definition)) {
    if (typeof value === 'function') page[name] = value;
  }
  page.onLoad(query);
  page.onShow();
  return page;
}

function snapshot(page) {
  return {
    state: page.data.state,
    durationSeconds: page.data.durationSeconds,
    label: page.data.label,
    remainingMs: page.data.remainingMs,
    deadlineMs: page.data.deadlineMs,
    displayTime: page.data.displayTime,
    progressPercent: page.data.progressPercent,
    intervals: intervals.size,
  };
}

function advance(ms) {
  nowMs += ms;
  for (const timer of [...intervals.values()]) timer.callback();
}

function isolated(query, exercise) {
  intervals.clear();
  nowMs = 100000;
  const page = mount(query);
  const result = exercise(page);
  page.onUnload();
  intervals.clear();
  return result;
}

const inputs = {
  min: isolated({ durationSeconds: 1 }, snapshot),
  max: isolated({ durationSeconds: 3600, label: '  原稿を書く  ' }, snapshot),
  zero: isolated({ durationSeconds: 0 }, snapshot),
  over: isolated({ durationSeconds: 3601 }, snapshot),
  fraction: isolated({ durationSeconds: 1.5 }, snapshot),
  stringDuration: isolated({ durationSeconds: '60' }, snapshot),
  missing: isolated({}, snapshot),
  nullRoot: isolated(null, snapshot),
  badLabel: isolated({ durationSeconds: 60, label: 7 }, snapshot),
  longLabel: isolated({ durationSeconds: 60, label: 'あ'.repeat(49) }, snapshot),
  emojiLimit: isolated({ durationSeconds: 60, label: '😀'.repeat(48) }, snapshot),
};

const flow = isolated({ durationSeconds: 10, label: '  読書  ' }, (page) => {
  const states = [snapshot(page)];
  page.startTimer();
  states.push(snapshot(page));
  const firstDeadline = page.data.deadlineMs;
  page.startTimer();
  states.push({ ...snapshot(page), sameDeadline: page.data.deadlineMs === firstDeadline });
  advance(2500);
  states.push(snapshot(page));
  page.pauseTimer();
  states.push(snapshot(page));
  const pausedRemaining = page.data.remainingMs;
  page.pauseTimer();
  advance(5000);
  states.push({ ...snapshot(page), pauseHeld: page.data.remainingMs === pausedRemaining });
  page.continueTimer();
  states.push(snapshot(page));
  const continuedDeadline = page.data.deadlineMs;
  page.continueTimer();
  states.push({ ...snapshot(page), sameDeadline: page.data.deadlineMs === continuedDeadline });
  advance(pausedRemaining);
  states.push(snapshot(page));
  page.restartTimer();
  states.push(snapshot(page));
  page.resetTimer();
  states.push(snapshot(page));
  return states;
});

const lifecycle = isolated({ durationSeconds: 10, label: '設計' }, (page) => {
  page.startTimer();
  advance(2000);
  page.onHide();
  const hidden = snapshot(page);
  nowMs += 3000;
  const hiddenLater = snapshot(page);
  page.onShow();
  const shown = snapshot(page);
  page.onHide();
  nowMs += 6000;
  page.onShow();
  const finishedOnShow = snapshot(page);
  page.onUnload();
  const unloaded = snapshot(page);
  return { hidden, hiddenLater, shown, finishedOnShow, unloaded };
});

const actions = isolated({ durationSeconds: 5 }, (page) => {
  page.onActionFocus();
  const focused = page.data.actionFocused;
  page.onActionBlur();
  const blurred = page.data.actionFocused;
  page.pauseTimer();
  const invalidPause = snapshot(page);
  page.restartTimer();
  const invalidRestart = snapshot(page);
  return { focused, blurred, invalidPause, invalidRestart };
});

console.log(JSON.stringify({ inputs, flow, lifecycle, actions }));
"""
        with tempfile.TemporaryDirectory(prefix="focus-timer-agent-") as directory:
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

        self.assertEqual(payload["inputs"]["min"]["state"], "idle")
        self.assertEqual(payload["inputs"]["min"]["displayTime"], "00:01")
        self.assertEqual(payload["inputs"]["min"]["label"], "フォーカスタイマー")
        self.assertEqual(payload["inputs"]["max"]["state"], "idle")
        self.assertEqual(payload["inputs"]["max"]["displayTime"], "60:00")
        self.assertEqual(payload["inputs"]["max"]["label"], "原稿を書く")
        for name in (
            "zero",
            "over",
            "fraction",
            "stringDuration",
            "missing",
            "nullRoot",
            "badLabel",
            "longLabel",
        ):
            self.assertEqual(payload["inputs"][name]["state"], "error", name)
        self.assertEqual(payload["inputs"]["emojiLimit"]["state"], "idle")

        flow = payload["flow"]
        self.assertEqual(
            [item["state"] for item in flow],
            [
                "idle",
                "running",
                "running",
                "running",
                "paused",
                "paused",
                "running",
                "running",
                "finished",
                "running",
                "idle",
            ],
        )
        self.assertTrue(flow[2]["sameDeadline"])
        self.assertEqual(flow[3]["remainingMs"], 7500)
        self.assertEqual(flow[3]["displayTime"], "00:08")
        self.assertEqual(flow[3]["progressPercent"], 25)
        self.assertEqual(flow[4]["intervals"], 0)
        self.assertTrue(flow[5]["pauseHeld"])
        self.assertTrue(flow[7]["sameDeadline"])
        self.assertEqual(flow[8]["remainingMs"], 0)
        self.assertEqual(flow[8]["displayTime"], "00:00")
        self.assertEqual(flow[8]["progressPercent"], 100)
        self.assertEqual(flow[8]["intervals"], 0)
        self.assertEqual(flow[9]["remainingMs"], 10000)
        self.assertEqual(flow[9]["intervals"], 1)
        self.assertEqual(flow[10]["remainingMs"], 10000)
        self.assertEqual(flow[10]["intervals"], 0)

        lifecycle = payload["lifecycle"]
        self.assertEqual(lifecycle["hidden"]["intervals"], 0)
        self.assertEqual(lifecycle["hiddenLater"]["remainingMs"], 8000)
        self.assertEqual(lifecycle["shown"]["remainingMs"], 5000)
        self.assertEqual(lifecycle["shown"]["intervals"], 1)
        self.assertEqual(lifecycle["finishedOnShow"]["state"], "finished")
        self.assertEqual(lifecycle["finishedOnShow"]["intervals"], 0)
        self.assertEqual(lifecycle["unloaded"]["intervals"], 0)

        self.assertEqual(
            payload["actions"],
            {
                "focused": True,
                "blurred": False,
                "invalidPause": {
                    "state": "idle",
                    "durationSeconds": 5,
                    "label": "フォーカスタイマー",
                    "remainingMs": 5000,
                    "deadlineMs": 0,
                    "displayTime": "00:05",
                    "progressPercent": 0,
                    "intervals": 0,
                },
                "invalidRestart": {
                    "state": "idle",
                    "durationSeconds": 5,
                    "label": "フォーカスタイマー",
                    "remainingMs": 5000,
                    "deadlineMs": 0,
                    "displayTime": "00:05",
                    "progressPercent": 0,
                    "intervals": 0,
                },
            },
        )


if __name__ == "__main__":
    unittest.main()
