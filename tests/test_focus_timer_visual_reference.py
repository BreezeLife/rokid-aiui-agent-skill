from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from PIL import Image
from pypdf import PdfReader

from scripts import build_focus_timer_visual_reference as visual_reference


ROOT = Path(__file__).resolve().parents[1]
BUILDER = ROOT / "scripts" / "build_focus_timer_visual_reference.py"
REQUIREMENTS = ROOT / "requirements-dev.txt"
WORKFLOW = ROOT / ".github" / "workflows" / "ci.yml"
INK = (
    ROOT
    / "skills"
    / "rokid-aiui-agent"
    / "assets"
    / "focus-timer-agent"
    / "pages"
    / "index"
    / "index.ink"
)


class FocusTimerVisualReferenceTests(unittest.TestCase):
    def test_pdf_font_registration_falls_back_for_unsupported_outlines(self) -> None:
        with tempfile.TemporaryDirectory(prefix="focus-timer-font-") as directory:
            unsupported = Path(directory) / "unsupported.ttc"
            unsupported.write_bytes(b"unsupported-font")
            try:
                registered = visual_reference.register_pdf_fonts(
                    unsupported, unsupported
                )
            except Exception as error:  # pragma: no cover - RED-path diagnostic
                self.fail(f"unsupported outlines must fall back: {error}")
            self.assertEqual(
                registered,
                ("STSong-Light", "STSong-Light"),
            )

    def test_ci_installs_visual_dependencies_and_linux_cjk_font(self) -> None:
        requirements = REQUIREMENTS.read_text(encoding="utf-8")
        for dependency in ("Pillow==", "pypdf==", "reportlab=="):
            self.assertIn(dependency, requirements)

        workflow = WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("fonts-noto-cjk", workflow)

        builder = BUILDER.read_text(encoding="utf-8")
        self.assertIn("/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc", builder)

    def test_builder_outputs_github_png_and_six_page_pdf(self) -> None:
        with tempfile.TemporaryDirectory(prefix="focus-timer-visual-") as directory:
            output = Path(directory)
            result = subprocess.run(
                [sys.executable, str(BUILDER), "--output-root", str(output)],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            summary = json.loads(result.stdout)
            png = output / "docs" / "assets" / "focus-timer-user-journey.png"
            pdf = output / "output" / "pdf" / "focus-timer-developer-reference.pdf"
            self.assertEqual(summary["png"], str(png))
            self.assertEqual(summary["pdf"], str(pdf))
            self.assertEqual(summary["pages"], 6)
            self.assertEqual(
                summary["png_sha256"], hashlib.sha256(png.read_bytes()).hexdigest()
            )
            self.assertEqual(
                summary["pdf_sha256"], hashlib.sha256(pdf.read_bytes()).hexdigest()
            )
            with Image.open(png) as image:
                self.assertEqual(image.size, (2400, 1200))
                self.assertEqual(image.mode, "RGB")
            reader = PdfReader(pdf)
            self.assertEqual(len(reader.pages), 6)
            text = "\n".join(page.extract_text() or "" for page in reader.pages)
            for fragment in (
                "Focus Timer",
                "AIUI 0.17.0",
                "开始专注",
                "专注 25 分钟",
                "durationSeconds: 600",
                "10:00",
                "開始",
                "一時停止",
                "再開",
                "最初から",
                "nod",
                "Enter",
                "GlobalHook",
                "bindtap",
                "bindfocus",
                "bindblur",
                "非真机实拍",
                "人工门槛",
            ):
                self.assertIn(fragment, text)

    def test_visual_copy_matches_current_page_contract(self) -> None:
        source = INK.read_text(encoding="utf-8")
        for fragment in (
            "const DEFAULT_DURATION_SECONDS = 600;",
            "nodHint: 'うなずく / タッチパッド：開始'",
            "event.code !== 'Enter'",
            "event.code !== 'GlobalHook'",
            'bindtap="startTimer"',
            'bindfocus="focusStartAction"',
            'bindblur="onActionBlur"',
        ):
            self.assertIn(fragment, source)


if __name__ == "__main__":
    unittest.main()
