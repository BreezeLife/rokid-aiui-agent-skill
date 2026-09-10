import json
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
README = ROOT / "README.md"
GUIDES = {
    "zh-CN": ROOT / "docs" / "usage.zh-CN.md",
    "en": ROOT / "docs" / "usage.en.md",
    "ja": ROOT / "docs" / "usage.ja.md",
}

README_STABLE_LITERALS = (
    "npx skills add BreezeLife/rokid-aiui-agent-skill --skill rokid-aiui-agent",
    "gh skill install BreezeLife/rokid-aiui-agent-skill rokid-aiui-agent --agent codex --scope user",
    "Repository: https://github.com/BreezeLife/rokid-aiui-agent-skill",
    "Ref: main",
    "Directory: skills/rokid-aiui-agent/assets/focus-timer-agent",
    "skills/rokid-aiui-agent/assets/focus-timer-agent",
    "](skills/rokid-aiui-agent/references/ux-and-capability-testing.md)",
)

README_FORBIDDEN_LITERALS = (
    "publicKeySha256",
    "claimsLedger",
    "SPKI DER",
    "attestations",
    "trust-policy",
)

SECTION_MARKERS = (
    "scope",
    "install",
    "invoke",
    "prompts",
    "verify",
    "audit",
    "import",
    "completion",
    "examples",
    "troubleshooting",
)

PROMPT_MARKERS = (
    "new-project",
    "timer",
    "review",
    "debug",
    "verify-package",
)

PROMPT_REQUIRED_LITERALS = {
    "new-project": (
        "AIUI 0.17.0",
        "_current",
        "_blank",
        "AIUI Studio",
        "Project UX evidence matrix",
        "Per-capability matrix",
        "BLOCKED",
    ),
    "timer": (
        "AIUI 0.17.0",
        "durationSeconds",
        "idle",
        "running",
        "paused",
        "finished",
        "error",
        "_current",
        "_blank",
        "AIUI Studio",
        "BLOCKED",
        "Project UX evidence matrix",
        "Per-capability matrix",
    ),
    "review": (
        "AIUI Studio",
        "Project UX evidence matrix",
        "Per-capability matrix",
        "PASS",
        "BLOCKED",
        "N/A",
    ),
    "debug": (
        "host focus",
        "element focus",
        "revision",
        "Project UX evidence matrix",
        "Per-capability matrix",
    ),
    "verify-package": (
        "scripts/fingerprint_aiui_project.py",
        "scripts/inventory_aiui_capabilities.py",
        "scripts/validate_aiui_project.py",
        "deterministic tests",
        "scripts/validate_aiui_audit.py",
        "aix --help",
        "preview",
        "pack",
        "list",
        ".git",
        ".aiui-evidence",
        "AIUI Studio",
        "Project UX evidence matrix",
        "Per-capability matrix",
    ),
}

COMMON_LITERALS = (
    "npx skills add BreezeLife/rokid-aiui-agent-skill --skill rokid-aiui-agent",
    "gh skill install BreezeLife/rokid-aiui-agent-skill rokid-aiui-agent --agent codex --scope user",
    "$rokid-aiui-agent",
    "AGENTS.md",
    "app.json",
    "aiui-audit-claims.json",
    "scripts/fingerprint_aiui_project.py",
    "scripts/inventory_aiui_capabilities.py",
    "scripts/validate_aiui_project.py",
    "scripts/validate_aiui_audit.py",
    "scripts/smoke_aix.sh",
    "PASS",
    "FAIL",
    "BLOCKED",
    "N/A",
    "RUNNER",
    "STUDIO",
    "DEVICE",
    "SCOPE",
    "SOURCE",
    "STATIC",
    "LOGIC",
    "AIX",
    "https://github.com/BreezeLife/rokid-aiui-agent-skill",
    "skills/rokid-aiui-agent/assets/focus-timer-agent",
)

DANGEROUS_AIX_COMMAND_RE = re.compile(
    r"(?im)^(?!\s*#)[^\n]*(?:\baix\b|\$\{?AIX_BIN\}?)[^\n]*"
    r"\b(?:create|dev|build|deploy|upload|publish)\b"
)

