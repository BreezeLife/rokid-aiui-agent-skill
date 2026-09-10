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

    def test_project_root_inside_reserved_directory_is_rejected(self) -> None:
        for reserved in (".git", ".Git", ".aiui-evidence", ".AIUI-EVIDENCE"):
            with self.subTest(reserved=reserved), self.make_project() as directory:
                project = Path(directory) / reserved / "project"
                project.mkdir(parents=True)
                self.write_support_files(project)
                (project / "app.json").write_text(
                    '{"pages":["pages/index/index"]}\n', encoding="utf-8"
                )
                self.write_page(project)

                self.assert_json_error(project, "RESERVED_PROJECT_ROOT")

    def test_explicit_repository_root_reserves_only_its_top_level_aliases(self) -> None:
        with self.make_project() as directory:
            repository = Path(directory) / "repository"
            project = repository / "examples" / "agent"
            project.mkdir(parents=True)
            self.write_support_files(project)
            nested_page = project / ".aiui-evidence" / "index.ink"
            nested_page.parent.mkdir()
            nested_page.write_text(
                "<page><view>Nested source</view></page>\n", encoding="utf-8"
            )
            (project / "app.json").write_text(
                json.dumps({"pages": [".aiui-evidence/index"]}),
                encoding="utf-8",
            )

            result = run_validator(
                project,
                "--repository-root",
                str(repository),
                "--strict",
                "--json",
            )

            self.assertEqual(0, result.returncode, result.stdout + result.stderr)

            repository_evidence = repository / ".AIUI-EVIDENCE"
            repository_evidence.mkdir()
            secret = repository_evidence / "secret.json"
            secret.write_text('{"secret":true}\n', encoding="utf-8")
            (project / "app.js").write_text(
                f"const secret = {json.dumps(str(secret))};\nexport default {{}};\n",
                encoding="utf-8",
            )
            absolute_runtime_reference = run_validator(
                project,
                "--repository-root",
                str(repository),
                "--strict",
                "--json",
            )
            self.assertEqual(1, absolute_runtime_reference.returncode)
            self.assertIn(
                "RESERVED_AUDIT_REFERENCE",
                diagnostic_codes(absolute_runtime_reference),
            )

            self.write_support_files(project)
            (project / "app.json").write_text(
                json.dumps(
                    {
                        "pages": [".aiui-evidence/index"],
                        "auditConfig": str(secret),
                    }
                ),
                encoding="utf-8",
            )
            absolute_manifest_reference = run_validator(
                project,
                "--repository-root",
                str(repository),
                "--strict",
                "--json",
            )
            self.assertEqual(1, absolute_manifest_reference.returncode)
            self.assertIn(
                "RESERVED_AUDIT_REFERENCE",
                diagnostic_codes(absolute_manifest_reference),
            )

            (project / "app.json").write_text(
                json.dumps({"pages": [".aiui-evidence/index"]}),
                encoding="utf-8",
            )
            (repository_evidence / "hidden.js").write_text(
                "export default {};\n", encoding="utf-8"
            )
            rejected = run_validator(
                project,
                "--repository-root",
                str(repository),
                "--strict",
                "--json",
            )
            self.assertEqual(1, rejected.returncode)
            self.assertIn("RESERVED_AUDIT_SOURCE", diagnostic_codes(rejected))

    def test_static_absolute_evidence_path_composition_is_rejected(self) -> None:
        with self.make_project() as directory:
            repository = Path(directory) / "repository with spaces"
            project = repository / "examples" / "agent"
            project.mkdir(parents=True)
            self.write_support_files(project)
            self.write_page(project)
            (project / "app.json").write_text(
                json.dumps({"pages": ["pages/index/index"]}), encoding="utf-8"
            )
            evidence = repository / ".aiui-evidence"
            evidence.mkdir()
            absolute_prefix = str(repository) + "/"
            sources = (
                "const path = "
                + json.dumps(absolute_prefix)
                + " + '.aiui-' + 'evidence/device proof.json';\n"
                + "export default {};\n",
                "const path = `${("
                + json.dumps(str(repository))
                + ")}/.aiui-evidence/device proof.json`;\n"
                + "export default {};\n",
                "const path = `${"
                + json.dumps(absolute_prefix)
                + " + ''}.aiui-evidence/device proof.json`;\n"
                + "export default {};\n",
            )

            for source in sources:
                with self.subTest(source=source.splitlines()[0]):
                    (project / "app.js").write_text(source, encoding="utf-8")
                    result = run_validator(
                        project,
                        "--repository-root",
                        str(repository),
                        "--strict",
                        "--json",
                    )
                    self.assertEqual(1, result.returncode)
                    self.assertIn(
                        "RESERVED_AUDIT_REFERENCE", diagnostic_codes(result)
                    )

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
                    ".aiui-evidence/page",
                    ".git/page",
                    ".Git/page",
                    "pages/.aiui-evidence/page",
                    "pages/.AIUI-EVIDENCE/page",
                ]
            }
            (project / "app.json").write_text(json.dumps(manifest), encoding="utf-8")

            result = run_validator(project, "--json")

            self.assertEqual(result.returncode, 1)
            codes = diagnostic_codes(result)
            self.assertEqual(7, codes.count("PAGE_ROUTE_UNSAFE"))
            self.assertEqual(2, codes.count("PAGE_ROUTE_NOT_FOUND"))

    def test_audit_evidence_directory_cannot_carry_runtime_source(self) -> None:
        with self.make_project() as directory:
            project = Path(directory)
            self.write_support_files(project)
            self.write_page(project)
            (project / "app.json").write_text(
                json.dumps({"pages": ["pages/index/index"]}), encoding="utf-8"
            )
            evidence_source = project / ".aiui-evidence" / "hidden.js"
            evidence_source.parent.mkdir()
            evidence_source.write_text(
                "fetch('https://example.invalid');\n", encoding="utf-8"
            )

            result = run_validator(project, "--json")

            self.assertEqual(result.returncode, 1)
            self.assertIn("RESERVED_AUDIT_SOURCE", diagnostic_codes(result))

            evidence_source.unlink()
            (evidence_source.parent / "config.json").write_text(
                '{"endpoint":"https://example.invalid"}\n', encoding="utf-8"
            )
            page = project / "pages/index/index.ink"
            page.write_text(
                "<page><view>OK</view><script>"
                "const config = '.aiui-evidence/config.json';"
                "</script></page>\n",
                encoding="utf-8",
            )

            referenced = run_validator(project, "--json")
            self.assertEqual(referenced.returncode, 1)
            self.assertIn("RESERVED_AUDIT_REFERENCE", diagnostic_codes(referenced))

            self.write_page(project)
            (project / "app.json").write_text(
                json.dumps(
                    {
                        "pages": ["pages/index/index"],
                        "usingComponents": {
                            "hidden": ".aiui-evidence/components/hidden"
                        },
                    }
                ),
                encoding="utf-8",
            )
            manifest_reference = run_validator(project, "--json")
            self.assertEqual(manifest_reference.returncode, 1)
            self.assertIn(
                "RESERVED_AUDIT_REFERENCE", diagnostic_codes(manifest_reference)
            )

            self.write_page(project)
            (project / "app.json").write_text(
                json.dumps(
                    {
                        "pages": ["pages/index/index"],
                        "usingComponents": {
                            "hidden": ".AIUI-EVIDENCE/components/hidden"
                        },
                    }
                ),
                encoding="utf-8",
            )
            mixed_case_reference = run_validator(project, "--json")
            self.assertEqual(mixed_case_reference.returncode, 1)
            self.assertIn(
                "RESERVED_AUDIT_REFERENCE", diagnostic_codes(mixed_case_reference)
            )

    def test_audit_evidence_root_cannot_be_a_symlink(self) -> None:
        with self.make_project() as directory:
            project = Path(directory) / "project"
            project.mkdir()
            self.write_support_files(project)
            self.write_page(project)
            (project / "app.json").write_text(
                json.dumps({"pages": ["pages/index/index"]}), encoding="utf-8"
            )
            outside = Path(directory) / "external-evidence"
            outside.mkdir()
            (project / ".aiui-evidence").symlink_to(outside, target_is_directory=True)

            result = run_validator(project, "--json")

            self.assertEqual(result.returncode, 1)
            self.assertIn("RESERVED_AUDIT_SOURCE", diagnostic_codes(result))

    def test_audit_evidence_root_must_be_a_directory(self) -> None:
        with self.make_project() as directory:
            project = Path(directory)
            self.write_support_files(project)
            self.write_page(project)
            (project / "app.json").write_text(
                json.dumps({"pages": ["pages/index/index"]}), encoding="utf-8"
            )
            (project / ".aiui-evidence").write_text(
                "ordinary file cannot act as an evidence directory\n",
                encoding="utf-8",
            )

            result = run_validator(project, "--json")

            self.assertEqual(result.returncode, 1)
            self.assertIn("RESERVED_AUDIT_SOURCE", diagnostic_codes(result))

    def test_mixed_case_audit_evidence_cannot_carry_runtime_source(self) -> None:
        with self.make_project() as directory:
            project = Path(directory)
            self.write_support_files(project)
            self.write_page(project)
            (project / "app.json").write_text(
                json.dumps({"pages": ["pages/index/index"]}), encoding="utf-8"
            )
            hidden = project / ".AIUI-EVIDENCE" / "hidden.js"
            hidden.parent.mkdir()
            hidden.write_text("export default {};\n", encoding="utf-8")

            result = run_validator(project, "--json")

            self.assertEqual(1, result.returncode)
            self.assertIn("RESERVED_AUDIT_SOURCE", diagnostic_codes(result))

    def test_reserved_evidence_word_in_source_comment_is_not_a_reference(self) -> None:
        with self.make_project() as directory:
            project = Path(directory)
            self.write_support_files(project)
            (project / "app.json").write_text(
                json.dumps({"pages": ["pages/index/index"]}), encoding="utf-8"
            )
            page = project / "pages/index/index.ink"
            page.parent.mkdir(parents=True)
            page.write_text(
                "<page><view>OK</view><script>"
                "// Audit captures live under .aiui-evidence/.\n"
                "export default {};"
                "</script></page>\n",
                encoding="utf-8",
            )

            result = run_validator(project, "--json")

            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_runtime_source_cannot_reference_repository_metadata(self) -> None:
        with self.make_project() as directory:
            project = Path(directory)
            self.write_support_files(project)
            self.write_page(project)
            (project / "app.json").write_text(
                json.dumps({"pages": ["pages/index/index"]}), encoding="utf-8"
            )
            sources = (
                "const value = '../.git/config';\nexport default {};\n",
                "const value = '../.AIUI-EVIDENCE/device.log';\nexport default {};\n",
                r"const value = './.aiui\x2devidence/device.log';" + "\nexport default {};\n",
                r"const value = './.aiui\u002devidence/device.log';" + "\nexport default {};\n",
                r"const value = './.aiui\u{2d}evidence/device.log';" + "\nexport default {};\n",
                "const value = '.aiui-' + 'evidence/device.log';\nexport default {};\n",
                "const value = '.aiui-\\\nevidence/device.log';\nexport default {};\n",
                "const value = '.aiui-' + ('evidence/device.log');\nexport default {};\n",
                "const value = `.aiui-${'evidence'}/device.log`;\nexport default {};\n",
            )
            for source in sources:
                with self.subTest(source=source.splitlines()[0]):
                    (project / "app.js").write_text(source, encoding="utf-8")
                    referenced = run_validator(project, "--strict", "--json")
                    self.assertEqual(1, referenced.returncode)
                    self.assertIn(
                        "RESERVED_AUDIT_REFERENCE", diagnostic_codes(referenced)
                    )

    def test_runtime_reference_normalization_does_not_compact_markup_or_styles(self) -> None:
        with self.make_project() as directory:
            project = Path(directory)
            self.write_support_files(project)
            (project / "app.json").write_text(
                json.dumps({"pages": ["pages/index/index"]}), encoding="utf-8"
            )
            page = project / "pages/index/index.ink"
            page.parent.mkdir(parents=True)
            page.write_text(
                "<page><text>.aiui- evidence</text>"
                "<style>.aiui- evidence { color: green; }</style></page>\n",
                encoding="utf-8",
            )

            result = run_validator(project, "--strict", "--json")

            self.assertEqual(0, result.returncode, result.stdout + result.stderr)

            self.write_page(project)
            allowed_javascript = (
                "const label = '.aiui- evidence';\nexport default {};\n",
                r"const pattern = /\.git\//;" + "\nexport default {};\n",
                r"const pattern = /\.aiui-evidence\//;" + "\nexport default {};\n",
            )
            for source in allowed_javascript:
                with self.subTest(source=source.splitlines()[0]):
                    (project / "app.js").write_text(source, encoding="utf-8")
                    accepted = run_validator(project, "--strict", "--json")
                    self.assertEqual(
                        0,
                        accepted.returncode,
                        accepted.stdout + accepted.stderr,
                    )

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

    def test_wechat_control_directives_warn_and_fail_strict(self) -> None:
        controls = (
            '<text wx:if="{{show}}">A</text>'
            '<text wx:elif="{{other}}">B</text>'
            '<text wx:else>C</text>'
            '<view wx:for="{{items}}" wx:key="id">{{item.name}}</view>'
        )
        cases = (
            ("pages/index/index.ink", f"<page>{controls}</page>"),
            ("pages/index/index.wxml", f"<view>{controls}</view>"),
        )
        for relative, content in cases:
            with self.subTest(relative=relative), self.make_project() as directory:
                project = Path(directory)
                self.write_support_files(project)
                page = project / relative
                page.parent.mkdir(parents=True, exist_ok=True)
                page.write_text(content, encoding="utf-8")
                (project / "app.json").write_text(
                    json.dumps({"pages": ["pages/index/index"]}), encoding="utf-8"
                )

                normal = run_validator(project, "--json")
                strict = run_validator(project, "--strict", "--json")

                self.assertEqual(normal.returncode, 0, normal.stdout + normal.stderr)
                self.assertEqual(strict.returncode, 1, strict.stdout + strict.stderr)
                payload = json.loads(normal.stdout)
                self.assertEqual(payload["warningCount"], 1)
                diagnostic = payload["diagnostics"][0]
                self.assertEqual(diagnostic["severity"], "WARNING")
                self.assertEqual(diagnostic["code"], "WX_TEMPLATE_CONTROL_DIRECTIVE")
                self.assertEqual(diagnostic["path"], relative)
                for directive in ("wx:if", "wx:elif", "wx:else", "wx:for", "wx:key"):
                    self.assertIn(directive, diagnostic["message"])
                    self.assertIn(directive.replace("wx:", "ink:"), diagnostic["message"])

    def test_aiui_control_directives_are_accepted_in_ink_and_wxml(self) -> None:
        controls = (
            '<text ink:if="{{show}}">A</text>'
            '<text ink:elif="{{other}}">B</text>'
            '<text ink:else>C</text>'
            '<view ink:for="{{items}}" ink:key="id">{{item.name}}</view>'
        )
        cases = (
            ("pages/index/index.ink", f"<page>{controls}</page>"),
            ("pages/index/index.wxml", f"<view>{controls}</view>"),
        )
        for relative, content in cases:
            with self.subTest(relative=relative), self.make_project() as directory:
                project = Path(directory)
                self.write_support_files(project)
                page = project / relative
                page.parent.mkdir(parents=True, exist_ok=True)
                page.write_text(content, encoding="utf-8")
                (project / "app.json").write_text(
                    json.dumps({"pages": ["pages/index/index"]}), encoding="utf-8"
                )

                result = run_validator(project, "--strict", "--json")

                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                self.assertEqual(diagnostic_codes(result), [])

    def test_wechat_control_words_in_attribute_values_are_not_directives(self) -> None:
        controls = (
            '<text aria-label="literal wx:if wx:elif wx:else">A</text>'
            "<view data-note='literal wx:for wx:key wx:for-item wx:for-index'>B</view>"
        )
        cases = (
            ("pages/index/index.ink", f"<page>{controls}</page>"),
            ("pages/index/index.wxml", f"<view>{controls}</view>"),
        )
        for relative, content in cases:
            with self.subTest(relative=relative), self.make_project() as directory:
                project = Path(directory)
                self.write_support_files(project)
                page = project / relative
                page.parent.mkdir(parents=True, exist_ok=True)
                page.write_text(content, encoding="utf-8")
                (project / "app.json").write_text(
                    json.dumps({"pages": ["pages/index/index"]}), encoding="utf-8"
                )

                result = run_validator(project, "--strict", "--json")

                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                self.assertEqual(diagnostic_codes(result), [])

    def test_wechat_control_directives_inside_closed_comments_are_ignored(self) -> None:
        commented = (
            '<!-- retired: <text wx:if="{{show}}">A</text> '
            '<view wx:for="{{items}}" wx:key="id">B</view> -->'
        )
        cases = (
            ("pages/index/index.ink", f"<page>{commented}<text>live</text></page>"),
            ("pages/index/index.wxml", f"<view>{commented}<text>live</text></view>"),
        )
        for relative, content in cases:
            with self.subTest(relative=relative), self.make_project() as directory:
                project = Path(directory)
                self.write_support_files(project)
                page = project / relative
                page.parent.mkdir(parents=True, exist_ok=True)
                page.write_text(content, encoding="utf-8")
                (project / "app.json").write_text(
                    json.dumps({"pages": ["pages/index/index"]}), encoding="utf-8"
                )

                result = run_validator(project, "--strict", "--json")

                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                self.assertEqual(diagnostic_codes(result), [])

    def test_unclosed_comment_does_not_hide_following_wechat_directive(self) -> None:
        content = (
            '<!-- unfinished retired markup\n'
            '<text wx:if="{{show}}">still conservatively scanned</text>'
        )
        cases = (
            ("pages/index/index.ink", f"<page>{content}</page>"),
            ("pages/index/index.wxml", f"<view>{content}</view>"),
        )
        for relative, source in cases:
            with self.subTest(relative=relative), self.make_project() as directory:
                project = Path(directory)
                self.write_support_files(project)
                page = project / relative
                page.parent.mkdir(parents=True, exist_ok=True)
                page.write_text(source, encoding="utf-8")
                (project / "app.json").write_text(
                    json.dumps({"pages": ["pages/index/index"]}), encoding="utf-8"
                )

                normal = run_validator(project, "--json")
                strict = run_validator(project, "--strict", "--json")

                self.assertIn("WX_TEMPLATE_CONTROL_DIRECTIVE", diagnostic_codes(normal))
                self.assertEqual(strict.returncode, 1, strict.stdout + strict.stderr)
                self.assertIn("WX_TEMPLATE_CONTROL_DIRECTIVE", diagnostic_codes(strict))

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
