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
EXAMPLE = ROOT / "examples" / "katari-agent"
INK = EXAMPLE / "pages" / "index" / "index.ink"
VALIDATOR = (
    ROOT
    / "skills"
    / "rokid-aiui-agent"
    / "scripts"
    / "validate_aiui_project.py"
)
SOURCE_SPOT = re.compile(r"^## Spot: ([a-z0-9-]+)$", re.MULTILINE)
AGENT_SPOT = re.compile(r"^### Story Spot: ([a-z0-9-]+)$", re.MULTILINE)


def read_example(relative: str) -> str:
    path = EXAMPLE / relative
    if not path.is_file():
        raise AssertionError(f"missing KATARI file: {relative}")
    return path.read_text(encoding="utf-8")


def extract_block(source: str, pattern: str, label: str) -> str:
    match = re.search(pattern, source, flags=re.DOTALL)
    if match is None:
        raise AssertionError(f"missing {label} block")
    return match.group(1).strip()


def run_page_cases(cases: list[dict[str, object]]) -> list[dict[str, object]]:
    node = shutil.which("node")
    if node is None:
        raise AssertionError("node is required for KATARI Page behavior tests")
    setup = extract_block(
        read_example("pages/index/index.ink"),
        r"<script setup>\s*(.*?)\s*</script>",
        "setup",
    )
    setup = setup.replace("export default", "const pageDefinition =", 1)
    with tempfile.TemporaryDirectory() as directory:
        module_path = Path(directory) / "page.mjs"
        runner_path = Path(directory) / "runner.mjs"
        module_path.write_text(
            setup + "\nexport { pageDefinition };\n", encoding="utf-8"
        )
        runner_path.write_text(
            """
import { pageDefinition } from './page.mjs';

const cases = JSON.parse(process.argv[2]);
const results = cases.map(({ name, query, omitQuery }) => {
  const instance = {
    data: structuredClone(pageDefinition.data),
    calls: [],
    setData(patch) {
      this.calls.push(structuredClone(patch));
      this.data = { ...this.data, ...patch };
    }
  };
  if (omitQuery) {
    pageDefinition.onLoad.call(instance);
  } else {
    pageDefinition.onLoad.call(instance, query);
  }
  return { name, calls: instance.calls, data: instance.data };
});
process.stdout.write(JSON.stringify(results));
""".strip(),
            encoding="utf-8",
        )
        completed = subprocess.run(
            [node, str(runner_path), json.dumps(cases, ensure_ascii=False)],
            check=True,
            capture_output=True,
            text=True,
        )
    return json.loads(completed.stdout)