STATUS_SEMANTICS = {
    "zh-CN": (
        "- `PASS`：该行要求的每个证据层都已对当前源码执行并支持结论；",
        "- `FAIL`：已执行证据明确反驳验收条件；",
        "- `BLOCKED`：所需环境、权限或当前 revision 证据未提供；",
        "- `N/A`：只有源码范围与闭合产品范围共同证明条件不适用时才能使用，缺设备或缺时间不是 `N/A`。",
        "六层证据互不替代",
        "缺少相应签名时保持 `BLOCKED`。",
    ),
    "en": (
        "- `PASS`: every evidence layer required by that row was executed against the current source and supports the conclusion;",
        "- `FAIL`: executed evidence contradicts the acceptance criterion;",
        "- `BLOCKED`: a required environment, authority, or current-revision evidence is unavailable;",
        "- `N/A`: allowed only when both the source scope and a closed product scope prove that the condition is inapplicable; missing hardware or time does not make a gate `N/A`.",
        "The six evidence layers are not interchangeable.",
        "Without the required signature, keep the gate `BLOCKED`.",
    ),
    "ja": (
        "- `PASS`：その行で必要なすべてのエビデンスレイヤーが現在のソースに対して実行され、判定条件を満たしている。",
        "- `FAIL`：実行済みのエビデンスが判定条件に反している。",
        "- `BLOCKED`：必要な環境、署名主体、または現在の revision に対するエビデンスが提供されていない。",
        "- `N/A`：ソース範囲と閉じた製品範囲の両方から、その条件が適用対象外だと証明できる場合だけ使用できる。デバイスや時間がないことは `N/A` ではありません。",
        "6つのエビデンスレイヤーは相互に代替できません。",
        "必要な署名がない項目は `BLOCKED` のままにします。",
    ),
}

STUDIO_BOUNDARIES = {
    "zh-CN": "即使源码严格验证、AIX preview 和 pack 都成功，未实际导入时仍只能报告“源码已准备好供 AIUI Studio 导入”，Studio gate 保持 `BLOCKED`，不能报告“Studio 已验证”。",
    "en": "Even if strict source validation, AIX preview, and pack all succeed, an unexecuted Studio import remains `BLOCKED` and may be described only as “source prepared for AIUI Studio import,” not “verified in Studio.”",
    "ja": "厳格なソース検証、AIX preview、pack がすべて成功していても、実際にインポートしていない場合は Studio の検証ゲートを `BLOCKED` とし、「AIUI Studio にインポートできるようソースを準備済み」とだけ報告してください。「Studio で検証済み」とは報告しないでください。",
}

EXIT_CODE_ROWS = {
    "zh-CN": (
        "| `0` | `release-ready-pass` | 结构有效，并且恰好是 `Final status: PASS` 与 `Release-ready: YES` |",
        "| `2` | `valid-not-release-ready` | 结构有效，但最终结果仍为 `FAIL` 或 `BLOCKED` |",
        "| `1` | `invalid-or-untrusted` | 报告无效、过期、被篡改或不受信任 |",
    ),
    "en": (
        "| `0` | `release-ready-pass` | Structurally valid with exactly `Final status: PASS` and `Release-ready: YES`. |",
        "| `2` | `valid-not-release-ready` | Structurally valid, but the result remains `FAIL` or `BLOCKED`. |",
        "| `1` | `invalid-or-untrusted` | Invalid, stale, tampered with, or untrusted. |",
    ),
    "ja": (
        "| `0` | `release-ready-pass` | 構造が有効で、`Final status: PASS` かつ `Release-ready: YES` |",
        "| `2` | `valid-not-release-ready` | 構造は有効だが、結果が `FAIL` または `BLOCKED` のためリリース不可 |",
        "| `1` | `invalid-or-untrusted` | レポートが無効、古い、改ざんされている、または信頼されていない |",
    ),
}


def executable_bash(markdown: str) -> str:
    blocks = re.findall(r"```bash\s*([\s\S]*?)```", markdown)
    executable = "\n".join(
        line
        for block in blocks
        for line in block.splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    )
    return executable.replace("\\\n", " ")

