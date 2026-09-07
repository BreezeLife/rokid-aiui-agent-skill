from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILL_ROOT = ROOT / "skills" / "rokid-aiui-agent"
EXAMPLE = SKILL_ROOT / "assets" / "studio-importable-minimal"
VALIDATOR = SKILL_ROOT / "scripts" / "validate_aiui_project.py"


class StudioImportContractTests(unittest.TestCase):
    def test_example_root_has_manifest_entry_and_resolved_first_page(self) -> None:
        manifest_path = EXAMPLE / "app.json"
        self.assertTrue(manifest_path.is_file())
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        self.assertIsInstance(manifest.get("pages"), list)
        self.assertGreater(len(manifest["pages"]), 0)
        self.assertNotIn("widgets", manifest)
        self.assertNotIn("agentWorkers", manifest)
        first_route = manifest["pages"][0]
        self.assertTrue(
            (EXAMPLE / f"{first_route}.ink").is_file()
            or (EXAMPLE / f"{first_route}.wxml").is_file()
        )

    def test_example_passes_strict_project_validation(self) -> None:
        result = subprocess.run(
            [sys.executable, str(VALIDATOR), str(EXAMPLE), "--strict"],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(result.stdout, "")
        self.assertEqual(result.stderr, "")


if __name__ == "__main__":
    unittest.main()
