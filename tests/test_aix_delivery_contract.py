import re
import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILL_ROOT = ROOT / "skills" / "rokid-aiui-agent"
SKILL = (SKILL_ROOT / "SKILL.md").read_text(encoding="utf-8")
AIX_REFERENCE = (SKILL_ROOT / "references" / "aix-workflow.md").read_text(
    encoding="utf-8"
)
README = (ROOT / "README.md").read_text(encoding="utf-8")
CI = (ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
GUIDES = {
    "zh-CN": (ROOT / "docs" / "usage.zh-CN.md").read_text(encoding="utf-8"),
    "en": (ROOT / "docs" / "usage.en.md").read_text(encoding="utf-8"),
    "ja": (ROOT / "docs" / "usage.ja.md").read_text(encoding="utf-8"),
}

PUBLIC_CONTRACTS = {
    "skill": SKILL,
    "aix-reference": AIX_REFERENCE,
    "readme": README,
    **{f"guide-{language}": guide for language, guide in GUIDES.items()},
}

CONTRADICTION_PATTERNS = (
    re.compile(
        r"(?i)(?:actual|attempted)\s+(?:pack/list|pack|list).{0,40}"
        r"\bfail(?:s|ed|ure)?\b.{0,24}\bBLOCKED\b"
    ),
    re.compile(
        r"(?:实际|已经)(?:执行(?:的)?)?\s*(?:pack/list|pack|list)"
        r".{0,24}失败.{0,24}BLOCKED"
    ),
    re.compile(r"実行した.{0,24}(?:pack|list).{0,24}失敗.{0,24}BLOCKED"),
    re.compile(
        r"(?i)(?:signed\s+)?wrapper(?:\s+command)?\s+alone.{0,40}"
        r"(?:enough|sufficient)"
    ),
    re.compile(
        r"(?i)\.aix.{0,60}\b(?:can|may)\b.{0,30}"
        r"(?:selected|used).{0,50}(?:AIUI\s+)?Studio\s+import\s+root"
    ),
    re.compile(r"\.aix.{0,60}(?:可|可以)作为.{0,30}AIUI Studio 导入根"),
    re.compile(
        r"\.aix.{0,60}AIUI Studio のインポートルート.{0,40}"
        r"(?:選択できます|利用できます)"
    ),
)


def contract_contradictions(text: str) -> list[str]:
    normalized = re.sub(r"\s+", " ", text)
    return [pattern.pattern for pattern in CONTRADICTION_PATTERNS if pattern.search(normalized)]


LOCALIZED_OUTPUT_CONTRACTS = {
    "zh-CN": (
        "完整、可编辑的源码工程始终是必交付物",
        "默认同时在导入根之外交付一个 `.aix` 包",
        "不能作为 AIUI Studio 导入根",
    ),
    "en": (
        "complete editable source project is always required",
        "also delivers a `.aix` archive outside that import root by default",
        "must not be selected as the AIUI Studio import root",
    ),
    "ja": (
        "完全で編集可能なソースプロジェクトが常に必須の成果物",
        "標準でインポートルート外に `.aix` を追加成果物として出力",
        "AIUI Studio のインポートルートとして選択しません",
    ),
}


class AixDeliveryContractTests(unittest.TestCase):
    def test_skill_requires_source_and_conditionally_delivers_aix(self) -> None:
        for literal in (
            "source project is always required",
            "additional `.aix` deliverable",
            "outside the Studio import root",
            "pack and list",
            "AIX deliverable is `BLOCKED`",
            "AIX deliverable is `FAIL`",
        ):
            with self.subTest(literal=literal):
                self.assertIn(literal, SKILL)

    def test_skill_keeps_executable_inventory_and_external_trust_contract(self) -> None:
        self.assertIn(
            "scripts/inventory_aiui_capabilities.py <import-root> "
            "--target-version <version> --repository-root <repository-root>",
            SKILL,
        )
        for literal in (
            "canonical SPKI DER identities",
            "absolute repository-external trust policy",
            "Roles cannot reuse one key",
            "repository-selected or self-declared keys are untrusted",
        ):
            with self.subTest(literal=literal):
                self.assertIn(literal, SKILL)

    def test_source_delivery_can_complete_independently_of_aix_and_release(self) -> None:
        self.assertIn(
            "A proven source delivery remains independently reportable", SKILL
        )
        self.assertIn(
            "forbids overall completion or release-ready claims", SKILL
        )
        self.assertNotIn("forbids complete/release-ready claims", SKILL)

    def test_aix_reference_defines_verified_handoff(self) -> None:
        for literal in (
            '"$AIUI_IMPORT_ROOT" "$AIUI_AIX_OUTPUT" "$AIUI_REPOSITORY_ROOT"',
            "outside the Studio import root",
            "refuses to overwrite",
            "AIUI source fingerprint",
            "AIX artifact",
            "AIX bytes",
            "AIX SHA-256",
            "random build ID",
            "does not by itself satisfy signed AIX audit evidence",
            "underlying `aix pack` and `aix list`",
            "verified source snapshot",
            "filesystem identity",
            "exclusive no-clobber copy",
            "same artifact identity and SHA-256",
        ):
            with self.subTest(literal=literal):
                self.assertIn(literal, AIX_REFERENCE)

    def test_readme_exposes_dual_output_without_making_aix_importable(self) -> None:
        output_start = README.index("## 你会得到什么")
        output_end = README.index("## 导入 AIUI Studio")
        output = README[output_start:output_end]
        for literal in (
            "完整、可编辑的源码工程始终是必交付物",
            "默认同时在导入根之外交付一个 `.aix` 包",
            "不能作为 AIUI Studio 导入根",
        ):
            self.assertIn(literal, output)

    def test_readme_requires_the_complete_persistent_aix_gate(self) -> None:
        self.assertIn("若完整 AIX pack/list 与指纹校验成功", README)
        self.assertNotIn("若 AIX 打包成功", README)

    def test_public_contracts_contain_no_known_semantic_contradictions(self) -> None:
        for name, contract in PUBLIC_CONTRACTS.items():
            with self.subTest(contract=name):
                self.assertEqual([], contract_contradictions(contract))

    def test_contradiction_guard_rejects_release_pressure_mutations(self) -> None:
        mutations = (
            "actual pack/list failure is BLOCKED",
            "实际 pack/list 失败 = BLOCKED",
            "実行した pack が失敗した場合は BLOCKED",
            "signed wrapper alone is sufficient",
            ".aix can be selected as the AIUI Studio import root",
            ".aix 可以作为 AIUI Studio 导入根",
            ".aix は AIUI Studio のインポートルートとして選択できます",
        )
        for mutation in mutations:
            with self.subTest(mutation=mutation):
                self.assertTrue(contract_contradictions(mutation))

    def test_guides_share_the_dual_output_and_status_contract(self) -> None:
        for language, guide in GUIDES.items():
            with self.subTest(language=language):
                for literal in LOCALIZED_OUTPUT_CONTRACTS[language]:
                    self.assertIn(literal, guide)
                self.assertIn("AIUI source fingerprint", guide)
                self.assertIn("AIX artifact", guide)
                self.assertIn("AIX bytes", guide)
                self.assertIn("AIX SHA-256", guide)
                self.assertRegex(
                    guide,
                    r"(?is)(?:unsupported|不支持|未対応).*`BLOCKED`",
                )
                self.assertRegex(
                    guide,
                    r"(?is)(?:pack|list)[^\n]{0,160}(?:fails|失败|失敗)[^\n]{0,80}`FAIL`",
                )

    def test_creation_prompts_request_real_aix_delivery(self) -> None:
        for language, guide in GUIDES.items():
            for marker in ("new-project", "timer"):
                start = guide.index(f"<!-- prompt:{marker} -->")
                next_prompt = re.search(r"<!-- prompt:[a-z-]+ -->", guide[start + 1 :])
                end = (
                    start + 1 + next_prompt.start()
                    if next_prompt
                    else guide.index("<!-- usage:verify -->", start)
                )
                prompt = guide[start:end]
                with self.subTest(language=language, prompt=marker):
                    self.assertIn(".aix", prompt)
                    self.assertRegex(
                        prompt,
                        r"(?is)(?:outside|之外|外)[^\n]{0,120}(?:import|导入|インポート)",
                    )

    def test_guides_execute_persistent_delivery_outside_import_root(self) -> None:
        expected = (
            'AIUI_AIX_OUTPUT="${AIUI_IMPORT_ROOT%/}.aix"',
            'AIUI_REPOSITORY_ROOT="$PWD"',
            'scripts/smoke_aix.sh "$AIUI_IMPORT_ROOT" "$AIUI_AIX_OUTPUT" "$AIUI_REPOSITORY_ROOT"',
        )
        bash_blocks = {}
        for language, guide in GUIDES.items():
            verify_start = guide.index("<!-- usage:verify -->")
            verify_end = guide.index("<!-- usage:audit -->")
            verify = guide[verify_start:verify_end]
            executable = "\n".join(
                block.strip()
                for block in re.findall(r"```bash\s*([\s\S]*?)```", verify)
            )
            bash_blocks[language] = executable
            with self.subTest(language=language):
                for literal in expected:
                    self.assertIn(literal, executable)
        self.assertEqual(bash_blocks["zh-CN"], bash_blocks["en"])
        self.assertEqual(bash_blocks["zh-CN"], bash_blocks["ja"])

    def test_repository_does_not_track_generated_aix_archives(self) -> None:
        result = subprocess.run(
            ["git", "ls-files", "*.aix"],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=True,
        )
        self.assertEqual("", result.stdout)

    def test_ci_preserves_pipeline_failures_for_persistent_delivery(self) -> None:
        start = CI.index("- name: Preserve and verify an external AIX deliverable")
        end = CI.index("- name: Generate the Focus Timer Agent static preview", start)
        step = CI[start:end]
        self.assertIn("shell: bash", step)
        self.assertIn("set -euo pipefail", step)
        self.assertIn('| tee "$delivery_log"', step)


if __name__ == "__main__":
    unittest.main()
