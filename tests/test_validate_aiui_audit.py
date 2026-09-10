"""Black-box tests for the packaged AIUI audit validator.

These tests intentionally do not import the large repository contract test.  They
create a real, minimal AIUI import root and invoke the same inventory/fingerprint
tools that a skill consumer will use.
"""

from __future__ import annotations

import base64
import hashlib
import json
import re
import runpy
import shutil
import subprocess
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "skills/rokid-aiui-agent/scripts/validate_aiui_audit.py"
INVENTORY = ROOT / "skills/rokid-aiui-agent/scripts/inventory_aiui_capabilities.py"

UX = {
    "UX-TARGET": ("all-targets", ("LOGIC", "STUDIO", "DEVICE")),
    "UX-STATE": ("all-states", ("LOGIC", "AIX", "STUDIO", "DEVICE")),
    "UX-TEXT": ("boundary-text", ("LOGIC", "AIX", "STUDIO", "DEVICE")),
    "UX-FOCUS": ("focus-model", ("STATIC", "STUDIO", "DEVICE")),
    "UX-INPUT": ("tap-primary", ("LOGIC", "STUDIO", "DEVICE")),
    "UX-RECOVERY": (
        "failure-recovery",
        ("STATIC", "LOGIC", "STUDIO", "DEVICE"),
    ),
    "UX-LIFECYCLE": ("page-lifecycle", ("LOGIC", "STUDIO", "DEVICE")),
    "UX-VISUAL": ("visual-system", ("STATIC", "AIX", "DEVICE")),
    "UX-ENVIRONMENT": ("optical-scenes", ("AIX", "DEVICE")),
    "UX-MOTION": ("motion-performance", ("LOGIC", "STUDIO", "DEVICE")),
}

UX_CONTRACT_TOKENS = {
    family: "ux-" + family.removeprefix("UX-").lower() + "-v1" for family in UX
}
UX_CONTRACTS = {
    "UX-TARGET": (
        "Every supported `_current`, `_blank`, and transition",
        "Wrong density, host behavior, or business-state drift",
        "Exercise each declared surface and target change with the same input",
    ),
    "UX-STATE": (
        "Every loading, empty, ready, active, success, error, denied, and recovery state used by the product",
        "Hidden, misleading, or dead-end states",
        "Reach each state and every legal and illegal transition",
    ),
    "UX-TEXT": (
        "Empty, minimum, maximum, long Chinese/English, mixed Unicode, and malformed input",
        "Clipping, unreadable wrapping, unsafe interpolation, or hidden actions",
        "Exercise boundary values, overflow, scrolling, and fixed-action visibility",
    ),
    "UX-FOCUS": (
        "Host and every actionable element",
        "Invisible focus, focus trap, or unfocused activation",
        "Exercise host focus/blur, element focus/blur, order, activation, and return",
    ),
    "UX-INPUT": (
        "One claimed tap, Enter, Back, directional, touchpad, voice, or gesture path",
        "Double action, stolen host default, unsupported event, or no fallback",
        "Exercise owned and ignored input, default prevention, and a non-sensor fallback",
    ),
    "UX-RECOVERY": (
        "Offline, timeout, denied, unavailable, invalid, and retry states that apply",
        "Silent failure or endless retry",
        "Force each failure, verify useful feedback, bounded retry, back/finish, and recovery",
    ),
    "UX-LIFECYCLE": (
        "First open, hide/show, unload/reopen, and repeated attach/open where applicable",
        "Stale state, duplicate work, leaked timers/listeners, or wrong resume",
        "Exercise lifecycle ordering, state reconciliation, and cleanup",
    ),
    "UX-VISUAL": (
        "Every meaningful state and focus level",
        "Meaning conveyed only by green luminance, weak hierarchy, excess fill, or clutter",
        "Check labels/shapes plus luminance, typography, spacing, line weight, fill, and information density",
    ),
    "UX-ENVIRONMENT": (
        "Runtime viewport and bright, dark, and cluttered real scenes",
        "Desktop-readable UI fails in physical optics",
        "Inspect the actual viewport, comfortable region, backgrounds, posture, and motion",
    ),
    "UX-MOTION": (
        "Transitions, animation, repeated navigation, and continuous use",
        "Distraction, unsupported motion, dropped frames, heat, or instability",
        "Exercise reduced/absent motion fallback, overlap, cold start, and endurance as applicable",
    ),
}

CAP_LAYERS = {
    "page.route": ("SOURCE", "STATIC", "LOGIC", "AIX", "STUDIO"),
    "page.target": ("SOURCE", "STATIC", "LOGIC", "AIX", "STUDIO", "DEVICE"),
    "event.bindtap": ("SOURCE", "STATIC", "LOGIC", "AIX", "STUDIO", "DEVICE"),
    "ui.button": ("SOURCE", "STATIC", "AIX", "STUDIO", "DEVICE"),
    "input.enter": ("SOURCE", "STATIC", "LOGIC", "STUDIO", "DEVICE"),
    "input.key.unknown": ("SOURCE", "STATIC", "LOGIC", "STUDIO", "DEVICE"),
    "input.voice.unknown": ("SOURCE", "STATIC", "LOGIC", "STUDIO", "DEVICE"),
    "input.gesture-fallback.unknown": (
        "SOURCE",
        "STATIC",
        "LOGIC",
        "STUDIO",
        "DEVICE",
    ),
    "network.https": ("SOURCE", "STATIC", "LOGIC", "AIX", "STUDIO", "DEVICE"),
    "widget.declaration": ("SOURCE", "STATIC", "LOGIC", "AIX", "STUDIO", "DEVICE"),
    "agent-worker.declaration": ("SOURCE", "STATIC", "LOGIC", "AIX", "STUDIO", "DEVICE"),
    "agent-worker.capability": ("SOURCE", "STATIC", "LOGIC", "AIX", "STUDIO", "DEVICE"),
    "agent-worker.on-open": ("SOURCE", "STATIC", "LOGIC", "AIX", "STUDIO", "DEVICE"),
    "agent-worker.wait-until": ("SOURCE", "STATIC", "LOGIC", "AIX", "STUDIO", "DEVICE"),
}

CAP_IDS = {
    "page.route": "CAP-PAGE-ROUTE",
    "page.target": "CAP-PAGE-TARGET",
    "event.bindtap": "CAP-BINDTAP",
    "ui.button": "CAP-BUTTON",
    "input.enter": "CAP-INPUT-ENTER",
    "input.key.unknown": "CAP-INPUT-KEY",
    "input.voice.unknown": "CAP-VOICE",
    "input.gesture-fallback.unknown": "CAP-GESTURE-FALLBACK",
    "network.https": "CAP-NETWORK-HTTPS",
    "widget.declaration": "CAP-WIDGET-DECLARATION",
    "agent-worker.declaration": "CAP-AGENT-WORKER-DECLARATION",
    "agent-worker.capability": "CAP-AGENT-WORKER-CAPABILITY",
    "agent-worker.on-open": "CAP-AGENT-WORKER-ON-OPEN",
    "agent-worker.wait-until": "CAP-AGENT-WORKER-WAIT-UNTIL",
}

SOURCE_PATHS = {
    "page.route": (("DOC", "documentation/1-framework/open-agent-format/app-json.en-US.md"),),
    "page.target": (("DOC", "documentation/1-framework/open-agent-format/target.en-US.md"),),
    "event.bindtap": (
        ("DOC", "documentation/2-components/button.en-US.md"),
        ("SAMPLE", "samples/capabilities/pages/close/index.ink"),
    ),
    "ui.button": (
        ("DOC", "documentation/2-components/button.en-US.md"),
        ("SAMPLE", "samples/capabilities/pages/close/index.ink"),
    ),
    "input.enter": (("DOC", "documentation/1-framework/open-agent-format/page-events.en-US.md"),),
    "input.key.unknown": (("DOC", "documentation/1-framework/open-agent-format/page-events.en-US.md"),),
    "input.voice.unknown": (
        ("SEARCH-SCOPE", "documentation/1-framework/open-agent-format"),
        ("SEARCH-SCOPE", "documentation/3-api/ai"),
    ),
    "input.gesture-fallback.unknown": (
        ("SEARCH-SCOPE", "documentation/1-framework/open-agent-format"),
        ("SEARCH-SCOPE", "documentation/2-components"),
    ),
    "network.https": (
        ("DOC", "documentation/3-api/network/https.en-US.md"),
        ("SAMPLE", "samples/capabilities/pages/network_https/index.ink"),
    ),
    "widget.declaration": (("DOC", "documentation/7-changelog/latest.en-US.md"),),
    "agent-worker.declaration": (("DOC", "documentation/7-changelog/latest.en-US.md"),),
    "agent-worker.capability": (("DOC", "documentation/7-changelog/latest.en-US.md"),),
    "agent-worker.on-open": (("DOC", "documentation/7-changelog/latest.en-US.md"),),
    "agent-worker.wait-until": (("DOC", "documentation/7-changelog/latest.en-US.md"),),
}

CAP_BEHAVIORS = {
    "page.route": (
        "The declared route opens exactly one intended Page",
        "Missing, malformed, or rejected navigation preserves a usable exit",
        "Repeated navigation and unload leave no stale route-owned work",
    ),
    "page.target": (
        "The declared target renders the intended layout and behavior",
        "Unsupported or changed targets preserve readable content and a usable fallback",
        "Target changes and repeated open reconcile without stale surface state",
    ),
    "event.bindtap": (
        "One owned tap invokes the bound action exactly once",
        "Ignored, repeated, or unavailable tap delivery does not duplicate or dead-end the action",
        "Hide/show and unload do not retain stale tap handlers or work",
    ),
    "ui.button": (
        "The button exposes and performs its intended action",
        "Disabled, unavailable, or repeated activation remains explicit and recoverable",
        "Repeated render and reopen preserve one current button action",
    ),
    "input.enter": (
        "One owned Enter input invokes the intended action exactly once",
        "Ignored or repeated Enter input preserves host defaults and a non-key fallback",
        "Hide/show and unload do not retain stale Enter handling",
    ),
    "input.key.unknown": (
        "The intended key input performs exactly one owned action",
        "Unknown, ignored, or repeated key delivery preserves host defaults and a non-key fallback",
        "Hide/show and unload do not retain stale key handling",
    ),
    "input.voice.unknown": (
        "The declared product intent is delivered once",
        "No-match, unavailable, repeated, and ignored input use a non-voice fallback",
        "Hide/show and unload do not retain stale voice work",
    ),
    "input.gesture-fallback.unknown": (
        "The core task remains usable without the gesture sensor",
        "Fallback failure leaves a clear exit without duplicate action",
        "Fallback remains available after hide/show and reopen",
    ),
    "network.https": (
        "A successful HTTPS request updates only the current intended state",
        "Offline, timeout, malformed, partial, and rejected responses use bounded retry and recovery",
        "Hide/show and unload cancel or reconcile every retained HTTPS request",
    ),
    "widget.declaration": (
        "The declared Widget path and family resolve to the intended Widget definition",
        "Missing, invalid, unsupported, or mismatched declarations remain blocked with an explicit fallback",
        "Repeated host attach and reopen resolve one current Widget declaration",
    ),
    "agent-worker.declaration": (
        "The declared Agent Worker resolves to the intended background entry",
        "Missing, invalid, unsupported, or mismatched declarations remain blocked without background side effects",
        "Repeated host open resolves one current Agent Worker declaration",
    ),
    "agent-worker.capability": (
        "The Agent Worker exposes only the declared background capability",
        "Unsupported, denied, invalid, or repeated capability delivery remains bounded and explicit",
        "Completed or cancelled delivery releases all worker-owned retained work",
    ),
    "agent-worker.on-open": (
        "One onOpen event starts one owned background operation",
        "Malformed, repeated, rejected, and unavailable open events remain bounded and observable",
        "Completion or cancellation settles every operation started by onOpen",
    ),
    "agent-worker.wait-until": (
        "waitUntil tracks the complete promise for each owned onOpen operation",
        "Rejected, timed-out, repeated, and missing promises fail explicitly without orphan work",
        "Every tracked promise settles before the worker operation is released",
    ),
}


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def public_key_fingerprint(public_key: Path) -> str:
    der = subprocess.run(
        ["openssl", "pkey", "-pubin", "-outform", "DER"],
        input=public_key.read_bytes(),
        capture_output=True,
        check=True,
    ).stdout
    return sha256(der)


