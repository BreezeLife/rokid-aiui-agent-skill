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


if __name__ == "__main__":
    unittest.main()
