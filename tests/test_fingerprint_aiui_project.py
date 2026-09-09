from __future__ import annotations

import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = (
    ROOT
    / "skills"
    / "rokid-aiui-agent"
    / "scripts"
    / "fingerprint_aiui_project.py"
)


class FingerprintAiuiProjectTests(unittest.TestCase):
    def run_script(self, project: Path) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(SCRIPT), str(project)],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )

    def test_fingerprint_is_deterministic_and_content_bound(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            project = Path(temporary_directory)
            (project / "pages" / "index").mkdir(parents=True)
            (project / "app.json").write_text(
                '{"pages":["pages/index/index"]}\n', encoding="utf-8"
            )
            page = project / "pages" / "index" / "index.ink"
            page.write_text("export default {}\n", encoding="utf-8")

            first = self.run_script(project)
            second = self.run_script(project)
            self.assertEqual(0, first.returncode, first.stderr)
            self.assertEqual(first.stdout, second.stdout)
            self.assertRegex(first.stdout.strip(), r"^WORKTREE:[0-9a-f]{64}$")

            page.write_text("export default { changed: true }\n", encoding="utf-8")
            changed = self.run_script(project)
            self.assertEqual(0, changed.returncode, changed.stderr)
            self.assertNotEqual(first.stdout, changed.stdout)

    def test_fingerprint_rejects_symlinks_and_non_directories(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            project = Path(temporary_directory) / "project"
            project.mkdir()
            outside = Path(temporary_directory) / "outside.txt"
            outside.write_text("outside\n", encoding="utf-8")
            (project / "escape.txt").symlink_to(outside)
            escaped = self.run_script(project)
            self.assertNotEqual(0, escaped.returncode)
            self.assertIn("symlink", escaped.stderr.lower())

            regular_file = self.run_script(outside)
            self.assertNotEqual(0, regular_file.returncode)
            self.assertIn("directory", regular_file.stderr.lower())

    def test_fingerprint_excludes_only_reserved_audit_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            project = Path(temporary_directory)
            (project / "app.json").write_text('{"pages":[]}\n', encoding="utf-8")
            before = self.run_script(project)
            self.assertEqual(0, before.returncode, before.stderr)

            audit_root = project / ".aiui-evidence"
            audit_root.mkdir()
            (audit_root / "capture.json").write_text("first\n", encoding="utf-8")
            after_audit = self.run_script(project)
            self.assertEqual(before.stdout, after_audit.stdout)

            (project / ".DS_Store").write_bytes(b"ignored-by-git-but-imported")
            after_ignored_file = self.run_script(project)
            self.assertNotEqual(before.stdout, after_ignored_file.stdout)

    def test_help_documents_the_fingerprint_format(self) -> None:
        result = subprocess.run(
            [sys.executable, str(SCRIPT), "--help"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertIn("WORKTREE:", result.stdout)
        self.assertIsNotNone(re.search(r"SHA-?256", result.stdout, flags=re.I))


if __name__ == "__main__":
    unittest.main()
