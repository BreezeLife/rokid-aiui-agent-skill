from __future__ import annotations

import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILL_ROOT = ROOT / "skills" / "rokid-aiui-agent"
SKILL_PATH = SKILL_ROOT / "SKILL.md"
REFERENCE_PATH = SKILL_ROOT / "references" / "ux-and-capability-testing.md"
INTERACTION_REFERENCE_PATH = (
    SKILL_ROOT / "references" / "interaction-and-design.md"
)


def table_after_heading(markdown: str, heading: str) -> tuple[list[str], list[list[str]]]:
    match = re.search(
        rf"(?ms)^## {re.escape(heading)}\s*$\n(?P<section>.*?)(?=^## |\Z)",
        markdown,
    )
    if match is None:
        return [], []

    table_lines = [
        line.strip()
        for line in match.group("section").splitlines()
        if line.strip().startswith("|") and line.strip().endswith("|")
    ]
    if len(table_lines) < 2:
        return [], []

    def cells(line: str) -> list[str]:
        return [cell.strip() for cell in line.strip("|").split("|")]

    return cells(table_lines[0]), [cells(line) for line in table_lines[2:]]


class UxCapabilityContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.skill = SKILL_PATH.read_text(encoding="utf-8")
        cls.reference = (
            REFERENCE_PATH.read_text(encoding="utf-8")
            if REFERENCE_PATH.is_file()
            else ""
        )
        cls.interaction_reference = INTERACTION_REFERENCE_PATH.read_text(
            encoding="utf-8"
        )

    def test_skill_makes_project_specific_audit_a_completion_gate(self) -> None:
        self.assertIn("`references/ux-and-capability-testing.md`", self.skill)
        self.assertRegex(
            self.skill,
            r"(?is)every (?:creation|implementation).*review.*must.*"
            r"UX.*capability.*evidence matrices",
        )
        for status in ("PASS", "FAIL", "BLOCKED", "N/A"):
            self.assertIn(f"`{status}`", self.skill)
        self.assertRegex(
            self.skill,
            r"(?is)(?:FAIL|BLOCKED).*must not.*(?:complete|release-ready)|"
            r"must not.*(?:complete|release-ready).*(?:FAIL|BLOCKED)",
        )

    def test_reference_defines_separate_ux_and_capability_matrices(self) -> None:
        self.assertTrue(REFERENCE_PATH.is_file(), f"missing {REFERENCE_PATH}")
        ux_header, _ = table_after_heading(self.reference, "Required UX matrix")
        capability_header, _ = table_after_heading(
            self.reference, "Required capability matrix"
        )
        self.assertEqual(
            [
                "ID",
                "Surface/state",
                "Risk",
                "Test",
                "Evidence layer",
                "Result",
                "Evidence",
            ],
            ux_header,
        )
        self.assertEqual(
            [
                "Capability",
                "Version/device/surface",
                "API/component/event",
                "Declaration/permission",
                "Official source/sample",
                "Positive path",
                "Negative/fallback path",
                "Lifecycle/cleanup",
                "Evidence layer",
                "Result",
                "Evidence",
            ],
            capability_header,
        )

    def test_ux_matrix_covers_aiui_interaction_and_optical_risks(self) -> None:
        _, rows = table_after_heading(self.reference, "Required UX matrix")
        identifiers = {row[0] for row in rows if row}
        self.assertEqual(
            {
                "UX-TARGET",
                "UX-STATE",
                "UX-TEXT",
                "UX-FOCUS",
                "UX-INPUT",
                "UX-RECOVERY",
                "UX-LIFECYCLE",
                "UX-VISUAL",
                "UX-ENVIRONMENT",
                "UX-MOTION",
            },
            identifiers,
        )

    def test_design_reference_exposes_official_canvas_acceptance_thresholds(self) -> None:
        for phrase in (
            "16px horizontal safe inset",
            "12px vertical safe inset",
            "72% green luminance",
        ):
            self.assertIn(phrase, self.interaction_reference)

    def test_evidence_layers_are_distinct_and_non_substitutable(self) -> None:
        header, rows = table_after_heading(self.reference, "Evidence ladder")
        self.assertEqual(["Layer", "Can establish", "Cannot establish"], header)
        layers = {row[0] for row in rows if row}
        self.assertEqual(
            {"SOURCE", "STATIC", "LOGIC", "AIX", "STUDIO", "DEVICE"},
            layers,
        )
        self.assertRegex(
            self.reference,
            r"(?is)preview.*must not.*(?:focus|keys|voice|gesture|permission|optics|performance)",
        )

    def test_result_rules_prevent_missing_evidence_from_becoming_pass(self) -> None:
        for status in ("`PASS`", "`FAIL`", "`BLOCKED`", "`N/A`"):
            self.assertIn(status, self.reference)
        self.assertRegex(
            self.reference,
            r"(?is)`PASS`.*required evidence layer.*executed.*captured",
        )
        self.assertRegex(
            self.reference,
            r"(?is)(?:not tested|unverified|missing evidence).*`BLOCKED`",
        )
        self.assertRegex(
            self.reference,
            r"(?is)(?:critical path|release).*`FAIL`.*`BLOCKED`.*"
            r"(?:must not|cannot).*(?:release-ready|complete)",
        )

    def test_capability_protocol_requires_source_negative_paths_and_cleanup(self) -> None:
        _, rows = table_after_heading(self.reference, "Required capability matrix")
        self.assertGreaterEqual(len(rows), 1)
        self.assertRegex(
            self.reference,
            r"(?is)version-matched.*official.*(?:runnable )?sample",
        )
        for term in (
            "denial",
            "revocation",
            "unavailable",
            "timeout",
            "malformed",
            "fallback",
            "hide/show",
            "unload",
        ):
            self.assertIn(term, self.reference.lower())


if __name__ == "__main__":
    unittest.main()
