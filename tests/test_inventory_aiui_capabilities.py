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
        repository_root: Path | None = None,
    ) -> subprocess.CompletedProcess[str]:
        argv = [
            sys.executable,
            str(SCRIPT),
            str(project),
            "--target-version",
            target_version,
        ]
        if repository_root is not None:
            argv.extend(("--repository-root", str(repository_root)))
        return subprocess.run(
            argv,
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
        result = self.run_script(
            ROOT / "skills" / "rokid-aiui-agent" / "assets" / "focus-timer-agent"
        )
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
        self.assertIn("input.key.unknown", by_family)
        self.assertIn(
            "onKeyUp(event.code=GlobalHook)",
            {item["mechanism"] for item in by_family["input.key.unknown"]},
        )
        unregistered_bindings = {
            item["apiBinding"]
            for item in by_family["project.unregistered"]
        }
        self.assertTrue(
            {
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

    def test_local_and_imported_wx_are_not_platform_capabilities(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory)
            (project / "pages" / "global").mkdir(parents=True)
            (project / "lib").mkdir()
            (project / "app.json").write_text(
                '{"pages":["pages/global/index"]}\n', encoding="utf-8"
            )
            (project / "pages" / "global" / "index.ink").write_text(
                "<page><text>Global</text></page>\n"
                "<script setup>export default { onLoad() { "
                "wx.request({ url: '/official' }); } };</script>\n",
                encoding="utf-8",
            )
            local_sources = {
                "default.js": (
                    "import wx from './fake';\n"
                    "wx.request({ url: '/default' });\n"
                ),
                "namespace.js": (
                    "import * as wx from './fake';\n"
                    "wx.request({ url: '/namespace' });\n"
                ),
                "named.js": (
                    "import { client as wx } from './fake';\n"
                    "wx.request({ url: '/named' });\n"
                ),
                "local.js": (
                    "const wx = { request(options) { return options; } };\n"
                    "wx.request({ url: '/local' });\n"
                ),
                "parameter.js": (
                    "function invoke(wx) { return wx.request({ url: '/param' }); }\n"
                ),
            }
            for name, source in local_sources.items():
                (project / "lib" / name).write_text(source, encoding="utf-8")
            (project / "lib" / "fake.js").write_text(
                "export const client = { request(options) { return options; } };\n"
                "export default client;\n",
                encoding="utf-8",
            )

            result = self.run_script(project)

            self.assertEqual(0, result.returncode, result.stderr)
            report = json.loads(result.stdout)
            network_paths = [
                item["locations"][0]["path"]
                for item in report["items"]
                if item["family"] == "network.https"
            ]
            self.assertEqual(["pages/global/index.ink"], network_paths)
            local_wx_findings = [
                (
                    entry["path"],
                    entry["line"],
                    entry["column"],
                    entry["symbol"],
                )
                for entry in report["unmatchedSymbols"]
                if entry["path"].startswith("lib/")
                and "wx" in entry["symbol"]
            ]
            self.assertEqual([], local_wx_findings)

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

    def test_key_callbacks_support_named_bracket_and_destructured_code_inputs(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory)
            page_sources = {
                "named": """
<page><text>Named</text></page>
<script setup>
export default {
  onKeyDown(e) { if (e.code === "Enter") return; }
};
</script>
""",
                "bracket": """
<page><text>Bracket</text></page>
<script setup>
export default {
  onKeyUp(event) { if (event['code'] === "Backspace") return; }
};
</script>
""",
                "destructured": """
<page><text>Destructured</text></page>
<script setup>
export default {
  onKeyUp({ code }) {
    switch (code) { case "ArrowDown": return; }
  }
};
</script>
""",
            }
            (project / "app.json").write_text(
                json.dumps(
                    {
                        "pages": [
                            f"pages/{name}/index" for name in sorted(page_sources)
                        ]
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            for name, source in page_sources.items():
                page = project / "pages" / name
                page.mkdir(parents=True)
                (page / "index.ink").write_text(
                    source.strip() + "\n", encoding="utf-8"
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
                    "onKeyDown(event.code=Enter)",
                    "onKeyUp(event.code=Backspace)",
                    "onKeyUp(event.code=ArrowDown)",
                },
                bindings,
            )
            self.assertFalse(
                any(
                    entry["symbol"].endswith(":input-unresolved")
                    for entry in report["unmatchedSymbols"]
                )
            )

    def test_partially_unresolved_key_callback_is_quarantined(self) -> None:
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
  onKeyUp(e) {
    if (e.code === "Enter") return;
    if (e.code === configuredCode) return;
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
            self.assertIn(
                "onKeyUp(event.code=Enter",
                " ".join(
                    str(item["apiBinding"])
                    for item in report["items"]
                    if item["family"] == "input.enter"
                ),
            )
            provisional = [
                item
                for item in report["items"]
                if item["family"] == "input.key.unknown"
            ]
            self.assertEqual(1, len(provisional))
            self.assertEqual("binding-unresolved", provisional[0]["policyState"])
            self.assertEqual(
                "PROJECT-BINDING:UNRESOLVED", provisional[0]["apiBinding"]
            )
            self.assertIn(
                provisional[0]["gate"],
                {
                    entry["gate"]
                    for entry in report["inputGates"]
                    if entry["family"] == "input.key.unknown"
                },
            )

    def test_unparsed_key_callback_syntax_retains_a_typed_input_gate(self) -> None:
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
  onKeyDown: (payload) => handleKey(payload),
  onKeyUp
};
</script>
""".strip()
                + "\n",
                encoding="utf-8",
            )

            result = self.run_script(project)
            self.assertEqual(0, result.returncode, result.stderr)
            report = json.loads(result.stdout)
            provisional = [
                item
                for item in report["items"]
                if item["family"] == "input.key.unknown"
            ]
            self.assertEqual(2, len(provisional))
            self.assertTrue(
                all(item["policyState"] == "binding-unresolved" for item in provisional)
            )
            self.assertEqual(
                {item["gate"] for item in provisional},
                {
                    entry["gate"]
                    for entry in report["inputGates"]
                    if entry["family"] == "input.key.unknown"
                },
            )

    def test_quoted_and_static_computed_key_callbacks_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory)
            (project / "pages" / "quoted").mkdir(parents=True)
            (project / "pages" / "computed").mkdir(parents=True)
            (project / "app.json").write_text(
                '{"pages":["pages/quoted/index","pages/computed/index"]}\n',
                encoding="utf-8",
            )
            (project / "pages" / "quoted" / "index.ink").write_text(
                """
<page><text>Quoted</text></page>
<script setup>
export default {
  'onKeyUp'(event) { return event.code === 'Enter'; }
};
</script>
""".strip()
                + "\n",
                encoding="utf-8",
            )
            (project / "pages" / "computed" / "index.ink").write_text(
                """
<page><text>Computed</text></page>
<script setup>
export default {
  ['onKey' + 'Down'](event) { return event.code === 'Backspace'; }
};
</script>
""".strip()
                + "\n",
                encoding="utf-8",
            )

            result = self.run_script(project)
            self.assertEqual(0, result.returncode, result.stderr)
            report = json.loads(result.stdout)
            provisional = [
                item
                for item in report["items"]
                if item["family"] == "input.key.unknown"
            ]
            self.assertEqual(
                {"pages/quoted/index.ink", "pages/computed/index.ink"},
                {item["locations"][0]["path"] for item in provisional},
            )
            self.assertTrue(
                all(item["policyState"] == "binding-unresolved" for item in provisional)
            )

    def test_nested_helper_parameter_shadow_is_not_outer_key_input(self) -> None:
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
    function helper(event) { return event.code === 'Enter'; }
    const arrow = (event) => event.code === 'Backspace';
    return helper(event) || arrow(event);
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
            self.assertFalse(
                any(
                    item["family"] in {"input.enter", "input.back"}
                    for item in report["items"]
                )
            )
            self.assertEqual(
                1,
                sum(
                    item["family"] == "input.key.unknown"
                    for item in report["items"]
                ),
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

    def test_typescript_type_only_fetch_is_not_runtime_network(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory)
            (project / "lib").mkdir()
            (project / "app.json").write_text(
                '{"pages":[]}\n', encoding="utf-8"
            )
            (project / "lib" / "types.ts").write_text(
                "interface Client {\n"
                "  fetch(url: string): Promise<Response>;\n"
                "}\n"
                "type ClientAlias = { fetch(url: string): Promise<Response> };\n"
                "type NativeFetch = typeof fetch;\n"
                "type Requester = (fetch: (url: string) => unknown) => unknown;\n"
                "abstract class AbstractClient {\n"
                "  abstract fetch(url: string): Promise<Response>;\n"
                "}\n"
                "function invoke(fetch: (url: string) => unknown) {\n"
                "  return fetch('/local');\n"
                "}\n",
                encoding="utf-8",
            )
            (project / "lib" / "runtime.ts").write_text(
                "fetch('/official');\n", encoding="utf-8"
            )

            result = self.run_script(project)

            self.assertEqual(0, result.returncode, result.stderr)
            report = json.loads(result.stdout)
            network_paths = [
                item["locations"][0]["path"]
                for item in report["items"]
                if item["family"] == "network.https"
            ]
            self.assertEqual(["lib/runtime.ts"], network_paths)
            self.assertFalse(
                any(
                    entry["path"] == "lib/types.ts"
                    and "fetch" in entry["symbol"]
                    for entry in report["unmatchedSymbols"]
                )
            )

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

    def test_unclosed_surface_owner_composition_is_quarantined(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory)
            (project / "pages" / "index").mkdir(parents=True)
            (project / "pages" / "proto").mkdir(parents=True)
            (project / "pages" / "reexport").mkdir(parents=True)
            (project / "pages" / "unicode").mkdir(parents=True)
            (project / "pages" / "generator").mkdir(parents=True)
            (project / "pages" / "async-generator").mkdir(parents=True)
            (project / "widgets" / "card").mkdir(parents=True)
            (project / "workers").mkdir()
            (project / "app.json").write_text(
                json.dumps(
                    {
                        "pages": [
                            "pages/index/index",
                            "pages/proto/index",
                            "pages/reexport/index",
                            "pages/unicode/index",
                            "pages/generator/index",
                            "pages/async-generator/index",
                        ],
                        "widgets": [
                            {"path": "widgets/card/index", "family": "1x1"}
                        ],
                        "agentWorkers": [
                            {
                                "name": "job",
                                "script": "workers/job.js",
                                "trigger": {"type": "open"},
                                "lifetime": "instant",
                            }
                        ],
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            (project / "pages" / "index" / "index.ink").write_text(
                """
<page><text>Page</text></page>
<script setup>
const hiddenHandlers = {
  onKeyUp(event) { return event.code === 'Enter'; }
};
export default { ...hiddenHandlers };
</script>
""".strip()
                + "\n",
                encoding="utf-8",
            )
            (project / "pages" / "proto" / "index.ink").write_text(
                "<page><text>Proto</text></page>\n"
                "<script setup>export default { __proto__: { "
                "onKeyUp(event) { return event.code === 'Enter'; } "
                "} };</script>\n",
                encoding="utf-8",
            )
            (project / "pages" / "reexport" / "index.ink").write_text(
                "<page><text>Re-export</text></page>\n"
                "<script setup>const page = { onLoad() {} }; "
                "export { page as default };</script>\n",
                encoding="utf-8",
            )
            (project / "pages" / "unicode" / "index.ink").write_text(
                "<page><text>Unicode</text></page>\n"
                "<script setup>export default { "
                "onK\\u0065yUp(event) { return event.code; } "
                "};</script>\n",
                encoding="utf-8",
            )
            (project / "pages" / "generator" / "index.ink").write_text(
                "<page><text>Generator</text></page>\n"
                "<script setup>export default { "
                "*onKeyUp(event) { yield event.code; } "
                "};</script>\n",
                encoding="utf-8",
            )
            (project / "pages" / "async-generator" / "index.ink").write_text(
                "<page><text>Async generator</text></page>\n"
                "<script setup>export default { "
                "async *onKeyUp(event) { yield event.code; } "
                "};</script>\n",
                encoding="utf-8",
            )
            (project / "widgets" / "card" / "index.ink").write_text(
                """
<widget><text>Widget</text></widget>
<script setup>
const widget = { onCreate() {} };
export default widget;
</script>
""".strip()
                + "\n",
                encoding="utf-8",
            )
            (project / "workers" / "job.js").write_text(
                """
import { handlers } from './handlers';
export default { ...handlers };
""".strip()
                + "\n",
                encoding="utf-8",
            )
            (project / "app.js").write_text(
                "const app = { onLaunch() {}, onError(error) {} };\n"
                "export default app;\n",
                encoding="utf-8",
            )

            result = self.run_script(project, target_version="0.18.0")
            self.assertEqual(0, result.returncode, result.stderr)
            report = json.loads(result.stdout)
            composition = {
                (entry["symbol"], entry["path"])
                for entry in report["unmatchedSymbols"]
                if entry["symbol"].endswith("owner-composition-unresolved")
            }
            self.assertEqual(
                {
                    (
                        "Page.owner-composition-unresolved",
                        "pages/index/index.ink",
                    ),
                    (
                        "Widget.owner-composition-unresolved",
                        "widgets/card/index.ink",
                    ),
                    (
                        "AgentWorker.owner-composition-unresolved",
                        "workers/job.js",
                    ),
                    (
                        "Page.owner-composition-unresolved",
                        "pages/proto/index.ink",
                    ),
                    (
                        "Page.owner-composition-unresolved",
                        "pages/reexport/index.ink",
                    ),
                    (
                        "Page.owner-composition-unresolved",
                        "pages/unicode/index.ink",
                    ),
                    (
                        "Page.owner-composition-unresolved",
                        "pages/generator/index.ink",
                    ),
                    (
                        "Page.owner-composition-unresolved",
                        "pages/async-generator/index.ink",
                    ),
                    (
                        "App.owner-composition-unresolved",
                        "app.js",
                    ),
                },
                composition,
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
            self.assertEqual(["Page"], report["supportedSurfaces"])

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
const helpers = {
  fetch() { return 'object method, not a global reference'; }
};
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
            self.assertNotIn(
                "REFERENCE:fetch",
                {entry["symbol"] for entry in report["unmatchedSymbols"]},
            )

    def test_global_fetch_call_followed_by_a_block_is_not_method_syntax(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory)
            (project / "lib").mkdir()
            (project / "app.json").write_text(
                '{"pages":[]}\n', encoding="utf-8"
            )
            (project / "lib" / "block.js").write_text(
                "fetch('/global')\n{ const marker = true; }\n",
                encoding="utf-8",
            )

            result = self.run_script(project)
            self.assertEqual(0, result.returncode, result.stderr)
            network = [
                item
                for item in json.loads(result.stdout)["items"]
                if item["family"] == "network.https"
            ]
            self.assertEqual(1, len(network))
            self.assertEqual(1, network[0]["locations"][0]["line"])

    def test_unconsumed_global_fetch_references_are_uniformly_quarantined(
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
fetch.call(undefined, 'https://call.example.invalid');
fetch.apply(undefined, ['https://apply.example.invalid']);
fetch.bind(undefined)('https://bind.example.invalid');
Reflect.apply(fetch, undefined, ['https://reflect.example.invalid']);
fetch?.('https://optional.example.invalid');
let net = fetch;
net('https://alias.example.invalid');
(0, fetch)('https://sequence.example.invalid');
function local(fetch) {
  fetch.call(undefined, '/local-call');
  (0, fetch)('/local-sequence');
}
</script>
""".strip()
                + "\n",
                encoding="utf-8",
            )

            result = self.run_script(project)
            self.assertEqual(0, result.returncode, result.stderr)
            report = json.loads(result.stdout)
            unmatched = report["unmatchedSymbols"]
            self.assertEqual(
                7,
                sum(entry["symbol"] == "REFERENCE:fetch" for entry in unmatched),
            )
            self.assertIn(
                "fetch-alias:net",
                {entry["symbol"] for entry in unmatched},
            )
            self.assertTrue(
                {3, 4, 5, 6, 7, 8, 10}.issubset(
                    {
                        entry["line"]
                        for entry in unmatched
                        if entry["symbol"] == "REFERENCE:fetch"
                    }
                )
            )

    def test_fetch_quarantine_distinguishes_imported_local_bindings(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory)
            (project / "pages" / "imported").mkdir(parents=True)
            (project / "pages" / "aliased").mkdir(parents=True)
            (project / "app.json").write_text(
                '{"pages":["pages/imported/index","pages/aliased/index"]}\n',
                encoding="utf-8",
            )
            (project / "pages" / "imported" / "index.js").write_text(
                "import fetch from './client';\nfetch.apply(null, []);\n",
                encoding="utf-8",
            )
            (project / "pages" / "aliased" / "index.js").write_text(
                "import { fetch as libraryFetch } from './client';\n"
                "fetch.apply(null, []);\n",
                encoding="utf-8",
            )

            result = self.run_script(project)
            self.assertEqual(0, result.returncode, result.stderr)
            report = json.loads(result.stdout)
            references = [
                entry
                for entry in report["unmatchedSymbols"]
                if entry["symbol"] == "REFERENCE:fetch"
            ]
            self.assertEqual(1, len(references))
            self.assertEqual("pages/aliased/index.js", references[0]["path"])
            self.assertEqual(2, references[0]["line"])

    def test_multiline_imported_fetch_is_not_a_platform_global(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory)
            (project / "lib").mkdir()
            (project / "app.json").write_text(
                '{"pages":[]}\n', encoding="utf-8"
            )
            (project / "lib" / "client.js").write_text(
                """
import {
  fetch
} from './client';
fetch('/local-import');
""".strip()
                + "\n",
                encoding="utf-8",
            )

            result = self.run_script(project)
            self.assertEqual(0, result.returncode, result.stderr)
            report = json.loads(result.stdout)
            self.assertFalse(
                any(
                    item["locations"][0]["path"] == "lib/client.js"
                    and item["family"]
                    in {"network.https", "project.unregistered"}
                    for item in report["items"]
                )
            )

    def test_unicode_escaped_fetch_identifiers_are_quarantined(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory)
            (project / "lib").mkdir()
            (project / "app.json").write_text(
                '{"pages":[]}\n', encoding="utf-8"
            )
            (project / "lib" / "escaped.js").write_text(
                "\\u0066etch('https://one.example.invalid');\n"
                "f\\u0065tch('https://two.example.invalid');\n"
                "// \\u0066etch('comment-only');\n",
                encoding="utf-8",
            )

            result = self.run_script(project)
            self.assertEqual(0, result.returncode, result.stderr)
            report = json.loads(result.stdout)
            references = [
                entry
                for entry in report["unmatchedSymbols"]
                if entry["symbol"] == "REFERENCE:fetch"
            ]
            self.assertEqual(2, len(references))
            self.assertEqual({1, 2}, {entry["line"] for entry in references})

    def test_unicode_escaped_platform_roots_are_quarantined_unless_shadowed(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory)
            (project / "lib").mkdir()
            (project / "app.json").write_text(
                '{"pages":[]}\n', encoding="utf-8"
            )
            (project / "lib" / "escaped.js").write_text(
                "\\u0077x.request({url: 'https://one.example.invalid'});\n"
                "navig\\u0061tor.mediaDevices.getUserMedia({video: true});\n"
                "function local(\\u0077x, navig\\u0061tor) {\n"
                "  \\u0077x.request({url: '/local'});\n"
                "  return navig\\u0061tor.mediaDevices;\n"
                "}\n",
                encoding="utf-8",
            )

            result = self.run_script(project)
            self.assertEqual(0, result.returncode, result.stderr)
            references = [
                entry
                for entry in json.loads(result.stdout)["unmatchedSymbols"]
                if entry["symbol"] in {"REFERENCE:wx", "REFERENCE:navigator"}
            ]
            self.assertEqual(
                {("REFERENCE:wx", 1), ("REFERENCE:navigator", 2)},
                {(entry["symbol"], entry["line"]) for entry in references},
            )

    def test_dynamic_code_entry_points_are_quarantined_unless_shadowed(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory)
            (project / "lib").mkdir()
            (project / "app.json").write_text(
                '{"pages":[]}\n', encoding="utf-8"
            )
            (project / "lib" / "dynamic.js").write_text(
                "eval(\"fetch('/direct')\");\n"
                "(0, eval)(\"fetch('/indirect')\");\n"
                "Function(\"return fetch('/function')\")();\n"
                "new Function(\"return wx.request({url:'/new'})\")();\n"
                "function local(eval, Function) {\n"
                "  eval('local');\n"
                "  return new Function('local');\n"
                "}\n",
                encoding="utf-8",
            )

            result = self.run_script(project)
            self.assertEqual(0, result.returncode, result.stderr)
            references = [
                entry
                for entry in json.loads(result.stdout)["unmatchedSymbols"]
                if entry["symbol"]
                in {"REFERENCE:eval", "REFERENCE:Function"}
            ]
            self.assertEqual(
                {
                    ("REFERENCE:eval", 1),
                    ("REFERENCE:eval", 2),
                    ("REFERENCE:Function", 3),
                    ("REFERENCE:Function", 4),
                },
                {(entry["symbol"], entry["line"]) for entry in references},
            )

    def test_loop_and_named_expression_bindings_do_not_shadow_later_fetch(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory)
            (project / "lib").mkdir()
            (project / "app.json").write_text(
                '{"pages":[]}\n', encoding="utf-8"
            )
            sources = {
                "loop-of.js": (
                    "for (const fetch of []) {}\n"
                    "fetch('/global-loop-of');\n"
                ),
                "loop-classic.js": (
                    "for (let fetch = local; false;) {}\n"
                    "fetch('/global-loop-classic');\n"
                ),
                "function-expression.js": (
                    "const helper = function fetch() {};\n"
                    "fetch('/global-function-expression');\n"
                ),
                "class-expression.js": (
                    "const Helper = class fetch {};\n"
                    "fetch('/global-class-expression');\n"
                ),
                "void-expression.js": (
                    "void function fetch() {};\n"
                    "fetch('/global-void-expression');\n"
                ),
                "typeof-expression.js": (
                    "typeof function fetch() {};\n"
                    "fetch('/global-typeof-expression');\n"
                ),
                "unary-expression.js": (
                    "~function fetch() {};\n"
                    "fetch('/global-unary-expression');\n"
                ),
                "function-declaration.js": (
                    "function fetch() {}\nfetch('/local-function');\n"
                ),
                "class-declaration.js": (
                    "class fetch {}\nnew fetch('/local-class');\n"
                ),
            }
            for name, source in sources.items():
                (project / "lib" / name).write_text(source, encoding="utf-8")

            result = self.run_script(project)
            self.assertEqual(0, result.returncode, result.stderr)
            report = json.loads(result.stdout)
            network_items = [
                item
                for item in report["items"]
                if item["family"] == "network.https"
            ]
            network_paths = {
                item["locations"][0]["path"]
                for item in network_items
            }
            self.assertEqual(
                {
                    "lib/class-expression.js",
                    "lib/function-expression.js",
                    "lib/loop-classic.js",
                    "lib/loop-of.js",
                    "lib/typeof-expression.js",
                    "lib/unary-expression.js",
                    "lib/void-expression.js",
                },
                network_paths,
            )
            self.assertEqual(7, len(network_items))
            self.assertTrue(
                all(item["locations"][0]["line"] == 2 for item in network_items)
            )

    def test_regex_literals_do_not_create_or_distort_global_findings(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory)
            (project / "lib").mkdir()
            (project / "app.json").write_text(
                '{"pages":[]}\n', encoding="utf-8"
            )
            (project / "lib" / "regex.js").write_text(
                "const names = /document|wx.request|fetch/;\n"
                "{ const document = {}; if (names) /{/.test('x'); }\n"
                "document.cookie;\n"
                "{ const document = {}; if (names) {} /{/.test('x'); }\n"
                "document.title;\n"
                "{ const document = {}; if (names) /x/; else /{/.test('x'); }\n"
                "document.body;\n"
                "{ const document = {}; do /{/.test('x'); while (false); }\n"
                "document.URL;\n"
                "const stringDivision = '1' / fetch('/string') / 2;\n"
                "const templateDivision = `1` / fetch('/template') / 2;\n"
                "const regexDivision = /x/ / fetch('/regex') / 2;\n"
                "let counter = 1; counter++ / fetch('/postfix') / counter;\n",
                encoding="utf-8",
            )

            result = self.run_script(project)
            self.assertEqual(0, result.returncode, result.stderr)
            report = json.loads(result.stdout)
            findings = {
                (entry["symbol"], entry["line"])
                for entry in report["unmatchedSymbols"]
                if any(
                    token in entry["symbol"]
                    for token in ("document", "fetch", "wx")
                )
            }
            self.assertEqual(
                {
                    ("REFERENCE:document.cookie", 3),
                    ("REFERENCE:document.title", 5),
                    ("REFERENCE:document.body", 7),
                    ("REFERENCE:document.URL", 9),
                },
                findings,
            )
            network_lines = {
                item["locations"][0]["line"]
                for item in report["items"]
                if item["family"] == "network.https"
            }
            self.assertEqual({10, 11, 12, 13}, network_lines)

    def test_template_expression_regex_does_not_hide_platform_calls(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory)
            (project / "lib").mkdir()
            (project / "app.json").write_text(
                '{"pages":[]}\n', encoding="utf-8"
            )
            (project / "lib" / "template.js").write_text(
                "const plain = `${/}/.test('}') && fetch('/plain')}`;\n"
                "const escaped = `${/\\}/.test('}') && fetch('/escaped')}`;\n"
                "const characterClass = `${/[}]/.test('}') && "
                "fetch('/class')}`;\n",
                encoding="utf-8",
            )

            result = self.run_script(project)
            self.assertEqual(0, result.returncode, result.stderr)
            network_lines = {
                item["locations"][0]["line"]
                for item in json.loads(result.stdout)["items"]
                if item["family"] == "network.https"
            }
            self.assertEqual({1, 2, 3}, network_lines)

    def test_self_namespace_fetch_is_quarantined_without_shadow_false_positives(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory)
            (project / "workers").mkdir(parents=True)
            (project / "lib").mkdir()
            (project / "app.json").write_text(
                json.dumps(
                    {
                        "pages": [],
                        "agentWorkers": [
                            {
                                "name": "network",
                                "script": "workers/network.js",
                                "trigger": {"type": "open"},
                                "lifetime": "instant",
                            }
                        ],
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            (project / "workers" / "network.js").write_text(
                "self.fetch('https://worker.example.invalid');\n",
                encoding="utf-8",
            )
            (project / "lib" / "local.js").write_text(
                """
function injected(self) {
  self.fetch('/local-parameter');
}
function declared() {
  const self = { fetch() {} };
  self.fetch('/local-constant');
}
""".strip()
                + "\n",
                encoding="utf-8",
            )

            result = self.run_script(project, target_version="0.18.0")
            self.assertEqual(0, result.returncode, result.stderr)
            report = json.loads(result.stdout)
            quarantines = [
                entry
                for entry in report["unmatchedSymbols"]
                if entry["symbol"] == "self.fetch"
            ]
            self.assertEqual(1, len(quarantines))
            self.assertEqual("workers/network.js", quarantines[0]["path"])
            self.assertEqual(1, quarantines[0]["line"])

    def test_parameter_destructuring_declares_bindings_not_property_keys(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory)
            (project / "lib").mkdir()
            (project / "app.json").write_text(
                '{"pages":[]}\n', encoding="utf-8"
            )
            sources = {
                "function-alias.js": """
function run({ fetch: localFetch }) {
  localFetch('/local');
  fetch('https://global.example.invalid');
}
""",
                "function-shorthand.js": """
function run({ fetch }) {
  fetch('/local');
}
""",
                "method-alias.js": """
const handlers = {
  run({ self: localSelf }) {
    localSelf.fetch('/local');
    self.fetch('https://global.example.invalid');
  }
};
""",
                "method-shorthand.js": """
const handlers = {
  run({ self }) {
    self.fetch('/local');
  }
};
""",
                "arrow-alias.js": """
const run = ({ document: localDocument }) =>
  document.querySelector('global');
""",
                "arrow-shorthand.js": """
const run = ({ document }) => document.querySelector('local');
""",
                "function-binding-alias.js": """
function run({ transport: fetch }) {
  fetch('/local');
}
""",
                "complex-alias.js": """
function run({ network: { fetch: localFetch } = defaults, ...rest }) {
  fetch('https://global.example.invalid');
}
""",
            }
            for name, source in sources.items():
                (project / "lib" / name).write_text(
                    source.strip() + "\n", encoding="utf-8"
                )

            result = self.run_script(project)
            self.assertEqual(0, result.returncode, result.stderr)
            report = json.loads(result.stdout)
            network_paths = {
                item["locations"][0]["path"]
                for item in report["items"]
                if item["family"] == "network.https"
            }
            self.assertEqual(
                {"lib/function-alias.js", "lib/complex-alias.js"},
                network_paths,
            )
            symbols_by_path = {
                (entry["symbol"], entry["path"])
                for entry in report["unmatchedSymbols"]
            }
            self.assertIn(("self.fetch", "lib/method-alias.js"), symbols_by_path)
            self.assertIn(
                ("document.querySelector", "lib/arrow-alias.js"),
                symbols_by_path,
            )
            self.assertFalse(
                any(
                    path in {
                        "lib/function-shorthand.js",
                        "lib/method-shorthand.js",
                        "lib/arrow-shorthand.js",
                    }
                    and symbol
                    in {"REFERENCE:fetch", "self.fetch", "document.querySelector"}
                    for symbol, path in symbols_by_path
                )
            )

    def test_evidence_exclusion_uses_only_the_explicit_repository_root(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repository = Path(directory) / "repository"
            (repository / ".Git").mkdir(parents=True)
            (repository / ".Git" / "hidden.js").write_text(
                "fetch('https://metadata.example.invalid');\n",
                encoding="utf-8",
            )

            nested_project = repository / "examples" / "agent"
            (nested_project / ".aiui-evidence").mkdir(parents=True)
            (nested_project / "app.json").write_text(
                '{"pages":[]}\n', encoding="utf-8"
            )
            (nested_project / ".aiui-evidence" / "hidden.js").write_text(
                "fetch('https://nested.example.invalid');\n", encoding="utf-8"
            )
            nested_result = self.run_script(nested_project)
            self.assertEqual(0, nested_result.returncode, nested_result.stderr)
            nested_report = json.loads(nested_result.stdout)
            self.assertIn(
                ".aiui-evidence/hidden.js",
                {
                    item["locations"][0]["path"]
                    for item in nested_report["items"]
                    if item["family"] == "network.https"
                },
            )

            explicit_nested_result = self.run_script(
                nested_project, repository_root=repository
            )
            self.assertEqual(
                0, explicit_nested_result.returncode, explicit_nested_result.stderr
            )
            self.assertIn(
                ".aiui-evidence/hidden.js",
                {
                    item["locations"][0]["path"]
                    for item in json.loads(explicit_nested_result.stdout)["items"]
                    if item["family"] == "network.https"
                },
            )

            (repository / "app.json").write_text('{"pages":[]}\n', encoding="utf-8")
            (repository / ".aiui-evidence").mkdir()
            (repository / ".aiui-evidence" / "capture.log").write_text(
                "executed evidence\n", encoding="utf-8"
            )
            unbounded_result = self.run_script(repository)
            self.assertEqual(0, unbounded_result.returncode, unbounded_result.stderr)
            unbounded_report = json.loads(unbounded_result.stdout)

            repository_result = self.run_script(
                repository, repository_root=repository
            )
            self.assertEqual(
                0, repository_result.returncode, repository_result.stderr
            )
            repository_report = json.loads(repository_result.stdout)
            self.assertNotEqual(
                unbounded_report["projectRevision"],
                repository_report["projectRevision"],
            )
            self.assertIn(
                "examples/agent/.aiui-evidence/hidden.js",
                {
                    item["locations"][0]["path"]
                    for item in repository_report["items"]
                    if item["family"] == "network.https"
                },
            )
            self.assertFalse(
                any(
                    item["locations"][0]["path"].startswith(".Git/")
                    for item in repository_report["items"]
                )
            )

    def test_nested_reserved_name_routes_and_references_remain_source(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repository = Path(directory) / "repository"
            project = repository / "examples" / "agent"
            nested_source = project / ".aiui-evidence"
            nested_source.mkdir(parents=True)
            (project / "lib").mkdir()
            (project / "app.json").write_text(
                '{"pages":[".aiui-evidence/index"]}\n', encoding="utf-8"
            )
            (nested_source / "index.ink").write_text(
                "<page><text>Nested</text></page>\n"
                "<script setup>fetch('/nested-source'); "
                "export default {};</script>\n",
                encoding="utf-8",
            )
            (project / "lib" / "reference.js").write_text(
                "const config = '../.aiui-evidence/config.json';\n",
                encoding="utf-8",
            )
            (nested_source / "config.json").write_text(
                '{"enabled":true}\n', encoding="utf-8"
            )

            result = self.run_script(project, repository_root=repository)
            self.assertEqual(0, result.returncode, result.stderr)
            report = json.loads(result.stdout)
            by_path = {
                (item["family"], item["locations"][0]["path"])
                for item in report["items"]
            }
            self.assertIn(
                ("network.https", ".aiui-evidence/index.ink"), by_path
            )
            self.assertIn(
                (
                    "project.unregistered",
                    ".aiui-evidence/config.json",
                ),
                by_path,
            )

    def test_absolute_repository_metadata_references_are_rejected(self) -> None:
        for kind in ("manifest", "runtime"):
            with self.subTest(kind=kind), tempfile.TemporaryDirectory() as directory:
                repository = Path(directory) / "repository"
                project = repository / "examples" / "agent"
                (project / "lib").mkdir(parents=True)
                reserved_path = repository / ".aiui-evidence" / "secret.json"
                manifest = {"pages": []}
                if kind == "manifest":
                    manifest["configuration"] = str(reserved_path)
                (project / "app.json").write_text(
                    json.dumps(manifest) + "\n", encoding="utf-8"
                )
                if kind == "runtime":
                    (project / "lib" / "path.js").write_text(
                        f"const hidden = {str(reserved_path)!r};\n",
                        encoding="utf-8",
                    )

                result = self.run_script(project, repository_root=repository)

                self.assertNotEqual(0, result.returncode)
                self.assertIn("RESERVED_PATH_REFERENCE", result.stderr)

    def test_explicit_repository_root_rejects_runtime_source_in_evidence(
        self,
    ) -> None:
        for evidence_name in (".aiui-evidence", ".AiUi-EvIdEnCe"):
            with self.subTest(evidence_name=evidence_name):
                with tempfile.TemporaryDirectory() as directory:
                    repository = Path(directory)
                    (repository / evidence_name).mkdir()
                    (repository / "app.json").write_text(
                        '{"pages":[]}\n', encoding="utf-8"
                    )
                    (repository / evidence_name / "hidden.js").write_text(
                        "export default { onLoad() {} };\n",
                        encoding="utf-8",
                    )

                    result = self.run_script(
                        repository, repository_root=repository
                    )
                    self.assertNotEqual(0, result.returncode)
                    self.assertIn("RESERVED_AUDIT_SOURCE", result.stderr)
                    self.assertIn(f"{evidence_name}/hidden.js", result.stderr)

    def test_nested_import_rejects_symlinked_repository_evidence_root(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            temporary = Path(directory)
            repository = temporary / "repository"
            project = repository / "examples" / "agent"
            project.mkdir(parents=True)
            (project / "app.json").write_text(
                '{"pages":[]}\n', encoding="utf-8"
            )
            external_evidence = temporary / "external-evidence"
            external_evidence.mkdir()
            (repository / ".aiui-evidence").symlink_to(
                external_evidence, target_is_directory=True
            )

            result = self.run_script(project, repository_root=repository)
            self.assertNotEqual(0, result.returncode)
            self.assertIn("RESERVED_AUDIT_SOURCE", result.stderr)
            self.assertIn(".aiui-evidence", result.stderr)

    def test_explicit_repository_root_rejects_file_evidence_root(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repository = Path(directory)
            (repository / "app.json").write_text(
                '{"pages":[]}\n', encoding="utf-8"
            )
            (repository / ".aiui-evidence").write_text(
                "not a directory\n", encoding="utf-8"
            )

            result = self.run_script(repository, repository_root=repository)
            self.assertNotEqual(0, result.returncode)
            self.assertIn("RESERVED_AUDIT_SOURCE", result.stderr)
            self.assertIn(".aiui-evidence", result.stderr)

    def test_import_root_inside_reserved_repository_directory_is_rejected(self) -> None:
        for reserved in (".git", ".Git", ".aiui-evidence", ".AiUi-EvIdEnCe"):
            with self.subTest(reserved=reserved), tempfile.TemporaryDirectory() as directory:
                repository = Path(directory) / "repository"
                project = repository / reserved / "project"
                project.mkdir(parents=True)
                (project / "app.json").write_text(
                    '{"pages":[]}\n', encoding="utf-8"
                )

                result = self.run_script(project, repository_root=repository)

                self.assertNotEqual(0, result.returncode)
                self.assertIn("reserved", result.stderr.lower())

    def test_reserved_path_references_fail_closed_while_comments_are_ignored(
        self,
    ) -> None:
        for reserved in (".git", ".Git", ".aiui-evidence", ".AiUi-EvIdEnCe"):
            with self.subTest(kind="manifest", reserved=reserved):
                with tempfile.TemporaryDirectory() as directory:
                    project = Path(directory)
                    (project / "app.json").write_text(
                        json.dumps({"pages": [f"pages/{reserved}/secret"]})
                        + "\n",
                        encoding="utf-8",
                    )
                    result = self.run_script(project)
                    self.assertNotEqual(0, result.returncode)
                    self.assertIn("RESERVED_PATH_REFERENCE", result.stderr)
                    self.assertIn(reserved, result.stderr)

            with self.subTest(kind="runtime", reserved=reserved):
                with tempfile.TemporaryDirectory() as directory:
                    project = Path(directory)
                    (project / "lib").mkdir()
                    (project / "app.json").write_text(
                        '{"pages":[]}\n', encoding="utf-8"
                    )
                    (project / "lib" / "paths.js").write_text(
                        f"const forbidden = '../{reserved}/secret';\n",
                        encoding="utf-8",
                    )
                    result = self.run_script(project)
                    self.assertNotEqual(0, result.returncode)
                    self.assertIn("RESERVED_PATH_REFERENCE", result.stderr)
                    self.assertIn(reserved, result.stderr)

        escaped_references = (
            "const path = './.aiui\\x2devidence/config.json';\n",
            "const path = './.aiui\\u002devidence/config.json';\n",
            "const path = './.aiui\\u{2d}evidence/config.json';\n",
            "const path = './.aiui-\\\nevidence/config.json';\n",
            "const path = '.aiui-' + 'evidence/config.json';\n",
            "const path = '.aiui-' + ('evidence/config.json');\n",
            "const path = `.aiui-${'evidence'}/config.json`;\n",
        )
        for source in escaped_references:
            with self.subTest(kind="escaped-runtime", source=source):
                with tempfile.TemporaryDirectory() as directory:
                    project = Path(directory)
                    (project / "lib").mkdir()
                    (project / "app.json").write_text(
                        '{"pages":[]}\n', encoding="utf-8"
                    )
                    (project / "lib" / "paths.js").write_text(
                        source, encoding="utf-8"
                    )
                    result = self.run_script(project)
                    self.assertNotEqual(0, result.returncode)
                    self.assertIn("RESERVED_PATH_REFERENCE", result.stderr)

        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory)
            (project / "lib").mkdir()
            (project / "app.json").write_text(
                '{"pages":[]}\n', encoding="utf-8"
            )
            (project / "lib" / "comments.js").write_text(
                "// .git/config is documentation only\n"
                "/* .aiui-evidence/capture.json is documentation only */\n"
                "// './.aiui\\x2devidence/config.json' is documentation only\n"
                "const reservedPattern = /\\.git\\/|\\.aiui-evidence\\//;\n"
                "const workflow = '.github/workflows/check.yml';\n",
                encoding="utf-8",
            )

            result = self.run_script(project)
            self.assertEqual(0, result.returncode, result.stderr)

    def test_project_json_configuration_is_never_silently_ignored(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory)
            (project / "pages" / "index").mkdir(parents=True)
            (project / "config").mkdir()
            (project / "app.json").write_text(
                '{"pages":["pages/index/index"]}\n', encoding="utf-8"
            )
            (project / "pages" / "index" / "index.json").write_text(
                '{"navigationBarTitleText":"Inventory"}\n', encoding="utf-8"
            )
            (project / "config" / "runtime.json").write_text(
                '{"feature":"dynamic"}\n', encoding="utf-8"
            )
            (project / "aiui-audit-scope.json").write_text(
                '{}\n', encoding="utf-8"
            )

            result = self.run_script(project)
            self.assertEqual(0, result.returncode, result.stderr)
            symbols = {
                entry["symbol"]
                for entry in json.loads(result.stdout)["unmatchedSymbols"]
            }
            self.assertEqual(
                {
                    "CONFIGURATION:config/runtime.json",
                    "CONFIGURATION:pages/index/index.json",
                },
                {symbol for symbol in symbols if symbol.startswith("CONFIGURATION:")},
            )
            self.assertFalse(
                any("aiui-audit-scope.json" in symbol for symbol in symbols)
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
            self.assertEqual(
                ["Page", "_blank", "_current"], report["supportedSurfaces"]
            )

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
            self.assertEqual(
                ["Page", "_blank", "_current"], report["supportedSurfaces"]
            )
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

    def test_indirect_world_awareness_calls_are_quarantined(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory)
            page_sources = {
                "direct": "this.enableWorldAwareness();",
                "optional": "this.enableWorldAwareness?.();",
                "call": "this.enableWorldAwareness.call(this);",
                "comma": "(0, this.enableWorldAwareness)();",
                "local": (
                    "const enableWorldAwareness = () => {}; "
                    "enableWorldAwareness?.();"
                ),
            }
            (project / "app.json").write_text(
                json.dumps(
                    {
                        "pages": [
                            f"pages/{name}/index" for name in sorted(page_sources)
                        ]
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            for name, body in page_sources.items():
                page = project / "pages" / name
                page.mkdir(parents=True)
                (page / "index.ink").write_text(
                    "<page><text>World</text></page>\n"
                    "<script setup>export default { onLoad() { "
                    f"{body}"
                    " } };</script>\n",
                    encoding="utf-8",
                )

            result = self.run_script(project)

            self.assertEqual(0, result.returncode, result.stderr)
            report = json.loads(result.stdout)
            world_paths = [
                item["locations"][0]["path"]
                for item in report["items"]
                if item["family"] == "page.world-awareness"
            ]
            self.assertEqual(["pages/direct/index.ink"], world_paths)
            unresolved_paths = {
                entry["path"]
                for entry in report["unmatchedSymbols"]
                if entry["symbol"] == "REFERENCE:enableWorldAwareness"
            }
            self.assertEqual(
                {
                    "pages/call/index.ink",
                    "pages/comma/index.ink",
                    "pages/optional/index.ink",
                },
                unresolved_paths,
            )

    def test_page_and_worker_surfaces_are_supported_without_target_media(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory)
            (project / "pages" / "index").mkdir(parents=True)
            (project / "workers").mkdir()
            (project / "app.json").write_text(
                json.dumps(
                    {
                        "pages": ["pages/index/index"],
                        "agentWorkers": [
                            {
                                "name": "sync",
                                "script": "workers/sync.js",
                                "trigger": {"type": "open"},
                                "lifetime": "instant",
                            }
                        ],
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            (project / "pages" / "index" / "index.ink").write_text(
                "<page><text>Ready</text></page>\n"
                "<script setup>export default { onLoad() {} };</script>\n",
                encoding="utf-8",
            )
            (project / "workers" / "sync.js").write_text(
                "export default { onOpen() {} };\n", encoding="utf-8"
            )

            result = self.run_script(project, target_version="0.18.0")
            self.assertEqual(0, result.returncode, result.stderr)
            report = json.loads(result.stdout)
            self.assertTrue(
                {"Page", "Agent Worker"}.issubset(report["supportedSurfaces"])
            )

    def test_css_motion_syntax_creates_explicit_inventory_gates(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory)
            (project / "pages" / "index").mkdir(parents=True)
            (project / "app.json").write_text(
                '{"pages":["pages/index/index"]}\n', encoding="utf-8"
            )
            (project / "pages" / "index" / "index.ink").write_text(
                """
<page><view style="animation-delay: 50ms"><text>Motion</text></view></page>
<style>
.surface {
  transition: opacity 200ms;
  animation-duration: 400ms;
  content: "animation: ignored";
}
/* transition-property: transform; */
@keyframes reveal { from { opacity: 0; } to { opacity: 1; } }
</style>
<script setup>export default {};</script>
""".strip()
                + "\n",
                encoding="utf-8",
            )
            (project / "pages" / "index" / "index.wxss").write_text(
                ".surface { -webkit-animation-name: reveal; }\n",
                encoding="utf-8",
            )
            (project / "pages" / "index" / "index.wxml").write_text(
                '<view style="anim\\61tion-play-state: paused">Motion</view>\n'
                '<view style="transition-property: opacity">Motion</view>\n',
                encoding="utf-8",
            )

            result = self.run_script(project)
            self.assertEqual(0, result.returncode, result.stderr)
            motion_symbols = {
                entry["symbol"]
                for entry in json.loads(result.stdout)["unmatchedSymbols"]
                if entry["symbol"].startswith("MOTION:")
            }
            self.assertEqual(
                {
                    "MOTION:-webkit-animation-name",
                    "MOTION:@keyframes",
                    "MOTION:animation-play-state",
                    "MOTION:animation-delay",
                    "MOTION:animation-duration",
                    "MOTION:transition",
                    "MOTION:transition-property",
                },
                motion_symbols,
            )

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
