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
    def run_script(
        self, project: Path, repository_root: Path | None = None
    ) -> subprocess.CompletedProcess[str]:
        arguments = [sys.executable, str(SCRIPT), str(project)]
        if repository_root is not None:
            arguments.extend(["--repository-root", str(repository_root)])
        return subprocess.run(
            arguments,
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )

    def initialize_git_repository(self, repository: Path) -> None:
        result = subprocess.run(
            ["git", "init", "--quiet", str(repository)],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(0, result.returncode, result.stderr)

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

    def test_explicit_non_git_repository_root_excludes_only_reserved_directories(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            project = Path(temporary_directory) / "repository"
            project.mkdir()
            (project / "app.json").write_text('{"pages":[]}\n', encoding="utf-8")
            before = self.run_script(project, project)
            self.assertEqual(0, before.returncode, before.stderr)

            audit_root = project / ".aiui-evidence"
            audit_root.mkdir()
            (audit_root / "capture.json").write_text("first\n", encoding="utf-8")
            (audit_root / "runner.log").write_text("passed\n", encoding="utf-8")
            (audit_root / "preview.png").write_bytes(b"image evidence")
            git_root = project / ".git"
            git_root.mkdir()
            (git_root / "metadata").write_text("repository metadata\n", encoding="utf-8")
            after_reserved = self.run_script(project, project)
            self.assertEqual(before.stdout, after_reserved.stdout)

            (project / ".DS_Store").write_bytes(b"ignored-by-git-but-imported")
            after_ignored_file = self.run_script(project, project)
            self.assertNotEqual(before.stdout, after_ignored_file.stdout)

    def test_reserved_evidence_rejects_aiui_runtime_source(self) -> None:
        for suffix in (".ink", ".js", ".ts", ".wxml", ".wxss"):
            with self.subTest(suffix=suffix), tempfile.TemporaryDirectory() as directory:
                project = Path(directory) / "repository"
                evidence = project / ".aiui-evidence" / "nested"
                evidence.mkdir(parents=True)
                (project / "app.json").write_text(
                    '{"pages":[]}\n', encoding="utf-8"
                )
                (evidence / f"hidden{suffix}").write_text(
                    "export default {};\n", encoding="utf-8"
                )

                result = self.run_script(project, project)
                self.assertNotEqual(0, result.returncode)
                self.assertIn("runtime source", result.stderr.lower())

    def test_mixed_case_reserved_evidence_rejects_aiui_runtime_source(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory) / "repository"
            evidence = project / ".AIUI-EVIDENCE" / "nested"
            evidence.mkdir(parents=True)
            (project / "app.json").write_text('{"pages":[]}\n', encoding="utf-8")
            (evidence / "hidden.js").write_text(
                "export default {};\n", encoding="utf-8"
            )

            result = self.run_script(project, project)

            self.assertNotEqual(0, result.returncode)
            self.assertIn("runtime source", result.stderr.lower())

    def test_reserved_evidence_rejects_symlinks(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            project = Path(temporary_directory) / "repository"
            evidence = project / ".aiui-evidence"
            evidence.mkdir(parents=True)
            (project / "app.json").write_text('{"pages":[]}\n', encoding="utf-8")
            outside = Path(temporary_directory) / "outside.log"
            outside.write_text("external evidence\n", encoding="utf-8")
            (evidence / "capture.log").symlink_to(outside)

            result = self.run_script(project, project)
            self.assertNotEqual(0, result.returncode)
            self.assertIn("symlink", result.stderr.lower())

    def test_reserved_evidence_root_must_be_a_directory(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            project = Path(temporary_directory) / "repository"
            project.mkdir()
            (project / "app.json").write_text('{"pages":[]}\n', encoding="utf-8")
            (project / ".aiui-evidence").write_text(
                "this ordinary file must not disappear from the fingerprint\n",
                encoding="utf-8",
            )

            result = self.run_script(project, project)

            self.assertNotEqual(0, result.returncode)
            self.assertIn("directory", result.stderr.lower())

    def test_nested_import_rejects_repository_evidence_root_symlink(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            repository = Path(temporary_directory) / "repository"
            project = repository / "examples" / "agent"
            project.mkdir(parents=True)
            (project / "app.json").write_text('{"pages":[]}\n', encoding="utf-8")
            outside = Path(temporary_directory) / "outside-evidence"
            outside.mkdir()
            (repository / ".aiui-evidence").symlink_to(outside, target_is_directory=True)

            result = self.run_script(project, repository)

            self.assertNotEqual(0, result.returncode)
            self.assertIn("symlink", result.stderr.lower())

    def test_nested_import_rejects_runtime_source_in_repository_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            repository = Path(temporary_directory) / "repository"
            project = repository / "examples" / "agent"
            project.mkdir(parents=True)
            (project / "app.json").write_text('{"pages":[]}\n', encoding="utf-8")
            evidence_source = repository / ".AIUI-EVIDENCE" / "nested" / "hidden.js"
            evidence_source.parent.mkdir(parents=True)
            evidence_source.write_text("export default {};\n", encoding="utf-8")

            result = self.run_script(project, repository)

            self.assertNotEqual(0, result.returncode)
            self.assertIn("runtime source", result.stderr.lower())

    def test_nested_import_root_fingerprints_same_named_evidence_directory(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            repository = Path(temporary_directory) / "repository"
            project = repository / "examples" / "agent"
            project.mkdir(parents=True)
            (project / "app.json").write_text('{"pages":[]}\n', encoding="utf-8")
            before = self.run_script(project, repository)
            self.assertEqual(0, before.returncode, before.stderr)

            hidden_source = project / ".aiui-evidence" / "hidden.js"
            hidden_source.parent.mkdir()
            hidden_source.write_text("export default { hidden: true };\n", encoding="utf-8")
            after = self.run_script(project, repository)
            self.assertEqual(0, after.returncode, after.stderr)
            self.assertNotEqual(before.stdout, after.stdout)

    def test_nested_git_import_root_fingerprints_same_named_evidence_directory(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            repository = Path(temporary_directory) / "repository"
            project = repository / "examples" / "agent"
            project.mkdir(parents=True)
            self.initialize_git_repository(repository)
            self.initialize_git_repository(project)
            (project / "app.json").write_text('{"pages":[]}\n', encoding="utf-8")
            before = self.run_script(project, repository)
            self.assertEqual(0, before.returncode, before.stderr)

            hidden_source = project / ".aiui-evidence" / "hidden.js"
            hidden_source.parent.mkdir()
            hidden_source.write_text("export default { hidden: true };\n", encoding="utf-8")
            after = self.run_script(project, repository)
            self.assertEqual(0, after.returncode, after.stderr)
            self.assertNotEqual(before.stdout, after.stdout)

    def test_import_root_inside_reserved_repository_directory_is_rejected(self) -> None:
        for reserved in (".git", ".Git", ".aiui-evidence", ".AIUI-EVIDENCE"):
            with self.subTest(reserved=reserved), tempfile.TemporaryDirectory() as directory:
                repository = Path(directory) / "repository"
                project = repository / reserved / "project"
                project.mkdir(parents=True)
                (project / "app.json").write_text(
                    '{"pages":[]}\n', encoding="utf-8"
                )

                result = self.run_script(project, repository)

                self.assertNotEqual(0, result.returncode)
                self.assertIn("reserved", result.stderr.lower())

    def test_without_repository_root_fingerprints_reserved_directories(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            project = Path(temporary_directory) / "project"
            project.mkdir()
            self.initialize_git_repository(project)
            (project / "app.json").write_text('{"pages":[]}\n', encoding="utf-8")
            before = self.run_script(project)
            self.assertEqual(0, before.returncode, before.stderr)

            evidence = project / ".aiui-evidence"
            evidence.mkdir()
            (evidence / "capture.json").write_text("captured\n", encoding="utf-8")
            after = self.run_script(project)
            self.assertEqual(0, after.returncode, after.stderr)
            self.assertNotEqual(before.stdout, after.stdout)

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
