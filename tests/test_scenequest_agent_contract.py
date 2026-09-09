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
EXAMPLE = ROOT / "examples" / "scenequest-agent"
INK = EXAMPLE / "pages" / "index" / "index.ink"
VALIDATOR = ROOT / "skills" / "rokid-aiui-agent" / "scripts" / "validate_aiui_project.py"
SOURCE_SPOT = re.compile(r"^## Spot: ([a-z0-9-]+)$", re.MULTILINE)


def read_example(relative: str) -> str:
    path = EXAMPLE / relative
    if not path.is_file():
        raise AssertionError(f"missing SceneQuest file: {relative}")
    return path.read_text(encoding="utf-8")


class SceneQuestAgentContractTests(unittest.TestCase):
    def test_source_registry_has_twelve_complete_spots(self) -> None:
        sources = read_example("SOURCES.md")
        ids = SOURCE_SPOT.findall(sources)
        self.assertEqual(len(ids), 12)
        self.assertEqual(len(set(ids)), 12)
        sections = re.split(r"(?=^## Spot: )", sources, flags=re.MULTILINE)[1:]
        for section in sections:
            for label in (
                "- Place:", "- Coordinates:", "- Work:", "- Media:",
                "- Episode/chapter/scene:", "- Visual anchors:",
                "- Photo position:", "- Safety:", "- Sources:",
                "- Source class:", "- Verified:", "- Uncertainty:",
            ):
                self.assertIn(label, section)
            self.assertRegex(section, r"https://")
            self.assertRegex(section, r"- Verified: 2026-\d{2}-\d{2}")
            self.assertNotRegex(section, r"\b(?:TBD|TODO|unknown)\b")
