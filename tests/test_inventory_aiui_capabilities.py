from __future__ import annotations

import hashlib
import json
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
    / "inventory_aiui_capabilities.py"
)


class InventoryAiuiCapabilitiesTests(unittest.TestCase):
    def run_script(
        self,
        project: Path,
        target_version: str = "0.17.0",
    ) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                str(project),
                "--target-version",
                target_version,
            ],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )

    def test_inventory_is_deterministic_and_finds_registered_mechanisms(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            project = Path(temporary_directory)
            (project / "pages" / "index").mkdir(parents=True)
            (project / "app.json").write_text(
                json.dumps(
                    {
                        "pages": ["pages/index/index"],
                        "permissions": ["CAMERA"],
                    }
                ),
                encoding="utf-8",
            )
            (project / "pages" / "index" / "index.ink").write_text(
                """
<page><button bindtap="start">Start</button></page>
<script setup>
export default {
  async start() {
    const stream = await navigator.mediaDevices.getUserMedia({ video: true });
    stream.getTracks().forEach((track) => track.stop());
    const socket = wx.connectSocket({ url: "wss://example.invalid" });
  },
  onVoiceWakeup(event) { return event.keyword; },
  onUnload() {}
};
</script>
""".strip()
                + "\n",
                encoding="utf-8",
            )

            first = self.run_script(project)
            second = self.run_script(project)
            self.assertEqual(0, first.returncode, first.stderr)
            self.assertEqual(first.stdout, second.stdout)
            report = json.loads(first.stdout)
            self.assertEqual(2, report["schemaVersion"])
            self.assertEqual("0.17.0", report["targetVersion"])
            self.assertEqual("aiui-0.17-policy-v1", report["policyVersion"])
            self.assertEqual([], report["versionViolations"])
            self.assertRegex(report["projectRevision"], r"^WORKTREE:[0-9a-f]{64}$")
            families = {item["family"] for item in report["items"]}
            self.assertTrue(
                {
                    "page.route",
                    "ui.button",
                    "event.bindtap",
                    "input.voice-wakeup",
                    "media.camera.permission",
                    "media.camera.runtime",
                    "media.camera.lifecycle",
                    "network.websocket",
                    "page.lifecycle",
                }.issubset(families)
            )
            ledger = report["claimedCapabilities"]
            self.assertEqual(ledger, sorted(ledger))
            self.assertEqual(len(ledger), len(set(ledger)))
            self.assertEqual(
                ledger,
                sorted(f"{item['family']}@{item['gate']}" for item in report["items"]),
            )
            for item in report["items"]:
                self.assertEqual(
                    {
                        "apiBinding",
                        "declarationBinding",
                        "family",
                        "gate",
                        "locations",
                        "mechanism",
                        "policyState",
                        "versionFeature",
                    },
                    set(item),
                )
            camera_permission = next(
                item
                for item in report["items"]
                if item["family"] == "media.camera.permission"
            )
            self.assertEqual("app.json#permissions", camera_permission["apiBinding"])
            self.assertEqual("CAMERA", camera_permission["declarationBinding"])
            websocket = next(
                item
                for item in report["items"]
                if item["family"] == "network.websocket"
            )
            self.assertEqual("wx.connectSocket(...)" , websocket["apiBinding"])
            self.assertEqual("NONE REQUIRED", websocket["declarationBinding"])
            self.assertEqual("registered", websocket["policyState"])

    def test_inventory_does_not_specialize_generic_words_and_reports_unknown_wx(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            project = Path(temporary_directory)
            (project / "app.json").write_text('{"pages":[]}\n', encoding="utf-8")
            (project / "notes.js").write_text(
                "// voice and network are product words, not mechanisms\n"
                "wx.someFutureCapability();\n",
                encoding="utf-8",
            )
            result = self.run_script(project)
            self.assertEqual(0, result.returncode, result.stderr)
            report = json.loads(result.stdout)
            families = {item["family"] for item in report["items"]}
            self.assertNotIn("input.voice-wakeup", families)
            self.assertNotIn("ai.speech-recognition", families)
            self.assertNotIn("network.https", families)
            self.assertEqual(
                ["wx.someFutureCapability"],
                [item["symbol"] for item in report["unmatchedSymbols"]],
            )
            unknown_item = next(
                item
                for item in report["items"]
                if item["family"] == "project.unregistered"
            )
            self.assertEqual(
                "PROJECT-SYMBOL:wx.someFutureCapability(...)" ,
                unknown_item["apiBinding"],
            )
            self.assertEqual(
                "UNKNOWN — source policy not registered",
                unknown_item["declarationBinding"],
            )
            self.assertEqual("unregistered", unknown_item["policyState"])
            self.assertEqual(unknown_item["gate"], report["unmatchedSymbols"][0]["gate"])

    def test_inventory_finds_version_gated_widgets_workers_and_capabilities(self) -> None:
        temporary_directory = tempfile.TemporaryDirectory()
        self.addCleanup(temporary_directory.cleanup)
        project = Path(temporary_directory.name)
        (project / "workers").mkdir()
        (project / "app.json").write_text(
            json.dumps(
                {
                    "pages": [],
                    "widgets": [
                        {"path": "widgets/status/index", "family": "1x2"}
                    ],
                    "agentWorkers": [
                        {
                            "name": "bluetooth",
                            "script": "workers/bluetooth.js",
                            "trigger": {"type": "open"},
                            "lifetime": "foreground",
                            "capabilities": ["bluetooth-peripheral"],
                        }
                    ],
                }
            )
            + "\n",
            encoding="utf-8",
        )
        (project / "workers" / "bluetooth.js").write_text(
            "export default { onOpen(event) { "
            "event.waitUntil(Promise.resolve()); } };\n",
            encoding="utf-8",
        )
        (project / "aiui-audit-claims.json").write_text(
            json.dumps(
                {
                    "schemaVersion": 1,
                    "scopeClosed": True,
                    "claims": [
                        {
                            "family": "agent-worker.declaration",
                            "surface": "Agent Worker",
                            "description": "Declares the Bluetooth worker",
                        }
                    ],
                }
            )
            + "\n",
            encoding="utf-8",
        )
        result = self.run_script(project, target_version="0.18.0")
        self.assertEqual(0, result.returncode, result.stderr)
        report = json.loads(result.stdout)
        self.assertEqual([], report["versionViolations"])
        self.assertEqual(["Agent Worker", "Widget"], report["supportedSurfaces"])
        claim_item = next(
            item
            for item in report["items"]
            if item["locations"][0]["path"] == "aiui-audit-claims.json"
        )
        self.assertEqual("agent-worker.declaration", claim_item["family"])
        self.assertEqual("binding-unresolved", claim_item["policyState"])
        self.assertEqual("PROJECT-BINDING:UNRESOLVED", claim_item["apiBinding"])
        items = report["items"]
        families = {item["family"] for item in items}
        self.assertTrue(
            {
                "widget.declaration",
                "agent-worker.declaration",
                "agent-worker.capability",
                "agent-worker.on-open",
                "agent-worker.wait-until",
            }.issubset(families)
        )
        for item in items:
            if item["family"].startswith(("widget.", "agent-worker.")):
                self.assertEqual("preview-0.18", item["versionFeature"])
                self.assertIn(
                    item["policyState"],
                    {"version-gated", "binding-unresolved", "unregistered"},
                )
        worker_capability = next(
            item for item in items if item["family"] == "agent-worker.capability"
        )
        self.assertEqual(
            "app.json#agentWorkers:bluetooth.capabilities",
            worker_capability["apiBinding"],
        )
        self.assertEqual(
            "bluetooth-peripheral", worker_capability["declarationBinding"]
        )

        stable_result = self.run_script(project, target_version="0.17.0")
        self.assertEqual(0, stable_result.returncode, stable_result.stderr)
        stable_report = json.loads(stable_result.stdout)
        self.assertEqual(
            ["Agent Worker", "Widget"], stable_report["supportedSurfaces"]
        )
        self.assertEqual(
            {"agentWorkers", "widgets"},
            {entry["feature"] for entry in stable_report["versionViolations"]},
        )

    def test_inventory_binds_key_and_timer_mechanisms_in_focus_timer(self) -> None:
        result = self.run_script(ROOT / "examples" / "focus-timer-agent")
        self.assertEqual(0, result.returncode, result.stderr)
        report = json.loads(result.stdout)
        items = report["items"]
        by_family: dict[str, list[dict[str, object]]] = {}
        for item in items:
            by_family.setdefault(item["family"], []).append(item)
        self.assertIn("input.enter", by_family)
        self.assertIn(
            "onKeyUp(event.code=Enter)",
            {item["apiBinding"] for item in by_family["input.enter"]},
        )
        unregistered_bindings = {
            item["apiBinding"]
            for item in by_family["project.unregistered"]
        }
        self.assertTrue(
            {
                "PROJECT-SYMBOL:onKeyUp(event.code=GlobalHook)",
                "PROJECT-SYMBOL:setInterval(...)",
                "PROJECT-SYMBOL:clearInterval(...)",
            }.issubset(unregistered_bindings)
        )

    def test_unknown_manifest_permission_binding_and_template_event_are_not_silent(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            project = Path(temporary_directory)
            (project / "pages" / "index").mkdir(parents=True)
            (project / "app.json").write_text(
                json.dumps(
                    {
                        "pages": ["pages/index/index"],
                        "permissions": ["FUTURE_SENSOR"],
                        "futureCapability": {"enabled": True},
                    }
                ),
                encoding="utf-8",
            )
            (project / "pages" / "index" / "index.ink").write_text(
                '<page><future-view bindactivate="activate" /></page>\n'
                '<script setup>export default { activate() {}, '
                'onMysteryHostEvent() { navigator.futureSensor.open(); } };</script>\n',
                encoding="utf-8",
            )
            result = self.run_script(project)
            self.assertEqual(0, result.returncode, result.stderr)
            report = json.loads(result.stdout)
            symbols = {item["symbol"] for item in report["unmatchedSymbols"]}
            self.assertTrue(
                {
                    "app.json#permissions:FUTURE_SENSOR",
                    "app.json#futureCapability",
                    "<future-view>",
                    "bindactivate=activate",
                    "onMysteryHostEvent",
                    "navigator.futureSensor.open",
                }.issubset(symbols)
            )
            unmatched_gates = {item["gate"] for item in report["unmatchedSymbols"]}
            item_gates = {
                item["gate"]
                for item in report["items"]
                if item["policyState"] == "unregistered"
            }
            self.assertTrue(unmatched_gates.issubset(item_gates))

    def test_inventory_rejects_duplicate_manifest_keys(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            project = Path(temporary_directory)
            (project / "app.json").write_text(
                '{"pages":[],"pages":["pages/index/index"]}\n',
                encoding="utf-8",
            )
            result = self.run_script(project)
            self.assertNotEqual(0, result.returncode)
            self.assertIn("duplicate JSON key", result.stderr)

    def test_same_line_instances_keep_distinct_column_bound_gates(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            project = Path(temporary_directory)
            (project / "pages" / "index").mkdir(parents=True)
            (project / "app.json").write_text(
                '{"pages":["pages/index/index"]}\n', encoding="utf-8"
            )
            (project / "pages" / "index" / "index.ink").write_text(
                '<page><button bindtap="go">A</button><button bindtap="go">B</button></page>\n',
                encoding="utf-8",
            )
            result = self.run_script(project)
            self.assertEqual(0, result.returncode, result.stderr)
            report = json.loads(result.stdout)
            buttons = [
                item for item in report["items"] if item["family"] == "ui.button"
            ]
            taps = [
                item for item in report["items"] if item["family"] == "event.bindtap"
            ]
            self.assertEqual(2, len(buttons))
            self.assertEqual(2, len(taps))
            self.assertEqual(2, len({item["gate"] for item in buttons}))
            self.assertEqual(2, len({item["locations"][0]["column"] for item in buttons}))

    def test_host_focus_pseudo_class_is_registered_with_exact_offset(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory)
            (project / "pages" / "index").mkdir(parents=True)
            (project / "app.json").write_text(
                '{"pages":["pages/index/index"]}\n', encoding="utf-8"
            )
            source = """
<page><view class="surface"><text>Ready</text></view></page>
<style>
.surface:host-focus { border-color: green; }
</style>
""".strip() + "\n"
            (project / "pages" / "index" / "index.ink").write_text(
                source, encoding="utf-8"
            )

            result = self.run_script(project)
            self.assertEqual(0, result.returncode, result.stderr)
            report = json.loads(result.stdout)
            host_focus = [
                item for item in report["items"] if item["family"] == "focus.host"
            ]
            self.assertEqual(1, len(host_focus))
            self.assertEqual(":host-focus", host_focus[0]["mechanism"])
            self.assertEqual(":host-focus", host_focus[0]["apiBinding"])
            self.assertEqual("NONE REQUIRED", host_focus[0]["declarationBinding"])
            self.assertEqual(
                {
                    "path": "pages/index/index.ink",
                    "line": source.splitlines().index(
                        ".surface:host-focus { border-color: green; }"
                    )
                    + 1,
                    "column": 9,
                },
                host_focus[0]["locations"][0],
            )

    def test_host_focus_pseudo_class_ignores_comments_and_strings(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory)
            (project / "pages" / "index").mkdir(parents=True)
            (project / "app.json").write_text(
                '{"pages":["pages/index/index"]}\n', encoding="utf-8"
            )
            (project / "pages" / "index" / "index.ink").write_text(
                """
<page><text>Ready</text></page>
<style>
/* .surface:host-focus { color: red; } */
.surface::before { content: ":host-focus"; }
.surface::after { content: ':host-focus'; }
</style>
<script setup>
const documentation = ':host-focus';
</script>
""".strip()
                + "\n",
                encoding="utf-8",
            )

            result = self.run_script(project)
            self.assertEqual(0, result.returncode, result.stderr)
            report = json.loads(result.stdout)
            self.assertFalse(
                any(item["family"] == "focus.host" for item in report["items"])
            )

    def test_app_callbacks_are_not_mislabeled_as_page_lifecycle(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            project = Path(temporary_directory)
            (project / "pages" / "index").mkdir(parents=True)
            (project / "app.json").write_text(
                '{"pages":["pages/index/index"]}\n', encoding="utf-8"
            )
            (project / "app.js").write_text(
                "export default { onShow() {}, onHide() {} };\n", encoding="utf-8"
            )
            (project / "pages" / "index" / "index.ink").write_text(
                "<page><text>Ready</text></page>\n", encoding="utf-8"
            )
            result = self.run_script(project)
            self.assertEqual(0, result.returncode, result.stderr)
            report = json.loads(result.stdout)
            page_lifecycle_paths = {
                item["locations"][0]["path"]
                for item in report["items"]
                if item["family"] == "page.lifecycle"
            }
            self.assertNotIn("app.js", page_lifecycle_paths)
            symbols = {entry["symbol"] for entry in report["unmatchedSymbols"]}
            self.assertTrue({"App.onShow", "App.onHide"}.issubset(symbols))

    def test_missing_or_wrong_typed_manifest_inventory_fails_closed(self) -> None:
        invalid_manifests = (
            None,
            {"pages": "pages/index/index"},
            {"pages": [1]},
            {"pages": [], "permissions": "CAMERA"},
            {"pages": [], "widgets": {}},
            {"pages": [], "widgets": [None]},
            {"pages": [], "widgets": [{"path": "widgets/x", "family": None}]},
            {"pages": [], "agentWorkers": {}},
            {"pages": [], "agentWorkers": [None]},
            {
                "pages": [],
                "agentWorkers": [
                    {
                        "name": "worker",
                        "script": "worker.js",
                        "trigger": {"type": "open"},
                        "lifetime": "instant",
                        "capabilities": "bluetooth-peripheral",
                    }
                ],
            },
            {"pages": [], "window": []},
            {"pages": [], "usingComponents": []},
            {"pages": [], "usingComponents": {"demo-card": 1}},
            {"pages": [], "fonts": {}},
            {"pages": [], "fonts": [{"family": "Bundled Serif"}]},
        )
        for manifest in invalid_manifests:
            with self.subTest(manifest=manifest), tempfile.TemporaryDirectory() as directory:
                project = Path(directory)
                if manifest is not None:
                    (project / "app.json").write_text(
                        json.dumps(manifest), encoding="utf-8"
                    )
                result = self.run_script(project)
                self.assertNotEqual(0, result.returncode)
                self.assertRegex(
                    result.stderr,
                    r"app\.json|pages|permissions|widgets|agentWorkers|window|usingComponents|fonts|capabilities",
                )

    def test_dynamic_and_catch_bindings_are_quarantined(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory)
            (project / "pages" / "index").mkdir(parents=True)
            (project / "app.json").write_text(
                '{"pages":["pages/index/index"]}\n', encoding="utf-8"
            )
            (project / "pages" / "index" / "index.ink").write_text(
                '<page><button bindtap="{{handler}}" catchtap="stop">Go</button></page>\n',
                encoding="utf-8",
            )
            result = self.run_script(project)
            self.assertEqual(0, result.returncode, result.stderr)
            report = json.loads(result.stdout)
            symbols = {entry["symbol"] for entry in report["unmatchedSymbols"]}
            self.assertTrue({"bindtap={{handler}}", "catchtap=stop"}.issubset(symbols))

    def test_aliased_and_namespaced_platform_calls_are_not_silent(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory)
            (project / "pages" / "index").mkdir(parents=True)
            (project / "app.json").write_text(
                '{"pages":["pages/index/index"]}\n', encoding="utf-8"
            )
            (project / "pages" / "index" / "index.ink").write_text(
                "<page><text>Ready</text></page>\n"
                "<script setup>const platform = wx; const request = wx.request; request(); "
                "window.fetch(); globalThis.setTimeout(() => {}, 1); "
                "window.wx.request(); "
                "globalThis.navigator.mediaDevices.getUserMedia({ video: true }); "
                "const timer = setTimeout; const store = localStorage; "
                "const mediaDevices = navigator.mediaDevices; "
                "localStorage.setItem('key', 'value'); const Capture = ImageCapture; "
                "new MediaRecorder();"
                "</script>\n",
                encoding="utf-8",
            )
            result = self.run_script(project)
            self.assertEqual(0, result.returncode, result.stderr)
            report = json.loads(result.stdout)
            symbols = {entry["symbol"] for entry in report["unmatchedSymbols"]}
            self.assertTrue(
                {
                    "REFERENCE:wx",
                    "REFERENCE:wx.request",
                    "window.fetch",
                    "globalThis.setTimeout",
                    "window.wx.request",
                    "globalThis.navigator.mediaDevices.getUserMedia",
                    "REFERENCE:setTimeout",
                    "REFERENCE:localStorage",
                    "localStorage.setItem",
                    "REFERENCE:navigator.mediaDevices",
                    "REFERENCE:ImageCapture",
                    "MediaRecorder",
                }.issubset(symbols)
            )
            self.assertNotIn(
                "network.https",
                {
                    item["family"]
                    for item in report["items"]
                    if item["locations"][0]["path"].endswith("index.ink")
                },
            )

    def test_widget_lifecycle_callbacks_are_version_gated_not_silent(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory)
            (project / "pages" / "index").mkdir(parents=True)
            (project / "widgets" / "status").mkdir(parents=True)
            (project / "app.json").write_text(
                json.dumps(
                    {
                        "pages": ["pages/index/index"],
                        "widgets": [{"path": "widgets/status/index", "family": "1x1"}],
                    }
                ),
                encoding="utf-8",
            )
            (project / "pages" / "index" / "index.ink").write_text(
                "<page><text>Ready</text></page>\n", encoding="utf-8"
            )
            (project / "widgets" / "status" / "index.ink").write_text(
                "<script setup>export default { onCreate() {}, onAttach() {}, "
                "onDetach() {}, onDestroy() {} };</script><widget><text>W</text></widget>\n",
                encoding="utf-8",
            )
            result = self.run_script(project, target_version="0.18.0")
            self.assertEqual(0, result.returncode, result.stderr)
            report = json.loads(result.stdout)
            callbacks = {
                item["mechanism"]
                for item in report["items"]
                if item["family"] == "widget.lifecycle"
            }
            self.assertEqual(
                {"onCreate()", "onAttach()", "onDetach()", "onDestroy()"},
                callbacks,
            )

    def test_camera_candidates_require_local_argument_and_cleanup_association(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory)
            (project / "pages" / "index").mkdir(parents=True)
            (project / "app.json").write_text(
                '{"pages":["pages/index/index"],"permissions":["CAMERA"]}\n',
                encoding="utf-8",
            )
            (project / "pages" / "index" / "index.ink").write_text(
                "<page><text>Ready</text></page>\n<script setup>"
                "const stream = await navigator.mediaDevices.getUserMedia({ audio: true }); "
                "const unrelated = { video: true }; "
                "stream.getTracks().forEach((track) => track.stop());"
                "</script>\n",
                encoding="utf-8",
            )
            result = self.run_script(project)
            self.assertEqual(0, result.returncode, result.stderr)
            report = json.loads(result.stdout)
            camera_runtime = [
                item
                for item in report["items"]
                if item["family"] == "media.camera.runtime"
            ]
            camera_cleanup = [
                item
                for item in report["items"]
                if item["family"] == "media.camera.lifecycle"
            ]
            self.assertEqual("binding-unresolved", camera_runtime[0]["policyState"])
            self.assertEqual("PROJECT-BINDING:UNRESOLVED", camera_runtime[0]["apiBinding"])
            self.assertEqual([], camera_cleanup)
            symbols = {entry["symbol"] for entry in report["unmatchedSymbols"]}
            self.assertIn("media-cleanup-association", symbols)

        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory)
            (project / "pages" / "index").mkdir(parents=True)
            (project / "app.json").write_text(
                '{"pages":["pages/index/index"]}\n', encoding="utf-8"
            )
            (project / "pages" / "index" / "index.ink").write_text(
                "<page><text>Ready</text></page><script setup>"
                "navigator.mediaDevices.getUserMedia({ video: true });"
                "</script>\n",
                encoding="utf-8",
            )
            result = self.run_script(project)
            self.assertEqual(0, result.returncode, result.stderr)
            report = json.loads(result.stdout)
            runtime = next(
                item
                for item in report["items"]
                if item["family"] == "media.camera.runtime"
            )
            self.assertEqual("binding-unresolved", runtime["policyState"])
            self.assertEqual("PROJECT-BINDING:UNRESOLVED", runtime["apiBinding"])
            self.assertEqual(
                "PROJECT-BINDING:UNRESOLVED", runtime["declarationBinding"]
            )

    def test_key_callbacks_bind_only_codes_in_their_own_method_body(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory)
            (project / "pages" / "index").mkdir(parents=True)
            (project / "app.json").write_text(
                '{"pages":["pages/index/index"]}\n', encoding="utf-8"
            )
            (project / "pages" / "index" / "index.ink").write_text(
                "<page><text>Ready</text></page>\n<script setup>export default {\n"
                "onKeyDown(event) { if (event.code === 'Backspace') return; },\n"
                "onKeyUp(event) { if (event.code === 'Enter') return; },\n"
                "helper(event) { if (event.code === 'ArrowDown') return; }\n"
                "};</script>\n",
                encoding="utf-8",
            )
            result = self.run_script(project)
            self.assertEqual(0, result.returncode, result.stderr)
            report = json.loads(result.stdout)
            bindings = {
                item["apiBinding"]
                for item in report["items"]
                if item["family"] in {"input.enter", "input.back", "input.scroll.host"}
            }
            self.assertEqual(
                {
                    "onKeyDown(event.code=Backspace)",
                    "onKeyUp(event.code=Enter)",
                },
                bindings,
            )

    def test_local_fetch_and_comment_target_are_not_registered_platform_capabilities(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory)
            (project / "pages" / "index").mkdir(parents=True)
            (project / "app.json").write_text(
                '{"pages":["pages/index/index"]}\n', encoding="utf-8"
            )
            (project / "pages" / "index" / "index.ink").write_text(
                "<page><text>Ready</text></page>\n<script setup>"
                "// _blank is documentation, not a target declaration\n"
                "function fetch() { return 1; } fetch();"
                "</script>\n",
                encoding="utf-8",
            )
            result = self.run_script(project)
            self.assertEqual(0, result.returncode, result.stderr)
            report = json.loads(result.stdout)
            families = {item["family"] for item in report["items"]}
            self.assertNotIn("network.https", families)
            targets = [
                item for item in report["items"] if item["family"] == "page.target"
            ]
            self.assertEqual([], targets)

    def test_platform_scan_is_scoped_to_executable_code(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory)
            (project / "pages" / "index").mkdir(parents=True)
            (project / "app.json").write_text(
                '{"pages":["pages/index/index"]}\n', encoding="utf-8"
            )
            (project / "pages" / "index" / "index.ink").write_text(
                "<page><text>Don't call wx.request() or window.fetch()</text></page>\n"
                '<script setup>const note = "wx.connectSocket()"; '
                "export default { start() { wx.request({}); "
                "const output = `${wx.request({})}`; return output; } };"
                "</script>\n",
                encoding="utf-8",
            )
            result = self.run_script(project)
            self.assertEqual(0, result.returncode, result.stderr)
            report = json.loads(result.stdout)
            network_items = [
                item
                for item in report["items"]
                if item["family"].startswith("network.")
            ]
            self.assertEqual(2, len(network_items))
            self.assertEqual(
                {"wx.request(...)"},
                {item["apiBinding"] for item in network_items},
            )
            symbols = {entry["symbol"] for entry in report["unmatchedSymbols"]}
            self.assertNotIn("window.fetch", symbols)

    def test_static_template_bindings_require_handlers_owned_by_the_surface(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory)
            (project / "pages" / "index").mkdir(parents=True)
            (project / "shared").mkdir()
            (project / "app.json").write_text(
                '{"pages":["pages/index/index"]}\n', encoding="utf-8"
            )
            (project / "pages" / "index" / "index.wxml").write_text(
                '<page><button bindtap="start" bindfocus="focus" '
                'bindblur="missing">Go</button></page>\n',
                encoding="utf-8",
            )
            (project / "pages" / "index" / "index.js").write_text(
                "export default { start() {}, methods: { focus() {} } };\n",
                encoding="utf-8",
            )
            (project / "shared" / "helpers.js").write_text(
                "export default { missing() {} };\n", encoding="utf-8"
            )
            result = self.run_script(project)
            self.assertEqual(0, result.returncode, result.stderr)
            report = json.loads(result.stdout)
            bindings = {
                item["apiBinding"]: item
                for item in report["items"]
                if item["family"] in {"event.bindtap", "focus.element"}
            }
            self.assertEqual("registered", bindings["bindtap=start"]["policyState"])
            self.assertEqual("NONE REQUIRED", bindings["bindtap=start"]["declarationBinding"])
            self.assertEqual("registered", bindings["bindfocus=focus"]["policyState"])
            unresolved = next(
                item
                for item in report["items"]
                if item["family"] == "focus.element"
                and item["mechanism"] == "bindblur=missing"
            )
            self.assertEqual("binding-unresolved", unresolved["policyState"])
            self.assertEqual("PROJECT-BINDING:UNRESOLVED", unresolved["apiBinding"])
            self.assertEqual(
                "PROJECT-BINDING:UNRESOLVED", unresolved["declarationBinding"]
            )

    def test_known_callbacks_are_scoped_to_exported_surface_owners(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory)
            (project / "pages" / "index").mkdir(parents=True)
            (project / "widgets" / "status").mkdir(parents=True)
            (project / "workers").mkdir()
            (project / "app.json").write_text(
                json.dumps(
                    {
                        "pages": ["pages/index/index"],
                        "widgets": [{"path": "widgets/status/index", "family": "1x1"}],
                        "agentWorkers": [
                            {
                                "name": "worker",
                                "script": "workers/worker.js",
                                "trigger": {"type": "open"},
                                "lifetime": "instant",
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )
            (project / "app.js").write_text(
                "export default { onShow() {} };\n", encoding="utf-8"
            )
            (project / "pages" / "index" / "index.ink").write_text(
                "<page><text>Ready</text></page><script setup>"
                "function onShow() {} export default { onCreate() {}, "
                "methods: { onReady() {} } };"
                "</script>\n",
                encoding="utf-8",
            )
            (project / "widgets" / "status" / "index.ink").write_text(
                "<widget><text>W</text></widget><script setup>export default { "
                "onCreate() {}, onVoiceWakeup() {} };</script>\n",
                encoding="utf-8",
            )
            (project / "workers" / "worker.js").write_text(
                "export default { onOpen() {}, onShow() {}, "
                "helper(event) { event.waitUntil(Promise.resolve()); } };\n",
                encoding="utf-8",
            )
            (project / "shared.js").write_text(
                "export default { onLoad() {} };\n", encoding="utf-8"
            )
            result = self.run_script(project, target_version="0.18.0")
            self.assertEqual(0, result.returncode, result.stderr)
            report = json.loads(result.stdout)
            page_lifecycle = [
                item
                for item in report["items"]
                if item["family"] == "page.lifecycle"
            ]
            self.assertEqual([], page_lifecycle)
            symbols = {entry["symbol"] for entry in report["unmatchedSymbols"]}
            self.assertTrue(
                {
                    "App.onShow",
                    "Page.onCreate",
                    "Page.onReady:owner-unresolved",
                    "Widget.onVoiceWakeup",
                    "AgentWorker.onShow",
                    "AgentWorker.event.waitUntil",
                    "Shared.onLoad",
                }.issubset(symbols)
            )

    def test_manifest_nested_capability_shapes_are_inventoried_or_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory)
            (project / "app.json").write_text(
                json.dumps(
                    {
                        "pages": [],
                        "window": {
                            "navigationBarTitleText": "Agent",
                            "viewport": {"width": "device-width"},
                        },
                        "usingComponents": {
                            "demo-card": "components/demo-card",
                        },
                        "fonts": [
                            {
                                "family": "Bundled Serif",
                                "src": "assets/fonts/regular.ttf",
                                "weight": 400,
                                "style": "normal",
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )
            result = self.run_script(project)
            self.assertEqual(0, result.returncode, result.stderr)
            report = json.loads(result.stdout)
            symbols = {entry["symbol"] for entry in report["unmatchedSymbols"]}
            self.assertTrue(
                {
                    "app.json#window.navigationBarTitleText=Agent",
                    "app.json#window.viewport.width=device-width",
                    "app.json#usingComponents:demo-card=components/demo-card",
                    "app.json#fonts:Bundled Serif@assets/fonts/regular.ttf#400/normal",
                }.issubset(symbols)
            )

    def test_speech_runtime_requires_same_instance_and_unique_companion(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory)
            (project / "pages" / "index").mkdir(parents=True)
            (project / "app.json").write_text(
                '{"pages":["pages/index/index"]}\n', encoding="utf-8"
            )
            (project / "pages" / "index" / "index.ink").write_text(
                "<page><text>Ready</text></page><script setup>"
                "if (typeof SpeechRecognition === 'undefined') throw new Error(); "
                "const first = new SpeechRecognition(); "
                "const second = new SpeechRecognition(); "
                "const third = new SpeechRecognition(); "
                "first.start(); this.recognition = second; "
                "this.recognition.start(); this.recognition = null; stranger.start();"
                "</script>\n",
                encoding="utf-8",
            )
            result = self.run_script(project)
            self.assertEqual(0, result.returncode, result.stderr)
            report = json.loads(result.stdout)
            runtime = [
                item
                for item in report["items"]
                if item["family"] == "ai.speech-recognition"
            ]
            companions = [
                item
                for item in report["items"]
                if item["family"] == "voice.declaration.unknown"
            ]
            self.assertEqual(2, len(runtime))
            self.assertEqual(2, len(companions))
            companion_bindings = {
                f"COMPANION:voice.declaration.unknown@{item['gate']}"
                for item in companions
            }
            self.assertEqual(
                companion_bindings,
                {item["declarationBinding"] for item in runtime},
            )
            self.assertEqual(
                {"new SpeechRecognition()->recognition.start()"},
                {item["apiBinding"] for item in runtime},
            )
            self.assertEqual(
                {"registered"}, {item["policyState"] for item in runtime}
            )
            self.assertEqual(
                {"binding-unresolved"},
                {item["policyState"] for item in companions},
            )
            symbols = {entry["symbol"] for entry in report["unmatchedSymbols"]}
            self.assertIn("new SpeechRecognition:instance-start-association", symbols)
            self.assertNotIn("REFERENCE:SpeechRecognition", symbols)

    def test_explicit_claims_are_strict_hashed_and_cannot_bypass_bindings(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory)
            (project / "app.json").write_text('{"pages":[]}\n', encoding="utf-8")
            (project / "aiui-audit-claims.json").write_text(
                json.dumps(
                    {
                        "schemaVersion": 1,
                        "scopeClosed": True,
                        "claims": [
                            {
                                "family": "network.https",
                                "surface": "_current",
                                "description": "Loads the current forecast",
                            },
                            {
                                "family": "business.retained-timer",
                                "surface": "_current",
                                "description": "Refreshes the countdown",
                            },
                        ],
                    }
                ),
                encoding="utf-8",
            )
            first = self.run_script(project)
            second = self.run_script(project)
            self.assertEqual(0, first.returncode, first.stderr)
            self.assertEqual(first.stdout, second.stdout)
            report = json.loads(first.stdout)
            claim_items = [
                item
                for item in report["items"]
                if item["locations"][0]["path"] == "aiui-audit-claims.json"
            ]
            self.assertEqual(2, len(claim_items))
            registered = next(
                item for item in claim_items if item["family"] == "network.https"
            )
            self.assertEqual("binding-unresolved", registered["policyState"])
            self.assertEqual("PROJECT-BINDING:UNRESOLVED", registered["apiBinding"])
            self.assertEqual(
                "PROJECT-BINDING:UNRESOLVED", registered["declarationBinding"]
            )
            unknown = next(
                item for item in claim_items if item["family"] == "project.unregistered"
            )
            self.assertEqual("PROJECT-BINDING:UNRESOLVED", unknown["apiBinding"])
            self.assertEqual("unregistered", unknown["policyState"])
            self.assertIn(
                "CLAIM:business.retained-timer@_current:Refreshes the countdown",
                {entry["symbol"] for entry in report["unmatchedSymbols"]},
            )
            self.assertEqual(
                report["claimedCapabilities"],
                sorted(
                    f"{item['family']}@{item['gate']}" for item in report["items"]
                ),
            )

    def test_explicit_claims_reject_bad_shapes_keys_and_duplicates(self) -> None:
        invalid_claims = (
            '{"schemaVersion":true,"scopeClosed":true,"claims":[]}',
            '{"schemaVersion":1,"claims":[]}',
            '{"schemaVersion":1,"scopeClosed":"true","claims":[]}',
            '{"schemaVersion":1,"scopeClosed":true,"claims":{}}',
            '{"schemaVersion":1,"scopeClosed":true,"claims":[{"family":"network.https","surface":"_current"}]}',
            '{"schemaVersion":1,"scopeClosed":true,"claims":[{"family":"network.https","surface":"_current","description":"x","extra":true}]}',
            '{"schemaVersion":1,"scopeClosed":true,"claims":[{"family":"network.https","surface":"_current","description":"x"},{"family":"network.https","surface":"_current","description":"x"}]}',
            '{"schemaVersion":1,"schemaVersion":1,"scopeClosed":true,"claims":[]}',
        )
        for claim_text in invalid_claims:
            with self.subTest(claim_text=claim_text), tempfile.TemporaryDirectory() as directory:
                project = Path(directory)
                (project / "app.json").write_text(
                    '{"pages":[]}\n', encoding="utf-8"
                )
                (project / "aiui-audit-claims.json").write_text(
                    claim_text + "\n", encoding="utf-8"
                )
                result = self.run_script(project)
                self.assertNotEqual(0, result.returncode)
                self.assertRegex(result.stderr, r"aiui-audit-claims|duplicate JSON key")

    def test_claim_surfaces_accept_only_the_canonical_enum(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory)
            (project / "app.json").write_text('{"pages":[]}\n', encoding="utf-8")
            claims_path = project / "aiui-audit-claims.json"
            claims_path.write_text(
                json.dumps(
                    {
                        "schemaVersion": 1,
                        "scopeClosed": True,
                        "claims": [
                            {
                                "family": "network.https",
                                "surface": "Agent Worker",
                                "description": "Loads worker data",
                            }
                        ],
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            accepted = self.run_script(project)
            self.assertEqual(0, accepted.returncode, accepted.stderr)
            self.assertEqual(
                ["Agent Worker"], json.loads(accepted.stdout)["supportedSurfaces"]
            )

            claims_path.write_text(
                json.dumps(
                    {
                        "schemaVersion": 1,
                        "scopeClosed": True,
                        "claims": [
                            {
                                "family": "network.https",
                                "surface": "Mars",
                                "description": "Loads Martian data",
                            }
                        ],
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            rejected = self.run_script(project)
            self.assertNotEqual(0, rejected.returncode)
            self.assertIn("surface", rejected.stderr)

    def test_js_literals_and_comments_do_not_create_markup_or_api_inventory(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory)
            (project / "pages" / "index").mkdir(parents=True)
            (project / "app.json").write_text(
                '{"pages":["pages/index/index"]}\n', encoding="utf-8"
            )
            (project / "pages" / "index" / "index.ink").write_text(
                """
<page><text>Ready; _blank is documentation, not a target declaration.</text></page>
<script setup>
const fakeMarkup = '<button bindtap="ghost">fake</button><scroll-view><future-view /></scroll-view>';
const fakeApis = "wx.request(); fetch('https://fake.invalid'); document.querySelector('body')";
// <button bindtap="commentGhost">fake</button> wx.request();
/* <scroll-view><future-view /></scroll-view> fetch('https://fake.invalid'); */
export default { ready() { return fakeMarkup + fakeApis; } };
</script>
""".strip()
                + "\n",
                encoding="utf-8",
            )

            result = self.run_script(project)
            self.assertEqual(0, result.returncode, result.stderr)
            report = json.loads(result.stdout)
            families = {item["family"] for item in report["items"]}
            self.assertTrue(families.isdisjoint({
                "ui.button",
                "event.bindtap",
                "component.scroll-view",
                "network.https",
            }))
            symbols = {entry["symbol"] for entry in report["unmatchedSymbols"]}
            self.assertNotIn("<future-view>", symbols)
            self.assertFalse(any("document" in symbol for symbol in symbols))
            self.assertEqual([], report["supportedSurfaces"])

    def test_speech_association_is_lexically_scoped_and_accepts_inline_start(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory)
            (project / "pages" / "index").mkdir(parents=True)
            (project / "app.json").write_text(
                '{"pages":["pages/index/index"]}\n', encoding="utf-8"
            )
            (project / "pages" / "index" / "index.ink").write_text(
                """
<page><text>Ready</text></page>
<script setup>
function orphanedConstructor() {
  const recognition = new SpeechRecognition();
}
function unrelatedObject() {
  const recognition = { start() {}, stop() {} };
  recognition.start();
  recognition.stop();
}
function crossScopeAlias() {
  const aliased = new SpeechRecognition();
  this.sharedRecognition = aliased;
}
function crossScopeUse() {
  this.sharedRecognition.start();
  this.sharedRecognition.stop();
}
function validOwned() {
  const owned = new SpeechRecognition();
  owned.start();
  owned.stop();
}
function validInline() {
  new SpeechRecognition().start();
}
function locallyShadowed(SpeechRecognition) {
  const localRecognition = new SpeechRecognition();
  localRecognition.start();
  localRecognition.stop();
}
</script>
""".strip()
                + "\n",
                encoding="utf-8",
            )

            result = self.run_script(project)
            self.assertEqual(0, result.returncode, result.stderr)
            report = json.loads(result.stdout)
            runtime = [
                item
                for item in report["items"]
                if item["family"] == "ai.speech-recognition"
            ]
            companions = [
                item
                for item in report["items"]
                if item["family"] == "voice.declaration.unknown"
            ]
            self.assertEqual(2, len(runtime))
            self.assertEqual(2, len(companions))
            self.assertEqual(
                {20, 25},
                {item["locations"][0]["line"] for item in runtime},
            )
            self.assertEqual(
                {
                    f"COMPANION:voice.declaration.unknown@{item['gate']}"
                    for item in companions
                },
                {item["declarationBinding"] for item in runtime},
            )
            symbols = {entry["symbol"] for entry in report["unmatchedSymbols"]}
            self.assertIn("new SpeechRecognition:instance-start-association", symbols)
            self.assertIn("SpeechRecognition.stop:instance-association", symbols)

    def test_fetch_and_document_shadowing_is_lexical(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory)
            (project / "pages" / "index").mkdir(parents=True)
            (project / "app.json").write_text(
                '{"pages":["pages/index/index"]}\n', encoding="utf-8"
            )
            (project / "pages" / "index" / "index.ink").write_text(
                """
<page><text>Ready</text></page>
<script setup>
function injected(fetch, document) {
  fetch('/local');
  document.querySelector('local');
}
function declarations() {
  const fetch = () => Promise.resolve();
  const document = { open() {} };
  fetch('/local');
  document.open();
}
function platform() {
  fetch('https://example.invalid');
  document.querySelector('body');
}
</script>
""".strip()
                + "\n",
                encoding="utf-8",
            )

            result = self.run_script(project)
            self.assertEqual(0, result.returncode, result.stderr)
            report = json.loads(result.stdout)
            network_items = [
                item for item in report["items"] if item["family"] == "network.https"
            ]
            self.assertEqual(1, len(network_items))
            self.assertEqual(14, network_items[0]["locations"][0]["line"])
            symbols = {entry["symbol"] for entry in report["unmatchedSymbols"]}
            self.assertIn("document.querySelector", symbols)
            self.assertNotIn("document.open", symbols)
            self.assertNotIn("REFERENCE:document", symbols)

    def test_fetch_alias_ignores_destructured_var_shadows_and_method_syntax(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory)
            (project / "pages" / "index").mkdir(parents=True)
            (project / "app.json").write_text(
                '{"pages":["pages/index/index"]}\n', encoding="utf-8"
            )
            source = """
<page><text>Ready</text></page>
<script setup>
function destructuredShadow() {
  const { fetch } = adapters;
  const request = fetch;
  return request('/local-destructured');
}
function varShadow(flag) {
  if (flag) { var fetch = adapters.fetch; }
  const request = fetch;
  return request('/local-var');
}
const load = fetch;
export default {
  load() { return 'method declaration, not an alias call'; },
  platform() {
    return load('https://example.invalid');
  }
};
</script>
""".strip() + "\n"
            (project / "pages" / "index" / "index.ink").write_text(
                source, encoding="utf-8"
            )

            result = self.run_script(project)
            self.assertEqual(0, result.returncode, result.stderr)
            report = json.loads(result.stdout)
            network_items = [
                item for item in report["items"] if item["family"] == "network.https"
            ]
            self.assertEqual(1, len(network_items))
            self.assertEqual("fetch-alias:load", network_items[0]["mechanism"])
            self.assertEqual(
                source.splitlines().index(
                    "    return load('https://example.invalid');"
                )
                + 1,
                network_items[0]["locations"][0]["line"],
            )

    def test_claims_ledger_reports_missing_and_closed_content_hash(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory)
            (project / "app.json").write_text('{"pages":[]}\n', encoding="utf-8")

            missing = self.run_script(project)
            self.assertEqual(0, missing.returncode, missing.stderr)
            self.assertEqual(
                {
                    "path": "aiui-audit-claims.json",
                    "present": False,
                    "scopeClosed": False,
                    "sha256": None,
                    "claimCount": 0,
                },
                json.loads(missing.stdout)["claimsLedger"],
            )

            claims_text = json.dumps(
                {
                    "schemaVersion": 1,
                    "scopeClosed": True,
                    "claims": [
                        {
                            "family": "network.https",
                            "surface": "_current",
                            "description": "Loads current conditions",
                        }
                    ],
                },
                ensure_ascii=False,
            )
            claims_bytes = (claims_text + "\n").encode("utf-8")
            (project / "aiui-audit-claims.json").write_bytes(claims_bytes)
            closed = self.run_script(project)
            self.assertEqual(0, closed.returncode, closed.stderr)
            self.assertEqual(
                {
                    "path": "aiui-audit-claims.json",
                    "present": True,
                    "scopeClosed": True,
                    "sha256": hashlib.sha256(claims_bytes).hexdigest(),
                    "claimCount": 1,
                },
                json.loads(closed.stdout)["claimsLedger"],
            )

    def test_registered_claims_never_borrow_an_unrelated_real_source_binding(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory)
            (project / "pages" / "index").mkdir(parents=True)
            (project / "app.json").write_text(
                '{"pages":["pages/index/index"]}\n', encoding="utf-8"
            )
            (project / "pages" / "index" / "index.ink").write_text(
                """
<page><text>Ready</text></page>
<style>@media (target: _current) { page { color: white; } }</style>
<script setup>fetch('https://example.invalid');</script>
""".strip()
                + "\n",
                encoding="utf-8",
            )
            (project / "aiui-audit-claims.json").write_text(
                json.dumps(
                    {
                        "schemaVersion": 1,
                        "scopeClosed": True,
                        "claims": [
                            {
                                "family": "network.https",
                                "surface": "_current",
                                "description": "Loads the current forecast",
                            },
                            {
                                "family": "network.https",
                                "surface": "_blank",
                                "description": "Loads a blank-surface forecast",
                            },
                            {
                                "family": "page.route",
                                "surface": "_current",
                                "description": "Routes to the current surface",
                            },
                            {
                                "family": "page.route",
                                "surface": "_blank",
                                "description": "Routes to the blank surface",
                            },
                        ],
                    }
                )
                + "\n",
                encoding="utf-8",
            )

            result = self.run_script(project)
            self.assertEqual(0, result.returncode, result.stderr)
            report = json.loads(result.stdout)
            network_items = [
                item for item in report["items"] if item["family"] == "network.https"
            ]
            self.assertEqual(3, len(network_items))
            source_item = next(
                item
                for item in network_items
                if item["locations"][0]["path"] != "aiui-audit-claims.json"
            )
            self.assertEqual("registered", source_item["policyState"])
            unresolved = [
                item
                for item in network_items
                if item["locations"][0]["path"] == "aiui-audit-claims.json"
            ]
            self.assertEqual(2, len(unresolved))
            self.assertTrue(
                all(item["policyState"] == "binding-unresolved" for item in unresolved)
            )
            self.assertTrue(
                any("@_current:" in item["mechanism"] for item in unresolved)
            )
            self.assertTrue(any("@_blank:" in item["mechanism"] for item in unresolved))
            route_items = [
                item for item in report["items"] if item["family"] == "page.route"
            ]
            self.assertEqual(3, len(route_items))
            self.assertEqual(
                2,
                sum(
                    item["locations"][0]["path"] == "aiui-audit-claims.json"
                    for item in route_items
                ),
            )
            unresolved_routes = [
                item
                for item in route_items
                if item["locations"][0]["path"] == "aiui-audit-claims.json"
            ]
            self.assertTrue(
                any("@_current:" in item["mechanism"] for item in unresolved_routes)
            )
            self.assertTrue(
                any("@_blank:" in item["mechanism"] for item in unresolved_routes)
            )
            self.assertEqual(["_blank", "_current"], report["supportedSurfaces"])

    def test_inventory_emits_supported_surfaces_and_distinct_input_gates(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory)
            (project / "pages" / "index").mkdir(parents=True)
            (project / "app.json").write_text(
                '{"pages":["pages/index/index"]}\n', encoding="utf-8"
            )
            (project / "aiui-audit-claims.json").write_text(
                json.dumps(
                    {
                        "schemaVersion": 1,
                        "scopeClosed": True,
                        "claims": [
                            {
                                "family": "page.target",
                                "surface": "_blank",
                                "description": "Supports blank display",
                            }
                        ],
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            (project / "pages" / "index" / "index.ink").write_text(
                """
<page>
  <button bindtap="start">Start</button>
  <button bindtap="stop">Stop</button>
  <scroll-view><text>Scrollable</text></scroll-view>
</page>
<style>@media (target: _current) { page { color: white; } }</style>
<script setup>
export default {
  start() {},
  stop() {},
  onKeyDown(event) {
    if (event.code === "Enter") this.start();
    if (event.code === "ArrowDown") this.stop();
  },
  onKeyUp(event) {
    if (event.code === "Backspace") this.stop();
  },
  onVoiceWakeup(event) { return event.keyword; },
  onHeadGesture(event) { return event.type; },
  onLoad() { this.enableWorldAwareness(); }
};
</script>
""".strip()
                + "\n",
                encoding="utf-8",
            )

            result = self.run_script(project)
            self.assertEqual(0, result.returncode, result.stderr)
            report = json.loads(result.stdout)
            self.assertEqual(["_blank", "_current"], report["supportedSurfaces"])
            input_gates = report["inputGates"]
            self.assertEqual(
                input_gates,
                sorted(
                    input_gates,
                    key=lambda entry: (entry["kind"], entry["gate"], entry["family"]),
                ),
            )
            self.assertTrue(
                all(set(entry) == {"family", "kind", "gate"} for entry in input_gates)
            )
            by_family: dict[str, list[dict[str, object]]] = {}
            for entry in input_gates:
                by_family.setdefault(str(entry["family"]), []).append(entry)
            self.assertEqual(2, len(by_family["event.bindtap"]))
            self.assertTrue(
                {
                    "component.scroll-view",
                    "event.bindtap",
                    "input.enter",
                    "input.back",
                    "input.scroll.host",
                    "input.voice-wakeup",
                    "input.head-gesture",
                }.issubset(by_family)
            )
            self.assertEqual(len(input_gates), len({entry["gate"] for entry in input_gates}))

    def test_const_fetch_alias_and_switch_key_cases_are_inventoried(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory)
            (project / "pages" / "index").mkdir(parents=True)
            (project / "app.json").write_text(
                '{"pages":["pages/index/index"]}\n', encoding="utf-8"
            )
            (project / "aiui-audit-claims.json").write_text(
                '{"schemaVersion":1,"scopeClosed":true,"claims":[]}\n',
                encoding="utf-8",
            )
            (project / "pages" / "index" / "index.ink").write_text(
                """
<page><text>Ready</text></page>
<style>@media (target: _current) { page { color: white; } }</style>
<script setup>
const request = fetch;
export default {
  load() { return request('https://example.invalid'); },
  onKeyUp(event) {
    switch (event.code) {
      case "Enter": this.load(); break;
      case "Backspace": return;
    }
  }
};
</script>
""".strip()
                + "\n",
                encoding="utf-8",
            )

            result = self.run_script(project)
            self.assertEqual(0, result.returncode, result.stderr)
            report = json.loads(result.stdout)
            families = {item["family"] for item in report["items"]}
            self.assertIn("network.https", families)
            self.assertIn("input.enter", families)
            self.assertIn("input.back", families)
            network = next(
                item for item in report["items"] if item["family"] == "network.https"
            )
            self.assertEqual("fetch(...)", network["apiBinding"])
            input_families = {entry["family"] for entry in report["inputGates"]}
            self.assertTrue({"input.enter", "input.back"}.issubset(input_families))

    def test_switch_key_cases_ignore_strings_and_nested_non_event_switches(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory)
            (project / "pages" / "index").mkdir(parents=True)
            (project / "app.json").write_text(
                '{"pages":["pages/index/index"]}\n', encoding="utf-8"
            )
            (project / "pages" / "index" / "index.ink").write_text(
                """
<page><text>Ready</text></page>
<script setup>
export default {
  onKeyUp(event) {
    const documentation = 'switch (event.code) { case "Backspace": break; }';
    switch (event.code) {
      case "Enter":
        switch (mode) {
          case "Backspace": break;
        }
        break;
      case "ArrowDown": break;
    }
  }
};
</script>
""".strip()
                + "\n",
                encoding="utf-8",
            )

            result = self.run_script(project)
            self.assertEqual(0, result.returncode, result.stderr)
            report = json.loads(result.stdout)
            key_items = [
                item
                for item in report["items"]
                if item["family"]
                in {"input.enter", "input.back", "input.scroll.host"}
            ]
            self.assertEqual(
                {"input.enter", "input.scroll.host"},
                {item["family"] for item in key_items},
            )
            self.assertEqual(2, len(key_items))

    def test_switch_key_cases_survive_regex_literals_with_exact_offsets(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory)
            (project / "pages" / "index").mkdir(parents=True)
            (project / "app.json").write_text(
                '{"pages":["pages/index/index"]}\n', encoding="utf-8"
            )
            source = """
<page><text>Ready</text></page>
<script setup>
export default {
  onKeyUp(event) {
    const closingBrace = /[}]/;
    switch (event.code) {
      case "Enter": break;
      case "Backspace": break;
    }
  }
};
</script>
""".strip() + "\n"
            (project / "pages" / "index" / "index.ink").write_text(
                source, encoding="utf-8"
            )

            result = self.run_script(project)
            self.assertEqual(0, result.returncode, result.stderr)
            report = json.loads(result.stdout)
            by_family = {
                item["family"]: item
                for item in report["items"]
                if item["family"] in {"input.enter", "input.back"}
            }
            self.assertEqual({"input.enter", "input.back"}, set(by_family))
            expected_locations = {
                "input.enter": (
                    source.splitlines().index('      case "Enter": break;') + 1,
                    7,
                ),
                "input.back": (
                    source.splitlines().index('      case "Backspace": break;') + 1,
                    7,
                ),
            }
            for family, (line, column) in expected_locations.items():
                self.assertEqual(
                    {"path": "pages/index/index.ink", "line": line, "column": column},
                    by_family[family]["locations"][0],
                )

    def test_claim_description_cannot_borrow_same_family_source(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory)
            (project / "pages" / "index").mkdir(parents=True)
            (project / "app.json").write_text(
                '{"pages":["pages/index/index"]}\n', encoding="utf-8"
            )
            (project / "pages" / "index" / "index.ink").write_text(
                """
<page><text>Weather</text></page>
<style>@media (target: _current) { page { color: white; } }</style>
<script setup>fetch('https://weather.example.invalid');</script>
""".strip()
                + "\n",
                encoding="utf-8",
            )
            (project / "aiui-audit-claims.json").write_text(
                json.dumps(
                    {
                        "schemaVersion": 1,
                        "scopeClosed": True,
                        "claims": [
                            {
                                "family": "network.https",
                                "surface": "_current",
                                "description": "Uploads biometric data",
                            }
                        ],
                    }
                )
                + "\n",
                encoding="utf-8",
            )

            result = self.run_script(project)
            self.assertEqual(0, result.returncode, result.stderr)
            report = json.loads(result.stdout)
            network_items = [
                item for item in report["items"] if item["family"] == "network.https"
            ]
            self.assertEqual(2, len(network_items))
            claim_item = next(
                item
                for item in network_items
                if item["locations"][0]["path"] == "aiui-audit-claims.json"
            )
            self.assertEqual("binding-unresolved", claim_item["policyState"])
            self.assertEqual("PROJECT-BINDING:UNRESOLVED", claim_item["apiBinding"])
            self.assertIn("Uploads biometric data", claim_item["mechanism"])

    def test_registered_provisional_claim_families_remain_typed_inputs(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory)
            (project / "app.json").write_text('{"pages":[]}\n', encoding="utf-8")
            families = (
                "input.scroll.unknown",
                "input.voice.unknown",
                "input.fallback.unknown",
                "input.touch-migration.unknown",
                "input.gesture-fallback.unknown",
                "network.unknown",
            )
            (project / "aiui-audit-claims.json").write_text(
                json.dumps(
                    {
                        "schemaVersion": 1,
                        "scopeClosed": True,
                        "claims": [
                            {
                                "family": family,
                                "surface": "Page",
                                "description": f"Product scope for {family}",
                            }
                            for family in families
                        ],
                    }
                )
                + "\n",
                encoding="utf-8",
            )

            result = self.run_script(project)
            self.assertEqual(0, result.returncode, result.stderr)
            report = json.loads(result.stdout)
            reported_families = {item["family"] for item in report["items"]}
            self.assertTrue(set(families).issubset(reported_families))
            self.assertNotIn("project.unregistered", reported_families)
            input_families = {entry["family"] for entry in report["inputGates"]}
            self.assertEqual(set(families) - {"network.unknown"}, input_families)
            self.assertTrue(
                all(
                    item["policyState"] == "binding-unresolved"
                    for item in report["items"]
                )
            )


if __name__ == "__main__":
    unittest.main()
