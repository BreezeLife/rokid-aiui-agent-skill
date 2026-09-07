from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
VALIDATOR = ROOT / "skills" / "rokid-aiui-agent" / "scripts" / "validate_aiui_project.py"
FIXTURES = Path(__file__).resolve().parent / "fixtures"


def run_validator(project: Path, *options: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(VALIDATOR), str(project), *options],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )


def diagnostic_codes(result: subprocess.CompletedProcess[str]) -> list[str]:
    payload = json.loads(result.stdout)
    return [diagnostic["code"] for diagnostic in payload["diagnostics"]]


class ValidatorFixtureTests(unittest.TestCase):
    def test_valid_minimal_project_passes_without_diagnostics(self) -> None:
        result = run_validator(FIXTURES / "valid-minimal")

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(result.stdout, "")
        self.assertEqual(result.stderr, "")

    def test_valid_widget_and_worker_project_passes(self) -> None:
        result = run_validator(
            FIXTURES / "valid-widget-worker",
            "--target-version",
            "0.18.0",
            "--json",
        )

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        payload = json.loads(result.stdout)
        self.assertTrue(payload["valid"])
        self.assertEqual(payload["errorCount"], 0)
        self.assertEqual(payload["warningCount"], 0)
        self.assertEqual(payload["diagnostics"], [])
        self.assertEqual(payload["targetVersion"], "0.18.0")

    def test_default_stable_target_rejects_preview_only_entries(self) -> None:
        result = run_validator(FIXTURES / "valid-widget-worker", "--json")

        self.assertEqual(result.returncode, 1)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["targetVersion"], "0.17.0")
        self.assertTrue(
            {
                "WIDGETS_UNSUPPORTED_TARGET",
                "AGENT_WORKERS_UNSUPPORTED_TARGET",
            }.issubset(set(diagnostic_codes(result)))
        )

    def test_missing_declared_route_is_an_error(self) -> None:
        result = run_validator(FIXTURES / "invalid-missing-route", "--json")

        self.assertEqual(result.returncode, 1)
        self.assertIn("PAGE_ROUTE_NOT_FOUND", diagnostic_codes(result))

    def test_invalid_ink_blocks_are_reported(self) -> None:
        result = run_validator(FIXTURES / "invalid-ink-blocks", "--json")

        self.assertEqual(result.returncode, 1)
        codes = set(diagnostic_codes(result))
        self.assertTrue(
            {
                "PAGE_ROOT_COUNT",
                "PAGE_HAS_WIDGET_ROOT",
                "INK_DUPLICATE_SCRIPT_DEF",
                "INK_DUPLICATE_SCRIPT_SETUP",
                "INK_DUPLICATE_STYLE",
                "INK_DEF_MALFORMED",
                "INK_DEF_NOT_OBJECT",
            }.issubset(codes),
            codes,
        )

    def test_invalid_widget_and_worker_manifests_are_reported(self) -> None:
        result = run_validator(
            FIXTURES / "invalid-manifest",
            "--target-version",
            "0.18.0",
            "--json",
        )

        self.assertEqual(result.returncode, 1)
        codes = set(diagnostic_codes(result))
        expected = {
            "WIDGET_ENTRY_NOT_OBJECT",
            "WIDGET_PATH_UNSAFE",
            "WIDGET_FAMILY_INVALID",
            "WIDGET_NOT_FOUND",
            "WIDGET_ROOT_COUNT",
            "WIDGET_HAS_PAGE_ROOT",
            "WIDGET_DEF_FAMILY_MISMATCH",
            "WORKER_ENTRY_NOT_OBJECT",
            "WORKER_NAME_INVALID",
            "WORKER_NAME_DUPLICATE",
            "WORKER_SCRIPT_UNSAFE",
            "WORKER_SCRIPT_EXTENSION",
            "WORKER_SCRIPT_NOT_FOUND",
            "WORKER_TRIGGER_INVALID",
            "WORKER_LIFETIME_INVALID",
            "WORKER_CAPABILITIES_NOT_LIST",
            "WORKER_CAPABILITY_UNSUPPORTED",
            "WORKER_OPEN_LIMIT",
            "WORKER_BLUETOOTH_REQUIRES_FOREGROUND",
        }
        self.assertTrue(expected.issubset(codes), expected - codes)

    def test_mixed_mode_warnings_pass_normally_and_fail_strict(self) -> None:
        project = FIXTURES / "warning-mixed-mode"

        normal = run_validator(project)
        strict = run_validator(project, "--strict")
        strict_json = run_validator(project, "--strict", "--json")

        self.assertEqual(normal.returncode, 0, normal.stdout + normal.stderr)
        self.assertEqual(strict.returncode, 1)
        self.assertEqual(strict_json.returncode, 1)
        self.assertRegex(
            normal.stdout.splitlines()[0],
            r"^WARNING [A-Z0-9_]+ [^:]+: .+$",
        )
        codes = set(diagnostic_codes(strict_json))
        self.assertTrue(
            {
                "MIXED_PAGE_DEFINITION",
                "MIXED_AUTHORING_MODES",
                "RESERVED_PACKAGE_PATH",
            }.issubset(codes),
            codes,
        )