SECTION_REQUIRED_LITERALS = {
    "scope": (
        ".aix",
        "AGENTS.md",
        "app.json",
        "aiui-audit-claims.json",
        "0.17.0",
        "0.18",
    ),
    "install": (
        "npx skills add BreezeLife/rokid-aiui-agent-skill --skill rokid-aiui-agent",
        "gh skill install BreezeLife/rokid-aiui-agent-skill rokid-aiui-agent --agent codex --scope user",
    ),
    "invoke": ("$rokid-aiui-agent", "AIUI Studio"),
    "verify": (
        "python3 -m pip install --only-binary=:all: -r requirements-dev.txt",
        "scripts/fingerprint_aiui_project.py",
        "scripts/inventory_aiui_capabilities.py",
        "scripts/validate_aiui_project.py",
        "scripts/validate_aiui_audit.py",
        "scripts/smoke_aix.sh",
        "npm ci --ignore-scripts --no-audit --no-fund",
        "@yodaos-pkg/aix-cli@0.8.2",
        "Node.js",
        ">=20",
        "node --version",
        "npm --version",
        "--help",
        "preview",
        "pack",
        "list",
        "Final status: PASS",
        "Release-ready: YES",
        "argv",
    ),
    "audit": (
        "## Project UX evidence matrix",
        "## Per-capability matrix",
        "PASS",
        "FAIL",
        "BLOCKED",
        "N/A",
        "SOURCE",
        "STATIC",
        "LOGIC",
        "AIX",
        "STUDIO",
        "DEVICE",
        "RUNNER",
        "SCOPE",
    ),
    "import": (
        "AIUI Studio",
        "app.json",
        "preview",
        "BLOCKED",
        "Repository: https://github.com/BreezeLife/rokid-aiui-agent-skill",
        "Ref: main",
        "Directory: skills/rokid-aiui-agent/assets/focus-timer-agent",
    ),
    "completion": ("FAIL", "BLOCKED", "Release-ready: YES"),
    "examples": ("skills/rokid-aiui-agent/assets/focus-timer-agent",),
    "troubleshooting": ("--help", "preview", "pack", "BLOCKED", "0.18"),
}


class MultilingualUsageDocsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.readme = README.read_text(encoding="utf-8")
        cls.guides = {
            language: path.read_text(encoding="utf-8")
            for language, path in GUIDES.items()
            if path.is_file()
        }

    @staticmethod
    def section(guide: str, marker: str) -> str:
        start_token = f"<!-- usage:{marker} -->"
        start = guide.index(start_token) + len(start_token)
        marker_index = SECTION_MARKERS.index(marker)
        if marker_index + 1 == len(SECTION_MARKERS):
            return guide[start:]
        end_token = f"<!-- usage:{SECTION_MARKERS[marker_index + 1]} -->"
        return guide[start : guide.index(end_token)]

    def test_all_three_localized_guides_exist(self) -> None:
        self.assertEqual(set(GUIDES), set(self.guides))

    def test_readme_exposes_all_language_entrypoints_near_the_top(self) -> None:
        introduction = "\n".join(self.readme.splitlines()[:15])
        for path in GUIDES.values():
            with self.subTest(path=path.name):
                self.assertIn(f"docs/{path.name}", introduction)

    def test_readme_is_a_prompt_first_quickstart(self) -> None:
        self.assertIn(
            "[![CI](https://github.com/BreezeLife/rokid-aiui-agent-skill/"
            "actions/workflows/ci.yml/badge.svg)]",
            self.readme,
        )
        for literal in README_STABLE_LITERALS:
            with self.subTest(required=literal):
                self.assertIn(literal, self.readme)

        text_blocks = re.findall(r"```text\s*\n([\s\S]*?)\n```", self.readme)
        prompts = [
            block
            for block in text_blocks
            if "使用 $rokid-aiui-agent" in block
            and re.search(r"[\u3400-\u4dbf\u4e00-\u9fff]", block)
        ]
        self.assertTrue(
            prompts,
            "README must include a copyable Chinese text prompt with "
            "$rokid-aiui-agent",
        )
        prompt = prompts[0]
        self.assertIn("/absolute/path/to/my_focus_timer", prompt)
        self.assertRegex(prompt, r"(?:独立|单独)[^。]*(?:目录|路径)")
        self.assertRegex(
            prompt,
            r"(?:(?:rokid-aiui-agent-skill|Skill)[^。]*(?:仓库之外|仓库外)|"
            r"不要[^。]*写入本 Skill 仓库)",
        )

        expected_headings = (
            "## 这个 Skill 能做什么",
            "## 快速开始",
            "## 你会得到什么",
            "## 导入 AIUI Studio",
            "## 内置 Focus Timer",
            "## 自动检查",
            "## 版本边界",
            "## 仓库内容",
            "## 深入指南",
            "## 来源与许可证",
        )
        positions = []
        for heading in expected_headings:
            self.assertEqual(1, self.readme.count(heading), heading)
            positions.append(self.readme.index(heading))
        self.assertEqual(sorted(positions), positions)

        sections = {
            heading: self.readme[
                self.readme.index(heading) : (
                    self.readme.index(expected_headings[index + 1])
                    if index + 1 < len(expected_headings)
                    else len(self.readme)
                )
            ]
            for index, heading in enumerate(expected_headings)
        }

        def section_has_all(section: str, patterns: tuple[str, ...]) -> bool:
            lines_and_paragraphs = [
                re.sub(r"\s+", " ", unit).strip()
                for unit in (
                    section.splitlines()
                    + re.split(r"\n\s*\n", section)
                )
                if unit.strip()
            ]
            return any(
                all(re.search(pattern, unit, re.IGNORECASE) for pattern in patterns)
                for unit in lines_and_paragraphs
            )

        capabilities = sections["## 这个 Skill 能做什么"]
        capability_contracts = {
            "create a complete AIUI project": (
                r"(?:创建|新建|生成)",
                r"(?:完整|可编辑)",
                r"AIUI",
                r"(?:项目|工程)",
            ),
            "modify an existing project": (
                r"(?:修改|迭代|扩展|完善)",
                r"(?:现有|已有)",
                r"(?:项目|工程)",
            ),
            "review or debug AIUI specifically": (
                r"AIUI",
                r"(?:审查|评审|检查|review|调试|排查|诊断|debug)",
            ),
            "validate and hand off to AIUI Studio": (
                r"(?:验证|验收|检查)",
                r"(?:交接|交付|导入)",
                r"AIUI Studio",
            ),
        }
        for task, patterns in capability_contracts.items():
            with self.subTest(capability=task):
                self.assertTrue(
                    section_has_all(capabilities, patterns),
                    f"capability overview must cover: {task}",
                )

        quickstart = sections["## 快速开始"]
        self.assertRegex(
            quickstart,
            r"支持\s*Agent Skills[^。\n]*编码环境[^。\n]*终端",
        )
        self.assertRegex(
            quickstart,
            r"`gh skill --help`[^。\n]*(?:可用|正常)",
        )

        output = sections["## 你会得到什么"]
        for literal in ("完整", "可编辑", "AIUI 项目目录", "AIUI Studio"):
            self.assertIn(literal, output)
        self.assertRegex(
            output,
            r"app\.json\.pages[^。]*(?:全部|所有)[^。]*页面",
        )
        self.assertRegex(
            output,
            r"页面[^。]*(?:引用|依赖)[^。]*(?:全部|所有)[^。]*资源",
        )
        self.assertNotRegex(output, r"如果[^。]*app\.json\.pages")
        self.assertRegex(output, r"_current[^。]*(?:嵌入|内嵌)[^。]*对话")
        self.assertRegex(output, r"_blank[^。]*全屏")
        self.assertRegex(output, r"BLOCKED[^。]*(?:待验证|等待验证)")

        studio_import = sections["## 导入 AIUI Studio"]
        for literal in ("本地检查", "AIUI Studio", "Rokid Glasses", "BLOCKED"):
            self.assertIn(literal, studio_import)

        focus_timer = sections["## 内置 Focus Timer"]
        self.assertNotIn("语音修改时长", focus_timer)
        self.assertRegex(focus_timer, r"对话[^。]*(?:变更|修改)[^。]*新的? Page")
        timer_mappings = (
            ("未开始", "开始"),
            ("进行中", "暂停"),
            ("已暂停", "继续"),
            ("已完成", "重新开始"),
        )
        timer_table_rows = set()
        for line in focus_timer.splitlines():
            stripped = line.strip()
            if not (stripped.startswith("|") and stripped.endswith("|")):
                continue
            cells = tuple(
                cell.strip(" `*_")
                for cell in stripped[1:-1].split("|")
            )
            if len(cells) == 2:
                timer_table_rows.add(cells)
        for state, action in timer_mappings:
            with self.subTest(timer_state=state, primary_action=action):
                self.assertIn((state, action), timer_table_rows)
        for literal in (
            "点头",
            "触摸板",
            "语音",
            "语音触发",
            "AIUI Studio",
            "Rokid Glasses",
            "BLOCKED",
        ):
            self.assertIn(literal, focus_timer)
        self.assertTrue(
            section_has_all(
                focus_timer,
                (
                    r"点头",
                    r"触摸板",
                    r"(?:Rokid Glasses|真机)",
                    r"BLOCKED",
                    r"(?:仍需|尚需|需要|待|未)",
                ),
            ),
            "nod and touchpad must share a pending glasses/device BLOCKED boundary",
        )
        self.assertTrue(
            section_has_all(
                focus_timer,
                (
                    r"语音(?:触发)?",
                    r"AIUI Studio",
                    r"(?:Rokid Glasses|真机)",
                    r"BLOCKED",
                    r"(?:仍需|尚需|需要|待|未)",
                ),
            ),
            "voice must share a pending Studio/glasses BLOCKED boundary",
        )

        version = sections["## 版本边界"]
        for literal in ("默认", "AIUI `0.17.0`", "`0.18`", "明确支持"):
            self.assertIn(literal, version)

        repository = sections["## 仓库内容"]
        repository_paths = (
            "skills/rokid-aiui-agent/SKILL.md",
            "skills/rokid-aiui-agent/references/",
            "skills/rokid-aiui-agent/scripts/",
            "skills/rokid-aiui-agent/assets/studio-importable-minimal/",
            "skills/rokid-aiui-agent/assets/focus-timer-agent/",
            "docs/usage.zh-CN.md",
            "docs/usage.en.md",
            "docs/usage.ja.md",
        )
        for path in repository_paths:
            with self.subTest(repository_path=path):
                self.assertIn(f"]({path})", repository)
        self.assertTrue(
            section_has_all(
                repository,
                (
                    r"studio-importable-minimal",
                    r"(?:最小|基础)",
                    r"(?:骨架|模板)",
                ),
            ),
            "studio-importable-minimal must be described as the minimal scaffold/template",
        )
        self.assertTrue(
            section_has_all(
                repository,
                (
                    r"focus-timer-agent",
                    r"(?:唯一|仅有)",
                    r"(?:产品化|产品形态|产品)",
                    r"Agent",
                ),
            ),
            "Focus Timer must remain the only productized example Agent",
        )

        folded_readme = self.readme.casefold()
        for literal in README_FORBIDDEN_LITERALS:
            with self.subTest(forbidden=literal):
                self.assertNotIn(literal.casefold(), folded_readme)

    def test_guides_share_complete_ordered_usage_contract(self) -> None:
        for language, guide in self.guides.items():
            with self.subTest(language=language):
                positions = []
                for marker in SECTION_MARKERS:
                    token = f"<!-- usage:{marker} -->"
                    self.assertEqual(1, guide.count(token), token)
                    positions.append(guide.index(token))
                self.assertEqual(sorted(positions), positions)

    def test_guides_link_to_each_language_and_back_to_readme(self) -> None:
        expected_links = (
            "usage.zh-CN.md",
            "usage.en.md",
            "usage.ja.md",
            "../README.md",
        )
        for language, guide in self.guides.items():
            with self.subTest(language=language):
                for link in expected_links:
                    self.assertIn(f"]({link})", guide)

    def test_each_guide_has_copyable_prompts_for_five_common_jobs(self) -> None:
        for language, guide in self.guides.items():
            with self.subTest(language=language):
                for index, marker in enumerate(PROMPT_MARKERS):
                    start_token = f"<!-- prompt:{marker} -->"
                    self.assertEqual(1, guide.count(start_token), start_token)
                    start = guide.index(start_token) + len(start_token)
                    if index + 1 < len(PROMPT_MARKERS):
                        end = guide.index(f"<!-- prompt:{PROMPT_MARKERS[index + 1]} -->")
                    else:
                        end = guide.index("<!-- usage:verify -->")
                    prompt_block = guide[start:end]
                    self.assertRegex(
                        prompt_block,
                        r"```text\s+[\s\S]*?\$rokid-aiui-agent[\s\S]*?```",
                    )
                    for literal in PROMPT_REQUIRED_LITERALS[marker]:
                        self.assertIn(literal, prompt_block)

    def test_guides_preserve_commands_outputs_and_audit_boundaries(self) -> None:
        for language, guide in self.guides.items():
            with self.subTest(language=language):
                for literal in COMMON_LITERALS:
                    self.assertIn(literal, guide)
                self.assertIn("0.17.0", guide)
                self.assertIn("0.18", guide)
                self.assertRegex(guide, r"(?m)^Repository: https://github.com/BreezeLife/rokid-aiui-agent-skill$")
                self.assertRegex(guide, r"(?m)^Ref: main$")
                self.assertRegex(
                    guide,
                    r"(?m)^Directory: skills/rokid-aiui-agent/assets/focus-timer-agent$",
                )
                self.assertNotRegex(executable_bash(guide), DANGEROUS_AIX_COMMAND_RE)

    def test_each_semantic_section_carries_its_own_contract(self) -> None:
        for language, guide in self.guides.items():
            for marker, literals in SECTION_REQUIRED_LITERALS.items():
                section = self.section(guide, marker)
                with self.subTest(language=language, section=marker):
                    for literal in literals:
                        self.assertIn(literal, section)

    def test_audit_exit_codes_are_documented_together(self) -> None:
        for language, guide in self.guides.items():
            verify = self.section(guide, "verify")
            with self.subTest(language=language):
                positions = []
                for row in EXIT_CODE_ROWS[language]:
                    self.assertIn(row, verify)
                    positions.append(verify.index(row))
                self.assertEqual(sorted(positions), positions)

    def test_localized_status_and_studio_semantics_are_canonical(self) -> None:
        for language, guide in self.guides.items():
            audit = self.section(guide, "audit")
            studio_import = self.section(guide, "import")
            with self.subTest(language=language):
                for literal in STATUS_SEMANTICS[language]:
                    self.assertIn(literal, audit)
                self.assertIn(STUDIO_BOUNDARIES[language], studio_import)

    def test_claims_ledger_example_is_valid_closed_schema_one(self) -> None:
        for language, guide in self.guides.items():
            scope = self.section(guide, "scope")
            with self.subTest(language=language):
                json_blocks = re.findall(r"```json\s*([\s\S]*?)```", scope)
                self.assertTrue(json_blocks)
                document = json.loads(json_blocks[0])
                self.assertEqual(
                    {"schemaVersion", "scopeClosed", "claims"}, set(document)
                )
                self.assertEqual(1, document["schemaVersion"])
                self.assertIs(document["scopeClosed"], True)
                self.assertEqual([], document["claims"])

    def test_verification_commands_follow_the_documented_flow(self) -> None:
        ordered_commands = (
            "python3 -m pip install --only-binary=:all: -r requirements-dev.txt",
            "scripts/fingerprint_aiui_project.py",
            "scripts/inventory_aiui_capabilities.py",
            "scripts/validate_aiui_project.py",
            "python3 -m unittest discover -s tests -v",
            "node --version",
            "npm --version",
            "npm ci --ignore-scripts --no-audit --no-fund",
            '"$AIX_BIN" --help',
            '"$AIX_BIN" preview "$AIUI_IMPORT_ROOT" --html-out "$AIUI_PREVIEW_HTML"',
            "scripts/smoke_aix.sh",
            "scripts/validate_aiui_audit.py",
        )
        for language, guide in self.guides.items():
            verify = self.section(guide, "verify")
            with self.subTest(language=language):
                executable = executable_bash(verify)
                positions = []
                for command in ordered_commands:
                    self.assertIn(command, executable)
                    positions.append(executable.index(command))
                self.assertEqual(sorted(positions), positions)
                self.assertNotRegex(executable, DANGEROUS_AIX_COMMAND_RE)

    def test_verification_bash_blocks_are_identical_across_languages(self) -> None:
        blocks_by_language = {
            language: tuple(
                block.strip()
                for block in re.findall(
                    r"```bash\s*([\s\S]*?)```", self.section(guide, "verify")
                )
            )
            for language, guide in self.guides.items()
        }
        self.assertEqual(blocks_by_language["en"], blocks_by_language["zh-CN"])
        self.assertEqual(blocks_by_language["en"], blocks_by_language["ja"])

    def test_aix_command_guard_rejects_wrapped_mutating_commands(self) -> None:
        dangerous_commands = (
            "env AIUI_MODE=test aix deploy .",
            "bash -c 'aix upload .'",
            "npx --yes --package @yodaos-pkg/aix-cli aix publish .",
            '"$AIX_BIN" upload .',
            '"${AIX_BIN}" deploy .',
            "./node_modules/.bin/aix publish .",
            "env AIUI_MODE=test aix \\\n  deploy .",
        )
        for command in dangerous_commands:
            with self.subTest(command=command):
                normalized = command.replace("\\\n", " ")
                self.assertRegex(normalized, DANGEROUS_AIX_COMMAND_RE)

    def test_local_markdown_links_resolve(self) -> None:
        documents = {README: self.readme}
        documents.update(
            {GUIDES[language]: guide for language, guide in self.guides.items()}
        )
        for document, text in documents.items():
            for raw_target in re.findall(r"\[[^]]*\]\(([^)]+)\)", text):
                target = raw_target.split("#", 1)[0]
                if not target or re.match(r"^[a-z][a-z0-9+.-]*:", target, re.I):
                    continue
                resolved = (document.parent / target).resolve()
                with self.subTest(document=document.name, target=target):
                    self.assertTrue(resolved.exists(), f"broken local link: {target}")

    def test_each_guide_is_predominantly_written_in_its_language(self) -> None:
        character_counts = {}
        for language, guide in self.guides.items():
            character_counts[language] = {
                "ascii": len(re.findall(r"[A-Za-z]", guide)),
                "han": len(re.findall(r"[\u3400-\u4dbf\u4e00-\u9fff]", guide)),
                "kana": len(re.findall(r"[\u3040-\u30ff]", guide)),
            }
        self.assertGreaterEqual(character_counts["zh-CN"]["han"], 1000)
        self.assertLess(character_counts["zh-CN"]["kana"], 20)
        self.assertGreaterEqual(character_counts["en"]["ascii"], 8000)
        self.assertLess(
            character_counts["en"]["han"] + character_counts["en"]["kana"], 100
        )
        self.assertGreaterEqual(character_counts["ja"]["kana"], 1000)

    def test_localized_timer_and_review_terms_are_present(self) -> None:
        expected_terms = {
            "zh-CN": ("计时器", "审查"),
            "en": ("timer", "review"),
            "ja": ("タイマー", "レビュー"),
        }
        for language, terms in expected_terms.items():
            guide = self.guides.get(language, "").lower()
            with self.subTest(language=language):
                for term in terms:
                    self.assertIn(term.lower(), guide)

    def test_guides_have_no_scaffold_placeholders(self) -> None:
        for language, guide in self.guides.items():
            with self.subTest(language=language):
                self.assertIsNone(
                    re.search(
                        r"(?i)\b(?:todo|tbd|fixme|placeholder)\b|\[insert[^]]*\]|"
                        r"待补充|占位文本|稍后填写|未記入|仮置き|後で記入|要記入",
                        guide,
                    )
                )


if __name__ == "__main__":
    unittest.main()