class KatariAgentContractTests(unittest.TestCase):
    def test_source_registry_has_twenty_complete_story_spots(self) -> None:
        sources = read_example("SOURCES.md")
        ids = SOURCE_SPOT.findall(sources)
        self.assertEqual(len(ids), 20)
        self.assertEqual(len(set(ids)), 20)
        sections = re.split(
            r"(?=^## Spot: )", sources, flags=re.MULTILINE
        )[1:]
        for section in sections:
            for label in (
                "- Place JA:",
                "- Place EN:",
                "- Category:",
                "- Locality:",
                "- Coordinates:",
                "- Candidate radius:",
                "- Visual anchors:",
                "- Facts:",
                "- Story claim:",
                "- Knowledge kind:",
                "- Sources:",
                "- Source classes:",
                "- Verified:",
                "- Uncertainty:",
            ):
                self.assertIn(label, section)
            self.assertRegex(section, r"https://")
            self.assertRegex(section, r"- Verified: 2026-\d{2}-\d{2}")
            self.assertRegex(
                section,
                r"(?m)^- Knowledge kind: (?:fact|legend|tradition)$",
            )
            facts = re.findall(r"^  \d+\. .+$", section, re.MULTILINE)
            self.assertGreaterEqual(len(facts), 3)
            self.assertLessEqual(len(facts), 5)
            self.assertNotRegex(section, r"\b(?:TBD|TODO)\b")

    def test_import_root_is_minimal_and_page_only(self) -> None:
        expected = {
            "AGENTS.md",
            "SOURCES.md",
            "app.js",
            "app.json",
            "pages/index/index.ink",
        }
        actual = {
            str(path.relative_to(EXAMPLE))
            for path in EXAMPLE.rglob("*")
            if path.is_file()
        }
        self.assertEqual(actual, expected)

        manifest = json.loads(read_example("app.json"))
        self.assertEqual(manifest["pages"], ["pages/index/index"])
        for forbidden in ("widgets", "agentWorkers", "permissions"):
            self.assertNotIn(forbidden, manifest)

        self.assertIn("App({", read_example("app.js"))
        ink = read_example("pages/index/index.ink")
        self.assertIn("<script def>", ink)
        self.assertIn("<script setup>", ink)
        self.assertIn("<page", ink)

    def test_agent_prompt_defines_bounded_local_story_behavior(self) -> None:
        agent = read_example("AGENTS.md")
        for heading in (
            "## System Prompts",
            "## Capabilities",
            "## Configuration",
            "## Dependencies",
        ):
            self.assertIn(heading, agent)
        for fragment in (
            "KATARI",
            "host supplies",
            "image",
            "GPS",
            "voice",
            "locale",
            "Japanese",
            "English",
            "matched",
            "uncertain",
            "no_story",
            "no_match",
            "invalid",
            "one specific view once",
            "15–30 seconds",
            "one authored story",
            "fact",
            "legend",
            "tradition",
            "_current",
            "_blank",
            "route planning",
            "recommendations",
            "live news",
            "proactive prompts",
            "Page does not access camera or GPS",
        ):
            self.assertIn(fragment, agent)

    def test_runtime_catalog_matches_source_registry(self) -> None:
        source_ids = SOURCE_SPOT.findall(read_example("SOURCES.md"))
        agent = read_example("AGENTS.md")
        agent_ids = AGENT_SPOT.findall(agent)
        self.assertEqual(len(agent_ids), 20)
        self.assertEqual(len(set(agent_ids)), 20)
        self.assertEqual(set(agent_ids), set(source_ids))

        sections = re.split(
            r"(?=^### Story Spot: )", agent, flags=re.MULTILINE
        )[1:]
        for section in sections:
            for label in (
                "- Coordinates / radius:",
                "- Anchors:",
                "- Accepted facts:",
                "- Story JA:",
                "- Story EN:",
                "- Memory hook JA:",
                "- Memory hook EN:",
                "- Knowledge kind:",
                "- Source IDs:",
                "- Duration:",
            ):
                self.assertIn(label, section)
            facts = re.findall(r"^  \d+\. .+$", section, re.MULTILINE)
            self.assertGreaterEqual(len(facts), 3)
            self.assertLessEqual(len(facts), 5)
            ja = re.search(r"(?m)^- Story JA: (.+)$", section).group(1)
            en = re.search(r"(?m)^- Story EN: (.+)$", section).group(1)
            duration = int(
                re.search(r"(?m)^- Duration: (\d+) seconds$", section).group(1)
            )
            self.assertGreaterEqual(len(ja), 60)
            self.assertLessEqual(len(ja), 120)
            self.assertGreaterEqual(len(en.split()), 35)
            self.assertLessEqual(len(en.split()), 70)
            self.assertGreaterEqual(duration, 15)
            self.assertLessEqual(duration, 30)
            self.assertRegex(
                section,
                r"(?m)^- Knowledge kind: (?:fact|legend|tradition)$",
            )
            self.assertNotRegex(section, r"\b(?:TBD|TODO)\b")

    def test_page_schema_declares_bounded_five_state_input(self) -> None:
        definition = json.loads(
            extract_block(
                read_example("pages/index/index.ink"),
                r"<script def>\s*(.*?)\s*</script>",
                "definition",
            )
        )
        schema = definition["schema"]["data"]
        self.assertEqual(schema["type"], "object")
        properties = schema["properties"]
        self.assertEqual(
            properties["status"]["enum"],
            ["matched", "uncertain", "no_story", "no_match", "invalid"],
        )
        for field, maximum in (
            ("spotId", 48),
            ("placeNameJa", 48),
            ("placeNameEn", 64),
            ("localityLabel", 48),
            ("memoryHook", 140),
            ("confidenceLabel", 64),
            ("evidenceNote", 160),
            ("recoveryHint", 160),
        ):
            self.assertEqual(properties[field], {
                "type": "string",
                "maxLength": maximum,
            })
        self.assertEqual(
            properties["storyDurationSeconds"],
            {"type": "integer", "minimum": 15, "maximum": 30},
        )
        self.assertEqual(
            properties["knowledgeKind"],
            {"type": "string", "enum": ["fact", "legend", "tradition"]},
        )

    def test_page_normalizer_accepts_valid_states_and_rejects_bad_roots(self) -> None:
        matched = {
            "status": "matched",
            "spotId": "ebisu-bridge",
            "placeNameJa": "戎橋",
            "placeNameEn": "Ebisu Bridge",
            "localityLabel": "Dotonbori, Osaka",
            "storyDurationSeconds": 24,
            "memoryHook": "参拝と芝居の橋",
            "confidenceLabel": "GPS + 2 VISUAL ANCHORS",
            "evidenceNote": "Bridge, canal, and adjacent signs agree.",
            "knowledgeKind": "fact",
            "recoveryHint": "",
        }
        cases = [
            {"name": "matched-ja", "query": matched},
            {
                "name": "matched-en",
                "query": {**matched, "placeNameEn": "Tower of the Sun"},
            },
            {"name": "uncertain", "query": {"status": "uncertain"}},
            {
                "name": "no-story",
                "query": {
                    "status": "no_story",
                    "placeNameJa": "確認済みの場所",
                    "placeNameEn": "CONFIRMED PLACE",
                },
            },
            {"name": "no-match", "query": {"status": "no_match"}},
            {"name": "explicit-invalid", "query": {"status": "invalid"}},
            {"name": "missing", "omitQuery": True},
            {"name": "array", "query": []},
            {"name": "number", "query": 7},
            {"name": "unknown", "query": {"status": "maybe"}},
        ]
        results = {item["name"]: item for item in run_page_cases(cases)}
        complete_keys = {
            "status", "spotId", "placeNameJa", "placeNameEn",
            "localityLabel", "storyDurationSeconds", "memoryHook",
            "confidenceLabel", "evidenceNote", "knowledgeKind",
            "knowledgeLabel", "recoveryHint", "showStoryMeta",
            "showExpandedDetail",
        }
        for item in results.values():
            self.assertEqual(len(item["calls"]), 1, item["name"])
            self.assertEqual(set(item["calls"][0]), complete_keys, item["name"])

        self.assertEqual(results["matched-ja"]["data"]["status"], "matched")
        self.assertEqual(results["matched-ja"]["data"]["knowledgeLabel"], "FACT")
        self.assertIs(results["matched-ja"]["data"]["showStoryMeta"], True)
        self.assertEqual(results["matched-en"]["data"]["placeNameEn"], "Tower of the Sun")
        recovery_titles = []
        for name, state in (
            ("uncertain", "uncertain"),
            ("no-story", "no_story"),
            ("no-match", "no_match"),
        ):
            self.assertEqual(results[name]["data"]["status"], state)
            self.assertFalse(results[name]["data"]["showStoryMeta"])
            self.assertTrue(results[name]["data"]["recoveryHint"])
            recovery_titles.append(results[name]["data"]["placeNameJa"])
        self.assertEqual(len(set(recovery_titles)), 3)

        safe_invalid = {
            "status": "invalid",
            "spotId": "",
            "placeNameJa": "場所を見せてください",
            "placeNameEn": "LOOK AT A LANDMARK",
            "localityLabel": "",
            "storyDurationSeconds": 0,
            "memoryHook": "",
            "confidenceLabel": "KATARI",
            "evidenceNote": "",
            "knowledgeKind": "fact",
            "knowledgeLabel": "",
            "recoveryHint": "建物や看板が見える向きでもう一度聞いてください。",
            "showStoryMeta": False,
            "showExpandedDetail": False,
        }
        for name in ("explicit-invalid", "missing", "array", "number", "unknown"):
            self.assertEqual(results[name]["calls"][0], safe_invalid, name)

    def test_page_normalizer_enforces_types_durations_and_unicode_limits(self) -> None:
        base = {
            "status": "matched",
            "spotId": "spot",
            "placeNameJa": "場所",
            "placeNameEn": "Place",
            "localityLabel": "Osaka",
            "storyDurationSeconds": 20,
            "memoryHook": "記憶",
            "confidenceLabel": "GPS + VISUAL",
            "evidenceNote": "Evidence agrees.",
            "knowledgeKind": "tradition",
            "recoveryHint": "",
        }
        cases: list[dict[str, object]] = []
        for value in (14, 31, 20.5, "20"):
            cases.append({
                "name": f"duration-{value}",
                "query": {**base, "storyDurationSeconds": value},
            })
        for field in (
            "spotId", "placeNameJa", "placeNameEn", "localityLabel",
            "memoryHook", "confidenceLabel", "evidenceNote", "recoveryHint",
        ):
            cases.append({
                "name": f"type-{field}",
                "query": {**base, field: 99},
            })
        for field, maximum in (
            ("spotId", 48),
            ("placeNameJa", 48),
            ("placeNameEn", 64),
            ("localityLabel", 48),
            ("memoryHook", 140),
            ("confidenceLabel", 64),
            ("evidenceNote", 160),
            ("recoveryHint", 160),
        ):
            for offset in (-1, 0, 1):
                cases.append({
                    "name": f"limit-{field}-{offset}",
                    "query": {**base, field: "𠮷" * (maximum + offset)},
                })
        results = {item["name"]: item["data"] for item in run_page_cases(cases)}
        for name, data in results.items():
            if name.endswith("--1") or name.endswith("-0"):
                self.assertEqual(data["status"], "matched", name)
            else:
                self.assertEqual(data["status"], "invalid", name)
                self.assertNotIn("99", json.dumps(data, ensure_ascii=False), name)
                self.assertNotIn("𠮷" * 49, json.dumps(data, ensure_ascii=False), name)

    def test_quiet_marker_has_target_aware_low_mass_ui(self) -> None:
        ink = read_example("pages/index/index.ink")
        page = extract_block(ink, r"<page\b[^>]*>(.*?)</page>", "page")
        style = extract_block(ink, r"<style>\s*(.*?)\s*</style>", "style")
        for fragment in (
            "KATARI / LOCAL MEMORY",
            "{{placeNameJa}}",
            "{{placeNameEn}}",
            "{{localityLabel}}",
            "LOCAL STORY · {{storyDurationSeconds}} SEC",
            "{{memoryHook}}",
            "{{confidenceLabel}}",
            "{{evidenceNote}}",
            "{{knowledgeLabel}}",
            "{{recoveryHint}}",
            'ink:if="{{showStoryMeta}}"',
            'ink:if="{{!showStoryMeta}}"',
        ):
            self.assertIn(fragment, page)
        self.assertIn("@media (target: _current)", style)
        self.assertIn("@media (target: _blank)", style)
        self.assertIn(".expanded-only { display: none; }", style)
        self.assertIn("background-color: #000000", style)
        self.assertIn("color: #72ff9e", style)
        self.assertIn("border-top: 1px solid", style)
        self.assertIn("border-radius: 6px", style)
        self.assertIn("padding: 30px 36px", style)
        self.assertNotIn("<button", page)
        self.assertNotIn("bindtap=", page)
        self.assertNotIn("onKeyUp", ink)
        self.assertNotIn("@keyframes", style)

    def test_capability_evaluation_records_fifteen_cases(self) -> None:
        report = (
            ROOT / "tests" / "evaluations" / "katari-capability.md"
        ).read_text(encoding="utf-8")
        cases = re.split(r"(?=^## Case: )", report, flags=re.MULTILINE)[1:]
        self.assertEqual(len(cases), 15)
        for case in cases:
            for label in (
                "- Input evidence:",
                "- Expected state:",
                "- Expected behavior:",
                "- Observed:",
                "- Result:",
                "- Evidence class:",
            ):
                self.assertIn(label, case)
            self.assertRegex(case, r"(?m)^- Result: (?:PASS|FAIL)$")
            self.assertIn(
                "- Evidence class: local prompt-contract evaluation", case
            )
        for state in (
            "matched", "uncertain", "no_story", "no_match", "invalid"
        ):
            self.assertIn(f"- Expected state: {state}", report)
        for fragment in (
            "Japanese",
            "English",
            "fact",
            "legend",
            "tradition",
            "GPS only",
            "vision only",
            "location/visual conflict",
            "look-alike",
            "retry exhaustion",
            "one bounded story",
            "route request",
            "not an authenticated Studio host",
        ):
            self.assertIn(fragment, report)

    def test_delivery_docs_and_ci_include_katari(self) -> None:
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        for fragment in (
            "KATARI Local Story Agent",
            "examples/katari-agent",
            "20 个",
            "15–30 秒",
            "katari-capability.md",
            "katari-ux.md",
            "Directory: examples/katari-agent",
            "codex/katari-agent",
        ):
            self.assertIn(fragment, readme)

        project = (ROOT / "PROJECT.md").read_text(encoding="utf-8")
        self.assertIn("`examples/katari-agent/`", project)
        self.assertIn("Page-only", project)
        self.assertIn("AIUI `0.17.0`", project)

        workflow = yaml.safe_load(
            (ROOT / ".github" / "workflows" / "ci.yml").read_text(
                encoding="utf-8"
            )
        )
        jobs = workflow["jobs"]

        def step_named(job: dict, name: str) -> dict:
            matches = [
                step for step in job["steps"] if step.get("name") == name
            ]
            self.assertEqual(len(matches), 1, name)
            return matches[0]

        validate = step_named(
            jobs["validate"], "Validate importable AIUI projects strictly"
        )
        self.assertIn(
            "python skills/rokid-aiui-agent/scripts/validate_aiui_project.py "
            "examples/katari-agent --target-version 0.17.0 --strict",
            validate["run"].splitlines(),
        )
        pack = step_named(
            jobs["aix-smoke"], "Pack and inspect stable AIUI projects"
        )
        self.assertIn(
            "bash skills/rokid-aiui-agent/scripts/smoke_aix.sh "
            "examples/katari-agent",
            pack["run"].splitlines(),
        )
        preview = step_named(
            jobs["aix-smoke"], "Generate the KATARI static preview"
        )
        self.assertEqual(preview["shell"], "bash")
        self.assertIn('"$AIX_BIN" --help', preview["run"])
        self.assertIn(
            '"$AIX_BIN" preview examples/katari-agent '
            '--html-out "$preview_html"',
            preview["run"],
        )
        self.assertIn('test -s "$preview_html"', preview["run"])
        self.assertIn(
            "grep -Fq 'pages/index/index.ink' \"$preview_html\"",
            preview["run"],
        )


if __name__ == "__main__":
    unittest.main()