class ValidatorGeneratedProjectTests(unittest.TestCase):
    def make_project(self) -> tempfile.TemporaryDirectory[str]:
        return tempfile.TemporaryDirectory(prefix="aiui-validator-")

    @staticmethod
    def write_support_files(project: Path) -> None:
        (project / "AGENTS.md").write_text("# Agent\n", encoding="utf-8")
        (project / "app.js").write_text("export default {};\n", encoding="utf-8")

    @staticmethod
    def write_page(project: Path, route: str = "pages/index/index") -> None:
        page = project / f"{route}.ink"
        page.parent.mkdir(parents=True, exist_ok=True)
        page.write_text("<page><view>OK</view></page>\n", encoding="utf-8")

    def assert_json_error(self, project: Path, code: str) -> None:
        result = run_validator(project, "--json")
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn(code, diagnostic_codes(result))

    def test_app_json_missing_malformed_and_non_object_are_errors(self) -> None:
        cases = (
            (None, "APP_JSON_MISSING"),
            ("{broken", "APP_JSON_MALFORMED"),
            ("[]", "APP_JSON_NOT_OBJECT"),
        )
        for content, code in cases:
            with self.subTest(code=code), self.make_project() as directory:
                project = Path(directory)
                self.write_support_files(project)
                if content is not None:
                    (project / "app.json").write_text(content, encoding="utf-8")
                self.assert_json_error(project, code)

    def test_pages_manifest_shape_and_duplicate_routes_are_errors(self) -> None:
        cases = (
            ({}, "PAGES_MISSING"),
            ({"pages": "pages/index/index"}, "PAGES_NOT_LIST"),
            ({"pages": []}, "PAGES_EMPTY"),
            ({"pages": [7]}, "PAGE_ROUTE_NOT_STRING"),
            (
                {"pages": ["pages/index/index", "pages/index/index"]},
                "PAGE_ROUTE_DUPLICATE",
            ),
        )
        for manifest, code in cases:
            with self.subTest(code=code), self.make_project() as directory:
                project = Path(directory)
                self.write_support_files(project)
                self.write_page(project)
                (project / "app.json").write_text(json.dumps(manifest), encoding="utf-8")
                self.assert_json_error(project, code)

    def test_unsafe_page_routes_are_rejected(self) -> None:
        with self.make_project() as directory:
            project = Path(directory)
            self.write_support_files(project)
            manifest = {
                "pages": [
                    "/absolute/page",
                    "pages\\windows\\page",
                    "pages/./dot/page",
                    "pages/../parent/page",
                ]
            }
            (project / "app.json").write_text(json.dumps(manifest), encoding="utf-8")

            result = run_validator(project, "--json")

            self.assertEqual(result.returncode, 1)
            self.assertGreaterEqual(diagnostic_codes(result).count("PAGE_ROUTE_UNSAFE"), 4)

    def test_widget_and_worker_collections_must_be_lists(self) -> None:
        with self.make_project() as directory:
            project = Path(directory)
            self.write_support_files(project)
            self.write_page(project)
            manifest = {
                "pages": ["pages/index/index"],
                "widgets": {},
                "agentWorkers": {},
            }
            (project / "app.json").write_text(json.dumps(manifest), encoding="utf-8")

            result = run_validator(project, "--json")

            self.assertEqual(result.returncode, 1)
            self.assertIn("WIDGETS_NOT_LIST", diagnostic_codes(result))
            self.assertIn("AGENT_WORKERS_NOT_LIST", diagnostic_codes(result))

    def test_missing_agents_and_application_entry_are_warnings(self) -> None:
        with self.make_project() as directory:
            project = Path(directory)
            self.write_page(project)
            (project / "app.json").write_text(
                json.dumps({"pages": ["pages/index/index"]}), encoding="utf-8"
            )

            normal = run_validator(project, "--json")
            strict = run_validator(project, "--strict", "--json")

            self.assertEqual(normal.returncode, 0)
            self.assertEqual(strict.returncode, 1)
            self.assertEqual(
                set(diagnostic_codes(normal)),
                {"AGENTS_MD_MISSING", "APP_ENTRY_MISSING"},
            )

    def test_app_ink_is_a_supported_application_entry(self) -> None:
        with self.make_project() as directory:
            project = Path(directory)
            (project / "AGENTS.md").write_text("# Agent\n", encoding="utf-8")
            (project / "app.ink").write_text(
                "<script setup>export default {};</script>\n", encoding="utf-8"
            )
            self.write_page(project)
            (project / "app.json").write_text(
                json.dumps({"pages": ["pages/index/index"]}), encoding="utf-8"
            )

            result = run_validator(project, "--strict", "--json")

            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertEqual(diagnostic_codes(result), [])

    def test_empty_or_unclosed_app_ink_fails_strict_delivery_validation(self) -> None:
        for content in ("\n", "<script setup>export default {};\n"):
            with self.subTest(content=content), self.make_project() as directory:
                project = Path(directory)
                (project / "AGENTS.md").write_text("# Agent\n", encoding="utf-8")
                (project / "app.ink").write_text(content, encoding="utf-8")
                self.write_page(project)
                (project / "app.json").write_text(
                    json.dumps({"pages": ["pages/index/index"]}), encoding="utf-8"
                )

                result = run_validator(project, "--strict", "--json")

                self.assertEqual(result.returncode, 1)
                self.assertIn("APP_ENTRY_INVALID", diagnostic_codes(result))

    def test_app_ink_requires_a_nonempty_setup_logic_block(self) -> None:
        cases = (
            "<script def>{}</script>\n",
            "<script setup>   </script>\n",
            "<script unknown>export default {};</script>\n",
        )
        for content in cases:
            with self.subTest(content=content), self.make_project() as directory:
                project = Path(directory)
                (project / "AGENTS.md").write_text("# Agent\n", encoding="utf-8")
                (project / "app.ink").write_text(content, encoding="utf-8")
                self.write_page(project)
                (project / "app.json").write_text(
                    json.dumps({"pages": ["pages/index/index"]}), encoding="utf-8"
                )

                result = run_validator(project, "--strict", "--json")

                self.assertEqual(result.returncode, 1)
                self.assertIn("APP_ENTRY_INVALID", diagnostic_codes(result))

    def test_empty_wxml_page_is_an_error(self) -> None:
        with self.make_project() as directory:
            project = Path(directory)
            self.write_support_files(project)
            page = project / "pages" / "index" / "index.wxml"
            page.parent.mkdir(parents=True, exist_ok=True)
            page.write_text(" \n", encoding="utf-8")
            (project / "app.json").write_text(
                json.dumps({"pages": ["pages/index/index"]}), encoding="utf-8"
            )

            result = run_validator(project, "--strict", "--json")

            self.assertEqual(result.returncode, 1)
            self.assertIn("WXML_EMPTY", diagnostic_codes(result))

    def test_malformed_ink_tag_nesting_is_an_error(self) -> None:
        cases = (
            "<page><view>broken</page>",
            "</page><page>",
        )
        for content in cases:
            with self.subTest(content=content), self.make_project() as directory:
                project = Path(directory)
                self.write_support_files(project)
                page = project / "pages" / "index" / "index.ink"
                page.parent.mkdir(parents=True, exist_ok=True)
                page.write_text(content, encoding="utf-8")
                (project / "app.json").write_text(
                    json.dumps({"pages": ["pages/index/index"]}), encoding="utf-8"
                )

                result = run_validator(project, "--json")

                self.assertEqual(result.returncode, 1)
                self.assertIn("INK_MARKUP_INVALID", diagnostic_codes(result))

    def test_malformed_wxml_tag_nesting_is_an_error(self) -> None:
        with self.make_project() as directory:
            project = Path(directory)
            self.write_support_files(project)
            page = project / "pages" / "index" / "index.wxml"
            page.parent.mkdir(parents=True, exist_ok=True)
            page.write_text("<view><text>broken</view>", encoding="utf-8")
            (project / "app.json").write_text(
                json.dumps({"pages": ["pages/index/index"]}), encoding="utf-8"
            )

            result = run_validator(project, "--json")

            self.assertEqual(result.returncode, 1)
            self.assertIn("WXML_MARKUP_INVALID", diagnostic_codes(result))

    def test_widget_requires_matching_family_in_script_def(self) -> None:
        with self.make_project() as directory:
            project = Path(directory)
            self.write_support_files(project)
            self.write_page(project)
            widget = project / "widgets" / "status" / "index.ink"
            widget.parent.mkdir(parents=True, exist_ok=True)
            widget.write_text(
                "<script setup>export default {};</script>\n"
                "<widget><text>Ready</text></widget>\n",
                encoding="utf-8",
            )
            (project / "app.json").write_text(
                json.dumps(
                    {
                        "pages": ["pages/index/index"],
                        "widgets": [
                            {"path": "widgets/status/index", "family": "1x1"}
                        ],
                    }
                ),
                encoding="utf-8",
            )

            result = run_validator(
                project, "--target-version", "0.18.0", "--strict", "--json"
            )

            self.assertEqual(result.returncode, 1)
            self.assertIn("WIDGET_DEF_FAMILY_MISSING", diagnostic_codes(result))

    def test_unclosed_ink_setup_style_and_page_root_are_errors(self) -> None:
        cases = (
            (
                "<script setup>export default {};\n<page></page>\n",
                "INK_SETUP_UNCLOSED",
            ),
            ("<page></page>\n<style>.x { color: green; }\n", "INK_STYLE_UNCLOSED"),
            ("<page><view>Open</view>\n", "PAGE_ROOT_UNBALANCED"),
        )
        for content, code in cases:
            with self.subTest(code=code), self.make_project() as directory:
                project = Path(directory)
                self.write_support_files(project)
                page = project / "pages" / "index" / "index.ink"
                page.parent.mkdir(parents=True, exist_ok=True)
                page.write_text(content, encoding="utf-8")
                (project / "app.json").write_text(
                    json.dumps({"pages": ["pages/index/index"]}), encoding="utf-8"
                )

                result = run_validator(project, "--json")

                self.assertEqual(result.returncode, 1)
                self.assertIn(code, diagnostic_codes(result))

    def test_unregistered_page_files_are_not_validated(self) -> None:
        with self.make_project() as directory:
            project = Path(directory)
            self.write_support_files(project)
            self.write_page(project)
            unregistered = project / "pages" / "unused" / "index.ink"
            unregistered.parent.mkdir(parents=True)
            unregistered.write_text("<page></page><page></page>", encoding="utf-8")
            (project / "app.json").write_text(
                json.dumps({"pages": ["pages/index/index"]}), encoding="utf-8"
            )

            result = run_validator(project, "--strict", "--json")

            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertEqual(diagnostic_codes(result), [])


if __name__ == "__main__":
    unittest.main()
