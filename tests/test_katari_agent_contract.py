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


if __name__ == "__main__":
    unittest.main()