def blocked_evidence(layers: tuple[str, ...]) -> str:
    return "; ".join(
        f"{layer}=blocked:current-revision evidence not supplied" for layer in layers
    )


def ux_criterion(family: str) -> str:
    return (
        f"{{contract={UX_CONTRACT_TOKENS[family]}}} "
        + UX_CONTRACTS[family][2]
    )


def capability_path(family: str, path: str, description: str) -> str:
    token = "cap-" + family.replace(".", "-") + "-v1"
    return f"{{contract={token}}} {{path={path}}} {description}"


def table(header: tuple[str, ...], rows: list[list[str]]) -> str:
    separator = tuple("---" for _ in header)
    return "\n".join(
        "| " + " | ".join(row) + " |"
        for row in (list(header), list(separator), *rows)
    )


def sign_manifest_entry(
    manifest: dict,
    entry: dict,
    private_key: Path,
    public_key: Path,
    role: str,
) -> None:
    unsigned_entry = dict(entry)
    unsigned_entry.pop("attestations", None)
    payload = {
        "schemaVersion": manifest["schemaVersion"],
        "projectRevision": manifest["projectRevision"],
        "subject": manifest["subject"],
        "sourceSnapshot": manifest["sourceSnapshot"],
        "completionSnapshot": manifest["completionSnapshot"],
        "entry": unsigned_entry,
    }
    canonical = json.dumps(
        payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    signature = subprocess.run(
        ["openssl", "dgst", "-sha256", "-sign", str(private_key)],
        input=canonical,
        capture_output=True,
        check=True,
    ).stdout
    entry.setdefault("attestations", {})[role] = {
        "algorithm": "rsa-sha256",
        "keyId": public_key_fingerprint(public_key),
        "signature": base64.b64encode(signature).decode("ascii"),
    }


SignerSet = dict[str, tuple[Path, Path]]


class AuditFixture:
    def __init__(self, root: Path, *, target_version: str = "0.17.0") -> None:
        self.root = root
        self.import_root = root / "project"
        (self.import_root / "pages/index").mkdir(parents=True)
        (self.import_root / "AGENTS.md").write_text(
            "# Audit fixture\n", encoding="utf-8"
        )
        (self.import_root / "app.js").write_text(
            "export default {};\n", encoding="utf-8"
        )
        (self.import_root / "app.json").write_text(
            json.dumps({"pages": ["pages/index/index"]}), encoding="utf-8"
        )
        (self.import_root / "aiui-audit-claims.json").write_text(
            json.dumps({"schemaVersion": 1, "scopeClosed": True, "claims": []}),
            encoding="utf-8",
        )
        (self.import_root / "pages/index/index.ink").write_text(
            "<page><button bindtap=\"handleTap\">timer</button>"
            "<style>@media (target: _current) {}</style>"
            "<script>export default { handleTap() {} };</script></page>\n",
            encoding="utf-8",
        )
        self.target_version = target_version
        self.report = self.inventory()
        self.ux_rows = self.default_ux_rows()
        self.cap_rows = self.default_capability_rows()
        self.device_host = "UNAVAILABLE"

    def inventory(self) -> dict:
        completed = subprocess.run(
            [
                sys.executable,
                str(INVENTORY),
                str(self.import_root),
                "--target-version",
                self.target_version,
                "--repository-root",
                str(self.root),
            ],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        if completed.returncode:
            raise AssertionError(completed.stderr)
        return json.loads(completed.stdout)

    def default_ux_rows(self) -> list[list[str]]:
        rows: list[list[str]] = []
        for family, (gate, layers) in UX.items():
            gates = (
                [entry["gate"] for entry in self.report["inputGates"]]
                or ["no-input"]
                if family == "UX-INPUT"
                else [gate]
            )
            for gate_index, actual_gate in enumerate(gates, start=1):
                identifier = family if len(gates) == 1 else f"{family}-GATE{gate_index}"
                rows.append(
                    [
                        f"[{identifier}] {{gate={actual_gate}}}",
                        UX_CONTRACTS[family][0],
                        UX_CONTRACTS[family][1],
                        ux_criterion(family),
                        ", ".join(layers),
                        "BLOCKED",
                        blocked_evidence(layers),
                    ]
                )
        return rows

    def default_capability_rows(self) -> list[list[str]]:
        rows: list[list[str]] = []
        by_claim = {
            f"{item['family']}@{item['gate']}": item for item in self.report["items"]
        }
        for claim in self.report["claimedCapabilities"]:
            item = by_claim[claim]
            family = item["family"]
            gate = item["gate"]
            if family == "project.unregistered":
                identifier = "CAP-UNREGISTERED-" + gate.rsplit("-", 1)[-1].upper()
                layers = ("SOURCE", "STATIC", "LOGIC", "AIX", "STUDIO", "DEVICE")
            else:
                identifier = CAP_IDS[family]
                if item["policyState"] == "binding-unresolved":
                    identifier += "-PROVISIONAL"
                layers = CAP_LAYERS[family]
            source_revision = (
                "88e70bb0382525c1a93ef077c2401dcc31a273ce"
                if self.target_version == "0.17.0"
                else "8b19a87b4ba8b486c0dd4dd3fd32290d27891069"
            )
            if family == "project.unregistered":
                source_cell = (
                    "SEARCH-SCOPE=[AIUI documentation index](https://github.com/"
                    f"yodaos-project/AIUI/tree/{source_revision}/documentation); "
                    "SEARCH-SCOPE=[AIUI samples index](https://github.com/"
                    f"yodaos-project/AIUI/tree/{source_revision}/samples)"
                )
            else:
                source_cell = "; ".join(
                    f"{role}=[source](https://github.com/yodaos-project/AIUI/"
                    f"{'tree' if role == 'SEARCH-SCOPE' else 'blob'}/"
                    f"{source_revision}/{path})"
                    for role, path in SOURCE_PATHS[family]
                )
            mechanism = str(item.get("mechanism", ""))
            if mechanism.startswith("CLAIM:") and "@" in mechanism:
                surface = mechanism.split("@", 1)[1].split(":", 1)[0]
            elif mechanism.startswith("target:"):
                surface = mechanism.split(":", 1)[1]
            else:
                surface = ",".join(self.report["supportedSurfaces"]) or "UNAVAILABLE"
            if family == "project.unregistered":
                behavior = (
                    "The declared capability performs its claimed outcome once",
                    "Unavailable, rejected, or ignored delivery preserves an explicit fallback",
                    "Hide/show and unload do not retain stale capability work",
                )
            else:
                behavior = CAP_BEHAVIORS[family]
            rows.append(
                [
                    f"[{identifier}] {{family={family}}} {{gate={gate}}} Page route",
                    f"AIUI {self.target_version}; device=UNAVAILABLE; surface={surface}",
                    item["apiBinding"],
                    item["declarationBinding"],
                    source_cell,
                    capability_path(family, "positive", behavior[0]),
                    capability_path(family, "negative-fallback", behavior[1]),
                    capability_path(family, "lifecycle-cleanup", behavior[2]),
                    ", ".join(layers),
                    "BLOCKED",
                    blocked_evidence(layers),
                ]
            )
        return rows

    def split_ux_outcome(
        self,
        family: str,
        layer: str,
        locator: str,
        kind: str,
        *,
        result: str = "PASS",
    ) -> str:
        index = next(
            i for i, row in enumerate(self.ux_rows) if row[0].startswith(f"[{family}]")
        )
        original = self.ux_rows.pop(index)
        gate = original[0].split("{gate=", 1)[1].split("}", 1)[0]
        outcome_id = f"{family}-{result}"
        blocked_id = f"{family}-BLOCKED"
        other_layers = tuple(
            value.strip() for value in original[4].split(",") if value.strip() != layer
        )
        prefix = original[1:4]
        self.ux_rows[index:index] = [
            [
                f"[{outcome_id}] {{gate={gate}}}",
                *prefix,
                layer,
                result,
                f"{layer}={kind}:{locator}",
            ],
            [
                f"[{blocked_id}] {{gate={gate}}}",
                *prefix,
                ", ".join(other_layers),
                "BLOCKED",
                blocked_evidence(other_layers),
            ],
        ]
        return outcome_id

    def render(self) -> str:
        ux_header = (
            "ID",
            "Surface/state",
            "Risk",
            "Test",
            "Evidence layer",
            "Result",
            "Evidence",
        )
        cap_header = (
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
        )
        results: list[tuple[str, str, tuple[str, ...]]] = []
        for row in self.ux_rows:
            identifier = row[0].split("]", 1)[0][1:]
            results.append((identifier, row[5], tuple(x.strip() for x in row[4].split(","))))
        for row in self.cap_rows:
            identifier = row[0].split("]", 1)[0][1:]
            results.append((identifier, row[9], tuple(x.strip() for x in row[8].split(","))))
        fail_ids = sorted(identifier for identifier, result, _ in results if result == "FAIL")
        blocked_ids = sorted(
            identifier for identifier, result, _ in results if result == "BLOCKED"
        )
        gates = sorted(
            f"{identifier}@{layer}"
            for identifier, result, layers in results
            if result in {"FAIL", "BLOCKED"}
            for layer in layers
        )
        status = "FAIL" if fail_ids else "BLOCKED" if blocked_ids else "PASS"
        ready = "YES" if status == "PASS" else "NO"
        fail_ledger = ",".join(fail_ids) if fail_ids else "none"
        blocked_ledger = ",".join(blocked_ids) if blocked_ids else "none"
        gate_ledger = ",".join(gates) if gates else "none"
        metadata = [
            f"Project revision: {self.report['projectRevision']}",
            f"Canonical version: AIUI {self.target_version}",
            "Import root: project",
            f"Device/host: {self.device_host}",
            "Supported surfaces: "
            + (",".join(self.report["supportedSurfaces"]) or "UNAVAILABLE"),
            "Inputs: "
            + (
                ",".join(
                    sorted(
                        f"{entry['kind']}@{entry['gate']}"
                        for entry in self.report["inputGates"]
                    )
                )
                or "none"
            ),
            "Claimed capabilities: " + ",".join(self.report["claimedCapabilities"]),
        ]
        rendered_cap_rows = [list(row) for row in self.cap_rows]
        if self.device_host != "UNAVAILABLE":
            for row in rendered_cap_rows:
                prefix = f"AIUI {self.target_version}; device=UNAVAILABLE; surface="
                if row[1].startswith(prefix):
                    row[1] = (
                        f"AIUI {self.target_version}; {self.device_host}; surface="
                        + row[1][len(prefix) :]
                    )
        return (
            "\n".join(metadata)
            + "\n\n## Project UX evidence matrix\n\n"
            + table(ux_header, self.ux_rows)
            + "\n\n## Per-capability matrix\n\n"
            + table(cap_header, rendered_cap_rows)
            + "\n\n## Final release decision\n\n"
            + f"Final status: {status}\n"
            + f"Release-ready: {ready}\n"
            + f"Reason: FAIL=[{fail_ledger}]; BLOCKED=[{blocked_ledger}]\n"
            + f"Required gates: {gate_ledger}\n"
        )

    def write_audit(self, markdown: str | None = None) -> Path:
        path = self.root / "audit.md"
        path.write_text(markdown if markdown is not None else self.render(), encoding="utf-8")
        return path

    def manifest_locator(
        self,
        *,
        row: str,
        gate: str,
        layer: str,
        criterion: str,
        kind: str = "command",
        environment: dict | None = None,
        outside: bool = False,
        mutate=None,
        entry_mutate=None,
        signer: SignerSet | None = None,
        result: str = "PASS",
        capability_binding: dict | None = None,
    ) -> str:
        directory_name = "outside-evidence" if outside else ".aiui-evidence"
        directory = self.root / directory_name
        directory.mkdir(exist_ok=True)
        inventory_path = directory / "inventory.json"
        inventory_bytes = json.dumps(
            self.report, ensure_ascii=False, sort_keys=True, indent=2
        ).encode()
        inventory_path.write_bytes(inventory_bytes)
        slug = f"{row.lower()}-{layer.lower()}"
        artifact_path = directory / f"{slug}.log"
        artifact_bytes = (
            f"executed evidence for {row} at {layer}: "
            f"{'criterion satisfied' if result == 'PASS' else 'criterion violation observed'}\n"
        ).encode()
        artifact_path.write_bytes(artifact_bytes)
        now = datetime.now(timezone.utc)
        source_time = (now - timedelta(minutes=4)).isoformat()
        start_time = (now - timedelta(minutes=3)).isoformat()
        capture_time = (now - timedelta(minutes=2)).isoformat()
        completion_time = (now - timedelta(minutes=1)).isoformat()
        entry = {
            "id": slug,
            "captureId": f"capture-{slug}-20260910",
            "collector": {"name": "audit-fixture-runner", "version": "1.0"},
            "row": row,
            "gate": gate,
            "layer": layer,
            "kind": kind,
            "result": result,
            "criterion": criterion,
            "observed": "The executed check produced the expected concrete outcome",
            "path": f"{directory_name}/{artifact_path.name}",
            "sha256": sha256(artifact_bytes),
            "bytes": len(artifact_bytes),
            "artifactRole": "stdout",
            "mediaType": "text/plain",
            "projectRevision": self.report["projectRevision"],
            "startedAt": start_time,
            "capturedAt": capture_time,
        }
        if kind in {"command", "log", "artifact"}:
            is_aix = layer == "AIX"
            operation = {
                "STATIC": "static-validate",
                "LOGIC": "logic-test",
                "AIX": "aix-preview",
                "STUDIO": "studio-capture",
                "DEVICE": "device-capture",
            }.get(layer, "capture-check")
            entry.update(
                {
                    "operation": operation,
                    "argv": (
                        ["/opt/aix/bin/aix", "preview", "project"]
                        if is_aix
                        else ["python3", "validate.py", "project"]
                    ),
                    "cwd": "project",
                    "tool": (
                        {"name": "aix", "version": "0.8.2"}
                        if is_aix
                        else {"name": "python", "version": "3.9.6"}
                    ),
                    "exitCode": 0 if result == "PASS" else 1,
                    "stdoutSha256": sha256(artifact_bytes),
                    "stderrSha256": sha256(b""),
                }
            )
        if capability_binding is not None:
            entry.update(capability_binding)
            if layer == "SOURCE":
                entry["inspectedSourceUrls"] = capability_binding["sourceUrls"]
        if environment is not None:
            entry["environment"] = environment
        if entry_mutate is not None:
            entry_mutate(entry)
        manifest = {
            "schemaVersion": 2,
            "projectRevision": self.report["projectRevision"],
            "subject": {
                "projectRevision": self.report["projectRevision"],
                "importRoot": "project",
            },
            "sourceSnapshot": {
                "fingerprint": self.report["projectRevision"],
                "inventoryPath": f"{directory_name}/{inventory_path.name}",
                "inventorySha256": sha256(inventory_bytes),
                "capturedAt": source_time,
            },
            "completionSnapshot": {
                "fingerprint": self.report["projectRevision"],
                "capturedAt": completion_time,
            },
            "entries": [entry],
        }
        if signer is not None:
            roles = set()
            if kind in {"command", "log", "artifact"} or layer == "AIX":
                roles.add("RUNNER")
            if layer in {"STUDIO", "DEVICE"}:
                roles.add(layer)
            for role in sorted(roles):
                private_key, public_key = signer[role]
                sign_manifest_entry(
                    manifest, entry, private_key, public_key, role
                )
        if mutate is not None:
            mutate(manifest)
        manifest_path = directory / f"manifest-{slug}.json"
        manifest_bytes = json.dumps(
            manifest, ensure_ascii=False, sort_keys=True, indent=2
        ).encode()
        manifest_path.write_bytes(manifest_bytes)
        return (
            f"manifest:{directory_name}/{manifest_path.name}"
            f"@sha256={sha256(manifest_bytes)}#{slug}"
        )

    def scope_locators(
        self,
        *,
        row: str,
        gate: str,
        criterion: str,
        signer: SignerSet | None = None,
    ) -> tuple[str, str]:
        directory = self.root / ".aiui-evidence"
        directory.mkdir(exist_ok=True)
        inventory_path = directory / "inventory.json"
        inventory_bytes = json.dumps(
            self.report, ensure_ascii=False, sort_keys=True, indent=2
        ).encode()
        inventory_path.write_bytes(inventory_bytes)
        scope_path = self.import_root / "aiui-audit-scope.json"
        scope_bytes = scope_path.read_bytes()
        now = datetime.now(timezone.utc)
        times = [
            (now - timedelta(minutes=value)).isoformat() for value in (4, 3, 2, 1)
        ]
        query = {"family": ".".join(row.lower().split("-")[:2]), "gate": gate}
        entries = []
        for aspect, content in (
            (
                "source",
                f"inventory replay found no matching UX source declaration for {row}\n".encode(),
            ),
            (
                "claim",
                f"closed product claim ledger found no matching UX promise for {row}\n".encode(),
            ),
        ):
            artifact_path = directory / f"{row.lower()}-{aspect}.log"
            artifact_path.write_bytes(content)
            proof = (
                {
                    "inventoryPath": ".aiui-evidence/inventory.json",
                    "inventorySha256": sha256(inventory_bytes),
                    "query": query,
                    "matches": [],
                }
                if aspect == "source"
                else {
                    "scopeManifestPath": "project/aiui-audit-scope.json",
                    "scopeManifestSha256": sha256(scope_bytes),
                    "query": query,
                    "matches": [],
                    "universeClosed": True,
                }
            )
            entries.append(
                {
                    "id": f"{row.lower()}-{aspect}",
                    "captureId": f"capture-{row.lower()}-{aspect}-20260910",
                    "collector": {"name": "scope-capture-runner", "version": "1.0"},
                    "row": row,
                    "gate": gate,
                    "kind": "scope",
                    "scopeAspect": aspect,
                    "result": "N/A",
                    "criterion": criterion,
                    "observed": f"The replayed {aspect} universe contains no matching entry",
                    "path": f".aiui-evidence/{artifact_path.name}",
                    "sha256": sha256(content),
                    "bytes": len(content),
                    "artifactRole": f"{aspect}-scope-report",
                    "mediaType": "text/plain",
                    "scopeProof": proof,
                    "projectRevision": self.report["projectRevision"],
                    "startedAt": times[1],
                    "capturedAt": times[2],
                }
            )
        manifest = {
            "schemaVersion": 2,
            "projectRevision": self.report["projectRevision"],
            "subject": {
                "projectRevision": self.report["projectRevision"],
                "importRoot": "project",
            },
            "sourceSnapshot": {
                "fingerprint": self.report["projectRevision"],
                "inventoryPath": ".aiui-evidence/inventory.json",
                "inventorySha256": sha256(inventory_bytes),
                "capturedAt": times[0],
            },
            "completionSnapshot": {
                "fingerprint": self.report["projectRevision"],
                "capturedAt": times[3],
            },
            "entries": entries,
        }
        if signer is not None:
            for entry in entries:
                private_key, public_key = signer["SCOPE"]
                sign_manifest_entry(
                    manifest, entry, private_key, public_key, "SCOPE"
                )
        manifest_path = directory / f"manifest-{row.lower()}-scope.json"
        manifest_bytes = json.dumps(
            manifest, ensure_ascii=False, sort_keys=True, indent=2
        ).encode()
        manifest_path.write_bytes(manifest_bytes)
        prefix = (
            f"manifest:.aiui-evidence/{manifest_path.name}"
            f"@sha256={sha256(manifest_bytes)}#"
        )
        return prefix + entries[0]["id"], prefix + entries[1]["id"]

    def materialize_full_pass(self, signer: SignerSet) -> None:
        self.device_host = (
            "device=Rokid Glasses; host=YodaOS 2.1.0; runtime="
            f"AIUI {self.target_version}"
        )
        device_environment = {
            "deviceModel": "Rokid Glasses",
            "hostBuild": "YodaOS 2.1.0",
            "runtimeVersion": f"AIUI {self.target_version}",
            "physicalDevice": True,
            "deviceIdHash": "a" * 64,
            "captureTool": "rokid-device-capture",
            "captureSessionId": "session-20260910-0001",
        }
        studio_environment = {
            "studioVersion": "AIUI Studio 1.2.0",
            "hostRuntime": f"AIUI {self.target_version}",
        }
        aix_environment = {
            "tool": "aix",
            "toolVersion": "0.8.2",
            "host": "release-runner-01",
        }

        for row in self.cap_rows:
            unavailable = f"AIUI {self.target_version}; device=UNAVAILABLE; surface="
            if row[1].startswith(unavailable):
                row[1] = (
                    f"AIUI {self.target_version}; {self.device_host}; surface="
                    + row[1][len(unavailable) :]
                )

        def executed_locator(
            *,
            identifier: str,
            gate: str,
            layer: str,
            criterion: str,
            capability_binding: dict | None = None,
        ) -> tuple[str, str]:
            if layer in {"STATIC", "LOGIC", "AIX"}:
                kind = "command"
            elif layer in {"STUDIO", "DEVICE"}:
                kind = "log"
            else:
                kind = "source"
            environment = (
                aix_environment
                if layer == "AIX"
                else studio_environment
                if layer == "STUDIO"
                else device_environment
                if layer == "DEVICE"
                else None
            )
            locator = self.manifest_locator(
                row=identifier,
                gate=gate,
                layer=layer,
                criterion=criterion,
                kind=kind,
                environment=environment,
                signer=signer,
                capability_binding=capability_binding,
            )
            return kind, locator

        for row in self.ux_rows:
            identifier = row[0].split("]", 1)[0][1:]
            gate = row[0].split("{gate=", 1)[1].split("}", 1)[0]
            mappings = []
            for layer in (value.strip() for value in row[4].split(",")):
                kind, locator = executed_locator(
                    identifier=identifier,
                    gate=gate,
                    layer=layer,
                    criterion=row[3],
                )
                mappings.append(f"{layer}={kind}:{locator}")
            row[5] = "PASS"
            row[6] = "; ".join(mappings)

        for row in self.cap_rows:
            identifier = row[0].split("]", 1)[0][1:]
            gate = row[0].split("{gate=", 1)[1].split("}", 1)[0]
            source_urls = re.findall(r"\]\((https://[^)]+)\)", row[4])
            criterion = (
                f"Positive={row[5]}; Negative={row[6]}; Lifecycle={row[7]}"
            )
            binding = {
                "target": row[1],
                "apiBinding": row[2],
                "declarationBinding": row[3],
                "sourceUrls": source_urls,
            }
            mappings = []
            for layer in (value.strip() for value in row[8].split(",")):
                if layer == "SOURCE" and len(source_urls) == 1:
                    kind, locator = "source", source_urls[0]
                else:
                    kind, locator = executed_locator(
                        identifier=identifier,
                        gate=gate,
                        layer=layer,
                        criterion=criterion,
                        capability_binding=binding,
                    )
                mappings.append(f"{layer}={kind}:{locator}")
            row[9] = "PASS"
            row[10] = "; ".join(mappings)

    def rewrite_signed_environments(
        self,
        markdown: str,
        *,
        layer: str,
        signer: SignerSet,
        mutate,
    ) -> tuple[str, int]:
        rewritten = 0
        locator_pattern = re.compile(
            r"manifest:(?P<path>[^\s@#;]+)@sha256=(?P<digest>[0-9a-f]{64})#"
            r"(?P<entry>[A-Za-z0-9._-]+)"
        )
        for match in tuple(locator_pattern.finditer(markdown)):
            manifest_path = self.root / match.group("path")
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            entries = [
                entry
                for entry in manifest["entries"]
                if entry["id"] == match.group("entry") and entry.get("layer") == layer
            ]
            if not entries:
                continue
            self.assert_single_manifest_entry(entries)
            entry = entries[0]
            mutate(entry["environment"])
            entry.pop("attestations", None)
            for role in ("RUNNER", layer):
                private_key, public_key = signer[role]
                sign_manifest_entry(manifest, entry, private_key, public_key, role)
            manifest_bytes = json.dumps(
                manifest, ensure_ascii=False, sort_keys=True, indent=2
            ).encode()
            manifest_path.write_bytes(manifest_bytes)
            replacement = (
                f"manifest:{match.group('path')}@sha256={sha256(manifest_bytes)}#"
                f"{match.group('entry')}"
            )
            markdown = markdown.replace(match.group(0), replacement, 1)
            rewritten += 1
        return markdown, rewritten

    @staticmethod
    def assert_single_manifest_entry(entries: list[dict]) -> None:
        if len(entries) != 1:
            raise AssertionError("expected one matching signed manifest entry")


class ValidateAiuiAuditTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.external_temporary = tempfile.TemporaryDirectory()
        self.repo = Path(self.temporary.name)
        self.external = Path(self.external_temporary.name)
        self.fixture = AuditFixture(self.repo)

    def tearDown(self) -> None:
        self.temporary.cleanup()
        self.external_temporary.cleanup()

    def test_cli_usage_errors_are_invalid_not_blocked_audits(self) -> None:
        cases = (
            [],
            ["--unknown-audit-option"],
        )
        for arguments in cases:
            with self.subTest(arguments=arguments):
                completed = subprocess.run(
                    [sys.executable, str(SCRIPT), *arguments],
                    cwd=ROOT,
                    text=True,
                    capture_output=True,
                    check=False,
                )
                self.assertEqual(1, completed.returncode)
                self.assertIn("usage:", completed.stderr.lower())

    @unittest.skipUnless(shutil.which("openssl"), "OpenSSL is required for trust test")
    def test_css_motion_cannot_be_scoped_to_na_or_release(self) -> None:
        page = self.fixture.import_root / "pages/index/index.ink"
        page.write_text(
            '<page><button bindtap="handleTap">timer</button>'
            '<style>@media (target: _current) {'
            'button { transition: opacity 100ms; } }</style>'
            '<script>export default { handleTap() {} };</script></page>\n',
            encoding="utf-8",
        )
        (self.fixture.import_root / "aiui-audit-scope.json").write_text(
            json.dumps({"schemaVersion": 1, "closed": True, "uxCriteria": []}),
            encoding="utf-8",
        )
        self.fixture.report = self.fixture.inventory()
        self.fixture.ux_rows = self.fixture.default_ux_rows()
        self.fixture.cap_rows = self.fixture.default_capability_rows()
        signers, policy = self.authority()
        self.fixture.materialize_full_pass(signers)
        row = next(
            candidate
            for candidate in self.fixture.ux_rows
            if candidate[0].startswith("[UX-MOTION]")
        )
        source, claim = self.fixture.scope_locators(
            row="UX-MOTION",
            gate="motion-performance",
            criterion=row[3],
            signer=signers,
        )
        row[5] = "N/A"
        row[6] = f"SCOPE: source={source}; claim={claim}"

        completed = self.validate(self.fixture.render(), trust_policy=policy)

        self.assertEqual(1, completed.returncode, completed.stdout + completed.stderr)
        self.assertIn("UX-MOTION", completed.stderr)
        self.assertIn("applicable", completed.stderr.lower())

    def authority(self) -> tuple[SignerSet, Path]:
        signers: SignerSet = {}
        authorities = {}
        for role in ("RUNNER", "STUDIO", "DEVICE", "SCOPE"):
            private_key = self.external / f"{role.lower()}-private.pem"
            public_key = self.external / f"{role.lower()}-public.pem"
            subprocess.run(
                [
                    "openssl",
                    "genpkey",
                    "-algorithm",
                    "RSA",
                    "-pkeyopt",
                    "rsa_keygen_bits:2048",
                    "-out",
                    str(private_key),
                ],
                capture_output=True,
                check=True,
            )
            subprocess.run(
                [
                    "openssl",
                    "pkey",
                    "-in",
                    str(private_key),
                    "-pubout",
                    "-out",
                    str(public_key),
                ],
                capture_output=True,
                check=True,
            )
            signers[role] = (private_key, public_key)
            authorities[role] = {
                "publicKeyPath": str(public_key),
                "publicKeySha256": public_key_fingerprint(public_key),
            }
        policy = self.external / "trust-policy.json"
        policy.write_text(
            json.dumps(
                {
                    "schemaVersion": 1,
                    "authorities": authorities,
                }
            ),
            encoding="utf-8",
        )
        return signers, policy

    def test_case_alias_cannot_make_repository_owned_trust_material_external(self) -> None:
        repository = self.repo / "RepoCase"
        repository.mkdir()
        internal_policy = repository / "policy.json"
        internal_key = repository / "runner-public.pem"
        internal_policy.write_text(
            json.dumps({"schemaVersion": 1, "authorities": {}}), encoding="utf-8"
        )
        internal_key.write_text("not reached\n", encoding="utf-8")
        alias_root = repository.with_name(repository.name.swapcase())
        alias_policy = alias_root / internal_policy.name
        alias_key = alias_root / internal_key.name
        if not alias_policy.exists():
            self.skipTest("case aliases require a case-insensitive filesystem")

        namespace = runpy.run_path(str(SCRIPT))
        error = namespace["AuditValidationError"]
        load_policy = namespace["load_trust_policy"]
        with self.assertRaisesRegex(error, "trust policy must be outside"):
            load_policy(alias_policy, repository.resolve())

        external_policy = self.external / "case-alias-policy.json"
        external_policy.write_text(
            json.dumps(
                {
                    "schemaVersion": 1,
                    "authorities": {
                        "RUNNER": {
                            "publicKeyPath": str(alias_key),
                            "publicKeySha256": "0" * 64,
                        }
                    },
                }
            ),
            encoding="utf-8",
        )
        with self.assertRaisesRegex(error, "public key must be outside"):
            load_policy(external_policy, repository.resolve())

    def test_commit_revision_includes_nested_same_named_evidence_directory(self) -> None:
        repository = self.repo / "commit-repository"
        project = repository / "examples" / "agent"
        project.mkdir(parents=True)
        (project / "app.json").write_text('{"pages":[]}\n', encoding="utf-8")

        commands = (
            ["git", "init", "--quiet"],
            ["git", "add", "examples/agent/app.json"],
            [
                "git",
                "-c",
                "user.name=AIUI Test",
                "-c",
                "user.email=aiui-test@example.invalid",
                "commit",
                "--quiet",
                "-m",
                "fixture",
            ],
        )
        for command in commands:
            completed = subprocess.run(
                command,
                cwd=repository,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(0, completed.returncode, completed.stderr)
        revision = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=repository,
            capture_output=True,
            text=True,
            check=True,
        ).stdout.strip()
        nested_evidence = project / ".aiui-evidence"
        nested_evidence.mkdir()
        (nested_evidence / "hidden.js").write_text(
            "fetch('https://example.invalid');\n", encoding="utf-8"
        )

        namespace = runpy.run_path(str(SCRIPT))
        with self.assertRaises(namespace["AuditValidationError"]):
            namespace["verify_commit_tree"](
                repository.resolve(), project.resolve(), revision
            )

    def test_commit_revision_excludes_mixed_case_repository_evidence_root(self) -> None:
        repository = self.repo / "case-evidence-repository"
        repository.mkdir()
        (repository / "app.json").write_text('{"pages":[]}\n', encoding="utf-8")
        evidence = repository / ".AIUI-EVIDENCE"
        evidence.mkdir()
        capture = evidence / "capture.json"
        capture.write_text("first\n", encoding="utf-8")
        for command in (
            ["git", "init", "--quiet"],
            ["git", "add", "app.json", ".AIUI-EVIDENCE/capture.json"],
            [
                "git",
                "-c",
                "user.name=AIUI Test",
                "-c",
                "user.email=aiui-test@example.invalid",
                "commit",
                "--quiet",
                "-m",
                "fixture",
            ],
        ):
            completed = subprocess.run(
                command,
                cwd=repository,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(0, completed.returncode, completed.stderr)
        revision = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=repository,
            capture_output=True,
            text=True,
            check=True,
        ).stdout.strip()
        capture.write_text("changed after commit\n", encoding="utf-8")

        namespace = runpy.run_path(str(SCRIPT))
        namespace["verify_commit_tree"](
            repository.resolve(), repository.resolve(), revision
        )

    def test_audit_validation_rejects_repository_evidence_runtime_reference(self) -> None:
        evidence = self.repo / ".aiui-evidence"
        evidence.mkdir()
        (evidence / "capture.json").write_text(
            '{"captured":true}\n', encoding="utf-8"
        )
        (self.fixture.import_root / "app.js").write_text(
            "const capture = '../.aiui-evidence/capture.json';\n"
            "export default {};\n",
            encoding="utf-8",
        )
        completed = self.validate()

        self.assertEqual(1, completed.returncode)
        self.assertIn("reserved_audit_reference", completed.stderr.lower())

    def test_audit_accepts_nested_same_named_source_with_explicit_repository(self) -> None:
        original_page = self.fixture.import_root / "pages/index/index.ink"
        nested_page = self.fixture.import_root / ".aiui-evidence" / "index.ink"
        nested_page.parent.mkdir()
        original_page.replace(nested_page)
        (self.fixture.import_root / "app.json").write_text(
            json.dumps({"pages": [".aiui-evidence/index"]}), encoding="utf-8"
        )
        self.fixture.report = self.fixture.inventory()
        self.fixture.ux_rows = self.fixture.default_ux_rows()
        self.fixture.cap_rows = self.fixture.default_capability_rows()

        completed = self.validate(self.fixture.render())

        self.assertEqual(2, completed.returncode, completed.stdout + completed.stderr)
        self.assertIn("structurally valid", completed.stdout.lower())

    def validate(
        self,
        markdown: str | None = None,
        *,
        public_key: Path | None = None,
        trust_policy: Path | None = None,
        import_root: str = "project",
    ) -> subprocess.CompletedProcess[str]:
        audit = self.fixture.write_audit(markdown)
        command = [
            sys.executable,
            str(SCRIPT),
            str(audit),
            "--repository-root",
            str(self.repo),
            "--import-root",
            import_root,
        ]
        if public_key is not None:
            command.extend(["--trusted-device-public-key", str(public_key)])
        if trust_policy is not None:
            command.extend(["--trust-policy", str(trust_policy)])
        return subprocess.run(command, cwd=ROOT, text=True, capture_output=True)

    def unavailable_audit(self) -> str:
        revision = "88e70bb0382525c1a93ef077c2401dcc31a273ce"
        input_row = next(
            row for row in self.fixture.ux_rows if row[0].startswith("[UX-INPUT]")
        )
        input_row[0] = re.sub(r"\{gate=[^}]+\}", "{gate=no-input}", input_row[0])
        self.fixture.cap_rows = [
            [
                "[CAP-UNREGISTERED-UNAVAILABLE] {family=project.unregistered} "
                "{gate=unavailable-source} Source unavailable",
                "AIUI 0.17.0; device=UNAVAILABLE; surface=UNAVAILABLE",
                "PROJECT-BINDING:UNRESOLVED",
                "UNKNOWN — source policy not registered",
                "SEARCH-SCOPE=[AIUI documentation index](https://github.com/"
                f"yodaos-project/AIUI/tree/{revision}/documentation); "
                "SEARCH-SCOPE=[AIUI samples index](https://github.com/"
                f"yodaos-project/AIUI/tree/{revision}/samples)",
                capability_path(
                    "project.unregistered",
                    "positive",
                    "The declared capability performs its claimed outcome once",
                ),
                capability_path(
                    "project.unregistered",
                    "negative-fallback",
                    "Unavailable, rejected, or ignored delivery preserves an explicit fallback",
                ),
                capability_path(
                    "project.unregistered",
                    "lifecycle-cleanup",
                    "Hide/show and unload do not retain stale capability work",
                ),
                "SOURCE, STATIC, LOGIC, AIX, STUDIO, DEVICE",
                "BLOCKED",
                blocked_evidence(("SOURCE", "STATIC", "LOGIC", "AIX", "STUDIO", "DEVICE")),
            ]
        ]
        markdown = self.fixture.render()
        return (
            markdown.replace(
                f"Project revision: {self.fixture.report['projectRevision']}",
                "Project revision: UNAVAILABLE",
                1,
            )
            .replace("Import root: project", "Import root: UNAVAILABLE", 1)
            .replace(
                "Supported surfaces: "
                + (",".join(self.fixture.report["supportedSurfaces"]) or "UNAVAILABLE"),
                "Supported surfaces: UNAVAILABLE",
                1,
            )
            .replace(
                "Inputs: "
                + ",".join(
                    sorted(
                        f"{entry['kind']}@{entry['gate']}"
                        for entry in self.fixture.report["inputGates"]
                    )
                ),
                "Inputs: none",
                1,
            )
            .replace(
                "Claimed capabilities: " + ",".join(self.fixture.report["claimedCapabilities"]),
                "Claimed capabilities: project.unregistered@unavailable-source",
                1,
            )
        )

    @unittest.skipUnless(shutil.which("openssl"), "OpenSSL is required for trust test")
    def test_full_pass_black_box_is_the_only_release_ready_exit_zero(self) -> None:
        signers, policy = self.authority()
        self.fixture.materialize_full_pass(signers)
        markdown = self.fixture.render()
        self.assertIn("Final status: PASS", markdown)
        self.assertIn("Release-ready: YES", markdown)
        completed = self.validate(markdown, trust_policy=policy)
        self.assertEqual(0, completed.returncode, completed.stderr)
        self.assertIn("Final status=PASS", completed.stdout)
        self.assertIn("Release-ready=YES", completed.stdout)

    @unittest.skipUnless(shutil.which("openssl"), "OpenSSL is required for trust test")
    def test_full_pass_cannot_release_a_project_with_a_missing_declared_route(self) -> None:
        (self.fixture.import_root / "app.json").write_text(
            json.dumps({"pages": ["pages/missing/index"]}), encoding="utf-8"
        )
        self.fixture.report = self.fixture.inventory()
        self.fixture.ux_rows = self.fixture.default_ux_rows()
        self.fixture.cap_rows = self.fixture.default_capability_rows()
        signers, policy = self.authority()
        self.fixture.materialize_full_pass(signers)

        completed = self.validate(trust_policy=policy)

        self.assertEqual(1, completed.returncode, completed.stdout + completed.stderr)
        self.assertIn("strict AIUI project validation failed", completed.stderr)
        self.assertIn("PAGE_ROUTE_NOT_FOUND", completed.stderr)

    @unittest.skipUnless(shutil.which("openssl"), "OpenSSL is required for trust test")
    def test_full_pass_rejects_resigned_studio_runtime_from_another_aiui_version(self) -> None:
        signers, policy = self.authority()
        self.fixture.materialize_full_pass(signers)
        markdown, rewritten = self.fixture.rewrite_signed_environments(
            self.fixture.render(),
            layer="STUDIO",
            signer=signers,
            mutate=lambda environment: environment.__setitem__(
                "hostRuntime", "AIUI 0.18.0"
            ),
        )
        self.assertGreater(rewritten, 0)

        completed = self.validate(markdown, trust_policy=policy)

        self.assertEqual(1, completed.returncode, completed.stdout + completed.stderr)
        self.assertIn("hostruntime", completed.stderr.lower())
        self.assertIn("canonical version", completed.stderr.lower())

    def test_complete_blocked_audit_is_accepted(self) -> None:
        completed = self.validate()
        self.assertEqual(2, completed.returncode, completed.stderr)
        self.assertIn("valid", completed.stdout.lower())
        self.assertIn("Final status=BLOCKED", completed.stdout)
        self.assertIn("Release-ready=NO", completed.stdout)

    def test_invalid_audit_uses_exit_one_not_release_blocked_exit_two(self) -> None:
        completed = self.validate(self.fixture.render().replace("Final status: BLOCKED", "Final status: PASS"))
        self.assertEqual(1, completed.returncode)
        self.assertIn("invalid", completed.stderr.lower())

    def test_source_unavailable_audit_is_valid_but_release_blocked(self) -> None:
        completed = self.validate(self.unavailable_audit(), import_root="UNAVAILABLE")
        self.assertEqual(2, completed.returncode, completed.stderr)
        self.assertIn("Final status=BLOCKED", completed.stdout)
        self.assertIn("Release-ready=NO", completed.stdout)

    def test_source_unavailable_mode_rejects_non_blocked_rows(self) -> None:
        markdown = self.unavailable_audit().replace(
            "| BLOCKED | SOURCE=blocked:", "| N/A | SOURCE=blocked:", 1
        )
        completed = self.validate(markdown, import_root="UNAVAILABLE")
        self.assertEqual(1, completed.returncode)

    def test_requires_exact_seven_metadata_lines_and_two_matrix_headers(self) -> None:
        baseline = self.fixture.render()
        invalid = (
            "Introduction: trust me\n" + baseline,
            baseline.replace("Inputs: tap@tap-primary\n", "", 1),
            baseline.replace("| Evidence |", "| Proof |", 1),
            baseline.replace("## Per-capability matrix", "## Capability matrix", 1),
        )
        for markdown in invalid:
            with self.subTest(markdown=markdown[:40]):
                self.assertNotEqual(0, self.validate(markdown).returncode)

    def test_ux_fixed_layers_and_input_gate_ledger_are_closed(self) -> None:
        missing_layer = self.fixture.render().replace(
            "LOGIC, STUDIO, DEVICE", "LOGIC, STUDIO", 1
        ).replace(
            "DEVICE=blocked:current-revision evidence not supplied", "", 1
        )
        wrong_input = self.fixture.render().replace(
            "Inputs: tap@tap-primary", "Inputs: tap@another-gate"
        )
        for markdown in (missing_layer, wrong_input):
            self.assertNotEqual(0, self.validate(markdown).returncode)

    def test_claimed_capabilities_must_equal_fresh_inventory(self) -> None:
        claim_line = "Claimed capabilities: " + ",".join(
            self.fixture.report["claimedCapabilities"]
        )
        invented_line = "Claimed capabilities: " + ",".join(
            sorted([*self.fixture.report["claimedCapabilities"], "network.https@invented"])
        )
        markdown = self.fixture.render().replace(
            claim_line,
            invented_line,
            1,
        )
        completed = self.validate(markdown)
        self.assertNotEqual(0, completed.returncode)
        self.assertIn("inventory", completed.stderr.lower())

    def test_supported_surfaces_must_equal_scanner_ledger(self) -> None:
        original_surfaces = ",".join(self.fixture.report["supportedSurfaces"])
        markdown = self.fixture.render().replace(
            f"Supported surfaces: {original_surfaces}",
            "Supported surfaces: banana",
            1,
        )
        completed = self.validate(markdown)
        self.assertEqual(1, completed.returncode)
        self.assertIn("supported surfaces", completed.stderr.lower())

    @unittest.skipUnless(shutil.which("openssl"), "OpenSSL is required for trust test")
    def test_unavailable_target_surface_cannot_claim_pass(self) -> None:
        signers, policy = self.authority()
        page = self.fixture.import_root / "pages/index/index.ink"
        page.write_text(
            page.read_text(encoding="utf-8").replace(
                "<style>@media (target: _current) {}</style>", ""
            ),
            encoding="utf-8",
        )
        self.fixture.report = self.fixture.inventory()
        self.assertEqual(["Page"], self.fixture.report["supportedSurfaces"])
        self.fixture.ux_rows = self.fixture.default_ux_rows()
        self.fixture.cap_rows = self.fixture.default_capability_rows()
        self.fixture.materialize_full_pass(signers)
        completed = self.validate(trust_policy=policy)
        self.assertEqual(1, completed.returncode)
        self.assertIn("ux-target", completed.stderr.lower())
        self.assertIn("blocked", completed.stderr.lower())

    def test_closed_claims_ledger_is_required_for_inspected_source(self) -> None:
        (self.fixture.import_root / "aiui-audit-claims.json").unlink()
        completed = self.validate()
        self.assertEqual(1, completed.returncode)
        self.assertIn("claims ledger", completed.stderr.lower())

    def test_inputs_must_equal_scanner_gates_and_combined_is_forbidden(self) -> None:
        combined = self.fixture.render().replace("Inputs: tap@", "Inputs: combined@", 1)
        combined_result = self.validate(combined)
        self.assertEqual(1, combined_result.returncode)
        self.assertIn("combined", combined_result.stderr.lower())

        page = self.fixture.import_root / "pages/index/index.ink"
        page.write_text(
            page.read_text(encoding="utf-8").replace(
                "export default { handleTap() {} };",
                "export default { handleTap() {}, onKeyUp(event) { "
                "if (event.code === 'Enter') this.handleTap(); } };",
            ),
            encoding="utf-8",
        )
        self.fixture.report = self.fixture.inventory()
        self.fixture.ux_rows = self.fixture.default_ux_rows()
        self.fixture.cap_rows = self.fixture.default_capability_rows()
        expected_inputs = sorted(
            f"{entry['kind']}@{entry['gate']}"
            for entry in self.fixture.report["inputGates"]
        )
        enter = next(value for value in expected_inputs if value.startswith("enter@"))
        self.fixture.ux_rows = [
            row
            for row in self.fixture.ux_rows
            if f"{{gate={enter.split('@', 1)[1]}}}" not in row[0]
        ]
        missing_enter = self.fixture.render().replace(
            "Inputs: " + ",".join(expected_inputs),
            "Inputs: " + ",".join(value for value in expected_inputs if value != enter),
            1,
        )
        missing_result = self.validate(missing_enter)
        self.assertEqual(1, missing_result.returncode)
        self.assertIn("scanner", missing_result.stderr.lower())

    def test_unresolved_key_input_forms_a_valid_blocked_audit_gate(self) -> None:
        page = self.fixture.import_root / "pages/index/index.ink"
        page.write_text(
            page.read_text(encoding="utf-8").replace(
                "export default { handleTap() {} };",
                "export default { handleTap() {}, onKeyUp(payload) { "
                "if (payload.code === configuredCode) this.handleTap(); } };",
            ),
            encoding="utf-8",
        )
        self.fixture.report = self.fixture.inventory()
        self.fixture.ux_rows = self.fixture.default_ux_rows()
        self.fixture.cap_rows = self.fixture.default_capability_rows()

        unknown = next(
            item
            for item in self.fixture.report["items"]
            if item["family"] == "input.key.unknown"
        )
        self.assertIn(
            {"family": "input.key.unknown", "kind": "key", "gate": unknown["gate"]},
            self.fixture.report["inputGates"],
        )
        completed = self.validate()

        self.assertEqual(2, completed.returncode, completed.stderr)
        self.assertIn("Final status=BLOCKED", completed.stdout)

    def test_capability_target_tuple_rejects_mixed_aiui_versions(self) -> None:
        markdown = self.fixture.render().replace(
            "AIUI 0.17.0; device=UNAVAILABLE; surface=_current",
            "AIUI 0.17.0; device=UNAVAILABLE; surface=_current; note=AIUI 0.18.0",
            1,
        )
        completed = self.validate(markdown)
        self.assertEqual(1, completed.returncode)
        self.assertIn("target tuple", completed.stderr.lower())

    def test_capability_binding_and_official_source_set_are_inventory_bound(self) -> None:
        baseline = self.fixture.render()
        invalid = (
            baseline.replace("app.json#pages:pages/index/index", "app.json#pages:invented", 1),
            baseline.replace(
                "documentation/1-framework/open-agent-format/app-json.en-US.md",
                "documentation/1-framework/open-agent-format/target.en-US.md",
                1,
            ),
        )
        for markdown in invalid:
            self.assertNotEqual(0, self.validate(markdown).returncode)

    def test_contract_registry_and_capability_paths_are_machine_closed(self) -> None:
        baseline = self.fixture.render()
        ux_token = UX_CONTRACT_TOKENS["UX-TARGET"]
        invalid = (
            baseline.replace(ux_token, "ux-banana-v1", 1),
            baseline.replace(
                UX_CONTRACTS["UX-TARGET"][0],
                "One convenient target only",
                1,
            ),
            baseline.replace(
                UX_CONTRACTS["UX-STATE"][1],
                "Something might look wrong",
                1,
            ),
            baseline.replace(
                UX_CONTRACTS["UX-TEXT"][2],
                "Open the page and look at ordinary text",
                1,
            ),
            baseline.replace("{path=negative-fallback}", "{path=positive}", 1),
            baseline.replace("{path=lifecycle-cleanup}", "{path=positive}", 1),
            baseline.replace(
                self.fixture.cap_rows[0][5],
                capability_path(
                    self.fixture.cap_rows[0][0].split("{family=", 1)[1].split("}", 1)[0],
                    "positive",
                    "A generic success happens somehow",
                ),
                1,
            ),
        )
        for markdown in invalid:
            with self.subTest(marker=markdown[:32]):
                completed = self.validate(markdown)
                self.assertEqual(1, completed.returncode)
                self.assertIn("contract", completed.stderr.lower())

    def test_capability_behavior_registry_covers_every_policy_family(self) -> None:
        namespace = runpy.run_path(str(SCRIPT))
        self.assertEqual(
            set(namespace["CAPABILITY_POLICIES"]),
            set(namespace["CAPABILITY_BEHAVIOR_CONTRACTS"]),
        )

    def test_binding_unresolved_claim_keeps_exact_family_behavior_contract(self) -> None:
        claims = self.fixture.import_root / "aiui-audit-claims.json"
        claims.write_text(
            json.dumps(
                {
                    "schemaVersion": 1,
                    "scopeClosed": True,
                    "claims": [
                        {
                            "family": "network.https",
                            "surface": "_blank",
                            "description": "Fetch the requested timer preset",
                        }
                    ],
                }
            ),
            encoding="utf-8",
        )
        self.fixture.report = self.fixture.inventory()
        self.fixture.ux_rows = self.fixture.default_ux_rows()
        self.fixture.cap_rows = self.fixture.default_capability_rows()
        provisional = next(
            row for row in self.fixture.cap_rows if "{family=network.https}" in row[0]
        )
        self.assertEqual(
            capability_path("network.https", "positive", CAP_BEHAVIORS["network.https"][0]),
            provisional[5],
        )
        baseline = self.fixture.render()
        self.assertEqual(2, self.validate(baseline).returncode)
        invalid = (
            baseline.replace("CAP-NETWORK-HTTPS-PROVISIONAL", "CAP-NETWORK-HTTPS", 1),
            baseline.replace(
                provisional[6],
                capability_path(
                    "network.https",
                    "negative-fallback",
                    "Call wx.request and assume it succeeds",
                ),
                1,
            ),
        )
        for markdown in invalid:
            completed = self.validate(markdown)
            self.assertEqual(1, completed.returncode)
            self.assertIn("contract", completed.stderr.lower())

    def test_multiple_same_family_claims_accept_unique_provisional_instance_ids(self) -> None:
        claims = self.fixture.import_root / "aiui-audit-claims.json"
        claims.write_text(
            json.dumps(
                {
                    "schemaVersion": 1,
                    "scopeClosed": True,
                    "claims": [
                        {
                            "family": "network.https",
                            "surface": "_current",
                            "description": "Load the compact result",
                        },
                        {
                            "family": "network.https",
                            "surface": "_blank",
                            "description": "Load the expanded result",
                        },
                    ],
                }
            ),
            encoding="utf-8",
        )
        self.fixture.report = self.fixture.inventory()
        self.fixture.ux_rows = self.fixture.default_ux_rows()
        self.fixture.cap_rows = self.fixture.default_capability_rows()
        provisional_rows = [
            row
            for row in self.fixture.cap_rows
            if "{family=network.https}" in row[0]
            and "PROJECT-BINDING:UNRESOLVED" in row[2]
        ]
        self.assertEqual(2, len(provisional_rows))
        for index, row in enumerate(provisional_rows, start=1):
            row[0] = row[0].replace(
                "[CAP-NETWORK-HTTPS-PROVISIONAL]",
                f"[CAP-NETWORK-HTTPS-CLAIM{index}-PROVISIONAL]",
                1,
            )

        valid = self.fixture.render()
        completed = self.validate(valid)
        self.assertEqual(2, completed.returncode, completed.stderr)

        duplicate = valid.replace(
            "CAP-NETWORK-HTTPS-CLAIM2-PROVISIONAL",
            "CAP-NETWORK-HTTPS-CLAIM1-PROVISIONAL",
        )
        rejected = self.validate(duplicate)
        self.assertEqual(1, rejected.returncode)
        self.assertIn("globally unique", rejected.stderr.lower())

    def test_source_unavailable_registered_family_keeps_canonical_behavior(self) -> None:
        family = "network.https"
        gate = "disclosed-network"
        revision = "88e70bb0382525c1a93ef077c2401dcc31a273ce"
        behavior = CAP_BEHAVIORS[family]
        source_cell = "; ".join(
            f"{role}=[source](https://github.com/yodaos-project/AIUI/"
            f"blob/{revision}/{path})"
            for role, path in SOURCE_PATHS[family]
        )
        self.fixture.cap_rows = [
            [
                f"[CAP-NETWORK-HTTPS-PROVISIONAL] {{family={family}}} "
                f"{{gate={gate}}} Disclosed HTTPS request",
                "AIUI 0.17.0; device=UNAVAILABLE; surface=UNAVAILABLE",
                "PROJECT-BINDING:UNRESOLVED",
                "PROJECT-BINDING:UNRESOLVED",
                source_cell,
                capability_path(family, "positive", behavior[0]),
                capability_path(family, "negative-fallback", behavior[1]),
                capability_path(family, "lifecycle-cleanup", behavior[2]),
                ", ".join(CAP_LAYERS[family]),
                "BLOCKED",
                blocked_evidence(CAP_LAYERS[family]),
            ]
        ]
        input_row = next(
            row for row in self.fixture.ux_rows if row[0].startswith("[UX-INPUT]")
        )
        input_row[0] = re.sub(r"\{gate=[^}]+\}", "{gate=no-input}", input_row[0])
        markdown = (
            self.fixture.render()
            .replace(
                f"Project revision: {self.fixture.report['projectRevision']}",
                "Project revision: UNAVAILABLE",
                1,
            )
            .replace("Import root: project", "Import root: UNAVAILABLE", 1)
            .replace(
                "Supported surfaces: "
                + (",".join(self.fixture.report["supportedSurfaces"]) or "UNAVAILABLE"),
                "Supported surfaces: UNAVAILABLE",
                1,
            )
            .replace(
                "Inputs: "
                + ",".join(
                    sorted(
                        f"{entry['kind']}@{entry['gate']}"
                        for entry in self.fixture.report["inputGates"]
                    )
                ),
                "Inputs: none",
                1,
            )
            .replace(
                "Claimed capabilities: "
                + ",".join(self.fixture.report["claimedCapabilities"]),
                f"Claimed capabilities: {family}@{gate}",
                1,
            )
        )
        accepted = self.validate(markdown, import_root="UNAVAILABLE")
        self.assertEqual(2, accepted.returncode, accepted.stderr)

        instance_id = markdown.replace(
            "CAP-NETWORK-HTTPS-PROVISIONAL",
            "CAP-NETWORK-HTTPS-DISCLOSED-PROVISIONAL",
        )
        accepted_instance = self.validate(instance_id, import_root="UNAVAILABLE")
        self.assertEqual(2, accepted_instance.returncode, accepted_instance.stderr)

        generic = markdown.replace(
            capability_path(family, "negative-fallback", behavior[1]),
            capability_path(
                family,
                "negative-fallback",
                "Unavailable, rejected, or ignored delivery preserves an explicit fallback",
            ),
            1,
        )
        rejected = self.validate(generic, import_root="UNAVAILABLE")
        self.assertEqual(1, rejected.returncode)
        self.assertIn("contract", rejected.stderr.lower())

    def test_source_unavailable_inputs_and_input_capabilities_close_both_ways(self) -> None:
        family = "event.bindtap"
        gate = "disclosed-tap"
        revision = "88e70bb0382525c1a93ef077c2401dcc31a273ce"
        behavior = CAP_BEHAVIORS[family]
        source_cell = "; ".join(
            f"{role}=[source](https://github.com/yodaos-project/AIUI/"
            f"blob/{revision}/{path})"
            for role, path in SOURCE_PATHS[family]
        )
        self.fixture.cap_rows = [
            [
                f"[CAP-BINDTAP-PROVISIONAL] {{family={family}}} "
                f"{{gate={gate}}} Disclosed tap binding",
                "AIUI 0.17.0; device=UNAVAILABLE; surface=UNAVAILABLE",
                "PROJECT-BINDING:UNRESOLVED",
                "PROJECT-BINDING:UNRESOLVED",
                source_cell,
                capability_path(family, "positive", behavior[0]),
                capability_path(family, "negative-fallback", behavior[1]),
                capability_path(family, "lifecycle-cleanup", behavior[2]),
                ", ".join(CAP_LAYERS[family]),
                "BLOCKED",
                blocked_evidence(CAP_LAYERS[family]),
            ]
        ]
        input_row = next(
            row for row in self.fixture.ux_rows if row[0].startswith("[UX-INPUT]")
        )
        input_row[0] = re.sub(
            r"\{gate=[^}]+\}", f"{{gate={gate}}}", input_row[0]
        )
        original_inputs = ",".join(
            sorted(
                f"{entry['kind']}@{entry['gate']}"
                for entry in self.fixture.report["inputGates"]
            )
        )
        original_claims = ",".join(self.fixture.report["claimedCapabilities"])
        markdown = (
            self.fixture.render()
            .replace(
                f"Project revision: {self.fixture.report['projectRevision']}",
                "Project revision: UNAVAILABLE",
                1,
            )
            .replace("Import root: project", "Import root: UNAVAILABLE", 1)
            .replace(
                "Supported surfaces: "
                + (",".join(self.fixture.report["supportedSurfaces"]) or "UNAVAILABLE"),
                "Supported surfaces: UNAVAILABLE",
                1,
            )
            .replace(f"Inputs: {original_inputs}", f"Inputs: tap@{gate}", 1)
            .replace(
                f"Claimed capabilities: {original_claims}",
                f"Claimed capabilities: {family}@{gate}",
                1,
            )
        )
        accepted = self.validate(markdown, import_root="UNAVAILABLE")
        self.assertEqual(2, accepted.returncode, accepted.stderr)

        orphan = markdown.replace(f"Inputs: tap@{gate}", "Inputs: tap@orphan", 1).replace(
            f"{{gate={gate}}}", "{gate=orphan}", 1
        )
        wrong_kind = markdown.replace(
            f"Inputs: tap@{gate}", f"Inputs: enter@{gate}", 1
        )
        missing_reverse = markdown.replace(
            f"Inputs: tap@{gate}", "Inputs: none", 1
        ).replace(f"{{gate={gate}}}", "{gate=no-input}", 1)
        for invalid in (orphan, wrong_kind, missing_reverse):
            with self.subTest(metadata=invalid.split("\n")[5]):
                rejected = self.validate(invalid, import_root="UNAVAILABLE")
                self.assertEqual(1, rejected.returncode)
                self.assertIn("input", rejected.stderr.lower())

    def test_inventory_version_violations_are_fatal(self) -> None:
        app_json = self.fixture.import_root / "app.json"
        app_json.write_text(
            json.dumps(
                {
                    "pages": ["pages/index/index"],
                    "widgets": [{"path": "widgets/clock", "family": "1x1"}],
                }
            ),
            encoding="utf-8",
        )
        self.fixture.report = self.fixture.inventory()
        completed = self.validate()
        self.assertNotEqual(0, completed.returncode)
        self.assertIn("widgets_unsupported_target", completed.stderr.lower())

    def test_result_requires_one_evidence_mapping_per_declared_layer(self) -> None:
        markdown = self.fixture.render().replace(
            "LOGIC=blocked:current-revision evidence not supplied; ", "", 1
        )
        self.assertNotEqual(0, self.validate(markdown).returncode)

    def test_final_precedence_reason_and_required_gate_ledgers_are_exact(self) -> None:
        baseline = self.fixture.render()
        invalid = (
            baseline.replace("Final status: BLOCKED", "Final status: PASS"),
            baseline.replace("BLOCKED=[CAP-PAGE-ROUTE", "BLOCKED=[UX-INVENTED,CAP-PAGE-ROUTE"),
            baseline.replace("Required gates: ", "Required gates: UX-INVENTED@DEVICE,", 1),
            baseline + "Release approval granted.\n",
        )
        for markdown in invalid:
            with self.subTest(tail=markdown[-80:]):
                self.assertNotEqual(0, self.validate(markdown).returncode)

    @unittest.skipUnless(shutil.which("openssl"), "OpenSSL is required for trust test")
    def test_schema2_snapshots_and_runner_attested_command_are_accepted(self) -> None:
        family = "UX-VISUAL"
        gate = UX[family][0]
        criterion = ux_criterion(family)
        signers, policy = self.authority()

        locator = self.fixture.manifest_locator(
            row=f"{family}-PASS",
            gate=gate,
            layer="STATIC",
            criterion=criterion,
            signer=signers,
        )
        self.fixture.split_ux_outcome(family, "STATIC", locator, "command")
        completed = self.validate(trust_policy=policy)
        self.assertEqual(2, completed.returncode, completed.stderr)
        self.assertIn("structurally valid", completed.stdout)

    def test_handwritten_command_evidence_without_runner_attestation_is_rejected(self) -> None:
        family = "UX-VISUAL"
        criterion = ux_criterion(family)
        locator = self.fixture.manifest_locator(
            row=f"{family}-PASS",
            gate=UX[family][0],
            layer="STATIC",
            criterion=criterion,
        )
        self.fixture.split_ux_outcome(family, "STATIC", locator, "command")
        completed = self.validate()
        self.assertEqual(1, completed.returncode)
        self.assertIn("runner", completed.stderr.lower())

    @unittest.skipUnless(shutil.which("openssl"), "OpenSSL is required for trust test")
    def test_signed_manifest_argv_is_validated_but_never_executed(self) -> None:
        signers, policy = self.authority()
        sentinel = self.repo / "argv-must-not-run.txt"
        family = "UX-VISUAL"

        def inject(entry: dict) -> None:
            entry["argv"] = [
                sys.executable,
                "-c",
                "from pathlib import Path; "
                f"Path({str(sentinel)!r}).write_text('executed')",
            ]

        locator = self.fixture.manifest_locator(
            row=f"{family}-PASS",
            gate=UX[family][0],
            layer="STATIC",
            criterion=ux_criterion(family),
            signer=signers,
            entry_mutate=inject,
        )
        self.fixture.split_ux_outcome(family, "STATIC", locator, "command")
        completed = self.validate(trust_policy=policy)
        self.assertEqual(2, completed.returncode, completed.stderr)
        self.assertFalse(sentinel.exists(), "validator executed untrusted manifest argv")

    def test_structurally_honest_fail_audit_validates_but_is_not_release_ready(self) -> None:
        family = "UX-VISUAL"
        gate = UX[family][0]
        criterion = ux_criterion(family)
        signers, policy = self.authority()
        locator = self.fixture.manifest_locator(
            row=f"{family}-FAIL",
            gate=gate,
            layer="STATIC",
            criterion=criterion,
            result="FAIL",
            signer=signers,
        )
        self.fixture.split_ux_outcome(
            family, "STATIC", locator, "command", result="FAIL"
        )
        markdown = self.fixture.render()
        self.assertIn("Final status: FAIL", markdown)
        self.assertIn("Release-ready: NO", markdown)
        completed = self.validate(markdown, trust_policy=policy)
        self.assertEqual(2, completed.returncode, completed.stderr)
        self.assertIn("Final status=FAIL", completed.stdout)
        self.assertIn("Release-ready=NO", completed.stdout)

    def test_production_manifest_and_artifacts_must_be_under_reserved_root(self) -> None:
        family = "UX-VISUAL"
        locator = self.fixture.manifest_locator(
            row=f"{family}-PASS",
            gate=UX[family][0],
            layer="STATIC",
            criterion=ux_criterion(family),
            outside=True,
        )
        self.fixture.split_ux_outcome(family, "STATIC", locator, "command")
        completed = self.validate()
        self.assertNotEqual(0, completed.returncode)
        self.assertIn(".aiui-evidence", completed.stderr)

    def test_manifest_schema_snapshot_artifact_and_command_tampering_fail_closed(self) -> None:
        mutations = {
            "schema": lambda manifest: manifest.__setitem__("schemaVersion", 1),
            "source snapshot": lambda manifest: manifest.pop("sourceSnapshot"),
            "completion snapshot": lambda manifest: manifest.pop("completionSnapshot"),
            "command": lambda manifest: manifest["entries"][0].pop("argv"),
            "artifact hash": lambda manifest: manifest["entries"][0].__setitem__(
                "sha256", "0" * 64
            ),
        }
        for label, mutation in mutations.items():
            with self.subTest(label=label):
                with tempfile.TemporaryDirectory() as temporary:
                    fixture = AuditFixture(Path(temporary))
                    family = "UX-VISUAL"
                    locator = fixture.manifest_locator(
                        row=f"{family}-PASS",
                        gate=UX[family][0],
                        layer="STATIC",
                        criterion=ux_criterion(family),
                        mutate=mutation,
                    )
                    fixture.split_ux_outcome(family, "STATIC", locator, "command")
                    audit = fixture.write_audit()
                    completed = subprocess.run(
                        [
                            sys.executable,
                            str(SCRIPT),
                            str(audit),
                            "--repo-root",
                            str(fixture.root),
                            "--import-root",
                            "project",
                        ],
                        cwd=ROOT,
                        text=True,
                        capture_output=True,
                    )
                    self.assertNotEqual(0, completed.returncode)

    def test_na_requires_replayable_source_and_closed_claim_proofs(self) -> None:
        row = self.fixture.ux_rows[0]
        row[5] = "N/A"
        row[6] = "SCOPE: source=absent.txt; claim=claims.txt"
        self.assertNotEqual(0, self.validate().returncode)

    @unittest.skipUnless(shutil.which("openssl"), "OpenSSL is required for trust test")
    def test_na_accepts_fingerprinted_inventory_and_closed_ux_scope(self) -> None:
        signers, policy = self.authority()
        scope = self.fixture.import_root / "aiui-audit-scope.json"
        scope.write_text(
            json.dumps({"schemaVersion": 1, "closed": True, "uxCriteria": []}),
            encoding="utf-8",
        )
        self.fixture.report = self.fixture.inventory()
        self.fixture.cap_rows = self.fixture.default_capability_rows()
        row = next(
            row
            for row in self.fixture.ux_rows
            if row[0].startswith("[UX-RECOVERY]")
        )
        identifier = row[0].split("]", 1)[0][1:]
        gate = row[0].split("{gate=", 1)[1].split("}", 1)[0]
        source, claim = self.fixture.scope_locators(
            row=identifier,
            gate=gate,
            criterion=row[3],
            signer=signers,
        )
        row[5] = "N/A"
        row[6] = f"SCOPE: source={source}; claim={claim}"
        completed = self.validate(trust_policy=policy)
        self.assertEqual(2, completed.returncode, completed.stderr)
        self.assertIn("structurally valid", completed.stdout)

    @unittest.skipUnless(shutil.which("openssl"), "OpenSSL is required for trust test")
    def test_scanner_input_gate_cannot_be_scoped_to_na(self) -> None:
        signers, policy = self.authority()
        scope = self.fixture.import_root / "aiui-audit-scope.json"
        scope.write_text(
            json.dumps({"schemaVersion": 1, "closed": True, "uxCriteria": []}),
            encoding="utf-8",
        )
        self.fixture.report = self.fixture.inventory()
        self.fixture.ux_rows = self.fixture.default_ux_rows()
        self.fixture.cap_rows = self.fixture.default_capability_rows()
        row = next(row for row in self.fixture.ux_rows if row[0].startswith("[UX-INPUT]"))
        gate = row[0].split("{gate=", 1)[1].split("}", 1)[0]
        source, claim = self.fixture.scope_locators(
            row="UX-INPUT",
            gate=gate,
            criterion=row[3],
            signer=signers,
        )
        row[5] = "N/A"
        row[6] = f"SCOPE: source={source}; claim={claim}"
        completed = self.validate(trust_policy=policy)
        self.assertEqual(1, completed.returncode)
        self.assertIn("input", completed.stderr.lower())

    @unittest.skipUnless(shutil.which("openssl"), "OpenSSL is required for trust test")
    def test_zero_input_project_uses_signed_no_input_na_gate(self) -> None:
        signers, policy = self.authority()
        page = self.fixture.import_root / "pages/index/index.ink"
        page.write_text(
            "<page><view>static</view><style>"
            "@media (target: _current) {}</style></page>\n",
            encoding="utf-8",
        )
        scope = self.fixture.import_root / "aiui-audit-scope.json"
        scope.write_text(
            json.dumps({"schemaVersion": 1, "closed": True, "uxCriteria": []}),
            encoding="utf-8",
        )
        self.fixture.report = self.fixture.inventory()
        self.assertEqual([], self.fixture.report["inputGates"])
        self.fixture.ux_rows = self.fixture.default_ux_rows()
        self.fixture.cap_rows = self.fixture.default_capability_rows()
        row = next(row for row in self.fixture.ux_rows if row[0].startswith("[UX-INPUT]"))
        source, claim = self.fixture.scope_locators(
            row="UX-INPUT",
            gate="no-input",
            criterion=row[3],
            signer=signers,
        )
        row[5] = "N/A"
        row[6] = f"SCOPE: source={source}; claim={claim}"
        completed = self.validate(trust_policy=policy)
        self.assertEqual(2, completed.returncode, completed.stderr)
        self.assertIn("Final status=BLOCKED", completed.stdout)

    @unittest.skipUnless(shutil.which("openssl"), "OpenSSL is required for trust test")
    def test_structurally_valid_worker_preview_remains_blocked(self) -> None:
        _, policy = self.authority()
        with tempfile.TemporaryDirectory() as temporary:
            fixture = AuditFixture(Path(temporary), target_version="0.18.0")
            (fixture.import_root / "workers").mkdir()
            (fixture.import_root / "app.json").write_text(
                json.dumps(
                    {
                        "pages": ["pages/index/index"],
                        "agentWorkers": [
                            {
                                "name": "timer-worker",
                                "script": "workers/timer.js",
                                "trigger": {"type": "open"},
                                "lifetime": "instant",
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )
            (fixture.import_root / "workers/timer.js").write_text(
                "export default { onOpen(event) { "
                "event.waitUntil(Promise.resolve()); } };\n",
                encoding="utf-8",
            )
            fixture.report = fixture.inventory()
            self.assertEqual(
                ["Agent Worker", "Page", "_current"],
                fixture.report["supportedSurfaces"],
            )
            self.assertEqual(1, len(fixture.report["inputGates"]))
            fixture.ux_rows = fixture.default_ux_rows()
            fixture.cap_rows = fixture.default_capability_rows()
            audit = fixture.write_audit()
            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    str(audit),
                    "--repository-root",
                    str(fixture.root),
                    "--import-root",
                    "project",
                    "--trust-policy",
                    str(policy),
                ],
                cwd=ROOT,
                text=True,
                capture_output=True,
            )
            self.assertEqual(2, completed.returncode, completed.stderr)
            self.assertIn("Final status=BLOCKED", completed.stdout)

    def test_ux_applicability_registry_is_closed(self) -> None:
        namespace = runpy.run_path(str(SCRIPT))
        self.assertEqual(
            set(namespace["UX_REQUIRED_LAYERS"]),
            set(namespace["UX_APPLICABILITY_MODES"]),
        )

    def test_scanner_input_gate_is_applicable_without_surface_inference(self) -> None:
        namespace = runpy.run_path(str(SCRIPT))
        validator_class = namespace["AuditValidator"]
        validator = validator_class.__new__(validator_class)
        validator.inventory = {"items": []}
        validator.supported_surfaces = ("Agent Worker",)
        validator.input_gates = frozenset({"tap"})

        self.assertTrue(validator._ux_is_applicable("UX-INPUT"))

    def test_page_route_keeps_ui_ux_applicable_when_surface_ledger_is_incomplete(self) -> None:
        namespace = runpy.run_path(str(SCRIPT))
        validator_class = namespace["AuditValidator"]
        validator = validator_class.__new__(validator_class)
        validator.inventory = {"items": [{"family": "page.route"}]}
        validator.supported_surfaces = ("Agent Worker",)
        validator.input_gates = frozenset()

        self.assertTrue(validator._ux_is_applicable("UX-TARGET"))
        self.assertTrue(validator._ux_is_applicable("UX-STATE"))

    @unittest.skipUnless(shutil.which("openssl"), "OpenSSL is required for trust test")
    def test_voice_and_gesture_claims_make_recovery_na_invalid(self) -> None:
        signers, policy = self.authority()
        for family in ("input.voice.unknown", "input.gesture-fallback.unknown"):
            with self.subTest(family=family):
                with tempfile.TemporaryDirectory() as temporary:
                    fixture = AuditFixture(Path(temporary))
                    (fixture.import_root / "aiui-audit-claims.json").write_text(
                        json.dumps(
                            {
                                "schemaVersion": 1,
                                "scopeClosed": True,
                                "claims": [
                                    {
                                        "family": family,
                                        "surface": "_current",
                                        "description": "Fallback recovery is required",
                                    }
                                ],
                            }
                        ),
                        encoding="utf-8",
                    )
                    (fixture.import_root / "aiui-audit-scope.json").write_text(
                        json.dumps(
                            {"schemaVersion": 1, "closed": True, "uxCriteria": []}
                        ),
                        encoding="utf-8",
                    )
                    fixture.report = fixture.inventory()
                    fixture.ux_rows = fixture.default_ux_rows()
                    fixture.cap_rows = fixture.default_capability_rows()
                    row = next(
                        row
                        for row in fixture.ux_rows
                        if row[0].startswith("[UX-RECOVERY]")
                    )
                    source, claim = fixture.scope_locators(
                        row="UX-RECOVERY",
                        gate="failure-recovery",
                        criterion=row[3],
                        signer=signers,
                    )
                    row[5] = "N/A"
                    row[6] = f"SCOPE: source={source}; claim={claim}"
                    audit = fixture.write_audit()

                    completed = subprocess.run(
                        [
                            sys.executable,
                            str(SCRIPT),
                            str(audit),
                            "--repository-root",
                            str(fixture.root),
                            "--import-root",
                            "project",
                            "--trust-policy",
                            str(policy),
                        ],
                        cwd=ROOT,
                        text=True,
                        capture_output=True,
                    )

                    self.assertEqual(1, completed.returncode, completed.stderr)
                    self.assertIn("applicable", completed.stderr.lower())

    @unittest.skipUnless(shutil.which("openssl"), "OpenSSL is required for trust test")
    def test_all_ux_families_cannot_be_scoped_away(self) -> None:
        signers, policy = self.authority()
        scope = self.fixture.import_root / "aiui-audit-scope.json"
        scope.write_text(
            json.dumps({"schemaVersion": 1, "closed": True, "uxCriteria": []}),
            encoding="utf-8",
        )
        self.fixture.report = self.fixture.inventory()
        self.fixture.ux_rows = self.fixture.default_ux_rows()
        self.fixture.cap_rows = self.fixture.default_capability_rows()
        for row in self.fixture.ux_rows:
            identifier = row[0].split("]", 1)[0][1:]
            gate = row[0].split("{gate=", 1)[1].split("}", 1)[0]
            source, claim = self.fixture.scope_locators(
                row=identifier,
                gate=gate,
                criterion=row[3],
                signer=signers,
            )
            row[5] = "N/A"
            row[6] = f"SCOPE: source={source}; claim={claim}"
        completed = self.validate(trust_policy=policy)
        self.assertEqual(1, completed.returncode)
        self.assertIn("all ux", completed.stderr.lower())

    def test_aiui_018_inventory_is_allowed_but_capabilities_cannot_pass(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            fixture = AuditFixture(Path(temporary), target_version="0.18.0")
            audit = fixture.write_audit()
            blocked = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    str(audit),
                    "--repository-root",
                    str(fixture.root),
                    "--import-root",
                    "project",
                ],
                cwd=ROOT,
                text=True,
                capture_output=True,
            )
            self.assertEqual(2, blocked.returncode, blocked.stderr)
            fixture.cap_rows[0][9] = "PASS"
            fixture.cap_rows[0][10] = fixture.cap_rows[0][10].replace(
                "blocked:", "command:", 1
            )
            audit = fixture.write_audit()
            attempted_pass = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    str(audit),
                    "--repository-root",
                    str(fixture.root),
                    "--import-root",
                    "project",
                ],
                cwd=ROOT,
                text=True,
                capture_output=True,
            )
            self.assertNotEqual(0, attempted_pass.returncode)
            self.assertIn("remain BLOCKED", attempted_pass.stderr)

    @unittest.skipUnless(shutil.which("openssl"), "OpenSSL is required for trust test")
    def test_repository_self_selected_device_key_is_not_a_trust_policy(self) -> None:
        private_key = self.repo / "device-private.pem"
        public_key = self.repo / "device-public.pem"
        subprocess.run(
            [
                "openssl",
                "genpkey",
                "-algorithm",
                "RSA",
                "-pkeyopt",
                "rsa_keygen_bits:2048",
                "-out",
                str(private_key),
            ],
            capture_output=True,
            check=True,
        )
        subprocess.run(
            [
                "openssl",
                "pkey",
                "-in",
                str(private_key),
                "-pubout",
                "-out",
                str(public_key),
            ],
            capture_output=True,
            check=True,
        )
        family = "UX-ENVIRONMENT"
        device_environment = {
            "deviceModel": "Rokid Glasses",
            "hostBuild": "YodaOS 2.1.0",
            "runtimeVersion": "AIUI 0.17.0",
            "physicalDevice": True,
            "deviceIdHash": "a" * 64,
            "captureTool": "rokid-device-capture",
            "captureSessionId": "session-20260910-0001",
        }
        locator = self.fixture.manifest_locator(
            row=f"{family}-PASS",
            gate=UX[family][0],
            layer="DEVICE",
            criterion=ux_criterion(family),
            kind="log",
            environment=device_environment,
            signer={
                "RUNNER": (private_key, public_key),
                "DEVICE": (private_key, public_key),
            },
        )
        self.fixture.device_host = (
            "device=Rokid Glasses; host=YodaOS 2.1.0; runtime=AIUI 0.17.0"
        )
        self.fixture.split_ux_outcome(family, "DEVICE", locator, "log")
        without_key = self.validate()
        self.assertEqual(1, without_key.returncode)
        self.assertIn("trust policy", without_key.stderr.lower())
        with_key = self.validate(public_key=public_key)
        self.assertEqual(1, with_key.returncode)
        self.assertIn("trust policy", with_key.stderr.lower())

    @unittest.skipUnless(shutil.which("openssl"), "OpenSSL is required for trust test")
    def test_external_policy_pins_device_capture_authority(self) -> None:
        signers, policy = self.authority()
        family = "UX-ENVIRONMENT"
        device_environment = {
            "deviceModel": "Rokid Glasses",
            "hostBuild": "YodaOS 2.1.0",
            "runtimeVersion": "AIUI 0.17.0",
            "physicalDevice": True,
            "deviceIdHash": "a" * 64,
            "captureTool": "rokid-device-capture",
            "captureSessionId": "session-20260910-0001",
        }
        locator = self.fixture.manifest_locator(
            row=f"{family}-PASS",
            gate=UX[family][0],
            layer="DEVICE",
            criterion=ux_criterion(family),
            kind="log",
            environment=device_environment,
            signer=signers,
        )
        self.fixture.device_host = (
            "device=Rokid Glasses; host=YodaOS 2.1.0; runtime=AIUI 0.17.0"
        )
        self.fixture.split_ux_outcome(family, "DEVICE", locator, "log")
        completed = self.validate(trust_policy=policy)
        self.assertEqual(2, completed.returncode, completed.stderr)
        self.assertIn("structurally valid", completed.stdout)

    @unittest.skipUnless(shutil.which("openssl"), "OpenSSL is required for trust test")
    def test_device_manifest_runtime_must_match_canonical_version(self) -> None:
        signers, policy = self.authority()
        family = "UX-ENVIRONMENT"
        device_environment = {
            "deviceModel": "Rokid Glasses",
            "hostBuild": "YodaOS 2.1.0",
            "runtimeVersion": "AIUI 0.18.0",
            "physicalDevice": True,
            "deviceIdHash": "a" * 64,
            "captureTool": "rokid-device-capture",
            "captureSessionId": "session-20260910-0001",
        }
        locator = self.fixture.manifest_locator(
            row=f"{family}-PASS",
            gate=UX[family][0],
            layer="DEVICE",
            criterion=ux_criterion(family),
            kind="log",
            environment=device_environment,
            signer=signers,
        )
        self.fixture.device_host = (
            "device=Rokid Glasses; host=YodaOS 2.1.0; runtime=AIUI 0.17.0"
        )
        self.fixture.split_ux_outcome(family, "DEVICE", locator, "log")
        completed = self.validate(trust_policy=policy)
        self.assertEqual(1, completed.returncode)
        self.assertIn("runtimeversion", completed.stderr.lower())
        self.assertIn("canonical version", completed.stderr.lower())

    @unittest.skipUnless(shutil.which("openssl"), "OpenSSL is required for trust test")
    def test_version_like_host_build_does_not_override_canonical_runtime(self) -> None:
        signers, policy = self.authority()
        family = "UX-ENVIRONMENT"
        version_like_build = "YodaOS host-build 0.18.0-r417"
        device_environment = {
            "deviceModel": "Rokid Glasses",
            "hostBuild": version_like_build,
            "runtimeVersion": "AIUI 0.17.0",
            "physicalDevice": True,
            "deviceIdHash": "a" * 64,
            "captureTool": "rokid-device-capture",
            "captureSessionId": "session-20260910-0001",
        }
        locator = self.fixture.manifest_locator(
            row=f"{family}-PASS",
            gate=UX[family][0],
            layer="DEVICE",
            criterion=ux_criterion(family),
            kind="log",
            environment=device_environment,
            signer=signers,
        )
        self.fixture.device_host = (
            f"device=Rokid Glasses; host={version_like_build}; runtime=AIUI 0.17.0"
        )
        self.fixture.split_ux_outcome(family, "DEVICE", locator, "log")
        completed = self.validate(trust_policy=policy)
        self.assertEqual(2, completed.returncode, completed.stderr)
        self.assertIn("structurally valid", completed.stdout)

    @unittest.skipUnless(shutil.which("openssl"), "OpenSSL is required for trust test")
    def test_studio_evidence_requires_external_capture_authority(self) -> None:
        family = "UX-FOCUS"
        environment = {
            "studioVersion": "AIUI Studio 1.2.3",
            "hostRuntime": "AIUI 0.17.0",
        }
        locator = self.fixture.manifest_locator(
            row=f"{family}-PASS",
            gate=UX[family][0],
            layer="STUDIO",
            criterion=ux_criterion(family),
            kind="log",
            environment=environment,
        )
        self.fixture.split_ux_outcome(family, "STUDIO", locator, "log")
        unsigned = self.validate()
        self.assertEqual(1, unsigned.returncode)
        self.assertIn("authority", unsigned.stderr.lower())

        with tempfile.TemporaryDirectory() as temporary:
            fixture = AuditFixture(Path(temporary))
            signers, policy = self.authority()
            locator = fixture.manifest_locator(
                row=f"{family}-PASS",
                gate=UX[family][0],
                layer="STUDIO",
                criterion=ux_criterion(family),
                kind="log",
                environment=environment,
                signer=signers,
            )
            fixture.split_ux_outcome(family, "STUDIO", locator, "log")
            audit = fixture.write_audit()
            signed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    str(audit),
                    "--repo-root",
                    str(fixture.root),
                    "--import-root",
                    "project",
                    "--trust-policy",
                    str(policy),
                ],
                cwd=ROOT,
                text=True,
                capture_output=True,
            )
            self.assertEqual(2, signed.returncode, signed.stderr)
            self.assertIn("structurally valid", signed.stdout)

    @unittest.skipUnless(shutil.which("openssl"), "OpenSSL is required for trust test")
    def test_studio_log_requires_both_runner_and_studio_authorities(self) -> None:
        signers, policy = self.authority()
        policy_document = json.loads(policy.read_text(encoding="utf-8"))
        policy_document["authorities"].pop("RUNNER")
        policy.write_text(json.dumps(policy_document), encoding="utf-8")
        family = "UX-FOCUS"
        locator = self.fixture.manifest_locator(
            row=f"{family}-PASS",
            gate=UX[family][0],
            layer="STUDIO",
            criterion=ux_criterion(family),
            kind="log",
            environment={
                "studioVersion": "AIUI Studio 1.2.3",
                "hostRuntime": "AIUI 0.17.0",
            },
            signer=signers,
        )
        self.fixture.split_ux_outcome(family, "STUDIO", locator, "log")
        completed = self.validate(trust_policy=policy)
        self.assertEqual(1, completed.returncode)
        self.assertIn("runner", completed.stderr.lower())

    @unittest.skipUnless(shutil.which("openssl"), "OpenSSL is required for trust test")
    def test_trust_policy_roles_must_use_distinct_pinned_keys(self) -> None:
        signers, policy = self.authority()
        document = json.loads(policy.read_text(encoding="utf-8"))
        reused_bytes = signers["RUNNER"][1].read_bytes()
        reused_authorities = {}
        for index, role in enumerate(("RUNNER", "STUDIO", "DEVICE", "SCOPE"), 1):
            encoded_key = self.external / f"same-key-{role.lower()}.pem"
            encoded_key.write_bytes(reused_bytes + b"\n" * index)
            reused_authorities[role] = {
                "publicKeyPath": str(encoded_key),
                "publicKeySha256": public_key_fingerprint(encoded_key),
            }
        document["authorities"] = reused_authorities
        policy.write_text(json.dumps(document), encoding="utf-8")
        completed = self.validate(trust_policy=policy)
        self.assertEqual(1, completed.returncode)
        self.assertIn("distinct", completed.stderr.lower())


if __name__ == "__main__":
    unittest.main()
