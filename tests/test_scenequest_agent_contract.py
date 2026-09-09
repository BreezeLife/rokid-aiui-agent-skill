from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from datetime import date
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
        self.assertIn(
            "Candidate search areas are retrieval hints only, not hard match boundaries.",
            sources,
        )
        sections = re.split(r"(?=^## Spot: )", sources, flags=re.MULTILINE)[1:]
        labels = (
            "- Place:", "- Coordinates:", "- Location precision:",
            "- Work:", "- Media:", "- Episode/chapter/scene:",
            "- Story significance:", "- Visual anchors:",
            "- Photo position:", "- Safety:", "- Nearby spot IDs:",
            "- Sources:", "- Source class:", "- Verified:",
            "- Uncertainty:",
        )
        records: dict[str, dict[str, str]] = {}
        self.assertEqual(len(sections), len(ids))
        for spot_id, section in zip(ids, sections):
            fields: dict[str, str] = {}
            for label in labels:
                matches = re.findall(
                    rf"^{re.escape(label)}[ \t]*(.*)$", section, re.MULTILINE
                )
                self.assertEqual(len(matches), 1, f"{spot_id}: {label}")
                value = matches[0].strip()
                self.assertTrue(value, f"{spot_id}: empty {label}")
                fields[label] = value
            records[spot_id] = fields

            self.assertIn(fields["- Media:"], {"anime", "manga", "game"})
            coordinate_match = re.fullmatch(
                r"(-?\d+(?:\.\d+)?),\s*(-?\d+(?:\.\d+)?); "
                r"candidate search area ([1-9]\d*) m",
                fields["- Coordinates:"],
            )
            self.assertIsNotNone(coordinate_match, f"{spot_id}: coordinates")
            latitude, longitude, radius = coordinate_match.groups()
            self.assertGreaterEqual(float(latitude), -90)
            self.assertLessEqual(float(latitude), 90)
            self.assertGreaterEqual(float(longitude), -180)
            self.assertLessEqual(float(longitude), 180)
            self.assertGreater(int(radius), 0)
            self.assertIn(
                fields["- Location precision:"],
                {"landmark", "sub-area", "venue-wide"},
            )
            if fields["- Location precision:"] == "venue-wide":
                self.assertIn(
                    "一致判定の境界には使わない", fields["- Uncertainty:"]
                )

            source_tokens = [
                value.strip() for value in fields["- Sources:"].split(";")
            ]
            self.assertTrue(
                all(re.fullmatch(r"<https://[^>]+>", token) for token in source_tokens),
                f"{spot_id}: sources must be direct HTTPS URLs",
            )
            source_urls = [token[1:-1] for token in source_tokens]
            self.assertGreaterEqual(len(source_urls), 3, f"{spot_id}: sources")
            self.assertEqual(len(source_urls), len(set(source_urls)))
            source_class = fields["- Source class:"]
            self.assertIn("作品公式", source_class)
            self.assertIn("大阪観光局公式", source_class)
            self.assertRegex(
                source_class, r"(?:施設|公園|神社|設置者|事業者)公式"
            )
            self.assertIn("独立地図", source_class)

            try:
                verified = date.fromisoformat(fields["- Verified:"])
            except ValueError as error:
                self.fail(f"{spot_id}: invalid verification date: {error}")
            self.assertLessEqual(verified, date.today())
            self.assertIsNone(
                re.search(r"\b(?:TBD|TODO|unknown)\b", section, flags=re.I)
            )

        for spot_id, fields in records.items():
            nearby_ids = [
                value.strip()
                for value in fields["- Nearby spot IDs:"].split(",")
            ]
            self.assertGreaterEqual(len(nearby_ids), 1)
            self.assertLessEqual(len(nearby_ids), 3)
            self.assertEqual(len(nearby_ids), len(set(nearby_ids)))
            self.assertNotIn(spot_id, nearby_ids)
            for nearby_id in nearby_ids:
                self.assertIn(nearby_id, records)

        sennan = records["sennan-long-park-seaside"]
        self.assertEqual(sennan["- Location precision:"], "venue-wide")
        self.assertIn("フレーム照合済みのサブエリア", sennan["- Uncertainty:"])
