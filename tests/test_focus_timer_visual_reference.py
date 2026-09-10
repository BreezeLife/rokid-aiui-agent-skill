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


ROOT = Path(__file__).resolve().parents[1]
BUILDER = ROOT / "scripts" / "build_focus_timer_visual_reference.py"
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
