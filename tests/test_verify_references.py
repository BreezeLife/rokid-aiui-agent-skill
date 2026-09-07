import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "skills" / "rokid-aiui-agent" / "scripts" / "verify_references.py"


class ReferenceVerifierTests(unittest.TestCase):
    def run_verifier(self, files, *, outside_files=None, symlinks=None):
        with tempfile.TemporaryDirectory() as directory:
            container = Path(directory)
            root = container / "repository"
            root.mkdir()
            for relative, content in files.items():
                path = root / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(content, encoding="utf-8")
            for relative, content in (outside_files or {}).items():
                path = container / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(content, encoding="utf-8")
            for relative, target in (symlinks or {}).items():
                path = root / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.symlink_to(container / target)
            return subprocess.run(
                [sys.executable, str(SCRIPT), str(root), "--json"],
                capture_output=True,
                text=True,
                check=False,
            )

    def test_accepts_existing_local_links_and_commit_pinned_sources(self):
        result = self.run_verifier(
            {
                "README.md": "[Guide](references/guide.md)\n",
                "references/guide.md": (
                    "[Pinned](https://github.com/yodaos-project/AIUI/blob/"
                    "8b19a87b4ba8b486c0dd4dd3fd32290d27891069/README.md)\n"
                ),
            }
        )
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        self.assertEqual([], json.loads(result.stdout)["diagnostics"])

    def test_ignores_local_dependency_and_worktree_markdown(self):
        result = self.run_verifier(
            {
                "README.md": "[Guide](references/guide.md)\n",
                "references/guide.md": "Repository guide.\n",
                "node_modules/vendor/README.md": "[Missing](missing.md)\n",
                ".worktrees/feature/README.md": "[Missing](missing.md)\n",
            }
        )
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        self.assertEqual([], json.loads(result.stdout)["diagnostics"])

    def test_rejects_missing_local_link(self):
        result = self.run_verifier({"README.md": "[Missing](references/nope.md)\n"})
        self.assertEqual(1, result.returncode)
        self.assertIn("LOCAL_LINK_MISSING", result.stdout)

    def test_rejects_mutable_source_file_link(self):
        result = self.run_verifier(
            {
                "references/guide.md": (
                    "[Mutable](https://github.com/yodaos-project/AIUI/blob/"
                    "main/documentation/0-guide/structure.md)\n"
                )
            }
        )
        self.assertEqual(1, result.returncode)
        self.assertIn("SOURCE_LINK_UNPINNED", result.stdout)

    def test_stale_aix_site_only_allowed_as_labeled_history(self):
        stale = "https://jsar-project.github.io/aix/"
        rejected = self.run_verifier({"README.md": f"[AIX]({stale})\n"})
        self.assertEqual(1, rejected.returncode)
        self.assertIn("STALE_AIX_HOST", rejected.stdout)

        accepted = self.run_verifier(
            {
                "references/source-of-truth.md": (
                    f"Historical note: [{stale}]({stale}) is stale and must not be used.\n"
                )
            }
        )
        self.assertEqual(0, accepted.returncode, accepted.stdout + accepted.stderr)

        nested = self.run_verifier(
            {
                "skills/rokid-aiui-agent/references/source-of-truth.md": (
                    f"Historical note: [{stale}]({stale}) is stale and must not be used.\n"
                )
            }
        )
        self.assertEqual(0, nested.returncode, nested.stdout + nested.stderr)

    def test_stale_history_exception_requires_label_at_root_and_nested_paths(self):
        stale = "https://jsar-project.github.io/aix/"
        paths = (
            "references/source-of-truth.md",
            "skills/rokid-aiui-agent/references/source-of-truth.md",
        )
        for path in paths:
            with self.subTest(path=path):
                rejected = self.run_verifier({path: f"[AIX]({stale})\n"})
                self.assertEqual(1, rejected.returncode, rejected.stdout)
                self.assertIn("STALE_AIX_HOST", rejected.stdout)

                accepted = self.run_verifier(
                    {path: f"Historical note: [{stale}]({stale}) is stale.\n"}
                )
                self.assertEqual(0, accepted.returncode, accepted.stdout)

    def test_reference_style_definitions_are_checked(self):
        result = self.run_verifier(
            {
                "README.md": (
                    "[AIUI guide][aiui]\n"
                    "[Old AIX][aix]\n\n"
                    "[aiui]: https://github.com/yodaos-project/AIUI/blob/main/README.md\n"
                    "[aix]: https://jsar-project.github.io/aix/\n"
                )
            }
        )
        self.assertEqual(1, result.returncode, result.stdout)
        self.assertIn("SOURCE_LINK_UNPINNED", result.stdout)
        self.assertIn("STALE_AIX_HOST", result.stdout)

    def test_https_autolinks_are_checked(self):
        result = self.run_verifier(
            {
                "README.md": (
                    "<https://github.com/yodaos-project/aix/tree/main/packages/cli>\n"
                    "<https://jsar-project.github.io/aix/>\n"
                )
            }
        )
        self.assertEqual(1, result.returncode, result.stdout)
        self.assertIn("SOURCE_LINK_UNPINNED", result.stdout)
        self.assertIn("STALE_AIX_HOST", result.stdout)

    def test_rejects_existing_local_link_outside_scan_root(self):
        result = self.run_verifier(
            {"README.md": "[Outside](../outside.md)\n"},
            outside_files={"outside.md": "outside\n"},
        )
        self.assertEqual(1, result.returncode, result.stdout)
        self.assertIn("LOCAL_LINK_OUTSIDE_ROOT", result.stdout)

    def test_rejects_symlink_whose_target_is_outside_scan_root(self):
        result = self.run_verifier(
            {"README.md": "[Outside](linked.md)\n"},
            outside_files={"outside.md": "outside\n"},
            symlinks={"linked.md": "outside.md"},
        )
        self.assertEqual(1, result.returncode, result.stdout)
        self.assertIn("LOCAL_LINK_OUTSIDE_ROOT", result.stdout)

    def test_rejects_missing_or_non_directory_root(self):
        with tempfile.TemporaryDirectory() as directory:
            container = Path(directory)
            roots = (container / "missing", container / "file.md")
            roots[1].write_text("not a directory\n", encoding="utf-8")
            for root in roots:
                with self.subTest(root=root.name):
                    result = subprocess.run(
                        [sys.executable, str(SCRIPT), str(root), "--json"],
                        capture_output=True,
                        text=True,
                        check=False,
                    )
                    self.assertEqual(1, result.returncode, result.stdout)
                    self.assertIn("ROOT_NOT_DIRECTORY", result.stdout)


if __name__ == "__main__":
    unittest.main()
