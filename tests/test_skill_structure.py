import json
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILL_ROOT = ROOT / "skills" / "rokid-aiui-agent"
SKILL_PATH = SKILL_ROOT / "SKILL.md"
METADATA_PATH = SKILL_ROOT / "agents" / "openai.yaml"
STUDIO_EXAMPLE_PATH = SKILL_ROOT / "assets" / "studio-importable-minimal"

REFERENCE_PATHS = (
    "references/source-of-truth.md",
    "references/project-anatomy.md",
    "references/ink-authoring.md",
    "references/interaction-and-design.md",
    "references/runtime-capabilities.md",
    "references/ux-and-capability-testing.md",
    "references/aix-workflow.md",
    "references/debugging-and-release.md",
)


class SkillStructureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not SKILL_PATH.is_file():
            raise AssertionError(f"missing packaged skill: {SKILL_PATH}")
        cls.skill = SKILL_PATH.read_text(encoding="utf-8")
        match = re.fullmatch(
            r"---\n(?P<frontmatter>.*?)\n---\n(?P<body>.*)",
            cls.skill,
            flags=re.DOTALL,
        )
        if match is None:
            raise AssertionError("SKILL.md must have YAML frontmatter")
        cls.frontmatter = match.group("frontmatter")
        cls.body = match.group("body")

    def test_frontmatter_has_exact_name_and_discriminating_description(self):
        self.assertRegex(self.frontmatter, r"(?m)^name: rokid-aiui-agent$")
        self.assertEqual(SKILL_ROOT.name, "rokid-aiui-agent")
        description_match = re.search(
            r"(?m)^description: (?P<description>.+)$", self.frontmatter
        )
        self.assertIsNotNone(description_match)
        description = description_match.group("description").lower()
        for term in (
            "rokid aiui",
            "create",
            "modify",
            "review",
            "debug",
            "preview",
            "package",
            "publish",
            ".ink",
            "wxml",
            "wxss",
            "pages",
            "widgets",
            "agent workers",
            "hardware input",
            "monochrome",
            "ux audit",
            "capability testing",
            "aix",
        ):
            self.assertIn(term, description)

    def test_routes_to_exactly_the_eight_planned_references(self):
        discovered = set(re.findall(r"references/[a-z0-9-]+\.md", self.body))
        self.assertEqual(set(REFERENCE_PATHS), discovered)
        for path in REFERENCE_PATHS:
            self.assertIn(f"`{path}`", self.body)

    def test_all_routed_reference_files_exist(self):
        for relative in REFERENCE_PATHS:
            with self.subTest(reference=relative):
                self.assertTrue(
                    (SKILL_ROOT / relative).is_file(),
                    f"missing routed reference file: {relative}",
                )

    def test_skill_is_compact_and_contains_no_scaffold_placeholders(self):
        self.assertLessEqual(len(re.findall(r"\b[\w'-]+\b", self.body)), 500)
        self.assertIsNone(
            re.search(r"(?i)\b(?:todo|tbd|fixme|placeholder)\b|\[insert[^]]*\]", self.skill)
        )

    def test_skill_requires_a_studio_importable_source_project(self):
        for phrase in (
            "complete AIUI project directory",
            "AIUI Studio",
            "repository root or explicitly named subdirectory",
            "0.17.0",
            "0.18",
        ):
            self.assertIn(phrase, self.body)
        self.assertRegex(
            self.body,
            r"(?is)0\.18.*(?:detect|confirm|target|support)|"
            r"(?:detect|confirm|target|support).*0\.18",
        )
        self.assertIn("Never claim that validation", self.body)
        self.assertIn("actually executed in the current environment", self.body)

    def test_repository_includes_a_studio_importable_example(self):
        expected = (
            "AGENTS.md",
            "app.json",
            "app.js",
            "pages/index/index.ink",
        )
        for relative in expected:
            self.assertTrue(
                (STUDIO_EXAMPLE_PATH / relative).is_file(),
                f"missing Studio example file: {relative}",
            )

    def test_page_definition_example_uses_schema_data_envelope(self):
        reference = (SKILL_ROOT / "references" / "ink-authoring.md").read_text(
            encoding="utf-8"
        )
        example_match = re.search(
            r"```html\s*<script def>\s*(?P<definition>\{.*?\})\s*</script>",
            reference,
            flags=re.DOTALL,
        )
        self.assertIsNotNone(example_match)
        definition = json.loads(example_match.group("definition"))
        schema = definition["schema"]
        self.assertNotIn("type", schema)
        self.assertNotIn("properties", schema)
        self.assertIn("data", schema)
        self.assertEqual("object", schema["data"]["type"])
        self.assertIn("properties", schema["data"])

    def test_metadata_is_complete_and_strings_are_quoted(self):
        self.assertTrue(METADATA_PATH.is_file(), f"missing metadata: {METADATA_PATH}")
        metadata = METADATA_PATH.read_text(encoding="utf-8")
        expected = {
            "display_name": "ROKID AIUI Agent Developer",
            "short_description": "Build and validate ROKID AIUI agents",
            "brand_color": "#40FF5E",
            "default_prompt": (
                "Use $rokid-aiui-agent to create and validate a complete ROKID AIUI "
                "project for AIUI Studio import."
            ),
        }
        for key, value in expected.items():
            self.assertRegex(
                metadata,
                rf'(?m)^  {key}: "{re.escape(value)}"$',
            )
        self.assertRegex(metadata, r"(?m)^  allow_implicit_invocation: true$")
        short_description = expected["short_description"]
        self.assertGreaterEqual(len(short_description), 25)
        self.assertLessEqual(len(short_description), 64)
        self.assertNotRegex(metadata, r"(?m)^\s*(?:icon_small|icon_large|dependencies):")
        for line in metadata.splitlines():
            if re.match(r"^\s+[a-z_]+:\s*", line) and not line.endswith("true"):
                self.assertRegex(line, r': "[^"]*"$')


if __name__ == "__main__":
    unittest.main()
