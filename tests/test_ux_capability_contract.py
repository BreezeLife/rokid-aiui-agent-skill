from __future__ import annotations

import hashlib
import json
import re
import runpy
import subprocess
import sys
import tempfile
import unittest
import unicodedata
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILL_ROOT = ROOT / "skills" / "rokid-aiui-agent"
SKILL_PATH = SKILL_ROOT / "SKILL.md"
REFERENCE_PATH = SKILL_ROOT / "references" / "ux-and-capability-testing.md"
RUNTIME_REFERENCE_PATH = SKILL_ROOT / "references" / "runtime-capabilities.md"
INTERACTION_REFERENCE_PATH = (
    SKILL_ROOT / "references" / "interaction-and-design.md"
)
FORWARD_EVALUATION_PATH = (
    ROOT / "tests" / "evaluations" / "forward" / "05-ux-capability-audit.md"
)
IMPLEMENTATION_FORWARD_EVALUATION_PATH = (
    ROOT
    / "tests"
    / "evaluations"
    / "forward"
    / "06-implementation-change-gate.md"
)
AUDIT_SCENARIO_PATH = ROOT / "tests" / "scenarios" / "05-ux-capability-audit.md"
IMPLEMENTATION_SCENARIO_PATH = (
    ROOT / "tests" / "scenarios" / "06-implementation-change-gate.md"
)
FINGERPRINT_SCRIPT = (
    SKILL_ROOT / "scripts" / "fingerprint_aiui_project.py"
)
INVENTORY_SCRIPT = (
    SKILL_ROOT / "scripts" / "inventory_aiui_capabilities.py"
)
AUDIT_VALIDATOR_SCRIPT = SKILL_ROOT / "scripts" / "validate_aiui_audit.py"
STABLE_AIUI_REVISION = "88e70bb0382525c1a93ef077c2401dcc31a273ce"
CHECKLIST_AIUI_REVISION = "63bb5f5efa2f0c11a2defca35bc00777150f43d2"
PREVIEW_AIUI_REVISION = "8b19a87b4ba8b486c0dd4dd3fd32290d27891069"
AUDIT_EVIDENCE_DIRECTORY = ".aiui-evidence"
UX_FAMILIES = (
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
)
UX_REQUIRED_LAYERS = {
    "UX-TARGET": frozenset({"LOGIC", "STUDIO", "DEVICE"}),
    "UX-STATE": frozenset({"LOGIC", "AIX", "STUDIO", "DEVICE"}),
    "UX-TEXT": frozenset({"LOGIC", "AIX", "STUDIO", "DEVICE"}),
    "UX-FOCUS": frozenset({"STATIC", "STUDIO", "DEVICE"}),
    "UX-INPUT": frozenset({"LOGIC", "STUDIO", "DEVICE"}),
    "UX-RECOVERY": frozenset({"STATIC", "LOGIC", "STUDIO", "DEVICE"}),
    "UX-LIFECYCLE": frozenset({"LOGIC", "STUDIO", "DEVICE"}),
    "UX-VISUAL": frozenset({"STATIC", "AIX", "DEVICE"}),
    "UX-ENVIRONMENT": frozenset({"AIX", "DEVICE"}),
    "UX-MOTION": frozenset({"LOGIC", "STUDIO", "DEVICE"}),
}
EVIDENCE_LAYERS = frozenset(
    {"SOURCE", "STATIC", "LOGIC", "AIX", "STUDIO", "DEVICE"}
)
ALLOWED_RESULTS = frozenset({"PASS", "FAIL", "BLOCKED", "N/A"})
ALLOWED_STABLE_SOURCE_PATHS = frozenset(
    {
        "documentation/1-framework/open-agent-format/focus.en-US.md",
        "documentation/1-framework/open-agent-format/app-json.en-US.md",
        "documentation/1-framework/open-agent-format/page-events.en-US.md",
        "documentation/1-framework/open-agent-format/target.en-US.md",
        "documentation/2-components/button.en-US.md",
        "documentation/2-components/scroll-view.en-US.md",
        "documentation/3-api/ai/speech-recognition.en-US.md",
        "documentation/3-api/framework/page.en-US.md",
        "documentation/3-api/media/media-capture.en-US.md",
        "documentation/3-api/network/event-source.en-US.md",
        "documentation/3-api/network/https.en-US.md",
        "documentation/3-api/network/websocket.en-US.md",
        "samples/capabilities/app.json",
        "samples/capabilities/pages/chat/index.ink",
        "samples/capabilities/pages/close/index.ink",
        "samples/capabilities/pages/head-gesture/index.ink",
        "samples/capabilities/pages/media_devices/index.ink",
        "samples/capabilities/pages/network_https/index.ink",
        "samples/capabilities/pages/network_sse/index.ink",
        "samples/capabilities/pages/network_websocket/index.ink",
        "samples/capabilities/pages/speech/index.ink",
    }
)
ALLOWED_PROVISIONAL_SOURCE_PATHS = frozenset(
    {
        "documentation",
        "samples",
        "documentation/1-framework/open-agent-format",
        "documentation/2-components",
        "documentation/3-api/ai",
        "documentation/3-api/network",
    }
)
PROJECT_BINDING_UNRESOLVED = "PROJECT-BINDING:UNRESOLVED"
SOURCE_ENTRY_RE = re.compile(
    r"^(?P<role>DOC|SAMPLE|DECLARATION-SNIPPET|SEARCH-SCOPE)="
    r"\[(?P<label>[^\]]+)\]\((?P<url>https?://[^)\s]+)\)$"
)
PINNED_AIUI_SOURCE_RE = re.compile(
    r"^https://github\.com/yodaos-project/AIUI/(?P<url_kind>blob|tree)/"
    r"(?P<revision>[0-9a-f]{40})/(?P<path>[^#?\s]+)"
    r"(?:#(?P<fragment>[^?\s]+))?$",
    flags=re.IGNORECASE,
)
CAPABILITY_ID_RE = re.compile(
    r"^`?\[(?P<identifier>CAP-[A-Z0-9-]+)\]`?\s+"
    r"\{family=(?P<family>[a-z0-9_.-]+)\}\s+"
    r"\{gate=(?P<gate>[a-z0-9_.-]+)\}`?\s+(?P<label>.+)$"
)
UX_ID_RE = re.compile(
    r"^`?\[(?P<identifier>UX-[A-Z0-9-]+)\]`?\s+"
    r"\{gate=(?P<gate>[a-z0-9_.-]+)\}`?$"
)
EVIDENCE_ENTRY_RE = re.compile(
    r"^(?P<layer>SOURCE|STATIC|LOGIC|AIX|STUDIO|DEVICE)="
    r"(?P<kind>source|command|log|screenshot|recording|artifact|blocked):"
    r"(?P<locator>\S.*)$"
)
MANIFEST_LOCATOR_RE = re.compile(
    r"manifest:(?P<path>[^@#]+)@sha256=(?P<digest>[0-9a-f]{64})#"
    r"(?P<entry>[A-Za-z0-9._-]+)"
)
INVALID_EXECUTED_LOCATOR_RE = re.compile(
    r"(?is)(?:^|\b)(?:none|n/?a|missing|unverified|not tested|not provided|"
    r"not executed|fake|fabricated|made[- ]?up|blocked)(?:\b|$)|"
    r"无真机|无设备|无证据|未提供|未执行|未测试|未验证|伪造|虚构|"
    r"仅(?:口头|声称|陈述)|待(?:执行|验证|补充|检查|核对)"
)
LAYER_ALLOWED_KINDS = {
    "SOURCE": frozenset({"source"}),
    "STATIC": frozenset({"source", "command", "log", "artifact"}),
    "LOGIC": frozenset({"command", "log", "artifact"}),
    "AIX": frozenset({"command", "screenshot", "recording"}),
    "STUDIO": frozenset({"log", "screenshot", "recording", "artifact"}),
    "DEVICE": frozenset({"log", "screenshot", "recording", "artifact"}),
}


def manifest_locator(relative_path: str, entry_id: str) -> str:
    manifest_path = ROOT / relative_path
    digest = hashlib.sha256(manifest_path.read_bytes()).hexdigest()
    return f"manifest:{relative_path}@sha256={digest}#{entry_id}"


@dataclass(frozen=True)
class CapabilityContract:
    family: str
    required_layers: frozenset[str]
    required_source_roles: frozenset[tuple[str, str]]
    required_source_fragments: tuple[tuple[str, str], ...] = ()
    provisional: bool = False
    provisional_cells: tuple[str, str, str, str] = ()
    pass_api_pattern: str = ""
    pass_declaration_pattern: str = ""
    pass_blocked_reason: str = ""


APP_JSON_DOC = "documentation/1-framework/open-agent-format/app-json.en-US.md"
TARGET_DOC = "documentation/1-framework/open-agent-format/target.en-US.md"
FOCUS_DOC = "documentation/1-framework/open-agent-format/focus.en-US.md"
PAGE_EVENTS_DOC = "documentation/1-framework/open-agent-format/page-events.en-US.md"
OPEN_AGENT_INDEX = "documentation/1-framework/open-agent-format"
BUTTON_DOC = "documentation/2-components/button.en-US.md"
COMPONENT_INDEX = "documentation/2-components"
AI_INDEX = "documentation/3-api/ai"
PAGE_API_DOC = "documentation/3-api/framework/page.en-US.md"
MEDIA_DOC = "documentation/3-api/media/media-capture.en-US.md"
NETWORK_INDEX = "documentation/3-api/network"
SPEECH_DOC = "documentation/3-api/ai/speech-recognition.en-US.md"
HTTPS_DOC = "documentation/3-api/network/https.en-US.md"
SSE_DOC = "documentation/3-api/network/event-source.en-US.md"
WEBSOCKET_DOC = "documentation/3-api/network/websocket.en-US.md"
SCROLL_VIEW_DOC = "documentation/2-components/scroll-view.en-US.md"
PERMISSION_MANIFEST = "samples/capabilities/app.json"
BUTTON_SAMPLE = "samples/capabilities/pages/close/index.ink"
HEAD_SAMPLE = "samples/capabilities/pages/head-gesture/index.ink"
MEDIA_SAMPLE = "samples/capabilities/pages/media_devices/index.ink"
VOICE_SAMPLE = "samples/capabilities/pages/chat/index.ink"
SPEECH_SAMPLE = "samples/capabilities/pages/speech/index.ink"
HTTPS_SAMPLE = "samples/capabilities/pages/network_https/index.ink"
SSE_SAMPLE = "samples/capabilities/pages/network_sse/index.ink"
WEBSOCKET_SAMPLE = "samples/capabilities/pages/network_websocket/index.ink"


def contract(
    family: str,
    layers: set[str],
    sources: set[tuple[str, str]],
    *,
    fragments: tuple[tuple[str, str], ...] = (),
    provisional: bool = False,
    provisional_cells: tuple[str, str, str, str] = (),
    pass_api_pattern: str = "",
    pass_declaration_pattern: str = "",
    pass_blocked_reason: str = "",
) -> CapabilityContract:
    return CapabilityContract(
        family=family,
        required_layers=frozenset(layers),
        required_source_roles=frozenset(sources),
        required_source_fragments=fragments,
        provisional=provisional,
        provisional_cells=provisional_cells,
        pass_api_pattern=pass_api_pattern,
        pass_declaration_pattern=pass_declaration_pattern,
        pass_blocked_reason=pass_blocked_reason,
    )


CAPABILITY_CONTRACTS = {
    "route": contract(
        "page.route",
        {"SOURCE", "STATIC", "LOGIC", "AIX", "STUDIO"},
        {("DOC", APP_JSON_DOC)},
        pass_api_pattern=(
            r"app\.json#pages:(?:[A-Za-z0-9_-]+/)*[A-Za-z0-9_-]+"
        ),
        pass_declaration_pattern=r"pages",
    ),
    "target": contract(
        "page.target",
        {"SOURCE", "STATIC", "LOGIC", "AIX", "STUDIO", "DEVICE"},
        {("DOC", TARGET_DOC)},
        pass_api_pattern=(
            r"(?:target:_(?:current|blank)|"
            r"onTargetChanged\(target,previousTarget\)|"
            r"@media\(target:_(?:current|blank)\))"
        ),
        pass_declaration_pattern=r"NONE REQUIRED",
    ),
    "host_focus": contract(
        "focus.host",
        {"SOURCE", "STATIC", "STUDIO", "DEVICE"},
        {("DOC", FOCUS_DOC)},
        pass_api_pattern=r"(?:onHostFocus\(\)|onHostBlur\(\))",
        pass_declaration_pattern=r"NONE REQUIRED",
    ),
    "element_focus": contract(
        "focus.element",
        {"SOURCE", "STATIC", "STUDIO", "DEVICE"},
        {("DOC", FOCUS_DOC)},
        pass_api_pattern=r"bind(?:focus|blur)=[A-Za-z_$][A-Za-z0-9_$]*",
        pass_declaration_pattern=r"NONE REQUIRED",
    ),
    "button": contract(
        "ui.button",
        {"SOURCE", "STATIC", "AIX", "STUDIO", "DEVICE"},
        {("DOC", BUTTON_DOC), ("SAMPLE", BUTTON_SAMPLE)},
        pass_api_pattern=r"<button(?:\s+[^<>]+)?>",
        pass_declaration_pattern=r"NONE REQUIRED",
    ),
    "bindtap": contract(
        "event.bindtap",
        {"SOURCE", "STATIC", "LOGIC", "AIX", "STUDIO", "DEVICE"},
        {("DOC", BUTTON_DOC), ("SAMPLE", BUTTON_SAMPLE)},
        pass_api_pattern=r"bindtap=[A-Za-z_$][A-Za-z0-9_$]*",
        pass_declaration_pattern=r"NONE REQUIRED",
    ),
    "enter": contract(
        "input.enter",
        {"SOURCE", "STATIC", "LOGIC", "STUDIO", "DEVICE"},
        {("DOC", PAGE_EVENTS_DOC)},
        pass_api_pattern=r"onKey(?:Down|Up)\(event\.code=Enter\)",
        pass_declaration_pattern=r"NONE REQUIRED",
    ),
    "back": contract(
        "input.back",
        {"SOURCE", "STATIC", "LOGIC", "STUDIO", "DEVICE"},
        {("DOC", PAGE_EVENTS_DOC)},
        pass_api_pattern=r"onKey(?:Down|Up)\(event\.code=Backspace\)",
        pass_declaration_pattern=r"NONE REQUIRED",
    ),
    "key": contract(
        "input.key.unknown",
        {"SOURCE", "STATIC", "LOGIC", "STUDIO", "DEVICE"},
        {("DOC", PAGE_EVENTS_DOC)},
        provisional=True,
        provisional_cells=(
            "Unresolved key input",
            "The intended key input performs exactly one owned action",
            "Unknown, ignored, or repeated key delivery preserves host defaults and a non-key fallback",
            "Hide/show and unload do not retain stale key handling",
        ),
    ),
    "scroll": contract(
        "input.scroll.unknown",
        {"SOURCE", "STATIC", "LOGIC", "STUDIO", "DEVICE"},
        {
            ("SEARCH-SCOPE", OPEN_AGENT_INDEX),
            ("SEARCH-SCOPE", COMPONENT_INDEX),
        },
        provisional=True,
        provisional_cells=(
            "Unresolved scroll input",
            "The declared product intent affects only its owned target",
            "Unsupported or ignored scrolling preserves host behavior",
            "Repeated open does not duplicate scroll handling",
        ),
    ),
    "voice": contract(
        "input.voice.unknown",
        {"SOURCE", "STATIC", "LOGIC", "STUDIO", "DEVICE"},
        {("SEARCH-SCOPE", OPEN_AGENT_INDEX), ("SEARCH-SCOPE", AI_INDEX)},
        provisional=True,
        provisional_cells=(
            "Unresolved voice input",
            "The declared product intent is delivered once",
            "No-match, unavailable, repeated, and ignored input use a non-voice fallback",
            "Hide/show and unload do not retain stale voice work",
        ),
    ),
    "voice_declaration": contract(
        "voice.declaration.unknown",
        {"SOURCE", "STATIC", "STUDIO", "DEVICE"},
        {("SEARCH-SCOPE", OPEN_AGENT_INDEX), ("SEARCH-SCOPE", AI_INDEX)},
        provisional=True,
        provisional_cells=(
            "Unresolved voice declaration",
            "The required declaration matches the inspected voice mechanism",
            "Missing, denied, or revoked access preserves a non-voice fallback",
            "Reopen reconciles the current declaration and access state",
        ),
    ),
    "scroll_host": contract(
        "input.scroll.host",
        {"SOURCE", "STATIC", "LOGIC", "STUDIO", "DEVICE"},
        {("DOC", PAGE_EVENTS_DOC)},
        pass_api_pattern=r"onKey(?:Down|Up)\(event\.code=Arrow(?:Up|Down)\)",
        pass_declaration_pattern=r"NONE REQUIRED",
    ),
    "scroll_view": contract(
        "component.scroll-view",
        {"SOURCE", "STATIC", "LOGIC", "AIX", "STUDIO", "DEVICE"},
        {("DOC", SCROLL_VIEW_DOC)},
        pass_api_pattern=r"<scroll-view(?:\s+[^<>]+)?>",
        pass_declaration_pattern=r"NONE REQUIRED",
    ),
    "voice_wakeup": contract(
        "input.voice-wakeup",
        {"SOURCE", "STATIC", "LOGIC", "STUDIO", "DEVICE"},
        {("DOC", PAGE_EVENTS_DOC), ("SAMPLE", VOICE_SAMPLE)},
        pass_api_pattern=r"onVoiceWakeup\(event\)(?:\+event\.keyword)?",
        pass_declaration_pattern=r"NONE REQUIRED",
    ),
    "speech_recognition": contract(
        "ai.speech-recognition",
        {"SOURCE", "STATIC", "LOGIC", "STUDIO", "DEVICE"},
        {("DOC", SPEECH_DOC), ("SAMPLE", SPEECH_SAMPLE)},
        pass_api_pattern=r"new SpeechRecognition\(\)->recognition\.start\(\)",
        pass_declaration_pattern=(
            r"COMPANION:voice\.declaration\.unknown@[a-z0-9_.-]+"
        ),
    ),
    "input_fallback": contract(
        "input.fallback.unknown",
        {"SOURCE", "STATIC", "LOGIC", "STUDIO", "DEVICE"},
        {("SEARCH-SCOPE", OPEN_AGENT_INDEX), ("SEARCH-SCOPE", COMPONENT_INDEX)},
        provisional=True,
        provisional_cells=(
            "Unresolved non-sensor fallback",
            "The core task remains usable without the primary sensor",
            "Fallback failure leaves a clear exit without duplicate action",
            "Fallback remains available after hide/show and reopen",
        ),
    ),
    "touch_migration": contract(
        "input.touch-migration.unknown",
        {"SOURCE", "STATIC", "LOGIC", "AIX", "STUDIO", "DEVICE"},
        {("SEARCH-SCOPE", COMPONENT_INDEX)},
        provisional=True,
        provisional_cells=(
            "Unresolved touch-to-primary-input migration",
            "The intended primary input performs exactly one owned action",
            "No stale touch binding, duplicate action, or dead end remains",
            "Repeated open does not restore obsolete bindings",
        ),
    ),
    "world_awareness": contract(
        "page.world-awareness",
        {"SOURCE", "STATIC", "LOGIC", "STUDIO", "DEVICE"},
        {("DOC", PAGE_API_DOC), ("SAMPLE", HEAD_SAMPLE)},
        pass_api_pattern=r"enableWorldAwareness\(\.\.\.\)",
        pass_declaration_pattern=r"NONE REQUIRED",
    ),
    "head_gesture": contract(
        "input.head-gesture",
        {"SOURCE", "STATIC", "LOGIC", "STUDIO", "DEVICE"},
        {("DOC", PAGE_API_DOC), ("SAMPLE", HEAD_SAMPLE)},
        pass_api_pattern=(
            r"enableWorldAwareness\(\.\.\.\)\+"
            r"onHeadGesture(?:StateChange)?\(event\)"
        ),
        pass_declaration_pattern=r"NONE REQUIRED",
    ),
    "gesture_fallback": contract(
        "input.gesture-fallback.unknown",
        {"SOURCE", "STATIC", "LOGIC", "STUDIO", "DEVICE"},
        {("SEARCH-SCOPE", OPEN_AGENT_INDEX), ("SEARCH-SCOPE", COMPONENT_INDEX)},
        provisional=True,
        provisional_cells=(
            "Unresolved gesture fallback",
            "The core task remains usable without the gesture sensor",
            "Fallback failure leaves a clear exit without duplicate action",
            "Fallback remains available after hide/show and reopen",
        ),
    ),
    "camera_permission": contract(
        "media.camera.permission",
        {"SOURCE", "STATIC", "STUDIO", "DEVICE"},
        {("DOC", MEDIA_DOC), ("DECLARATION-SNIPPET", PERMISSION_MANIFEST)},
        fragments=((PERMISSION_MANIFEST, "L57"),),
        pass_api_pattern=r"app\.json#permissions",
        pass_declaration_pattern=r"CAMERA",
    ),
    "camera_runtime": contract(
        "media.camera.runtime",
        {"SOURCE", "STATIC", "LOGIC", "STUDIO", "DEVICE"},
        {
            ("DOC", MEDIA_DOC),
            ("SAMPLE", MEDIA_SAMPLE),
            ("DECLARATION-SNIPPET", PERMISSION_MANIFEST),
        },
        fragments=((PERMISSION_MANIFEST, "L57"),),
        pass_api_pattern=(
            r"navigator\.mediaDevices\.getUserMedia"
            r"\(video=(?:true|constraints\.video=(?:true|object))\)"
        ),
        pass_declaration_pattern=r"CAMERA",
    ),
    "media_lifecycle": contract(
        "media.camera.lifecycle",
        {"SOURCE", "STATIC", "LOGIC", "STUDIO", "DEVICE"},
        {
            ("DOC", MEDIA_DOC),
            ("SAMPLE", MEDIA_SAMPLE),
            ("DECLARATION-SNIPPET", PERMISSION_MANIFEST),
        },
        fragments=((PERMISSION_MANIFEST, "L57"),),
        pass_api_pattern=(
            r"MediaStream\.getTracks\(\)->MediaStreamTrack\.stop\(\)"
        ),
        pass_declaration_pattern=r"CAMERA",
    ),
    "network": contract(
        "network.unknown",
        {"SOURCE", "STATIC", "LOGIC", "AIX", "STUDIO", "DEVICE"},
        {("SEARCH-SCOPE", NETWORK_INDEX)},
        provisional=True,
        provisional_cells=(
            "Unresolved network transport",
            "The declared product outcome is delivered without stale updates",
            "Offline, timeout, malformed, and partial results recover with bounded retry",
            "Hide/show and unload cancel or reconcile retained network work",
        ),
    ),
    "network_https": contract(
        "network.https",
        {"SOURCE", "STATIC", "LOGIC", "AIX", "STUDIO", "DEVICE"},
        {("DOC", HTTPS_DOC), ("SAMPLE", HTTPS_SAMPLE)},
        pass_api_pattern=r"(?:fetch|wx\.request)\(\.\.\.\)",
        pass_declaration_pattern=r"NONE REQUIRED",
    ),
    "network_sse": contract(
        "network.sse",
        {"SOURCE", "STATIC", "LOGIC", "AIX", "STUDIO", "DEVICE"},
        {("DOC", SSE_DOC), ("SAMPLE", SSE_SAMPLE)},
        pass_api_pattern=r"wx\.createEventSource\(\.\.\.\)",
        pass_declaration_pattern=r"NONE REQUIRED",
    ),
    "network_websocket": contract(
        "network.websocket",
        {"SOURCE", "STATIC", "LOGIC", "AIX", "STUDIO", "DEVICE"},
        {("DOC", WEBSOCKET_DOC), ("SAMPLE", WEBSOCKET_SAMPLE)},
        pass_api_pattern=r"wx\.connectSocket\(\.\.\.\)",
        pass_declaration_pattern=r"NONE REQUIRED",
    ),
    "page_lifecycle": contract(
        "page.lifecycle",
        {"SOURCE", "STATIC", "LOGIC", "AIX", "STUDIO", "DEVICE"},
        {("DOC", PAGE_API_DOC)},
        pass_api_pattern=r"CALLBACK:on(?:Load|Show|Ready|Hide|Unload)",
        pass_declaration_pattern=r"NONE REQUIRED",
    ),
    "unregistered": contract(
        "project.unregistered",
        set(EVIDENCE_LAYERS),
        {("SEARCH-SCOPE", "documentation"), ("SEARCH-SCOPE", "samples")},
        provisional=True,
        provisional_cells=(
            "Unregistered project capability",
            "The declared capability performs its claimed outcome once",
            "Unavailable, rejected, or ignored delivery preserves an explicit fallback",
            "Hide/show and unload do not retain stale capability work",
        ),
    ),
}

AUDIT_CAPABILITY_CONTRACTS = (
    "route",
    "target",
    "host_focus",
    "element_focus",
    "button",
    "bindtap",
    "enter",
    "back",
    "scroll",
    "voice",
    "world_awareness",
    "head_gesture",
    "gesture_fallback",
    "camera_permission",
    "camera_runtime",
    "media_lifecycle",
    "page_lifecycle",
)
IMPLEMENTATION_CAPABILITY_CONTRACTS = (
    "route",
    "target",
    "host_focus",
    "element_focus",
    "voice",
    "input_fallback",
    "touch_migration",
    "network",
    "page_lifecycle",
)
CAPABILITY_BASE_IDS = {
    "route": "CAP-PAGE-ROUTE",
    "target": "CAP-PAGE-TARGET",
    "host_focus": "CAP-HOST-FOCUS",
    "element_focus": "CAP-ELEMENT-FOCUS",
    "button": "CAP-BUTTON",
    "bindtap": "CAP-BINDTAP",
    "enter": "CAP-INPUT-ENTER",
    "back": "CAP-INPUT-BACK",
    "key": "CAP-INPUT-KEY",
    "scroll": "CAP-INPUT-SCROLL",
    "voice": "CAP-VOICE",
    "voice_declaration": "CAP-VOICE-DECLARATION",
    "scroll_host": "CAP-INPUT-SCROLL-HOST",
    "scroll_view": "CAP-SCROLL-VIEW",
    "voice_wakeup": "CAP-VOICE-WAKEUP",
    "speech_recognition": "CAP-SPEECH-RECOGNITION",
    "input_fallback": "CAP-INPUT-FALLBACK",
    "touch_migration": "CAP-INPUT-TOUCH-MIGRATION",
    "world_awareness": "CAP-WORLD-AWARENESS",
    "head_gesture": "CAP-HEAD-GESTURE",
    "gesture_fallback": "CAP-GESTURE-FALLBACK",
    "camera_permission": "CAP-CAMERA-PERMISSION",
    "camera_runtime": "CAP-CAMERA-RUNTIME",
    "media_lifecycle": "CAP-CAMERA-LIFECYCLE",
    "network": "CAP-NETWORK",
    "network_https": "CAP-NETWORK-HTTPS",
    "network_sse": "CAP-NETWORK-SSE",
    "network_websocket": "CAP-NETWORK-WEBSOCKET",
    "page_lifecycle": "CAP-PAGE-LIFECYCLE",
    "unregistered": "CAP-UNREGISTERED",
}
PROVISIONAL_FORBIDDEN_TERMS = {
    "voice": r"(?i)onVoiceWakeup|SpeechRecognition|RECORD_AUDIO|pages/(?:chat|speech)/",
    "voice_declaration": (
        r"(?i)onVoiceWakeup|SpeechRecognition|CAMERA|RECORD_AUDIO|"
        r"samples/capabilities/app\.json"
    ),
    "network": r"(?i)\bfetch\b|EventSource|WebSocket|\bHTTPS?\b|\bSSE\b",
    "touch_migration": r"(?i)\bbindtap\b|\bonTap\b",
}


def table_after_heading(markdown: str, heading: str) -> tuple[list[str], list[list[str]]]:
    match = re.search(
        rf"(?ms)^## {re.escape(heading)}\s*$\n(?P<section>.*?)(?=^## |\Z)",
        markdown,
    )
    if match is None:
        return [], []

    table_lines: list[str] = []
    for line in match.group("section").splitlines():
        stripped = line.strip()
        if stripped.startswith("|") and stripped.endswith("|"):
            table_lines.append(stripped)
        elif table_lines:
            break
    if len(table_lines) < 2:
        return [], []

    def cells(line: str) -> list[str]:
        return [cell.strip() for cell in line.strip("|").split("|")]

    return cells(table_lines[0]), [cells(line) for line in table_lines[2:]]


def section_after_heading(markdown: str, heading: str) -> str:
    match = re.search(
        rf"(?ms)^## {re.escape(heading)}\s*$\n(?P<section>.*?)(?=^## |\Z)",
        markdown,
    )
    return match.group("section") if match is not None else ""


def replace_capability_cells(
    markdown: str,
    capability_id: str,
    replacements: dict[int, str],
) -> str:
    lines = markdown.splitlines()
    replaced = False
    for index, line in enumerate(lines):
        if not line.startswith("|"):
            continue
        cells = [cell.strip() for cell in line.strip("|").split("|")]
        if not cells or capability_id not in cells[0]:
            continue
        for cell_index, value in replacements.items():
            cells[cell_index] = value
        lines[index] = "| " + " | ".join(cells) + " |"
        replaced = True
        break
    if not replaced:
        raise AssertionError(f"capability row not found: {capability_id}")
    return "\n".join(lines) + ("\n" if markdown.endswith("\n") else "")


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
        cls.runtime_reference = RUNTIME_REFERENCE_PATH.read_text(encoding="utf-8")
        cls.forward_evaluation = FORWARD_EVALUATION_PATH.read_text(encoding="utf-8")
        cls.implementation_forward_evaluation = (
            IMPLEMENTATION_FORWARD_EVALUATION_PATH.read_text(encoding="utf-8")
            if IMPLEMENTATION_FORWARD_EVALUATION_PATH.is_file()
            else ""
        )
        cls.audit_prompt = section_after_heading(
            AUDIT_SCENARIO_PATH.read_text(encoding="utf-8"), "Prompt"
        ).strip()
        cls.implementation_prompt = section_after_heading(
            IMPLEMENTATION_SCENARIO_PATH.read_text(encoding="utf-8"), "Prompt"
        ).strip()

    def assert_complete_evaluation_matrices(
        self,
        markdown: str,
        capability_contract_names: tuple[str, ...],
        forbidden_results: frozenset[str] = frozenset(),
        request_prompt: str = "",
    ) -> None:
        artifact_registry: dict[str, tuple[str, ...]] = {}
        revision_matches = re.findall(
            r"(?m)^Project revision: "
            r"(UNAVAILABLE|[0-9a-f]{40}|WORKTREE:[0-9a-f]{64})\s*$",
            markdown,
        )
        self.assertEqual(
            1,
            len(revision_matches),
            "audit must declare exactly one canonical Project revision",
        )
        project_revision = revision_matches[0]
        metadata_lines = [
            line.strip()
            for line in markdown.split("## Project UX evidence matrix", 1)[0].splitlines()
            if line.strip()
        ]
        metadata_fields: dict[str, str] = {}
        for line in metadata_lines:
            metadata_field = re.fullmatch(
                r"(Project revision|Canonical version|Import root|Device/host|"
                r"Supported surfaces|Inputs|Claimed capabilities):\s+(.+?)\s*",
                line,
            )
            self.assertIsNotNone(metadata_field, f"invalid audit metadata line: {line}")
            self.assertNotIn(metadata_field.group(1), metadata_fields)
            metadata_fields[metadata_field.group(1)] = metadata_field.group(2)
        self.assertEqual(
            [
                "Project revision",
                "Canonical version",
                "Import root",
                "Device/host",
                "Supported surfaces",
                "Inputs",
                "Claimed capabilities",
            ],
            list(metadata_fields),
        )
        self.assert_project_revision(
            project_revision,
            metadata_fields["Import root"],
        )
        canonical_version = metadata_fields["Canonical version"]
        self.assertIn(canonical_version, {"AIUI 0.17.0", "AIUI 0.18.0"})
        device_environment = self.parse_device_host_metadata(
            metadata_fields["Device/host"]
        )
        device_aiui_versions = re.findall(
            r"\bAIUI\s+(\d+\.\d+\.\d+)\b",
            metadata_fields["Device/host"],
        )
        self.assertTrue(
            not device_aiui_versions
            or set(device_aiui_versions)
            == {canonical_version.removeprefix("AIUI ")},
            "Device/host contains a conflicting AIUI runtime version",
        )
        claimed_capability_entries = metadata_fields["Claimed capabilities"].split(",")
        self.assertTrue(all(claimed_capability_entries))
        self.assertEqual(
            sorted(claimed_capability_entries),
            claimed_capability_entries,
            "Claimed capabilities must be sorted by ASCII code-point order",
        )
        self.assertEqual(
            len(claimed_capability_entries),
            len(set(claimed_capability_entries)),
            "Claimed capabilities must not contain duplicates",
        )
        claimed_capability_gates: set[tuple[str, str]] = set()
        for claimed_entry in claimed_capability_entries:
            claimed_capability = re.fullmatch(
                r"(?P<family>[a-z0-9_.-]+)@(?P<gate>[a-z0-9_.-]+)",
                claimed_entry,
            )
            self.assertIsNotNone(
                claimed_capability,
                f"invalid Claimed capabilities entry: {claimed_entry}",
            )
            claimed_capability_gates.add(
                (claimed_capability.group("family"), claimed_capability.group("gate"))
            )
        inventory_report: dict[str, object] | None = None
        scanner_items_by_gate: dict[tuple[str, str], dict[str, object]] = {}
        if project_revision != "UNAVAILABLE":
            inventory = subprocess.run(
                [
                    sys.executable,
                    str(INVENTORY_SCRIPT),
                    str(self.resolve_import_root(metadata_fields["Import root"])),
                    "--target-version",
                    canonical_version.removeprefix("AIUI "),
                    "--repository-root",
                    str(ROOT),
                ],
                cwd=ROOT,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(0, inventory.returncode, inventory.stderr)
            inventory_report = json.loads(inventory.stdout)
            self.assertEqual(
                canonical_version.removeprefix("AIUI "),
                inventory_report.get("targetVersion"),
            )
            if project_revision.startswith("WORKTREE:"):
                self.assertEqual(
                    project_revision, inventory_report.get("projectRevision")
                )
            else:
                self.assertRegex(
                    str(inventory_report.get("projectRevision")),
                    r"^WORKTREE:[0-9a-f]{64}$",
                )
            scanner_gates = {
                tuple(entry.split("@", 1))
                for entry in inventory_report.get("claimedCapabilities", [])
            }
            scanner_items_by_gate = {
                (str(item["family"]), str(item["gate"])): item
                for item in inventory_report.get("items", [])
                if isinstance(item, dict)
            }
            self.assertEqual(scanner_gates, set(scanner_items_by_gate))
            self.assert_scanner_claims_closed(
                scanner_gates, claimed_capability_gates
            )
            self.assertEqual(
                [],
                inventory_report.get("versionViolations"),
                "target-version violations must be resolved before an audit can pass",
            )
        for heading in ("Project UX evidence matrix", "Per-capability matrix"):
            section_lines = [
                line.strip()
                for line in section_after_heading(markdown, heading).splitlines()
                if line.strip()
            ]
            self.assertTrue(section_lines, f"empty matrix section: {heading}")
            self.assertTrue(
                all(line.startswith("|") and line.endswith("|") for line in section_lines),
                f"only the required table is allowed under {heading}",
            )
        ux_header, ux_rows = table_after_heading(
            markdown, "Project UX evidence matrix"
        )
        capability_header, capability_rows = table_after_heading(
            markdown, "Per-capability matrix"
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
        self.assertGreaterEqual(len(ux_rows), 10)
        self.assertGreaterEqual(len(capability_rows), 1)

        ux_identifiers = []
        ux_gates = []
        for row in ux_rows:
            parsed_ux_id = UX_ID_RE.fullmatch(row[0])
            self.assertIsNotNone(parsed_ux_id, f"invalid UX ID/gate: {row[0]}")
            ux_identifiers.append(parsed_ux_id.group("identifier"))
            ux_gates.append(parsed_ux_id.group("gate"))
        self.assertEqual(
            len(ux_identifiers),
            len(set(ux_identifiers)),
            "UX row IDs must be unique",
        )
        observed_families: set[str] = set()
        observed_family_gate_layers = {family: {} for family in UX_FAMILIES}
        ux_gate_signatures: dict[tuple[str, str], tuple[str, ...]] = {}
        ux_gate_outcomes: dict[tuple[str, str], list[tuple[str, str]]] = {}
        ux_input_gates: set[str] = set()
        for row, identifier, gate in zip(ux_rows, ux_identifiers, ux_gates):
            self.assertEqual(7, len(row))
            self.assertTrue(all(row))
            families = {
                family
                for family in UX_FAMILIES
                if identifier == family or identifier.startswith(f"{family}-")
            }
            self.assertEqual(1, len(families), f"unknown UX row family: {identifier}")
            family = next(iter(families))
            observed_families.add(family)
            if family == "UX-INPUT":
                ux_input_gates.add(gate)
            ux_gate_key = (family, gate)
            ux_signature = tuple(" ".join(cell.split()) for cell in row[1:4])
            prior_ux_signature = ux_gate_signatures.setdefault(
                ux_gate_key, ux_signature
            )
            self.assertEqual(
                prior_ux_signature,
                ux_signature,
                f"split UX rows changed the contract inside {family}/{gate}",
            )
            ux_gate_outcomes.setdefault(ux_gate_key, []).append(
                (identifier, row[5])
            )
            layers = self.assert_exact_evidence_layers(row[4])
            gate_layers = observed_family_gate_layers[family].setdefault(gate, set())
            self.assertFalse(
                gate_layers.intersection(layers),
                f"duplicate UX evidence layer inside gate {family}/{gate}",
            )
            gate_layers.update(layers)
            self.assertNotIn(row[5], forbidden_results)
            if row[5] in {"PASS", "FAIL"} and "DEVICE" in layers:
                self.assertIsNotNone(
                    device_environment,
                    f"executed DEVICE result needs concrete audit metadata: {identifier}",
                )
            self.assert_result_evidence(
                row[5],
                row[6],
                layers,
                row_id=identifier,
                gate=gate,
                criterion=row[3],
                project_revision=project_revision,
                project_import_root=metadata_fields["Import root"],
                request_prompt=request_prompt,
                artifact_registry=artifact_registry,
                device_environment=device_environment,
            )
        self.assertEqual(set(UX_FAMILIES), observed_families)
        self.assert_input_ledger(metadata_fields["Inputs"], ux_input_gates)
        self.assert_split_outcome_ids(ux_gate_outcomes)
        for family, required_layers in UX_REQUIRED_LAYERS.items():
            for gate, observed_layers in observed_family_gate_layers[family].items():
                self.assertEqual(
                    required_layers,
                    frozenset(observed_layers),
                    f"incomplete or extra evidence layers for {family}/{gate}",
                )

        capability_ids: list[str] = []
        allowed_contract_names = tuple(
            dict.fromkeys(capability_contract_names + ("unregistered",))
        )
        observed_contract_gate_layers = {
            name: {} for name in allowed_contract_names
        }
        observed_contracts: set[str] = set()
        observed_capability_gates: set[tuple[str, str]] = set()
        required_companion_gates: set[tuple[str, str]] = set()
        capability_gate_signatures: dict[tuple[str, str], tuple[str, ...]] = {}
        capability_gate_outcomes: dict[
            tuple[str, str], list[tuple[str, str]]
        ] = {}
        capability_gate_surfaces: dict[tuple[str, str], set[str]] = {}
        capability_gate_bindings: dict[tuple[str, str], tuple[str, str]] = {}
        companion_parent_gates: dict[
            tuple[str, str], set[tuple[str, str]]
        ] = {}
        companion_parent_surfaces: dict[tuple[str, str], set[str]] = {}
        for row in capability_rows:
            self.assertEqual(11, len(row))
            self.assertTrue(all(row))
            capability_id = CAPABILITY_ID_RE.match(row[0])
            self.assertIsNotNone(
                capability_id, f"missing stable CAP identifier: {row[0]}"
            )
            identifier = capability_id.group("identifier")
            family = capability_id.group("family")
            gate = capability_id.group("gate")
            observed_capability_gates.add((family, gate))
            normalized_surface = " ".join(row[1].split())
            capability_gate_surfaces.setdefault((family, gate), set()).add(
                normalized_surface
            )
            capability_ids.append(identifier)
            matched_contract_names = [
                name
                for name in allowed_contract_names
                if CAPABILITY_CONTRACTS[name].family == family
            ]
            self.assertEqual(
                1,
                len(matched_contract_names),
                f"capability ID must match exactly one required family: "
                f"{identifier} / {family} -> {matched_contract_names}",
            )
            contract_name = matched_contract_names[0]
            capability_contract = CAPABILITY_CONTRACTS[contract_name]
            base_id = CAPABILITY_BASE_IDS[contract_name]
            self.assertRegex(
                identifier,
                rf"^{re.escape(base_id)}(?:-[A-Z0-9]+)*$",
                f"non-canonical capability ID for {family}: {identifier}",
            )
            matching_base_contracts = [
                (name, candidate_base_id)
                for name, candidate_base_id in CAPABILITY_BASE_IDS.items()
                if identifier == candidate_base_id
                or identifier.startswith(f"{candidate_base_id}-")
            ]
            longest_base_length = max(
                len(candidate_base_id)
                for _, candidate_base_id in matching_base_contracts
            )
            longest_base_contracts = [
                name
                for name, candidate_base_id in matching_base_contracts
                if len(candidate_base_id) == longest_base_length
            ]
            self.assertEqual(
                [contract_name],
                longest_base_contracts,
                f"capability ID resolves to the wrong canonical base: {identifier}",
            )
            observed_contracts.add(contract_name)
            layers = self.assert_exact_evidence_layers(row[8])
            gate_layers = observed_contract_gate_layers[contract_name].setdefault(
                gate, set()
            )
            self.assertFalse(
                gate_layers.intersection(layers),
                f"duplicate capability evidence layer inside gate {family}/{gate}",
            )
            gate_layers.update(layers)
            self.assertNotIn(row[9], forbidden_results)
            self.assertNotEqual("N/A", row[9], "inventoried capabilities are applicable")
            source_entries = []
            for entry in (part.strip() for part in row[4].split(";")):
                source_entry = SOURCE_ENTRY_RE.fullmatch(entry)
                self.assertIsNotNone(
                    source_entry,
                    f"source must be ROLE=[label](commit-pinned-url): {entry}",
                )
                source_entries.append(source_entry)
            self.assertTrue(source_entries, f"no source URL for {row[0]}")
            normalized_version_cell = unicodedata.normalize("NFKC", row[1])
            self.assertNotRegex(
                row[1],
                r"[０-９．；]",
                f"capability version must use ASCII digits and punctuation: {row[0]}",
            )
            self.assertRegex(
                normalized_version_cell,
                rf"^{re.escape(canonical_version)};",
                f"capability version must start with the audit canonical version: {row[0]}",
            )
            version_context = normalized_version_cell.replace(
                metadata_fields["Device/host"],
                "",
            )
            zero_major_versions = re.findall(
                r"(?<!\d)0\.\d+(?:\.\d+)?(?!\d)",
                version_context,
            )
            aiui_versions = re.findall(
                r"\bAIUI\s+(\d+\.\d+\.\d+)\b",
                normalized_version_cell,
            )
            self.assertTrue(zero_major_versions)
            self.assertEqual(
                {canonical_version.removeprefix("AIUI ")},
                set(zero_major_versions),
                f"capability row contains a conflicting AIUI version: {row[0]}",
            )
            self.assertEqual(
                {canonical_version.removeprefix("AIUI ")},
                set(aiui_versions),
                f"capability row contains a conflicting AIUI major version: {row[0]}",
            )
            version = canonical_version.removeprefix("AIUI ")
            if version == "0.17.0":
                expected_revision = STABLE_AIUI_REVISION
            elif version == "0.18.0":
                expected_revision = PREVIEW_AIUI_REVISION
                self.assertEqual(
                    "BLOCKED",
                    row[9],
                    "0.18 capability PASS/FAIL policy is not registered; "
                    "keep the gate blocked until a version-specific contract exists",
                )
            else:
                self.fail(f"capability row has unsupported/noncanonical version: {row[0]}")
            source_roles: set[tuple[str, str]] = set()
            source_fragments: set[tuple[str, str]] = set()
            allowed_source_urls: set[str] = set()
            for source_entry in source_entries:
                source_url = source_entry.group("url")
                allowed_source_urls.add(source_url)
                self.assertNotRegex(
                    source_entry.group("label"),
                    r"(?i)https?://|github\.com|/(?:blob|tree)/",
                    f"URL-like text hidden in source label for {identifier}",
                )
                source = PINNED_AIUI_SOURCE_RE.fullmatch(source_url)
                self.assertIsNotNone(
                    source, f"unapproved source URL for {row[0]}: {source_url}"
                )
                self.assertEqual(expected_revision, source.group("revision"))
                if source_entry.group("role") == "SEARCH-SCOPE":
                    self.assertEqual("tree", source.group("url_kind"))
                else:
                    self.assertEqual("blob", source.group("url_kind"))
                source_path = source.group("path").rstrip("/")
                source_roles.add((source_entry.group("role"), source_path))
                if source.group("fragment"):
                    source_fragments.add((source_path, source.group("fragment")))
                if source_path not in ALLOWED_STABLE_SOURCE_PATHS:
                    self.assertEqual("BLOCKED", row[9])
                    self.assertIn(source_path, ALLOWED_PROVISIONAL_SOURCE_PATHS)
                    unresolved_context = " ".join((row[2], row[3], row[4], row[10]))
                    self.assertRegex(
                        unresolved_context,
                        r"(?i)unknown|unresolved|not (?:provided|inspected)|"
                        r"待|未|未知|缺口|缺失|无法",
                    )
            self.assertEqual(
                len(source_entries),
                len(source_roles),
                f"duplicate source role/path entries for {identifier}",
            )
            self.assertEqual(
                len(capability_contract.required_source_roles),
                len(source_entries),
                f"extra or missing source entries for {identifier}",
            )
            self.assertEqual(
                capability_contract.required_source_roles,
                frozenset(source_roles),
                f"wrong or incomplete official sources for {identifier}",
            )
            self.assertEqual(
                frozenset(capability_contract.required_source_fragments),
                frozenset(source_fragments),
                f"wrong, extra, or missing source fragment for {identifier}",
            )
            capability_gate_key = (family, gate)
            capability_gate_bindings[capability_gate_key] = (
                self.normalize_machine_cell(row[2]),
                self.normalize_machine_cell(row[3]),
            )
            capability_signature = tuple(
                " ".join(cell.split()) for cell in row[1:8]
            )
            prior_capability_signature = capability_gate_signatures.setdefault(
                capability_gate_key, capability_signature
            )
            self.assertEqual(
                prior_capability_signature,
                capability_signature,
                f"split capability rows changed the mechanism or contract inside "
                f"{family}/{gate}",
            )
            capability_gate_outcomes.setdefault(capability_gate_key, []).append(
                (identifier, row[9])
            )
            if contract_name == "speech_recognition":
                companion = re.fullmatch(
                    r"COMPANION:(?P<family>voice\.declaration\.unknown)@"
                    r"(?P<gate>[a-z0-9_.-]+)",
                    self.normalize_machine_cell(row[3]),
                )
                self.assertIsNotNone(
                    companion,
                    f"speech runtime requires an explicit declaration companion: {identifier}",
                )
                companion_key = (
                    companion.group("family"),
                    companion.group("gate"),
                )
                required_companion_gates.add(companion_key)
                companion_parent_gates.setdefault(companion_key, set()).add(
                    (family, gate)
                )
                companion_parent_surfaces.setdefault(companion_key, set()).add(
                    normalized_surface
                )
            if contract_name == "unregistered":
                self.assertEqual("BLOCKED", row[9])
                identifier_key = re.fullmatch(
                    r"CAP-UNREGISTERED-(?P<key>[0-9A-F]{12})", identifier
                )
                gate_key = re.fullmatch(
                    r"unregistered-(?P<key>[0-9a-f]{12})", gate
                )
                self.assertIsNotNone(identifier_key)
                self.assertIsNotNone(gate_key)
                self.assertEqual(
                    identifier_key.group("key").lower(), gate_key.group("key")
                )
                self.assertRegex(
                    row[2],
                    r"^(?:PROJECT-SYMBOL:.+|PROJECT-BINDING:UNRESOLVED)$",
                )
                self.assertEqual(
                    "UNKNOWN — source policy not registered", row[3]
                )
                self.assertEqual(
                    capability_contract.provisional_cells,
                    (capability_id.group("label"), row[5], row[6], row[7]),
                )
            elif capability_contract.provisional:
                self.assertEqual(
                    "BLOCKED",
                    row[9],
                    f"provisional source family cannot pass: {identifier}",
                )
                if project_revision == "UNAVAILABLE":
                    self.assertTrue(
                        identifier.endswith("-PROVISIONAL"),
                        f"source-unavailable family needs -PROVISIONAL: {identifier}",
                    )
                    self.assertEqual(PROJECT_BINDING_UNRESOLVED, row[2])
                    self.assertEqual(PROJECT_BINDING_UNRESOLVED, row[3])
                else:
                    self.assertEqual("UNKNOWN — source not inspected", row[2])
                    self.assertEqual("UNKNOWN — source not inspected", row[3])
                provisional_label, *provisional_descriptions = (
                    capability_contract.provisional_cells
                )
                provisional_token = "cap-" + family.replace(".", "-") + "-v1"
                expected_provisional_cells = (
                    provisional_label,
                    *(
                        f"{{contract={provisional_token}}} {{path={path}}} "
                        f"{description}"
                        for path, description in zip(
                            ("positive", "negative-fallback", "lifecycle-cleanup"),
                            provisional_descriptions,
                        )
                    ),
                )
                self.assertEqual(
                    expected_provisional_cells,
                    (capability_id.group("label"), row[5], row[6], row[7]),
                    f"provisional row must use non-speculative contract cells: {identifier}",
                )
            elif capability_contract.pass_blocked_reason:
                self.assertEqual(
                    "BLOCKED",
                    row[9],
                    f"unresolved declaration forbids PASS/FAIL: {identifier}",
                )
                self.assertEqual(
                    "UNKNOWN — declaration source not established",
                    row[3],
                )
                self.assertIsNotNone(
                    re.fullmatch(
                        capability_contract.pass_api_pattern,
                        self.normalize_machine_cell(row[2]),
                    ),
                    f"exact API family needs its canonical mechanism: {identifier}",
                )
            else:
                binding_unresolved = (
                    row[2] == PROJECT_BINDING_UNRESOLVED
                    or row[3] == PROJECT_BINDING_UNRESOLVED
                )
                if binding_unresolved:
                    self.assertEqual(PROJECT_BINDING_UNRESOLVED, row[2])
                    self.assertEqual(PROJECT_BINDING_UNRESOLVED, row[3])
                    self.assertEqual("BLOCKED", row[9])
                    self.assertTrue(
                        identifier.endswith("-PROVISIONAL"),
                        f"uninspected project binding needs -PROVISIONAL: {identifier}",
                    )
                else:
                    self.assertFalse(
                        identifier.endswith("-PROVISIONAL"),
                        f"inspected project binding must drop -PROVISIONAL: {identifier}",
                    )
                    self.assertNotRegex(
                        " ".join((row[2], row[3])),
                        r"(?i)\b(?:unknown|unavailable|unresolved)\b|"
                        r"source not inspected|未知|不可用|未(?:检查|核对|解析)|待(?:检查|核对|解析)",
                    )
                    self.assert_exact_pass_cells(contract_name, row[2], row[3])
                if project_revision == "UNAVAILABLE":
                    self.assertTrue(
                        binding_unresolved,
                        f"UNAVAILABLE source cannot establish project binding: {identifier}",
                    )
            if row[9] in {"PASS", "FAIL"} and "DEVICE" in layers:
                self.assertIsNotNone(
                    device_environment,
                    f"executed DEVICE result needs concrete audit metadata: {identifier}",
                )
                self.assertIn(
                    metadata_fields["Device/host"],
                    row[1],
                    f"DEVICE row must repeat the exact audit environment: {identifier}",
                )
            if contract_name in PROVISIONAL_FORBIDDEN_TERMS:
                source_claim_text = re.sub(
                    r"\]\(https?://[^)]+\)", "]", row[4], flags=re.IGNORECASE
                )
                self.assertNotRegex(
                    " ".join(row[:4] + [source_claim_text] + row[5:8] + [row[10]]),
                    PROVISIONAL_FORBIDDEN_TERMS[contract_name],
                    f"unresolved family was specialized without source: {identifier}",
                )
            for cell_index, cell in enumerate(row):
                if cell_index != 4:
                    self.assertNotRegex(
                        cell,
                        r"(?i)https?://|github\.com/(?:[^\s|]+)",
                        f"URL-like text outside source cell for {identifier}",
                    )
            self.assert_result_evidence(
                row[9],
                row[10],
                layers,
                row_id=identifier,
                gate=gate,
                criterion=(
                    f"Positive={row[5]}; Negative={row[6]}; Lifecycle={row[7]}"
                ),
                project_revision=project_revision,
                project_import_root=metadata_fields["Import root"],
                request_prompt=request_prompt,
                allowed_source_urls=frozenset(allowed_source_urls),
                artifact_registry=artifact_registry,
                device_environment=device_environment,
                capability_binding={
                    "target": normalized_surface,
                    "apiBinding": self.normalize_machine_cell(row[2]),
                    "declarationBinding": self.normalize_machine_cell(row[3]),
                    "sourceUrls": sorted(allowed_source_urls),
                },
            )

        self.assertEqual(
            len(capability_ids),
            len(set(capability_ids)),
            "capability row IDs must be unique",
        )
        self.assertTrue(set(capability_contract_names).issubset(observed_contracts))
        self.assertTrue(
            observed_contracts.issubset(set(capability_contract_names) | {"unregistered"})
        )
        self.assert_split_outcome_ids(capability_gate_outcomes)
        self.assertEqual(
            claimed_capability_gates,
            observed_capability_gates,
            "Claimed capabilities metadata and capability matrix gates must be identical",
        )
        for scanner_gate, scanner_item in scanner_items_by_gate.items():
            self.assertIn(
                scanner_gate,
                capability_gate_bindings,
                f"scanner inventory item has no matrix binding: {scanner_gate}",
            )
            self.assertEqual(
                (
                    scanner_item.get("apiBinding"),
                    scanner_item.get("declarationBinding"),
                ),
                capability_gate_bindings[scanner_gate],
                f"matrix changed the scanner mechanism/declaration: {scanner_gate}",
            )
        if inventory_report is not None:
            unmatched_gates = {
                (str(item.get("family")), str(item.get("gate")))
                for item in inventory_report.get("unmatchedSymbols", [])
                if isinstance(item, dict)
            }
            self.assertTrue(unmatched_gates.issubset(observed_capability_gates))
        self.assertTrue(
            required_companion_gates.issubset(observed_capability_gates),
            "every PASS companion declaration must have its own capability gate",
        )
        for companion_key in required_companion_gates:
            self.assertEqual(
                1,
                len(companion_parent_gates[companion_key]),
                f"one declaration companion cannot serve multiple speech gates: "
                f"{companion_key}",
            )
            self.assertEqual(
                companion_parent_surfaces[companion_key],
                capability_gate_surfaces.get(companion_key, set()),
                f"speech runtime and declaration companion must use the same "
                f"version/device/surface: {companion_key}",
            )
        for name in observed_contracts:
            for gate, observed_layers in observed_contract_gate_layers[name].items():
                self.assertEqual(
                    CAPABILITY_CONTRACTS[name].required_layers,
                    frozenset(observed_layers),
                    f"incomplete or extra evidence layers for capability family "
                    f"{name}/{gate}",
                )

        headings = re.findall(r"(?m)^## (.+?)\s*$", markdown)
        self.assertEqual(
            [
                "Project UX evidence matrix",
                "Per-capability matrix",
                "Final release decision",
            ],
            headings,
        )
        final_decision = section_after_heading(
            markdown, "Final release decision"
        ).strip()
        self.assertTrue(final_decision)
        decision_fields: dict[str, str] = {}
        for field_name in (
            "Final status",
            "Release-ready",
            "Reason",
            "Required gates",
        ):
            self.assertEqual(
                1,
                len(re.findall(rf"(?m)^{re.escape(field_name)}:", markdown)),
                f"{field_name} must appear exactly once in the entire audit",
            )
        decision_lines = [line.strip() for line in final_decision.splitlines() if line.strip()]
        for line in decision_lines:
            field = re.fullmatch(
                r"(Final status|Release-ready|Reason|Required gates):\s+(.+)",
                line,
            )
            self.assertIsNotNone(field, f"invalid final decision line: {line}")
            self.assertNotIn(field.group(1), decision_fields)
            decision_fields[field.group(1)] = field.group(2)
        self.assertEqual(
            ["Final status", "Release-ready", "Reason", "Required gates"],
            list(decision_fields),
        )
        self.assertIn(decision_fields["Final status"], {"PASS", "FAIL", "BLOCKED"})
        self.assertIn(decision_fields["Release-ready"], {"YES", "NO"})
        matrix_results = [row[5] for row in ux_rows] + [
            row[9] for row in capability_rows
        ]
        result_rows = [
            (
                UX_ID_RE.fullmatch(row[0]).group("identifier"),
                row[5],
                self.assert_exact_evidence_layers(row[4]),
            )
            for row in ux_rows
        ] + [
            (
                CAPABILITY_ID_RE.match(row[0]).group("identifier"),
                row[9],
                self.assert_exact_evidence_layers(row[8]),
            )
            for row in capability_rows
        ]
        fail_ids = [identifier for identifier, result, _ in result_rows if result == "FAIL"]
        blocked_ids = [
            identifier for identifier, result, _ in result_rows if result == "BLOCKED"
        ]
        reason_match = re.fullmatch(
            r"FAIL=\[(?P<fail>none|[A-Z0-9,-]+)\]; "
            r"BLOCKED=\[(?P<blocked>none|[A-Z0-9,-]+)\]",
            decision_fields["Reason"],
        )
        self.assertIsNotNone(reason_match, "Reason must be an exact FAIL/BLOCKED ID ledger")

        def parse_identifier_ledger(value: str) -> list[str]:
            return [] if value == "none" else value.split(",")

        stated_fail_ids = parse_identifier_ledger(reason_match.group("fail"))
        stated_blocked_ids = parse_identifier_ledger(reason_match.group("blocked"))
        self.assertEqual(len(stated_fail_ids), len(set(stated_fail_ids)))
        self.assertEqual(len(stated_blocked_ids), len(set(stated_blocked_ids)))
        self.assertEqual(sorted(stated_fail_ids), stated_fail_ids)
        self.assertEqual(sorted(stated_blocked_ids), stated_blocked_ids)
        self.assertEqual(set(fail_ids), set(stated_fail_ids))
        self.assertEqual(set(blocked_ids), set(stated_blocked_ids))
        required_gate_pairs = {
            f"{identifier}@{layer}"
            for identifier, result, layers in result_rows
            if result in {"FAIL", "BLOCKED"}
            for layer in layers
        }
        if any(result in {"FAIL", "BLOCKED"} for result in matrix_results):
            if "FAIL" in matrix_results:
                self.assertEqual("FAIL", decision_fields["Final status"])
            else:
                self.assertEqual("BLOCKED", decision_fields["Final status"])
            self.assertEqual("NO", decision_fields["Release-ready"])
            stated_gate_pairs = decision_fields["Required gates"].split(",")
            self.assertEqual(len(stated_gate_pairs), len(set(stated_gate_pairs)))
            self.assertEqual(sorted(stated_gate_pairs), stated_gate_pairs)
            for pair in stated_gate_pairs:
                self.assertRegex(
                    pair,
                    r"^[A-Z0-9-]+@(SOURCE|STATIC|LOGIC|AIX|STUDIO|DEVICE)$",
                )
            self.assertEqual(required_gate_pairs, set(stated_gate_pairs))
        else:
            self.assertEqual("PASS", decision_fields["Final status"])
            self.assertEqual("YES", decision_fields["Release-ready"])
            self.assertEqual("none", decision_fields["Required gates"].lower())
        pre_decision = unicodedata.normalize(
            "NFKC", markdown.split("## Final release decision", 1)[0]
        )
        self.assertNotRegex(
            pre_decision,
            r"(?is)\*\*PASS\*\*|release[- ]?ready|ready to release|"
            r"release approval|approved for release|ship now|go-live approved|"
            r"release gate cleared|ready[- ]?to[- ]?ship|production[- ]?ready|"
            r"ready for deployment|\bgreenlit\b|all[- ]?gates?[- ]?clear|"
            r"\bLGTM\b|开发完成|已经完成|已完成|可以发布|可发布|"
            r"可以上线|可上线|可交付|批准上线|准予上线|具备上线条件|准许交付|"
            r"交付验收通过|验收合格.{0,8}投产|签字通过|所有能力均通过|"
            r"(?:发布|上线|投产|部署|交付|验收).{0,8}"
            r"(?:允许|批准|准许|就绪|合格|通过)|"
            r"(?:允许|批准|准许|具备).{0,8}"
            r"(?:发布|上线|投产|部署|交付|验收)",
        )

    def assert_exact_evidence_layers(self, value: str) -> tuple[str, ...]:
        layers = tuple(layer.strip() for layer in value.split(","))
        self.assertTrue(all(layers))
        self.assertEqual(len(layers), len(set(layers)))
        self.assertTrue(set(layers).issubset(EVIDENCE_LAYERS))
        return layers

    def assert_input_ledger(self, value: str, ux_input_gates: set[str]) -> None:
        entries = value.split(",")
        self.assertTrue(all(entries), "Inputs must be a non-empty kind@gate ledger")
        self.assertEqual(sorted(entries), entries, "Inputs must use ASCII sort order")
        self.assertEqual(len(entries), len(set(entries)), "Inputs must be unique")
        observed_gates: set[str] = set()
        for entry in entries:
            parsed = re.fullmatch(
                r"(?P<kind>[a-z0-9][a-z0-9.-]*)@(?P<gate>[a-z0-9][a-z0-9.-]*)",
                entry,
            )
            self.assertIsNotNone(parsed, f"invalid Inputs ledger entry: {entry}")
            observed_gates.add(parsed.group("gate"))
        self.assertEqual(
            len(entries),
            len(observed_gates),
            "each input kind must map to one distinct UX-INPUT gate",
        )
        self.assertEqual(
            ux_input_gates,
            observed_gates,
            "Inputs ledger and distinct UX-INPUT gates must be identical",
        )

    def assert_scanner_claims_closed(
        self,
        scanner_gates: set[tuple[str, str]],
        claimed_gates: set[tuple[str, str]],
    ) -> None:
        self.assertEqual(
            scanner_gates,
            claimed_gates,
            "Claimed capabilities must equal the deterministic inventory; put "
            "explicit product claims in aiui-audit-claims.json so the scanner "
            "can emit provenance-bound provisional gates",
        )

    def assert_split_outcome_ids(
        self,
        gate_outcomes: dict[tuple[str, str], list[tuple[str, str]]],
    ) -> None:
        for gate_key, outcomes in gate_outcomes.items():
            if len(outcomes) == 1:
                continue
            for identifier, result in outcomes:
                self.assertRegex(
                    identifier,
                    rf"-{re.escape(result)}(?:-|$)",
                    f"split row IDs must expose their result for {gate_key}: "
                    f"{identifier}/{result}",
                )

    def assert_exact_pass_cells(
        self,
        contract_name: str,
        api_cell: str,
        declaration_cell: str,
    ) -> None:
        capability_contract = CAPABILITY_CONTRACTS[contract_name]
        self.assertFalse(capability_contract.provisional)
        self.assertFalse(
            capability_contract.pass_blocked_reason,
            f"{contract_name} cannot PASS: {capability_contract.pass_blocked_reason}",
        )
        self.assertTrue(
            capability_contract.pass_api_pattern,
            f"exact family lacks a PASS API contract: {contract_name}",
        )
        self.assertTrue(
            capability_contract.pass_declaration_pattern,
            f"exact family lacks a PASS declaration contract: {contract_name}",
        )
        self.assertIsNotNone(
            re.fullmatch(
                capability_contract.pass_api_pattern,
                self.normalize_machine_cell(api_cell),
            ),
            f"PASS API/component/event does not match {contract_name}: {api_cell}",
        )
        normalized_declaration = self.normalize_machine_cell(declaration_cell)
        self.assertIsNotNone(
            re.fullmatch(
                capability_contract.pass_declaration_pattern,
                normalized_declaration,
            ),
            f"PASS declaration does not match {contract_name}: {declaration_cell}",
        )

    def normalize_machine_cell(self, value: str) -> str:
        normalized = value.strip()
        if len(normalized) >= 2 and normalized.startswith("`") and normalized.endswith("`"):
            return normalized[1:-1]
        return normalized

    def parse_device_host_metadata(self, value: str) -> dict[str, str] | None:
        if value == "UNAVAILABLE":
            return None
        parsed = re.fullmatch(
            r"device=(?P<device>[^;]+); host=(?P<host>[^;]+); "
            r"runtime=(?P<runtime>[^;]+)",
            value,
        )
        self.assertIsNotNone(
            parsed,
            "Device/host must be UNAVAILABLE or a device/host/runtime tuple",
        )
        environment = {
            "deviceModel": parsed.group("device").strip(),
            "hostBuild": parsed.group("host").strip(),
            "runtimeVersion": parsed.group("runtime").strip(),
        }
        for field_name, field_value in environment.items():
            self.assertGreaterEqual(len(field_value), 3)
            self.assertNotRegex(
                field_value,
                r"(?i)^(?:unknown|unavailable|unspecified|none|n/?a|x)$|"
                r"未知|不可用|未指定|未提供",
                f"non-concrete device environment {field_name}: {field_value}",
            )
            self.assertNotRegex(
                field_value,
                r"(?i)\b(?:simulator|emulator|browser|chrome|safari|firefox|"
                r"edge|mock|fixture|test|tbd|placeholder|fake|abc|def|ghi)\b|"
                r"模拟器|浏览器|测试|占位|伪造",
                f"DEVICE metadata must identify physical hardware: "
                f"{field_name}={field_value}",
            )
        self.assertRegex(
            environment["deviceModel"],
            r"(?i)\brokid\b",
            "DEVICE evidence is scoped to named physical Rokid glasses",
        )
        self.assertRegex(
            environment["runtimeVersion"],
            r"\bAIUI\s+\d+\.\d+\.\d+\b",
            "DEVICE runtime must include an exact AIUI version",
        )
        return environment

    def assert_project_revision(self, revision: str, import_root: str) -> None:
        if revision == "UNAVAILABLE":
            self.assertEqual(
                "UNAVAILABLE",
                import_root,
                "missing project source requires Import root: UNAVAILABLE",
            )
            return

        self.assertNotEqual(
            "UNAVAILABLE",
            import_root,
            "a concrete project revision requires a concrete import root",
        )
        root_path = self.resolve_import_root(import_root)
        if revision.startswith("WORKTREE:"):
            fingerprint = subprocess.run(
                [
                    sys.executable,
                    str(FINGERPRINT_SCRIPT),
                    str(root_path),
                    "--repository-root",
                    str(ROOT),
                ],
                cwd=ROOT,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(0, fingerprint.returncode, fingerprint.stderr)
            self.assertEqual(revision, fingerprint.stdout.strip())
            return

        self.assertRegex(revision, r"^[0-9a-f]{40}$")
        commit = subprocess.run(
            ["git", "cat-file", "-e", f"{revision}^{{commit}}"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(0, commit.returncode, f"unresolvable project commit: {revision}")
        relative_root = root_path.relative_to(ROOT.resolve()).as_posix()
        tree_object = f"{revision}^{{tree}}" if relative_root == "." else f"{revision}:{relative_root}"
        tracked_root = subprocess.run(
            ["git", "cat-file", "-e", tree_object],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(
            0,
            tracked_root.returncode,
            f"import root does not exist at project revision: {relative_root}",
        )
        tree = subprocess.run(
            ["git", "ls-tree", "-r", "-z", revision, "--", relative_root],
            cwd=ROOT,
            capture_output=True,
            check=False,
        )
        self.assertEqual(0, tree.returncode, tree.stderr.decode(errors="replace"))
        expected_files: dict[str, tuple[str, str]] = {}
        root_prefix = "" if relative_root == "." else f"{relative_root}/"
        for raw_entry in tree.stdout.split(b"\0"):
            if not raw_entry:
                continue
            metadata, raw_path = raw_entry.split(b"\t", 1)
            mode, object_type, object_id = metadata.decode("ascii").split()
            repository_path = raw_path.decode("utf-8")
            self.assertTrue(repository_path.startswith(root_prefix))
            import_path = repository_path[len(root_prefix) :]
            if import_path.split("/", 1)[0] == AUDIT_EVIDENCE_DIRECTORY:
                continue
            self.assertEqual(
                "blob",
                object_type,
                f"unsupported git object in import root: {repository_path}",
            )
            self.assertIn(
                mode,
                {"100644", "100755"},
                f"symlink or unsupported mode in import root: {repository_path}",
            )
            expected_files[import_path] = (mode, object_id)

        actual_files: dict[str, tuple[str, bytes]] = {}
        for candidate in root_path.rglob("*"):
            relative = candidate.relative_to(root_path)
            if relative.parts and relative.parts[0] in {
                ".git",
                AUDIT_EVIDENCE_DIRECTORY,
            }:
                continue
            self.assertFalse(
                candidate.is_symlink(),
                f"symlink is not allowed in import root: {relative}",
            )
            if candidate.is_dir():
                continue
            self.assertTrue(
                candidate.is_file(),
                f"unsupported filesystem entry in import root: {relative}",
            )
            mode = "100755" if candidate.stat().st_mode & 0o111 else "100644"
            actual_files[relative.as_posix()] = (mode, candidate.read_bytes())

        self.assertEqual(
            set(expected_files),
            set(actual_files),
            "filesystem paths differ from the declared commit; ignored and "
            "untracked files are part of the import tree",
        )
        for import_path, (expected_mode, object_id) in expected_files.items():
            actual_mode, actual_content = actual_files[import_path]
            self.assertEqual(expected_mode, actual_mode, f"mode changed: {import_path}")
            committed_content = subprocess.run(
                ["git", "cat-file", "blob", object_id],
                cwd=ROOT,
                capture_output=True,
                check=False,
            )
            self.assertEqual(0, committed_content.returncode)
            self.assertEqual(
                committed_content.stdout,
                actual_content,
                f"content changed from declared commit: {import_path}",
            )

    def resolve_import_root(self, import_root: str) -> Path:
        self.assertTrue(import_root.strip())
        self.assertFalse(Path(import_root).is_absolute())
        self.assertNotIn("\\", import_root)
        self.assertNotRegex(import_root, r"(?i)%2e|[\x00-\x1f\x7f]")
        self.assertNotIn("..", Path(import_root).parts)
        root_path = (ROOT / import_root).resolve()
        try:
            root_path.relative_to(ROOT.resolve())
        except ValueError:
            self.fail(f"import root escapes repository: {import_root}")
        self.assertTrue(root_path.is_dir(), f"import root is not a directory: {import_root}")
        return root_path

    def assert_result_evidence(
        self,
        result: str,
        evidence: str,
        layers: tuple[str, ...],
        *,
        row_id: str = "",
        gate: str = "",
        criterion: str = "",
        project_revision: str = "",
        project_import_root: str = "",
        request_prompt: str = "",
        allowed_source_urls: frozenset[str] = frozenset(),
        artifact_registry: dict[str, tuple[str, ...]] | None = None,
        device_environment: dict[str, str] | None = None,
        capability_binding: dict[str, object] | None = None,
    ) -> None:
        self.assertIn(result, ALLOWED_RESULTS)
        if result in {"PASS", "FAIL", "BLOCKED"}:
            evidence_entries: dict[str, tuple[str, str]] = {}
            for entry in (part.strip() for part in evidence.split(";")):
                parsed = EVIDENCE_ENTRY_RE.fullmatch(entry)
                self.assertIsNotNone(parsed, f"invalid {result} evidence: {entry}")
                layer = parsed.group("layer")
                self.assertNotIn(layer, evidence_entries)
                kind = parsed.group("kind")
                locator = parsed.group("locator")
                if result == "BLOCKED":
                    self.assertEqual(
                        "blocked",
                        kind,
                        f"BLOCKED rows must keep every named layer blocked: {entry}",
                    )
                    self.assertGreaterEqual(len(locator.strip()), 6)
                else:
                    self.assertNotEqual("blocked", kind)
                    self.assertIn(
                        kind,
                        LAYER_ALLOWED_KINDS[layer],
                        f"invalid evidence kind for {layer}: {kind}",
                    )
                    self.assert_executed_locator(
                        result,
                        layer,
                        kind,
                        locator,
                        row_id=row_id,
                        gate=gate,
                        criterion=criterion,
                        project_revision=project_revision,
                        project_import_root=project_import_root,
                        request_prompt=request_prompt,
                        allowed_source_urls=allowed_source_urls,
                        artifact_registry=artifact_registry,
                        device_environment=device_environment,
                        capability_binding=capability_binding,
                    )
                evidence_entries[layer] = (kind, locator)
            self.assertEqual(set(layers), set(evidence_entries))
        elif result == "N/A":
            scope_evidence = re.fullmatch(
                r"SCOPE: source=(?P<source>manifest:[^;\s]+@sha256="
                r"[0-9a-f]{64}#[A-Za-z0-9._-]+); claim=(?P<claim>"
                r"manifest:[^;\s]+@sha256=[0-9a-f]{64}#[A-Za-z0-9._-]+)",
                evidence,
            )
            self.assertIsNotNone(
                scope_evidence,
                "N/A requires source and claim absence manifest entries",
            )
            self.assertNotEqual(
                scope_evidence.group("source"), scope_evidence.group("claim")
            )
            self.assert_scope_locator(
                scope_evidence.group("source"),
                "source",
                row_id=row_id,
                gate=gate,
                criterion=criterion,
                project_revision=project_revision,
                project_import_root=project_import_root,
                artifact_registry=artifact_registry,
            )
            self.assert_scope_locator(
                scope_evidence.group("claim"),
                "claim",
                row_id=row_id,
                gate=gate,
                criterion=criterion,
                project_revision=project_revision,
                project_import_root=project_import_root,
                artifact_registry=artifact_registry,
            )

    def assert_executed_locator(
        self,
        result: str,
        layer: str,
        kind: str,
        locator: str,
        *,
        row_id: str,
        gate: str,
        criterion: str,
        project_revision: str,
        project_import_root: str,
        request_prompt: str,
        allowed_source_urls: frozenset[str],
        artifact_registry: dict[str, tuple[str, ...]] | None,
        device_environment: dict[str, str] | None,
        capability_binding: dict[str, object] | None,
    ) -> None:
        self.assertNotRegex(locator, INVALID_EXECUTED_LOCATOR_RE)
        if kind == "source" and re.fullmatch(r"https?://\S+", locator):
            self.assertEqual(
                "SOURCE",
                layer,
                "official documentation URLs prove SOURCE, not project STATIC state",
            )
            self.assertEqual(
                1,
                len(allowed_source_urls),
                "multi-source gates require one manifest entry that binds the "
                "complete inspected URL set",
            )
            source = PINNED_AIUI_SOURCE_RE.fullmatch(locator)
            self.assertIsNotNone(source, f"unverifiable source locator: {locator}")
            self.assertIn(
                source.group("revision"),
                {STABLE_AIUI_REVISION, PREVIEW_AIUI_REVISION},
            )
            source_path = source.group("path").rstrip("/")
            self.assertIn(
                source_path,
                ALLOWED_STABLE_SOURCE_PATHS | ALLOWED_PROVISIONAL_SOURCE_PATHS,
                f"official source locator path is not registered: {locator}",
            )
            self.assertIn(
                locator,
                allowed_source_urls,
                f"official source evidence is not declared on row {row_id}: {locator}",
            )
            return

        if kind == "source" and locator.startswith("request://current#"):
            self.assertEqual("FAIL", result)
            claim = locator.split("#", 1)[1]
            self.assertGreaterEqual(len(claim), 8)
            self.assertIn(
                claim,
                request_prompt,
                f"request evidence is not a verbatim current-request fact: {claim}",
            )
            return

        entry, evidence_path = self.assert_manifest_entry(
            locator,
            row_id=row_id,
            project_revision=project_revision,
            project_import_root=project_import_root,
            artifact_registry=artifact_registry,
        )
        self.assertEqual(layer, entry.get("layer"))
        self.assertEqual(gate, entry.get("gate"))
        self.assertEqual(
            " ".join(criterion.split()),
            " ".join(entry.get("criterion", "").split()),
        )
        self.assertEqual(kind, entry.get("kind"))
        self.assertEqual(result, entry.get("result"))
        if capability_binding is not None:
            for field_name, expected_value in capability_binding.items():
                self.assertEqual(
                    expected_value,
                    entry.get(field_name),
                    f"evidence does not bind capability {field_name}: {row_id}",
                )
            if layer == "SOURCE":
                self.assertEqual(
                    capability_binding["sourceUrls"],
                    entry.get("inspectedSourceUrls"),
                    f"SOURCE evidence did not inspect the complete source set: {row_id}",
                )
        environment = entry.get("environment")
        if layer == "AIX":
            self.assertIsInstance(environment, dict)
            self.assertEqual({"tool", "toolVersion", "host"}, set(environment))
            self.assertEqual("aix", environment.get("tool"))
            self.assertTrue(
                all(
                    isinstance(value, str) and len(value.strip()) >= 2
                    for value in environment.values()
                )
            )
        elif layer == "STUDIO":
            self.assertIsInstance(environment, dict)
            self.assertEqual({"studioVersion", "hostRuntime"}, set(environment))
            self.assertTrue(
                all(
                    isinstance(value, str) and len(value.strip()) >= 2
                    for value in environment.values()
                )
            )
        elif layer == "DEVICE":
            self.assertIsNotNone(
                device_environment,
                "DEVICE evidence requires concrete Device/host metadata",
            )
            self.assertIsInstance(environment, dict)
            self.assertEqual(
                {
                    "deviceModel",
                    "hostBuild",
                    "runtimeVersion",
                    "physicalDevice",
                    "deviceIdHash",
                    "captureTool",
                    "captureSessionId",
                },
                set(environment),
            )
            for field_name, expected_value in device_environment.items():
                self.assertEqual(expected_value, environment.get(field_name))
            self.assertIs(True, environment.get("physicalDevice"))
            self.assertIsInstance(environment.get("deviceIdHash"), str)
            self.assertRegex(environment.get("deviceIdHash", ""), r"^[0-9a-f]{64}$")
            for field_name in ("captureTool", "captureSessionId"):
                field_value = environment.get(field_name)
                self.assertIsInstance(field_value, str)
                self.assertGreaterEqual(len(field_value.strip()), 8)
                self.assertNotRegex(field_value, INVALID_EXECUTED_LOCATOR_RE)
            self.fail(
                "self-declared DEVICE provenance is not trusted evidence; keep "
                "DEVICE BLOCKED unless the packaged validator verifies a capture "
                "signature against an external trust key"
            )
        if layer == "AIX" and kind in {"artifact", "log"}:
            self.fail(
                "AIX text artifacts/logs cannot prove a render; use a bound AIX "
                "command and visual capture as separate evidence entries"
            )
        if kind == "command" or (
            layer in {"STATIC", "LOGIC"} and kind in {"artifact", "log"}
        ):
            self.assert_command_provenance(
                entry,
                evidence_path,
                layer=layer,
                result=result,
                project_import_root=project_import_root,
            )
        if kind == "screenshot":
            self.assertIn(
                evidence_path.suffix.lower(), {".png", ".jpg", ".jpeg", ".webp"}
            )
            media_bytes = evidence_path.read_bytes()
            if evidence_path.suffix.lower() == ".png":
                self.assertTrue(media_bytes.startswith(b"\x89PNG\r\n\x1a\n"))
            elif evidence_path.suffix.lower() in {".jpg", ".jpeg"}:
                self.assertTrue(media_bytes.startswith(b"\xff\xd8\xff"))
            else:
                self.assertTrue(
                    len(media_bytes) >= 12
                    and media_bytes.startswith(b"RIFF")
                    and media_bytes[8:12] == b"WEBP"
                )
        elif kind == "recording":
            self.assertIn(evidence_path.suffix.lower(), {".mp4", ".mov", ".webm"})
            media_bytes = evidence_path.read_bytes()
            if evidence_path.suffix.lower() == ".webm":
                self.assertTrue(media_bytes.startswith(b"\x1a\x45\xdf\xa3"))
            else:
                self.assertTrue(
                    len(media_bytes) >= 12 and media_bytes[4:8] == b"ftyp"
                )
        elif layer == "DEVICE" and kind in {"artifact", "log"}:
            self.assertIn(evidence_path.suffix.lower(), {".json", ".log", ".zip"})

    def assert_command_provenance(
        self,
        entry: dict,
        evidence_path: Path,
        *,
        layer: str,
        result: str,
        project_import_root: str,
    ) -> None:
        required_fields = {
            "operation",
            "argv",
            "cwd",
            "tool",
            "exitCode",
            "stdoutSha256",
            "stderrSha256",
        }
        self.assertTrue(
            required_fields.issubset(entry),
            f"{layer} command evidence lacks execution provenance: "
            f"{sorted(required_fields - set(entry))}",
        )
        operation = entry.get("operation")
        self.assertIsInstance(operation, str)
        self.assertRegex(operation, r"^[a-z][a-z0-9.-]{2,63}$")
        self.assertNotRegex(operation, INVALID_EXECUTED_LOCATOR_RE)
        argv = entry.get("argv")
        self.assertIsInstance(argv, list)
        self.assertGreaterEqual(len(argv), 1)
        for argument in argv:
            self.assertIsInstance(argument, str)
            self.assertTrue(argument)
            self.assertNotRegex(argument, r"[\x00\r\n]")
        self.assertEqual(project_import_root, entry.get("cwd"))
        tool = entry.get("tool")
        self.assertIsInstance(tool, dict)
        self.assertEqual({"name", "version"}, set(tool))
        for value in tool.values():
            self.assertIsInstance(value, str)
            self.assertGreaterEqual(len(value.strip()), 2)
            self.assertNotRegex(value, INVALID_EXECUTED_LOCATOR_RE)
        self.assertIs(type(entry.get("exitCode")), int)
        if result == "PASS":
            self.assertEqual(0, entry.get("exitCode"))
        for field_name in ("stdoutSha256", "stderrSha256"):
            self.assertRegex(str(entry.get(field_name, "")), r"^[0-9a-f]{64}$")
        artifact_digest = hashlib.sha256(evidence_path.read_bytes()).hexdigest()
        self.assertIn(
            artifact_digest,
            {entry.get("stdoutSha256"), entry.get("stderrSha256")},
            "command artifact must be the captured stdout or stderr bytes",
        )
        if layer == "AIX":
            self.assertEqual("aix", tool.get("name"))
            self.assertRegex(operation, r"^aix-(?:preview|pack|list|validate)$")
            self.assertEqual("aix", Path(argv[0]).name)

    def assert_scope_locator(
        self,
        locator: str,
        scope_aspect: str,
        *,
        row_id: str,
        gate: str,
        criterion: str,
        project_revision: str,
        project_import_root: str,
        artifact_registry: dict[str, tuple[str, ...]] | None,
    ) -> None:
        entry, _ = self.assert_manifest_entry(
            locator,
            row_id=row_id,
            project_revision=project_revision,
            project_import_root=project_import_root,
            artifact_registry=artifact_registry,
        )
        self.assertEqual("N/A", entry.get("result"))
        self.assertEqual("scope", entry.get("kind"))
        self.assertEqual(gate, entry.get("gate"))
        self.assertEqual(
            " ".join(criterion.split()),
            " ".join(entry.get("criterion", "").split()),
        )
        self.assertEqual(scope_aspect, entry.get("scopeAspect"))
        proof = entry.get("scopeProof")
        self.assertIsInstance(proof, dict)
        expected_family = ".".join(row_id.lower().split("-")[:2])
        expected_query = {"family": expected_family, "gate": gate}
        self.assertEqual(expected_query, proof.get("query"))
        self.assertEqual([], proof.get("matches"))

        def load_strict_json(path: Path) -> dict:
            def reject_duplicate_keys(pairs: list[tuple[str, object]]) -> dict:
                parsed: dict[str, object] = {}
                for key, value in pairs:
                    if key in parsed:
                        raise ValueError(f"duplicate JSON key: {key}")
                    parsed[key] = value
                return parsed

            try:
                document = json.loads(
                    path.read_text(encoding="utf-8"),
                    object_pairs_hook=reject_duplicate_keys,
                )
            except (OSError, UnicodeError, ValueError, json.JSONDecodeError) as error:
                self.fail(f"invalid scope proof JSON {path}: {error}")
            self.assertIsInstance(document, dict)
            return document

        fixture_mode = project_revision == "TEST-FIXTURE"
        if scope_aspect == "source":
            self.assertEqual(
                {"inventoryPath", "inventorySha256", "query", "matches"},
                set(proof),
            )
            inventory_path = self.resolve_evidence_path(
                proof.get("inventoryPath", ""), fixture_mode=fixture_mode
            )
            inventory_bytes = inventory_path.read_bytes()
            self.assertEqual(
                hashlib.sha256(inventory_bytes).hexdigest(),
                proof.get("inventorySha256"),
            )
            inventory = load_strict_json(inventory_path)
            self.assertEqual(2, inventory.get("schemaVersion"))
            self.assertIsInstance(inventory.get("claimedCapabilities"), list)
            selector = f"{expected_family}@{gate}"
            actual_matches = sorted(
                claim
                for claim in inventory.get("claimedCapabilities", [])
                if claim == selector
            )
            self.assertEqual(actual_matches, proof.get("matches"))
        else:
            self.assertEqual(
                {
                    "scopeManifestPath",
                    "scopeManifestSha256",
                    "query",
                    "matches",
                    "universeClosed",
                },
                set(proof),
            )
            self.assertIs(True, proof.get("universeClosed"))
            scope_path_value = proof.get("scopeManifestPath", "")
            if fixture_mode:
                scope_path = self.resolve_evidence_path(
                    scope_path_value, fixture_mode=True
                )
            else:
                self.assertTrue(project_import_root)
                self.assertEqual("aiui-audit-scope.json", Path(scope_path_value).name)
                scope_path = self.resolve_project_scope_path(
                    scope_path_value, project_import_root
                )
            scope_bytes = scope_path.read_bytes()
            self.assertEqual(
                hashlib.sha256(scope_bytes).hexdigest(),
                proof.get("scopeManifestSha256"),
            )
            scope_document = load_strict_json(scope_path)
            self.assertEqual(
                {"schemaVersion", "closed", "uxCriteria"},
                set(scope_document),
            )
            self.assertEqual(1, scope_document.get("schemaVersion"))
            self.assertIs(True, scope_document.get("closed"))
            self.assertIsInstance(scope_document.get("uxCriteria"), list)
            actual_matches = sorted(
                f"{criterion_entry.get('family')}@{criterion_entry.get('gate')}"
                for criterion_entry in scope_document.get("uxCriteria", [])
                if isinstance(criterion_entry, dict)
                and criterion_entry.get("family") == expected_family
                and criterion_entry.get("gate") == gate
            )
            self.assertEqual(actual_matches, proof.get("matches"))

    def assert_manifest_entry(
        self,
        locator: str,
        *,
        row_id: str,
        project_revision: str,
        project_import_root: str = "",
        artifact_registry: dict[str, tuple[str, ...]] | None = None,
    ) -> tuple[dict, Path]:
        self.assertNotEqual(
            "UNAVAILABLE",
            project_revision,
            "manifest evidence requires a concrete project revision",
        )
        manifest_locator = MANIFEST_LOCATOR_RE.fullmatch(locator)
        self.assertIsNotNone(
            manifest_locator,
            "executed evidence must use "
            f"manifest:<path>@sha256=<manifest-hash>#<entry-id>: {locator}",
        )
        fixture_mode = project_revision == "TEST-FIXTURE"
        manifest_path = self.resolve_evidence_path(
            manifest_locator.group("path"), fixture_mode=fixture_mode
        )
        manifest_bytes = manifest_path.read_bytes()
        self.assertEqual(
            manifest_locator.group("digest"),
            hashlib.sha256(manifest_bytes).hexdigest(),
            f"manifest locator hash does not match current bytes: {locator}",
        )

        def reject_duplicate_keys(pairs: list[tuple[str, object]]) -> dict:
            parsed: dict[str, object] = {}
            for key, value in pairs:
                if key in parsed:
                    raise ValueError(f"duplicate JSON key: {key}")
                parsed[key] = value
            return parsed

        try:
            manifest = json.loads(
                manifest_bytes.decode("utf-8"),
                object_pairs_hook=reject_duplicate_keys,
            )
        except (OSError, UnicodeError, ValueError, json.JSONDecodeError) as error:
            self.fail(f"invalid evidence manifest {manifest_path}: {error}")
        self.assertIs(type(manifest.get("schemaVersion")), int)
        self.assertEqual(2, manifest.get("schemaVersion"))
        self.assertEqual(project_revision, manifest.get("projectRevision"))
        subject = manifest.get("subject")
        self.assertIsInstance(subject, dict)
        self.assertEqual(
            {"projectRevision", "importRoot"},
            set(subject),
            "manifest subject must bind only revision and import root",
        )
        self.assertEqual(project_revision, subject.get("projectRevision"))
        self.assertIsInstance(subject.get("importRoot"), str)
        self.assertTrue(subject.get("importRoot"))
        if project_import_root:
            self.assertEqual(project_import_root, subject.get("importRoot"))
            if re.fullmatch(
                r"[0-9a-f]{40}|WORKTREE:[0-9a-f]{64}", project_revision
            ):
                self.assert_project_revision(project_revision, project_import_root)

        def parse_manifest_time(value: object, field_name: str) -> datetime:
            self.assertIsInstance(value, str, f"{field_name} must be an ISO timestamp")
            try:
                parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
            except ValueError as error:
                self.fail(f"invalid {field_name}: {error}")
            self.assertIsNotNone(parsed.tzinfo, f"{field_name} lacks timezone")
            self.assertLessEqual(
                parsed.astimezone(timezone.utc),
                datetime.now(timezone.utc) + timedelta(minutes=5),
                f"{field_name} is in the future",
            )
            return parsed

        source_snapshot = manifest.get("sourceSnapshot")
        completion_snapshot = manifest.get("completionSnapshot")
        self.assertIsInstance(source_snapshot, dict)
        self.assertIsInstance(completion_snapshot, dict)
        self.assertEqual(
            {"fingerprint", "inventoryPath", "inventorySha256", "capturedAt"},
            set(source_snapshot),
            "sourceSnapshot must bind fingerprint, inventory, hash, and capture time",
        )
        self.assertEqual(
            {"fingerprint", "capturedAt"},
            set(completion_snapshot),
            "completionSnapshot must bind the final fingerprint and capture time",
        )
        snapshot_fingerprint = source_snapshot.get("fingerprint")
        self.assertEqual(snapshot_fingerprint, completion_snapshot.get("fingerprint"))
        if fixture_mode:
            self.assertEqual("TEST-FIXTURE", snapshot_fingerprint)
        else:
            self.assertTrue(
                project_import_root,
                "production manifest validation requires the audited import root",
            )
            fingerprint = subprocess.run(
                [
                    sys.executable,
                    str(FINGERPRINT_SCRIPT),
                    str(self.resolve_import_root(project_import_root)),
                    "--repository-root",
                    str(ROOT),
                ],
                cwd=ROOT,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(0, fingerprint.returncode, fingerprint.stderr)
            self.assertEqual(fingerprint.stdout.strip(), snapshot_fingerprint)
        snapshot_time = parse_manifest_time(
            source_snapshot.get("capturedAt"), "sourceSnapshot.capturedAt"
        )
        completion_time = parse_manifest_time(
            completion_snapshot.get("capturedAt"),
            "completionSnapshot.capturedAt",
        )
        self.assertLessEqual(snapshot_time, completion_time)
        inventory_path = self.resolve_evidence_path(
            source_snapshot.get("inventoryPath", ""), fixture_mode=fixture_mode
        )
        inventory_bytes = inventory_path.read_bytes()
        self.assertRegex(
            str(source_snapshot.get("inventorySha256", "")), r"^[0-9a-f]{64}$"
        )
        self.assertEqual(
            source_snapshot.get("inventorySha256"),
            hashlib.sha256(inventory_bytes).hexdigest(),
        )
        try:
            inventory_document = json.loads(
                inventory_bytes.decode("utf-8"),
                object_pairs_hook=reject_duplicate_keys,
            )
        except (UnicodeError, ValueError, json.JSONDecodeError) as error:
            self.fail(f"invalid sourceSnapshot inventory: {error}")
        self.assertIsInstance(inventory_document, dict)
        self.assertEqual(2, inventory_document.get("schemaVersion"))
        self.assertEqual(
            snapshot_fingerprint, inventory_document.get("projectRevision")
        )
        self.assertIsInstance(inventory_document.get("items"), list)
        self.assertIsInstance(inventory_document.get("claimedCapabilities"), list)
        self.assertIsInstance(inventory_document.get("unmatchedSymbols"), list)
        self.assertIsInstance(inventory_document.get("versionViolations"), list)
        entries = manifest.get("entries")
        self.assertIsInstance(entries, list)
        for candidate_entry in entries:
            self.assertIsInstance(candidate_entry, dict)
            candidate_started = parse_manifest_time(
                candidate_entry.get("startedAt"), "entry.startedAt"
            )
            candidate_captured = parse_manifest_time(
                candidate_entry.get("capturedAt"), "entry.capturedAt"
            )
            self.assertLessEqual(
                snapshot_time,
                candidate_started,
                "evidence capture started before the bound source snapshot",
            )
            self.assertLessEqual(candidate_started, candidate_captured)
            self.assertLessEqual(
                candidate_captured,
                completion_time,
                "completion snapshot predates an evidence capture",
            )
        matching_entries = [
            entry
            for entry in entries
            if isinstance(entry, dict)
            and entry.get("id") == manifest_locator.group("entry")
        ]
        self.assertEqual(1, len(matching_entries), f"missing/duplicate manifest entry: {locator}")
        entry = matching_entries[0]
        self.assertEqual(row_id, entry.get("row"))
        self.assertEqual(project_revision, entry.get("projectRevision"))
        capture_id = entry.get("captureId")
        self.assertIsInstance(capture_id, str)
        self.assertRegex(capture_id, r"^[A-Za-z0-9][A-Za-z0-9._-]{15,127}$")
        collector = entry.get("collector")
        self.assertIsInstance(collector, dict)
        self.assertEqual({"name", "version"}, set(collector))
        for collector_value in collector.values():
            self.assertIsInstance(collector_value, str)
            self.assertGreaterEqual(len(collector_value.strip()), 2)
            self.assertNotRegex(collector_value, INVALID_EXECUTED_LOCATOR_RE)
        for field_name in ("criterion", "observed"):
            field_value = entry.get(field_name)
            self.assertIsInstance(field_value, str)
            self.assertGreaterEqual(
                len(field_value.strip()),
                8,
                f"evidence manifest {field_name} is too weak for {locator}",
            )
        self.assertNotRegex(entry.get("observed", ""), INVALID_EXECUTED_LOCATOR_RE)

        parsed_times: dict[str, datetime] = {}
        for time_field in ("startedAt", "capturedAt"):
            timestamp = entry.get(time_field)
            self.assertIsInstance(timestamp, str)
            try:
                parsed_time = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
            except ValueError as error:
                self.fail(f"invalid evidence timestamp for {locator}: {error}")
            self.assertIsNotNone(
                parsed_time.tzinfo,
                f"evidence timestamp lacks timezone: {locator}",
            )
            parsed_times[time_field] = parsed_time
        self.assertLessEqual(parsed_times["startedAt"], parsed_times["capturedAt"])
        self.assertLessEqual(
            parsed_times["capturedAt"].astimezone(timezone.utc),
            datetime.now(timezone.utc) + timedelta(minutes=5),
            f"evidence timestamp is in the future: {locator}",
        )
        evidence_path = self.resolve_evidence_path(
            entry.get("path", ""), fixture_mode=fixture_mode
        )
        before = evidence_path.stat()
        evidence_bytes = evidence_path.read_bytes()
        after = evidence_path.stat()
        self.assertEqual(
            (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns),
            (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns),
            f"evidence artifact changed while being read: {locator}",
        )
        digest = hashlib.sha256(evidence_bytes).hexdigest()
        self.assertEqual(digest, entry.get("sha256"))
        self.assertEqual(len(evidence_bytes), entry.get("bytes"))
        self.assertIs(type(entry.get("bytes")), int)
        self.assertGreater(entry.get("bytes"), 0)
        for field_name in ("artifactRole", "mediaType"):
            field_value = entry.get(field_name)
            self.assertIsInstance(field_value, str)
            self.assertGreaterEqual(len(field_value.strip()), 3)
            self.assertNotRegex(field_value, INVALID_EXECUTED_LOCATOR_RE)
        if entry.get("result") in {"PASS", "FAIL"} and evidence_path.suffix.lower() in {
            ".txt",
            ".log",
            ".json",
            ".md",
            ".html",
            ".xml",
        }:
            try:
                evidence_text = evidence_bytes.decode("utf-8")
            except UnicodeDecodeError as error:
                self.fail(f"text evidence is not UTF-8 for {locator}: {error}")
            self.assertNotRegex(evidence_text, INVALID_EXECUTED_LOCATOR_RE)
        reused_artifact_entries = [
            candidate
            for candidate in entries
            if isinstance(candidate, dict)
            and candidate.get("sha256") == entry.get("sha256")
        ]
        self.assertEqual(
            1,
            len(reused_artifact_entries),
            f"one artifact cannot be reused across evidence entries: {locator}",
        )
        reused_capture_entries = [
            candidate
            for candidate in entries
            if isinstance(candidate, dict)
            and candidate.get("captureId") == capture_id
        ]
        self.assertEqual(
            1,
            len(reused_capture_entries),
            f"one capture ID cannot prove multiple evidence entries: {locator}",
        )
        if artifact_registry is not None:
            evidence_slot = str(entry.get("layer") or entry.get("scopeAspect"))
            artifact_identity = (
                str(manifest_path),
                str(entry.get("id")),
                row_id,
                str(entry.get("gate")),
                evidence_slot,
            )
            for registry_key, description in (
                (f"artifact:{digest}", "artifact content hash"),
                (f"capture:{capture_id}", "capture ID"),
            ):
                prior_identity = artifact_registry.get(registry_key)
                self.assertTrue(
                    prior_identity is None or prior_identity == artifact_identity,
                    f"one {description} cannot prove multiple audit entries: "
                    f"{locator}; already used by {prior_identity}",
                )
                artifact_registry[registry_key] = artifact_identity
        return entry, evidence_path

    def resolve_evidence_path(
        self, local_path: str, *, fixture_mode: bool = False
    ) -> Path:
        self.assertTrue(local_path)
        self.assertFalse(Path(local_path).is_absolute(), f"absolute evidence locator: {local_path}")
        self.assertNotIn("\\", local_path, f"non-POSIX evidence locator: {local_path}")
        self.assertNotRegex(local_path, r"(?i)%2e|[\x00-\x1f\x7f]")
        self.assertNotIn(".", Path(local_path).parts)
        self.assertNotIn("..", Path(local_path).parts)
        if not fixture_mode:
            self.assertEqual(
                AUDIT_EVIDENCE_DIRECTORY,
                Path(local_path).parts[0],
                "production evidence manifests and artifacts must stay under "
                f"{AUDIT_EVIDENCE_DIRECTORY}/",
            )
        unresolved_path = ROOT / local_path
        current_path = ROOT
        for part in Path(local_path).parts:
            current_path = current_path / part
            self.assertFalse(
                current_path.is_symlink(),
                f"symlink is not allowed in evidence path: {local_path}",
            )
        evidence_path = unresolved_path.resolve()
        try:
            evidence_path.relative_to(ROOT.resolve())
        except ValueError:
            self.fail(f"evidence locator escapes repository: {local_path}")
        self.assertTrue(
            evidence_path.is_file(),
            f"evidence locator does not exist in the current repository: {local_path}",
        )
        self.assertGreater(evidence_path.stat().st_size, 0, f"empty evidence file: {local_path}")
        return evidence_path

    def resolve_project_scope_path(
        self, local_path: str, project_import_root: str
    ) -> Path:
        self.assertTrue(local_path)
        self.assertFalse(Path(local_path).is_absolute())
        self.assertNotIn("\\", local_path)
        self.assertNotIn("..", Path(local_path).parts)
        root_path = self.resolve_import_root(project_import_root)
        candidate = ROOT / local_path
        current = ROOT
        for part in Path(local_path).parts:
            current = current / part
            self.assertFalse(current.is_symlink())
        resolved = candidate.resolve()
        try:
            relative = resolved.relative_to(root_path)
        except ValueError:
            self.fail("claim universe must be stored inside the fingerprinted import root")
        self.assertNotEqual(
            AUDIT_EVIDENCE_DIRECTORY,
            relative.parts[0],
            "claim universe must be source-bound, not stored as mutable evidence",
        )
        self.assertTrue(resolved.is_file())
        self.assertGreater(resolved.stat().st_size, 0)
        return resolved

    def test_evaluation_guard_rejects_semantic_false_greens(self) -> None:
        self.assert_complete_evaluation_matrices(
            self.implementation_forward_evaluation,
            capability_contract_names=IMPLEMENTATION_CAPABILITY_CONTRACTS,
            forbidden_results=frozenset({"PASS", "N/A"}),
            request_prompt=self.implementation_prompt,
        )
        self.assert_complete_evaluation_matrices(
            self.forward_evaluation,
            capability_contract_names=AUDIT_CAPABILITY_CONTRACTS,
            forbidden_results=frozenset({"PASS", "N/A"}),
            request_prompt=self.audit_prompt,
        )

        missing_ux_family = self.implementation_forward_evaluation.replace(
            "| [UX-STATE] {gate=network-voice-states} |",
            "| [UX-TARGET-STATE] {gate=network-voice-states} |",
            1,
        )
        duplicate_ux_id = self.implementation_forward_evaluation.replace(
            "| [UX-STATE] {gate=network-voice-states} |",
            "| [UX-TARGET] {gate=network-voice-states} |",
            1,
        )
        fabricated_layer = self.implementation_forward_evaluation.replace(
            "| LOGIC, STUDIO, DEVICE | BLOCKED |",
            "| LOGIC, FABRICATED | BLOCKED |",
            1,
        )
        missing_required_ux_layer = self.implementation_forward_evaluation.replace(
            "| AIX, DEVICE | BLOCKED |",
            "| AIX | BLOCKED |",
            1,
        )
        pass_without_evidence = re.sub(
            r"\| BLOCKED \| [^|\n]+ \|",
            "| PASS | none |",
            self.implementation_forward_evaluation,
            count=1,
        )
        pass_without_per_layer_evidence = re.sub(
            r"\| BLOCKED \| [^|\n]+ \|",
            "| PASS | LOGIC=log:artifacts/logic.log |",
            self.implementation_forward_evaluation,
            count=1,
        )
        na_without_scope_reason = re.sub(
            r"\| BLOCKED \| [^|\n]+ \|",
            "| N/A | none |",
            self.implementation_forward_evaluation,
            count=1,
        )
        preview_revision_for_stable = self.implementation_forward_evaluation.replace(
            "88e70bb0382525c1a93ef077c2401dcc31a273ce",
            "63bb5f5efa2f0c11a2defca35bc00777150f43d2",
        )
        arbitrary_revision = self.implementation_forward_evaluation.replace(
            "88e70bb0382525c1a93ef077c2401dcc31a273ce",
            "0000000000000000000000000000000000000000",
        )
        mixed_good_and_bad_sources = self.implementation_forward_evaluation.replace(
            "target.en-US.md)",
            "target.en-US.md); DOC=[unapproved](https://github.com/yodaos-project/AIUI/blob/0000000000000000000000000000000000000000/documentation/1-framework/open-agent-format/target.en-US.md)",
            1,
        )
        nonexistent_source_path = self.implementation_forward_evaluation.replace(
            "documentation/1-framework/open-agent-format/target.en-US.md",
            "documentation/1-framework/open-agent-format/fabricated.en-US.md",
            1,
        )
        missing_network_capability = re.sub(
            r"(?m)^\| `?\[CAP-[^]\n]*NETWORK[^\n]+\n",
            "",
            self.implementation_forward_evaluation,
        )
        contradictory_sign_off = (
            self.implementation_forward_evaluation
            + "\n开发完成，可以发布。\n"
        )
        mixed_version = replace_capability_cells(
            self.implementation_forward_evaluation,
            "CAP-PAGE-TARGET",
            {1: "AIUI 0.17.0 and AIUI 0.18.0; device UNAVAILABLE; `_current`"},
        )
        noncanonical_family_id = self.implementation_forward_evaluation.replace(
            "[CAP-PAGE-TARGET-PROVISIONAL]", "[CAP-UNRELATED-PROVISIONAL]", 1
        )
        colliding_canonical_id = self.implementation_forward_evaluation.replace(
            "[CAP-VOICE-PROVISIONAL]", "[CAP-VOICE-DECLARATION-PROVISIONAL]", 1
        )
        voice_candidate_outside_unknown_cells = replace_capability_cells(
            self.implementation_forward_evaluation,
            "CAP-VOICE",
            {5: "onVoiceWakeup triggers the primary action"},
        )
        network_candidate_outside_unknown_cells = replace_capability_cells(
            self.implementation_forward_evaluation,
            "CAP-NETWORK",
            {6: "HTTPS/SSE/WebSocket failure and fallback"},
        )
        hidden_source_url = re.sub(
            r"DOC=\[[^\]]+\](\(https://github\.com/yodaos-project/AIUI/[^)]+\))",
            r"DOC=[https://hidden.example]\1",
            self.implementation_forward_evaluation,
            count=1,
        )
        adversarial_cases = {
            "missing UX family": missing_ux_family,
            "duplicate UX ID": duplicate_ux_id,
            "fabricated evidence layer": fabricated_layer,
            "missing required UX layer": missing_required_ux_layer,
            "PASS without evidence": pass_without_evidence,
            "PASS missing required layers": pass_without_per_layer_evidence,
            "N/A without scope reason": na_without_scope_reason,
            "0.18 revision for 0.17 row": preview_revision_for_stable,
            "arbitrary revision": arbitrary_revision,
            "mixed good and bad sources": mixed_good_and_bad_sources,
            "nonexistent official source": nonexistent_source_path,
            "missing scenario capability": missing_network_capability,
            "contradictory sign-off": contradictory_sign_off,
            "mixed canonical versions": mixed_version,
            "family paired with noncanonical CAP ID": noncanonical_family_id,
            "family ID swallowed by another canonical base": colliding_canonical_id,
            "voice candidate outside UNKNOWN cells": voice_candidate_outside_unknown_cells,
            "network candidates outside UNKNOWN cells": network_candidate_outside_unknown_cells,
            "URL hidden in source label": hidden_source_url,
        }
        for name, markdown in adversarial_cases.items():
            with self.subTest(name=f"mutation changed base: {name}"):
                self.assertNotEqual(self.implementation_forward_evaluation, markdown)
        for name, markdown in adversarial_cases.items():
            with self.subTest(name=name), self.assertRaises(AssertionError):
                self.assert_complete_evaluation_matrices(
                    markdown,
                    capability_contract_names=IMPLEMENTATION_CAPABILITY_CONTRACTS,
                    forbidden_results=frozenset({"PASS", "N/A"}),
                    request_prompt=self.implementation_prompt,
                )

        all_na_release = re.sub(
            r"\| (?:BLOCKED|FAIL) \| [^|\n]+ \|",
            "| N/A | SCOPE: shipped source and product claims exclude this row |",
            self.forward_evaluation,
        )
        all_na_release = all_na_release.replace(
            "Final status: FAIL", "Final status: PASS"
        ).replace("Release-ready: NO", "Release-ready: YES")
        all_na_release = re.sub(
            r"(?m)^Required gates: .+$",
            "Required gates: none",
            all_na_release,
        )
        deleted_layers_fake_pass = replace_capability_cells(
            self.forward_evaluation,
            "CAP-BUTTON",
            {8: "STATIC", 9: "PASS", 10: "STATIC=log:fake.log"},
        )
        camera_without_permission_fragment = self.forward_evaluation.replace(
            "samples/capabilities/app.json#L57",
            "samples/capabilities/app.json",
            1,
        )
        camera_manifest_mislabeled_as_sample = self.forward_evaluation.replace(
            "DECLARATION-SNIPPET=[CAMERA permission line 57]",
            "SAMPLE=[CAMERA permission line 57]",
            1,
        )
        audit_false_greens = {
            "all applicable rows disguised as N/A": all_na_release,
            "capability PASS after deleting required layers": deleted_layers_fake_pass,
            "CAMERA declaration missing exact permission fragment": (
                camera_without_permission_fragment
            ),
            "CAMERA declaration mislabeled as sample": (
                camera_manifest_mislabeled_as_sample
            ),
        }
        for name, markdown in audit_false_greens.items():
            with self.subTest(name=f"mutation changed base: {name}"):
                self.assertNotEqual(self.forward_evaluation, markdown)
        for name, markdown in audit_false_greens.items():
            with self.subTest(name=name), self.assertRaises(AssertionError):
                self.assert_complete_evaluation_matrices(
                    markdown,
                    capability_contract_names=AUDIT_CAPABILITY_CONTRACTS,
                    forbidden_results=frozenset({"PASS", "N/A"}),
                    request_prompt=self.audit_prompt,
                )

        wrong_capability_source = replace_capability_cells(
            self.implementation_forward_evaluation,
            "CAP-VOICE",
            {
                4: (
                    "DOC=[wrong docs](https://github.com/yodaos-project/AIUI/blob/"
                    f"{STABLE_AIUI_REVISION}/documentation/2-components/button.en-US.md); "
                    "SAMPLE=[wrong sample](https://github.com/yodaos-project/AIUI/blob/"
                    f"{STABLE_AIUI_REVISION}/samples/capabilities/pages/close/index.ink)"
                )
            },
        )
        token_disguised_omission = re.sub(
            r"(?m)^\| `?\[CAP-[^]\n]*NETWORK[^\n]+\n",
            "",
            self.implementation_forward_evaluation,
        )
        token_disguised_omission = replace_capability_cells(
            token_disguised_omission,
            "CAP-PAGE-TARGET",
            {2: "route handling; unrelated CAP-NETWORK token"},
        )
        contradictory_before_final = self.implementation_forward_evaluation.replace(
            "## Final release decision",
            "Release approval granted; ship now.\n\n## Final release decision",
            1,
        )
        blocked_with_no_gates = re.sub(
            r"(?m)^Required gates: .+$",
            "Required gates: none",
            self.implementation_forward_evaluation,
        )
        duplicate_release_field = self.implementation_forward_evaluation.replace(
            "## Final release decision",
            "Release-ready: YES\n\n## Final release decision",
            1,
        )
        blocked_with_no_remaining_gates = re.sub(
            r"(?m)^Required gates: .+$",
            "Required gates: no remaining gates",
            self.implementation_forward_evaluation,
        )
        implementation_false_greens = {
            "wrong official sources attached to capability": wrong_capability_source,
            "missing capability token hidden in another column": token_disguised_omission,
            "contradictory release claim before final section": contradictory_before_final,
            "blocked release with no required gates": blocked_with_no_gates,
            "extra positive release field before final section": duplicate_release_field,
            "blocked release says no remaining gates": blocked_with_no_remaining_gates,
        }
        for name, markdown in implementation_false_greens.items():
            with self.subTest(name=f"mutation changed base: {name}"):
                self.assertNotEqual(self.implementation_forward_evaluation, markdown)
        for name, markdown in implementation_false_greens.items():
            with self.subTest(name=name), self.assertRaises(AssertionError):
                self.assert_complete_evaluation_matrices(
                    markdown,
                    capability_contract_names=IMPLEMENTATION_CAPABILITY_CONTRACTS,
                    forbidden_results=frozenset({"PASS", "N/A"}),
                    request_prompt=self.implementation_prompt,
                )

    def test_structured_pass_and_na_evidence_have_positive_controls(self) -> None:
        fixture_manifest = "tests/fixtures/evidence/manifest.json"
        self.assert_result_evidence(
            "PASS",
            f"LOGIC=log:{manifest_locator(fixture_manifest, 'logic-pass')}; "
            f"AIX=command:{manifest_locator(fixture_manifest, 'aix-pass')}",
            ("LOGIC", "AIX"),
            row_id="CONTROL-PASS",
            gate="control-pass",
            criterion="CONTROL PASS criterion",
            project_revision="TEST-FIXTURE",
            project_import_root="tests/fixtures/valid-minimal",
        )
        self.assert_result_evidence(
            "FAIL",
            f"STATIC=artifact:{manifest_locator(fixture_manifest, 'static-fail')}",
            ("STATIC",),
            row_id="CONTROL-FAIL",
            gate="control-fail",
            criterion="CONTROL FAIL criterion",
            project_revision="TEST-FIXTURE",
            project_import_root="tests/fixtures/valid-minimal",
        )
        self.assert_result_evidence(
            "FAIL",
            "STATIC=source:request://current#页面用亮/暗绿色区分成功与失败但没有文字标签",
            ("STATIC",),
            row_id="CONTROL-REQUEST-FAIL",
            project_revision="UNAVAILABLE",
            request_prompt=self.audit_prompt,
        )
        self.assert_result_evidence(
            "BLOCKED",
            "STUDIO=blocked:authenticated Studio run has not been executed; "
            "DEVICE=blocked:target glasses and host build are unavailable",
            ("STUDIO", "DEVICE"),
        )
        self.assert_result_evidence(
            "N/A",
            f"SCOPE: source={manifest_locator(fixture_manifest, 'source-absence')}; "
            f"claim={manifest_locator(fixture_manifest, 'claim-absence')}",
            ("DEVICE",),
            row_id="CONTROL-NA",
            gate="control-na",
            criterion="CONTROL N/A criterion",
            project_revision="TEST-FIXTURE",
            project_import_root="tests/fixtures/valid-minimal",
        )

    def test_production_evidence_requires_reserved_root(self) -> None:
        base_manifest = json.loads(
            (ROOT / "tests/fixtures/evidence/manifest.json").read_text(
                encoding="utf-8"
            )
        )
        project_revision = "WORKTREE:" + "a" * 64
        base_manifest["projectRevision"] = project_revision
        base_manifest["subject"]["projectRevision"] = project_revision
        base_manifest["entries"][0]["projectRevision"] = project_revision
        fixture_directory = ROOT / "tests/fixtures/evidence"
        with tempfile.TemporaryDirectory(dir=fixture_directory) as temporary_directory:
            manifest_path = Path(temporary_directory) / "outside-reserved-root.json"
            manifest_path.write_text(json.dumps(base_manifest), encoding="utf-8")
            relative = manifest_path.relative_to(ROOT).as_posix()
            with self.assertRaises(AssertionError):
                self.assert_manifest_entry(
                    manifest_locator(relative, "logic-pass"),
                    row_id="CONTROL-PASS",
                    project_revision=project_revision,
                )

    def test_command_pass_requires_operation_argv_cwd_tool_and_output_hashes(self) -> None:
        base_manifest = json.loads(
            (ROOT / "tests/fixtures/evidence/manifest.json").read_text(
                encoding="utf-8"
            )
        )
        entry = base_manifest["entries"][0]
        entry["kind"] = "command"
        entry["exitCode"] = 0
        for field_name in (
            "operation",
            "argv",
            "cwd",
            "tool",
            "stdoutSha256",
            "stderrSha256",
        ):
            entry.pop(field_name, None)
        fixture_directory = ROOT / "tests/fixtures/evidence"
        with tempfile.TemporaryDirectory(dir=fixture_directory) as temporary_directory:
            manifest_path = Path(temporary_directory) / "weak-command.json"
            manifest_path.write_text(json.dumps(base_manifest), encoding="utf-8")
            relative = manifest_path.relative_to(ROOT).as_posix()
            with self.assertRaises(AssertionError):
                self.assert_result_evidence(
                    "PASS",
                    "LOGIC=command:" + manifest_locator(relative, "logic-pass"),
                    ("LOGIC",),
                    row_id="CONTROL-PASS",
                    gate="control-pass",
                    criterion="CONTROL PASS criterion",
                    project_revision="TEST-FIXTURE",
                    project_import_root="tests/fixtures/valid-minimal",
                )

    def test_aix_render_rejects_naked_artifact_log(self) -> None:
        base_manifest = json.loads(
            (ROOT / "tests/fixtures/evidence/manifest.json").read_text(
                encoding="utf-8"
            )
        )
        entry = base_manifest["entries"][1]
        entry["kind"] = "artifact"
        for field_name in (
            "operation",
            "argv",
            "cwd",
            "tool",
            "exitCode",
            "stdoutSha256",
            "stderrSha256",
        ):
            entry.pop(field_name, None)
        fixture_directory = ROOT / "tests/fixtures/evidence"
        with tempfile.TemporaryDirectory(dir=fixture_directory) as temporary_directory:
            manifest_path = Path(temporary_directory) / "naked-aix.json"
            manifest_path.write_text(json.dumps(base_manifest), encoding="utf-8")
            relative = manifest_path.relative_to(ROOT).as_posix()
            with self.assertRaises(AssertionError):
                self.assert_result_evidence(
                    "PASS",
                    "AIX=artifact:" + manifest_locator(relative, "aix-pass"),
                    ("AIX",),
                    row_id="CONTROL-PASS",
                    gate="control-pass",
                    criterion="CONTROL PASS criterion",
                    project_revision="TEST-FIXTURE",
                    project_import_root="tests/fixtures/valid-minimal",
                )

    def test_device_self_assertion_without_verified_attestation_is_blocked(self) -> None:
        base_manifest = json.loads(
            (ROOT / "tests/fixtures/evidence/manifest.json").read_text(
                encoding="utf-8"
            )
        )
        device_environment = self.parse_device_host_metadata(
            "device=Rokid Glasses; host=YodaOS 2.1.0; runtime=AIUI 0.17.0"
        )
        entry = base_manifest["entries"][0]
        entry.update(
            {
                "row": "CONTROL-DEVICE",
                "gate": "control-device",
                "layer": "DEVICE",
                "kind": "log",
                "criterion": "CONTROL DEVICE criterion",
                "environment": {
                    **device_environment,
                    "physicalDevice": True,
                    "deviceIdHash": "a" * 64,
                    "captureTool": "rokid-device-capture",
                    "captureSessionId": "session-20260909-0001",
                },
            }
        )
        fixture_directory = ROOT / "tests/fixtures/evidence"
        with tempfile.TemporaryDirectory(dir=fixture_directory) as temporary_directory:
            manifest_path = Path(temporary_directory) / "self-asserted-device.json"
            manifest_path.write_text(json.dumps(base_manifest), encoding="utf-8")
            relative = manifest_path.relative_to(ROOT).as_posix()
            with self.assertRaises(AssertionError):
                self.assert_result_evidence(
                    "PASS",
                    "DEVICE=log:" + manifest_locator(relative, "logic-pass"),
                    ("DEVICE",),
                    row_id="CONTROL-DEVICE",
                    gate="control-device",
                    criterion="CONTROL DEVICE criterion",
                    project_revision="TEST-FIXTURE",
                    project_import_root="tests/fixtures/valid-minimal",
                    device_environment=device_environment,
                )

    def test_scope_na_requires_replayable_inventory_and_closed_claim_universe(self) -> None:
        base_manifest = json.loads(
            (ROOT / "tests/fixtures/evidence/manifest.json").read_text(
                encoding="utf-8"
            )
        )
        del base_manifest["entries"][3]["scopeProof"]
        del base_manifest["entries"][4]["scopeProof"]
        fixture_directory = ROOT / "tests/fixtures/evidence"
        with tempfile.TemporaryDirectory(dir=fixture_directory) as temporary_directory:
            manifest_path = Path(temporary_directory) / "weak-scope.json"
            manifest_path.write_text(json.dumps(base_manifest), encoding="utf-8")
            relative = manifest_path.relative_to(ROOT).as_posix()
            with self.assertRaises(AssertionError):
                self.assert_result_evidence(
                    "N/A",
                    f"SCOPE: source={manifest_locator(relative, 'source-absence')}; "
                    f"claim={manifest_locator(relative, 'claim-absence')}",
                    ("DEVICE",),
                    row_id="CONTROL-NA",
                    gate="control-na",
                    criterion="CONTROL N/A criterion",
                    project_revision="TEST-FIXTURE",
                    project_import_root="tests/fixtures/valid-minimal",
                )

    def test_capture_starts_after_source_snapshot_and_finishes_unchanged(self) -> None:
        base_manifest = json.loads(
            (ROOT / "tests/fixtures/evidence/manifest.json").read_text(
                encoding="utf-8"
            )
        )
        del base_manifest["sourceSnapshot"]
        del base_manifest["completionSnapshot"]
        fixture_directory = ROOT / "tests/fixtures/evidence"
        with tempfile.TemporaryDirectory(dir=fixture_directory) as temporary_directory:
            manifest_path = Path(temporary_directory) / "no-snapshot.json"
            manifest_path.write_text(json.dumps(base_manifest), encoding="utf-8")
            relative = manifest_path.relative_to(ROOT).as_posix()
            with self.assertRaises(AssertionError):
                self.assert_manifest_entry(
                    manifest_locator(relative, "logic-pass"),
                    row_id="CONTROL-PASS",
                    project_revision="TEST-FIXTURE",
                    project_import_root="tests/fixtures/valid-minimal",
                )

    def test_ux_input_ledger_equals_distinct_ux_input_gates(self) -> None:
        self.assert_input_ledger(
            "back@back,enter@enter,tap@tap,voice@voice",
            {"back", "enter", "tap", "voice"},
        )
        for invalid in (
            "tap@tap,voice@voice",
            "voice@voice,tap@tap,enter@enter,back@back",
            "tap,tap@tap,voice@voice,enter@enter,back@back",
        ):
            with self.subTest(invalid=invalid), self.assertRaises(AssertionError):
                self.assert_input_ledger(
                    invalid,
                    {"back", "enter", "tap", "voice"},
                )

    def test_scanner_claims_are_a_closed_set(self) -> None:
        scanner = {("page.route", "route-a")}
        self.assert_scanner_claims_closed(scanner, scanner)
        with self.assertRaises(AssertionError):
            self.assert_scanner_claims_closed(
                scanner,
                scanner | {("network.https", "self-declared-pass")},
            )

    def test_executed_evidence_rejects_wrong_kinds_placeholders_and_missing_files(self) -> None:
        invalid_cases = (
            (
                "PASS",
                "DEVICE=source:README.md",
                ("DEVICE",),
            ),
            (
                "FAIL",
                "DEVICE=recording:未执行（无设备）",
                ("DEVICE",),
            ),
            (
                "PASS",
                "LOGIC=log:未提供任何日志",
                ("LOGIC",),
            ),
            (
                "PASS",
                "STATIC=source:made-up-proof.txt",
                ("STATIC",),
            ),
            (
                "PASS",
                "LOGIC=command:exit=0@README.md#not-command-output",
                ("LOGIC",),
            ),
            (
                "PASS",
                "DEVICE=artifact:README.md#not-device-output",
                ("DEVICE",),
            ),
            (
                "PASS",
                "SOURCE=source:https://github.com/yodaos-project/AIUI/blob/"
                f"{STABLE_AIUI_REVISION}/documentation/fabricated.md",
                ("SOURCE",),
            ),
        )
        for result, evidence, layers in invalid_cases:
            with self.subTest(evidence=evidence), self.assertRaises(AssertionError):
                self.assert_result_evidence(result, evidence, layers)

        with self.assertRaises(AssertionError):
            self.assert_result_evidence(
                "PASS",
                "LOGIC=log:"
                + manifest_locator(
                    "tests/fixtures/evidence/manifest.json", "logic-pass"
                ),
                ("LOGIC",),
                row_id="WRONG-ROW",
                gate="control-pass",
                criterion="CONTROL PASS criterion",
                project_revision="TEST-FIXTURE",
            )
        with self.assertRaises(AssertionError):
            self.assert_result_evidence(
                "PASS",
                "LOGIC=log:"
                + manifest_locator(
                    "tests/fixtures/evidence/manifest.json", "logic-pass"
                ),
                ("LOGIC",),
                row_id="CONTROL-PASS",
                gate="control-pass",
                criterion="CONTROL PASS criterion",
                project_revision="0" * 40,
            )
        with self.assertRaises(AssertionError):
            self.assert_result_evidence(
                "PASS",
                "STATIC=artifact:"
                + manifest_locator(
                    "tests/fixtures/evidence/manifest.json", "static-fail"
                ),
                ("STATIC",),
                row_id="CONTROL-FAIL",
                gate="control-fail",
                criterion="CONTROL FAIL criterion",
                project_revision="TEST-FIXTURE",
            )
        with self.assertRaises(AssertionError):
            self.assert_result_evidence(
                "FAIL",
                "STATIC=source:request://current#不存在于请求中的伪造事实",
                ("STATIC",),
                row_id="CONTROL-REQUEST-FAIL",
                project_revision="UNAVAILABLE",
                request_prompt=self.audit_prompt,
            )
        with self.assertRaises(AssertionError):
            self.assert_result_evidence(
                "N/A",
                "SCOPE: source=ABSENT(fake); claim=ABSENT(fake)",
                ("DEVICE",),
                row_id="CONTROL-NA",
                project_revision="TEST-FIXTURE",
            )

    def test_evidence_artifacts_are_unique_across_the_whole_audit(self) -> None:
        artifact_registry: dict[str, tuple[str, ...]] = {}
        self.assert_result_evidence(
            "PASS",
            "LOGIC=log:"
            + manifest_locator(
                "tests/fixtures/evidence/manifest.json", "logic-pass"
            ),
            ("LOGIC",),
            row_id="CONTROL-PASS",
            gate="control-pass",
            criterion="CONTROL PASS criterion",
            project_revision="TEST-FIXTURE",
            project_import_root="tests/fixtures/valid-minimal",
            artifact_registry=artifact_registry,
        )
        with self.assertRaises(AssertionError):
            self.assert_result_evidence(
                "PASS",
                "AIX=command:"
                + manifest_locator(
                    "tests/fixtures/evidence/manifest-reuse.json", "reused-proof"
                ),
                ("AIX",),
                row_id="CONTROL-REUSE",
                gate="control-reuse",
                criterion="CONTROL REUSE criterion",
                project_revision="TEST-FIXTURE",
                project_import_root="tests/fixtures/valid-minimal",
                artifact_registry=artifact_registry,
            )

    def test_manifest_locator_is_content_addressed_and_json_is_strict(self) -> None:
        fixture_path = ROOT / "tests/fixtures/evidence/manifest.json"
        base_manifest = json.loads(fixture_path.read_text(encoding="utf-8"))
        fixture_directory = ROOT / "tests/fixtures/evidence"
        with tempfile.TemporaryDirectory(dir=fixture_directory) as temporary_directory:
            temporary_root = Path(temporary_directory)
            temporary_manifest = temporary_root / "manifest.json"
            temporary_manifest.write_text(
                json.dumps(base_manifest, ensure_ascii=False), encoding="utf-8"
            )
            relative_manifest = temporary_manifest.relative_to(ROOT).as_posix()
            bound_locator = manifest_locator(relative_manifest, "logic-pass")

            changed_manifest = json.loads(json.dumps(base_manifest))
            changed_manifest["entries"][0]["observed"] = (
                "rewritten observation for the same old artifact"
            )
            temporary_manifest.write_text(
                json.dumps(changed_manifest, ensure_ascii=False), encoding="utf-8"
            )
            with self.assertRaises(AssertionError):
                self.assert_manifest_entry(
                    bound_locator,
                    row_id="CONTROL-PASS",
                    project_revision="TEST-FIXTURE",
                    project_import_root="tests/fixtures/valid-minimal",
                )

            duplicate_manifest = temporary_root / "duplicate.json"
            duplicate_manifest.write_text(
                '{"schemaVersion":2,"schemaVersion":2,"projectRevision":'
                '"TEST-FIXTURE","entries":[]}\n',
                encoding="utf-8",
            )
            duplicate_relative = duplicate_manifest.relative_to(ROOT).as_posix()
            with self.assertRaises(AssertionError):
                self.assert_manifest_entry(
                    manifest_locator(duplicate_relative, "anything"),
                    row_id="CONTROL-PASS",
                    project_revision="TEST-FIXTURE",
                )

    def test_manifest_rejects_placeholder_future_and_boolean_metadata(self) -> None:
        base_manifest = json.loads(
            (ROOT / "tests/fixtures/evidence/manifest.json").read_text(
                encoding="utf-8"
            )
        )
        fixture_directory = ROOT / "tests/fixtures/evidence"
        mutations = {
            "boolean schema": lambda document: document.update(
                {"schemaVersion": True}
            ),
            "placeholder observation": lambda document: document["entries"][0].update(
                {"observed": "not tested yet"}
            ),
            "future capture": lambda document: document["entries"][0].update(
                {
                    "startedAt": "2099-01-01T00:00:00+00:00",
                    "capturedAt": "2099-01-01T00:00:01+00:00",
                }
            ),
            "reversed capture": lambda document: document["entries"][0].update(
                {
                    "startedAt": "2026-09-09T20:00:01+08:00",
                    "capturedAt": "2026-09-09T20:00:00+08:00",
                }
            ),
        }
        with tempfile.TemporaryDirectory(dir=fixture_directory) as temporary_directory:
            temporary_root = Path(temporary_directory)
            for name, mutate in mutations.items():
                with self.subTest(name=name):
                    document = json.loads(json.dumps(base_manifest))
                    mutate(document)
                    path = temporary_root / f"{name.replace(' ', '-')}.json"
                    path.write_text(json.dumps(document), encoding="utf-8")
                    relative = path.relative_to(ROOT).as_posix()
                    with self.assertRaises(AssertionError):
                        self.assert_manifest_entry(
                            manifest_locator(relative, "logic-pass"),
                            row_id="CONTROL-PASS",
                            project_revision="TEST-FIXTURE",
                            project_import_root="tests/fixtures/valid-minimal",
                        )

            boolean_exit = json.loads(json.dumps(base_manifest))
            boolean_exit["entries"][0].update(
                {"kind": "command", "exitCode": False}
            )
            boolean_exit_path = temporary_root / "boolean-exit.json"
            boolean_exit_path.write_text(json.dumps(boolean_exit), encoding="utf-8")
            boolean_exit_relative = boolean_exit_path.relative_to(ROOT).as_posix()
            with self.assertRaises(AssertionError):
                self.assert_result_evidence(
                    "PASS",
                    "LOGIC=command:"
                    + manifest_locator(boolean_exit_relative, "logic-pass"),
                    ("LOGIC",),
                    row_id="CONTROL-PASS",
                    gate="control-pass",
                    criterion="CONTROL PASS criterion",
                    project_revision="TEST-FIXTURE",
                    project_import_root="tests/fixtures/valid-minimal",
                )

    def test_capability_evidence_binds_exact_source_set_and_mechanism(self) -> None:
        base_manifest = json.loads(
            (ROOT / "tests/fixtures/evidence/manifest.json").read_text(
                encoding="utf-8"
            )
        )
        source_urls = [
            "https://github.com/yodaos-project/AIUI/blob/"
            f"{STABLE_AIUI_REVISION}/{BUTTON_DOC}",
            "https://github.com/yodaos-project/AIUI/blob/"
            f"{STABLE_AIUI_REVISION}/{BUTTON_SAMPLE}",
        ]
        binding: dict[str, object] = {
            "target": "AIUI 0.17.0; device UNAVAILABLE; _current",
            "apiBinding": "<button>",
            "declarationBinding": "NONE REQUIRED",
            "sourceUrls": source_urls,
        }
        source_entry = base_manifest["entries"][0]
        source_entry.update(
            {
                "row": "CONTROL-SOURCE",
                "gate": "control-source",
                "layer": "SOURCE",
                "kind": "source",
                "criterion": "CONTROL SOURCE criterion",
                "target": binding["target"],
                "apiBinding": binding["apiBinding"],
                "declarationBinding": binding["declarationBinding"],
                "sourceUrls": source_urls,
                "inspectedSourceUrls": source_urls,
            }
        )
        fixture_directory = ROOT / "tests/fixtures/evidence"
        with tempfile.TemporaryDirectory(dir=fixture_directory) as temporary_directory:
            temporary_root = Path(temporary_directory)

            def write_document(document: dict, name: str) -> str:
                path = temporary_root / name
                path.write_text(json.dumps(document), encoding="utf-8")
                return path.relative_to(ROOT).as_posix()

            valid_relative = write_document(base_manifest, "source-valid.json")
            self.assert_result_evidence(
                "PASS",
                "SOURCE=source:"
                + manifest_locator(valid_relative, "logic-pass"),
                ("SOURCE",),
                row_id="CONTROL-SOURCE",
                gate="control-source",
                criterion="CONTROL SOURCE criterion",
                project_revision="TEST-FIXTURE",
                project_import_root="tests/fixtures/valid-minimal",
                allowed_source_urls=frozenset(source_urls),
                capability_binding=binding,
            )

            incomplete = json.loads(json.dumps(base_manifest))
            incomplete["entries"][0]["inspectedSourceUrls"] = source_urls[:1]
            incomplete_relative = write_document(incomplete, "source-incomplete.json")
            with self.assertRaises(AssertionError):
                self.assert_result_evidence(
                    "PASS",
                    "SOURCE=source:"
                    + manifest_locator(incomplete_relative, "logic-pass"),
                    ("SOURCE",),
                    row_id="CONTROL-SOURCE",
                    gate="control-source",
                    criterion="CONTROL SOURCE criterion",
                    project_revision="TEST-FIXTURE",
                    project_import_root="tests/fixtures/valid-minimal",
                    allowed_source_urls=frozenset(source_urls),
                    capability_binding=binding,
                )

            with self.assertRaises(AssertionError):
                self.assert_result_evidence(
                    "PASS",
                    f"SOURCE=source:{source_urls[0]}",
                    ("SOURCE",),
                    row_id="CONTROL-SOURCE",
                    gate="control-source",
                    criterion="CONTROL SOURCE criterion",
                    project_revision="TEST-FIXTURE",
                    allowed_source_urls=frozenset(source_urls),
                    capability_binding=binding,
                )

    def test_pass_bindings_cannot_use_unscanned_management_sentinels(self) -> None:
        sentinels = ("HOST-MANAGED:", "HOST-DEFAULT:", "FRAMEWORK-MANAGED:")
        for sentinel in sentinels:
            self.assertNotIn(sentinel, self.reference)
            for capability_contract in CAPABILITY_CONTRACTS.values():
                self.assertNotIn(sentinel, capability_contract.pass_api_pattern)

    def test_exact_family_passes_require_registered_symbols_and_declarations(self) -> None:
        for contract_name, capability_contract in CAPABILITY_CONTRACTS.items():
            if capability_contract.provisional:
                continue
            with self.subTest(contract_name=contract_name, coverage="policy"):
                self.assertTrue(capability_contract.pass_api_pattern)
                re.compile(capability_contract.pass_api_pattern)
                self.assertNotEqual(
                    bool(capability_contract.pass_declaration_pattern),
                    bool(capability_contract.pass_blocked_reason),
                )
                if capability_contract.pass_declaration_pattern:
                    re.compile(capability_contract.pass_declaration_pattern)

        positive_controls = (
            ("camera_permission", "app.json#permissions", "CAMERA"),
            (
                "camera_runtime",
                "navigator.mediaDevices.getUserMedia(video=true)",
                "CAMERA",
            ),
            (
                "camera_runtime",
                "navigator.mediaDevices.getUserMedia(video=constraints.video=object)",
                "CAMERA",
            ),
            (
                "voice_wakeup",
                "onVoiceWakeup(event)+event.keyword",
                "NONE REQUIRED",
            ),
            ("network_https", "`fetch(...)`", "`NONE REQUIRED`"),
            ("network_sse", "wx.createEventSource(...)", "NONE REQUIRED"),
            ("network_websocket", "wx.connectSocket(...)", "NONE REQUIRED"),
            ("enter", "onKeyDown(event.code=Enter)", "NONE REQUIRED"),
            (
                "head_gesture",
                "enableWorldAwareness(...)+onHeadGesture(event)",
                "NONE REQUIRED",
            ),
            (
                "speech_recognition",
                "new SpeechRecognition()->recognition.start()",
                "COMPANION:voice.declaration.unknown@speech-declaration",
            ),
        )
        for contract_name, api_cell, declaration_cell in positive_controls:
            with self.subTest(contract_name=contract_name):
                self.assert_exact_pass_cells(
                    contract_name,
                    api_cell,
                    declaration_cell,
                )

        invalid_controls = (
            ("camera_permission", "foo.bar", "XYZ"),
            ("camera_permission", "app.json#permissions", "RECORD_AUDIO"),
            ("camera_runtime", "MediaRecorder", "CAMERA"),
            (
                "camera_runtime",
                "navigator.mediaDevices.getUserMedia(video=false)",
                "CAMERA",
            ),
            (
                "camera_runtime",
                "navigator.mediaDevices.getUserMedia(video=constraints)",
                "CAMERA",
            ),
            (
                "voice_wakeup",
                "onVoiceWakeup(event.keyword)",
                "NONE REQUIRED",
            ),
            ("network_https", "new EventSource(url)", "NONE REQUIRED"),
            ("enter", "onKeyDown(event.code=Backspace)", "NONE REQUIRED"),
            ("head_gesture", "onHeadGesture(event)", "NONE REQUIRED"),
            (
                "speech_recognition",
                "new SpeechRecognition()->recognition.start()",
                "NONE REQUIRED",
            ),
        )
        for contract_name, api_cell, declaration_cell in invalid_controls:
            with self.subTest(contract_name=contract_name), self.assertRaises(
                AssertionError
            ):
                self.assert_exact_pass_cells(
                    contract_name,
                    api_cell,
                    declaration_cell,
                )

    def test_device_metadata_requires_a_concrete_environment_tuple(self) -> None:
        self.assertIsNone(self.parse_device_host_metadata("UNAVAILABLE"))
        self.assertEqual(
            {
                "deviceModel": "Rokid Glasses",
                "hostBuild": "YodaOS 2.1.0",
                "runtimeVersion": "AIUI 0.17.0",
            },
            self.parse_device_host_metadata(
                "device=Rokid Glasses; host=YodaOS 2.1.0; runtime=AIUI 0.17.0"
            ),
        )
        for invalid_value in (
            "x",
            "device=Rokid Glasses",
            "device=unknown; host=x; runtime=x",
            "device=Rokid Glasses; host=UNAVAILABLE; runtime=AIUI 0.17.0",
            "device=desktop simulator; host=Chrome 130; runtime=mock-build",
            "device=Rokid simulator; host=YodaOS 2.1.0; runtime=AIUI 0.17.0",
        ):
            with self.subTest(invalid_value=invalid_value), self.assertRaises(
                AssertionError
            ):
                self.parse_device_host_metadata(invalid_value)

    def test_device_evidence_requires_physical_capture_provenance(self) -> None:
        base_manifest = json.loads(
            (ROOT / "tests/fixtures/evidence/manifest.json").read_text(
                encoding="utf-8"
            )
        )
        device_environment = self.parse_device_host_metadata(
            "device=Rokid Glasses; host=YodaOS 2.1.0; runtime=AIUI 0.17.0"
        )
        self.assertIsNotNone(device_environment)
        full_environment: dict[str, object] = {
            **device_environment,
            "physicalDevice": True,
            "deviceIdHash": "a" * 64,
            "captureTool": "rokid-device-capture",
            "captureSessionId": "session-20260909-0001",
        }
        entry = base_manifest["entries"][0]
        entry.update(
            {
                "row": "CONTROL-DEVICE",
                "gate": "control-device",
                "layer": "DEVICE",
                "kind": "log",
                "criterion": "CONTROL DEVICE criterion",
                "environment": full_environment,
            }
        )
        fixture_directory = ROOT / "tests/fixtures/evidence"
        with tempfile.TemporaryDirectory(dir=fixture_directory) as temporary_directory:
            temporary_root = Path(temporary_directory)
            valid_path = temporary_root / "device-valid.json"
            valid_path.write_text(json.dumps(base_manifest), encoding="utf-8")
            valid_relative = valid_path.relative_to(ROOT).as_posix()
            with self.assertRaises(AssertionError):
                self.assert_result_evidence(
                    "PASS",
                    "DEVICE=log:" + manifest_locator(valid_relative, "logic-pass"),
                    ("DEVICE",),
                    row_id="CONTROL-DEVICE",
                    gate="control-device",
                    criterion="CONTROL DEVICE criterion",
                    project_revision="TEST-FIXTURE",
                    project_import_root="tests/fixtures/valid-minimal",
                    device_environment=device_environment,
                )

            for name, invalid_value in (
                ("simulated", False),
                ("boolean-id", True),
            ):
                with self.subTest(name=name):
                    invalid_manifest = json.loads(json.dumps(base_manifest))
                    if name == "simulated":
                        invalid_manifest["entries"][0]["environment"][
                            "physicalDevice"
                        ] = invalid_value
                    else:
                        invalid_manifest["entries"][0]["environment"][
                            "deviceIdHash"
                        ] = invalid_value
                    invalid_path = temporary_root / f"device-{name}.json"
                    invalid_path.write_text(
                        json.dumps(invalid_manifest), encoding="utf-8"
                    )
                    invalid_relative = invalid_path.relative_to(ROOT).as_posix()
                    with self.assertRaises(AssertionError):
                        self.assert_result_evidence(
                            "PASS",
                            "DEVICE=log:"
                            + manifest_locator(invalid_relative, "logic-pass"),
                            ("DEVICE",),
                            row_id="CONTROL-DEVICE",
                            gate="control-device",
                            criterion="CONTROL DEVICE criterion",
                            project_revision="TEST-FIXTURE",
                            project_import_root="tests/fixtures/valid-minimal",
                            device_environment=device_environment,
                        )

    def test_project_revision_is_resolvable_or_recomputed(self) -> None:
        import_root = "tests/fixtures/valid-minimal"
        head = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=True,
        ).stdout.strip()
        self.assert_project_revision(head, import_root)

        ignored_extra = ROOT / import_root / ".DS_Store"
        self.assertFalse(ignored_extra.exists())
        try:
            ignored_extra.write_bytes(b"ignored by git, visible to Studio")
            with self.assertRaises(AssertionError):
                self.assert_project_revision(head, import_root)
        finally:
            ignored_extra.unlink(missing_ok=True)

        fingerprint = subprocess.run(
            [
                sys.executable,
                str(FINGERPRINT_SCRIPT),
                import_root,
                "--repository-root",
                str(ROOT),
            ],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=True,
        ).stdout.strip()
        self.assert_project_revision(fingerprint, import_root)
        self.assert_project_revision("UNAVAILABLE", "UNAVAILABLE")

        for revision, root_value in (
            ("0" * 40, import_root),
            ("WORKTREE:" + "0" * 64, import_root),
            (head, "UNAVAILABLE"),
            ("UNAVAILABLE", import_root),
        ):
            with self.subTest(revision=revision), self.assertRaises(AssertionError):
                self.assert_project_revision(revision, root_value)

    def test_skill_makes_project_specific_audit_a_completion_gate(self) -> None:
        self.assertIn("`references/ux-and-capability-testing.md`", self.skill)
        gate = self.skill.lower()
        for task_type in ("creation", "implementation", "code change", "review"):
            self.assertIn(task_type, gate)
        for status in ("PASS", "FAIL", "BLOCKED", "N/A"):
            self.assertIn(f"`{status}`", self.skill)
        for phrase in (
            "both exact evidence matrices",
            "even explicitly",
            "{family=...}",
            "{gate=...}",
            "source roles",
            "fixed layers",
            "inventory_aiui_capabilities.py",
        ):
            self.assertIn(phrase, self.skill)
        self.assertRegex(
            self.skill,
            r"(?is)(?:FAIL|BLOCKED).*(?:forbid|must not).*(?:complete|release-ready)",
        )

    def test_public_fingerprint_and_inventory_commands_bind_repository_root(self) -> None:
        for document in (self.skill, self.reference):
            with self.subTest(document=document[:40]):
                self.assertRegex(
                    document,
                    r"fingerprint_aiui_project\.py[^\n]*--repository-root",
                )
                self.assertRegex(
                    document,
                    r"inventory_aiui_capabilities\.py[^\n]*--repository-root",
                )

    def test_reference_defines_separate_ux_and_capability_matrices(self) -> None:
        self.assertTrue(REFERENCE_PATH.is_file(), f"missing {REFERENCE_PATH}")
        ux_header, _ = table_after_heading(self.reference, "Project UX evidence matrix")
        capability_header, _ = table_after_heading(
            self.reference, "Per-capability matrix"
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

    def test_reference_requires_exact_output_sections_and_narrow_sources(self) -> None:
        for heading in (
            "`## Project UX evidence matrix`",
            "`## Per-capability matrix`",
        ):
            self.assertIn(heading, self.reference)
        for phrase in (
            "umbrella inventory",
            "host focus",
            "element focus",
            "narrowest exact",
            "{family=",
            "{gate=",
            "declaration-snippet",
            "search-scope",
            "inventory_aiui_capabilities.py",
            "unmatchedsymbols",
        ):
            self.assertIn(phrase, self.reference.lower())
        for path in (
            "documentation/1-framework/open-agent-format/target.en-US.md",
            "documentation/2-components/button.en-US.md",
            "samples/capabilities/pages/close/index.ink",
            "documentation/3-api/media/media-capture.en-US.md",
            "samples/capabilities/pages/media_devices/index.ink",
            "samples/capabilities/app.json",
            "documentation/1-framework/open-agent-format/page-events.en-US.md",
            "samples/capabilities/pages/chat/index.ink",
            "documentation/3-api/framework/page.en-US.md",
            "samples/capabilities/pages/head-gesture/index.ink",
        ):
            self.assertIn(path, self.reference)
        self.assertIn("samples/capabilities/app.json#L57", self.reference)
        self.assertRegex(
            self.reference,
            r"(?is)never copy the (?:whole|full).*(?:AIUI 0\.17|0\.17).*template",
        )
        self.assertRegex(
            self.reference,
            r"(?is)unqualified .voice.*family=input\.voice\.unknown.*"
            r"do not infer `onVoiceWakeup`.*`SpeechRecognition`.*manifest permission",
        )

    def test_runtime_permission_guidance_scopes_mixed_manifest_and_generic_voice(self) -> None:
        self.assertIn("samples/capabilities/app.json#L57", self.runtime_reference)
        self.assertRegex(
            self.runtime_reference,
            r"(?is)lines 5.54.*widget declarations.*never copy the full.*manifest",
        )
        self.assertRegex(
            self.runtime_reference,
            r"(?is)`RECORD_AUDIO`.*does not prove.*unqualified voice.*"
            r"SpeechRecognition.*`onVoiceWakeup`.*permission",
        )

    def test_forward_evaluation_preserves_every_required_matrix_column(self) -> None:
        self.assert_complete_evaluation_matrices(
            self.forward_evaluation,
            capability_contract_names=AUDIT_CAPABILITY_CONTRACTS,
            forbidden_results=frozenset({"PASS", "N/A"}),
            request_prompt=self.audit_prompt,
        )

    def test_forward_known_hardware_capabilities_link_runnable_samples(self) -> None:
        _, rows = table_after_heading(
            self.forward_evaluation, "Per-capability matrix"
        )
        row_by_id = {
            CAPABILITY_ID_RE.match(row[0]).group("identifier"): row
            for row in rows
        }

        def row_for_base(base_id: str) -> list[str]:
            matches = [
                row
                for identifier, row in row_by_id.items()
                if identifier == base_id or identifier.startswith(f"{base_id}-")
            ]
            self.assertEqual(1, len(matches), f"ambiguous/missing row for {base_id}")
            return matches[0]
        camera_rows = [
            row
            for row in rows
            if re.search(r"(?i)camera|media|相机", row[0])
        ]
        head_rows = [
            row
            for row in rows
            if re.search(r"(?i)head|nod|world awareness|点头", row[0])
        ]
        self.assertTrue(camera_rows)
        self.assertTrue(head_rows)
        for row in camera_rows:
            self.assertIn(
                "documentation/3-api/media/media-capture.en-US.md", row[4]
            )
        camera_permission_rows = [
            row for row in camera_rows if "permission" in row[0].lower()
        ]
        camera_runtime_rows = [
            row
            for row in camera_rows
            if "permission" not in row[0].lower()
            and re.search(r"(?i)media|runtime|lifecycle|调用|资源", row[0])
        ]
        self.assertTrue(camera_permission_rows)
        self.assertTrue(camera_runtime_rows)
        for row in camera_permission_rows:
            self.assertIn(
                "samples/capabilities/app.json#L57", row[4]
            )
        for row in camera_runtime_rows:
            self.assertIn(
                "samples/capabilities/pages/media_devices/index.ink", row[4]
            )
        for row in head_rows:
            self.assertIn(
                "samples/capabilities/pages/head-gesture/index.ink", row[4]
            )
        expected_sources = {
            "CAP-BUTTON": (
                "documentation/2-components/button.en-US.md",
                "samples/capabilities/pages/close/index.ink",
            ),
            "CAP-HEAD-GESTURE": (
                "documentation/3-api/framework/page.en-US.md",
                "samples/capabilities/pages/head-gesture/index.ink",
            ),
        }
        for capability_id, paths in expected_sources.items():
            with self.subTest(capability_id=capability_id):
                for path in paths:
                    self.assertIn(path, row_for_base(capability_id)[4])
        voice_row = row_for_base("CAP-VOICE")
        self.assertEqual("BLOCKED", voice_row[9])
        self.assertIn("{family=input.voice.unknown}", voice_row[0])
        self.assertIn("documentation/1-framework/open-agent-format", voice_row[4])
        self.assertIn("documentation/3-api/ai", voice_row[4])
        self.assertNotRegex(
            " ".join((voice_row[2], voice_row[3], voice_row[4])),
            r"(?i)onVoiceWakeup|SpeechRecognition|pages/(?:chat|speech)/",
        )

    def test_implementation_known_families_use_narrow_sources(self) -> None:
        _, rows = table_after_heading(
            self.implementation_forward_evaluation, "Per-capability matrix"
        )
        row_by_id = {
            CAPABILITY_ID_RE.match(row[0]).group("identifier"): row
            for row in rows
        }

        def row_for_base(base_id: str) -> list[str]:
            matches = [
                row
                for identifier, row in row_by_id.items()
                if identifier == base_id or identifier.startswith(f"{base_id}-")
            ]
            self.assertEqual(1, len(matches), f"ambiguous/missing row for {base_id}")
            return matches[0]
        expected_sources = {
            "CAP-VOICE": (
                "documentation/1-framework/open-agent-format",
                "documentation/3-api/ai",
            ),
            "CAP-INPUT-TOUCH-MIGRATION": (
                "documentation/2-components",
            ),
        }
        for capability_id, paths in expected_sources.items():
            with self.subTest(capability_id=capability_id):
                for path in paths:
                    self.assertIn(path, row_for_base(capability_id)[4])
        network_row = row_for_base("CAP-NETWORK")
        self.assertEqual("BLOCKED", network_row[9])
        self.assertIn("documentation/3-api/network", network_row[4])
        self.assertEqual(PROJECT_BINDING_UNRESOLVED, network_row[2])
        self.assertEqual(PROJECT_BINDING_UNRESOLVED, network_row[3])

    def test_implementation_change_pressure_still_delivers_both_matrices(self) -> None:
        self.assertTrue(
            IMPLEMENTATION_FORWARD_EVALUATION_PATH.is_file(),
            f"missing {IMPLEMENTATION_FORWARD_EVALUATION_PATH}",
        )
        self.assertIn(
            "Final status: BLOCKED", self.implementation_forward_evaluation
        )
        self.assertIn(
            "Release-ready: NO", self.implementation_forward_evaluation
        )
        self.assert_complete_evaluation_matrices(
            self.implementation_forward_evaluation,
            capability_contract_names=IMPLEMENTATION_CAPABILITY_CONTRACTS,
            forbidden_results=frozenset({"PASS", "N/A"}),
            request_prompt=self.implementation_prompt,
        )

    def test_ux_matrix_covers_aiui_interaction_and_optical_risks(self) -> None:
        _, rows = table_after_heading(self.reference, "Project UX evidence matrix")
        row_by_id = {
            UX_ID_RE.fullmatch(row[0]).group("identifier"): row
            for row in rows
            if row and UX_ID_RE.fullmatch(row[0])
        }
        identifiers = set(row_by_id)
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
        expected_terms = {
            "UX-TARGET": ("_current", "_blank", "transition"),
            "UX-STATE": ("loading", "empty", "success", "error"),
            "UX-TEXT": ("chinese", "english", "unicode", "overflow"),
            "UX-FOCUS": ("host", "element", "focus/blur"),
            "UX-INPUT": ("enter", "back", "voice", "gesture", "fallback"),
            "UX-RECOVERY": ("offline", "timeout", "denied", "retry", "recovery"),
            "UX-LIFECYCLE": ("hide/show", "unload", "cleanup"),
            "UX-VISUAL": ("luminance", "typography", "fill", "density"),
            "UX-ENVIRONMENT": ("bright", "dark", "cluttered", "optics"),
            "UX-MOTION": ("animation", "cold start", "endurance", "performance"),
        }
        for identifier, terms in expected_terms.items():
            with self.subTest(identifier=identifier):
                row = row_by_id[identifier]
                self.assertEqual(7, len(row))
                self.assertTrue(all(cell for cell in row))
                row_text = " ".join(row).lower()
                for term in terms:
                    self.assertIn(term, row_text)

    def test_design_reference_exposes_official_canvas_acceptance_thresholds(self) -> None:
        for phrase in (
            "16px horizontal safe inset",
            "12px vertical safe inset",
            "72% green luminance",
        ):
            self.assertIn(phrase, self.interaction_reference)
        self.assertIn(
            "explicitly marked `version: beta`",
            self.reference,
        )
        self.assertNotIn("official stable green design", self.reference)

    def test_evidence_layers_are_distinct_and_non_substitutable(self) -> None:
        header, rows = table_after_heading(self.reference, "Evidence ladder")
        self.assertEqual(["Layer", "Can establish", "Cannot establish"], header)
        layers = {row[0] for row in rows if row}
        self.assertEqual(
            {"SOURCE", "STATIC", "LOGIC", "AIX", "STUDIO", "DEVICE"},
            layers,
        )
        prohibition = re.search(
            r"(?is)an AIX/browser preview must not be used as proof of ([^.]+)\.",
            self.reference,
        )
        self.assertIsNotNone(prohibition)
        for term in ("focus", "keys", "voice", "gesture", "permission", "optics", "performance"):
            self.assertIn(term, prohibition.group(1).lower())

    def test_result_rules_prevent_missing_evidence_from_becoming_pass(self) -> None:
        for status in ("`PASS`", "`FAIL`", "`BLOCKED`", "`N/A`"):
            self.assertIn(status, self.reference)
        self.assertRegex(
            self.reference,
            r"(?is)`PASS`.*every named evidence layer.*executed.*"
            r"map every layer exactly once",
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
        self.assertRegex(
            self.reference,
            r"(?is)`PASS`.*LAYER=kind:locator.*source.*command.*log.*"
            r"screenshot.*recording.*artifact",
        )
        self.assertRegex(
            self.reference,
            r"(?is)`N/A`.*`SCOPE: source=manifest:<path>@sha256="
            r"<manifest-hash>#<entry>; claim=manifest:<path>@sha256="
            r"<manifest-hash>#<entry>`.*"
            r"lack of time.*credentials.*source.*execution.*hardware.*`BLOCKED`",
        )
        self.assertRegex(
            self.reference,
            r"(?is)`FAIL`.*uniquely suffixed `-FAIL` and `-BLOCKED` rows",
        )
        self.assertRegex(
            self.reference,
            r"(?is)`BLOCKED`.*LAYER=blocked:reason",
        )

    def test_capability_protocol_requires_source_negative_paths_and_cleanup(self) -> None:
        _, rows = table_after_heading(self.reference, "Per-capability matrix")
        self.assertGreaterEqual(len(rows), 1)
        for row in rows:
            self.assertEqual(11, len(row))
            self.assertTrue(all(cell for cell in row))
        capability_section = section_after_heading(
            self.reference, "Per-capability matrix"
        ).lower()
        self.assertNotIn("non-trivial", capability_section)
        self.assertRegex(
            capability_section,
            r"repeated instances may share a row only when their exact version.*"
            r"required evidence layers.*identical",
        )
        for phrase in (
            "template-bound event",
            "zero unaccounted items",
            "unique stable identifier",
            "[cap-network] {family=network.unknown}",
            "named provisional `blocked` row",
            "directory/index is allowed only as `search-scope`",
            "project-binding:unresolved",
            "stable instance or surface suffix before the final `-provisional`",
            "cap-unregistered-<key>",
        ):
            self.assertIn(phrase, capability_section)
        self.assertRegex(capability_section, r"every url is commit-pinned")
        self.assertRegex(
            capability_section,
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
            self.assertIn(term, capability_section)

    def test_reference_requires_one_structured_final_decision(self) -> None:
        decision = self.reference.split("## Required final decision", 1)[1].split(
            "## Execution order", 1
        )[0]
        for field in (
            "Final status: PASS | FAIL | BLOCKED",
            "Release-ready: YES | NO",
            "Reason:",
            "Required gates:",
            "Each field appears exactly once",
            "sole release decision",
        ):
            self.assertIn(field, decision)
        self.assertRegex(
            decision,
            r"(?is)precedence.*`FAIL`.*`BLOCKED`.*`PASS`",
        )
        self.assertIn(
            "the bracketed token only",
            decision.lower(),
        )
        self.assertIn("CAP-CAMERA-RUNTIME-FAIL@STATIC", decision)

    def test_reference_defines_unavailable_and_declared_surface_semantics(self) -> None:
        authority = section_after_heading(
            self.reference, "Authority and version boundary"
        )
        self.assertRegex(
            authority,
            r"(?is)exact project revision.*or.*`UNAVAILABLE`.*not supplied",
        )
        self.assertRegex(
            authority,
            r"(?is)supported surfaces.*only.*(?:declared|source-inspected).*"
            r"do not infer.*`_blank`",
        )
        result_contract = section_after_heading(
            self.reference, "Result contract"
        )
        self.assertRegex(
            result_contract,
            r"(?is)request.*(?:validator|unit test|AIX).*without.*schema-2.*`BLOCKED`",
        )

    def test_scenarios_remove_blind_audit_ambiguity(self) -> None:
        audit_scenario = AUDIT_SCENARIO_PATH.read_text(encoding="utf-8")
        implementation_scenario = IMPLEMENTATION_SCENARIO_PATH.read_text(
            encoding="utf-8"
        )
        for phrase in (
            "Project revision: UNAVAILABLE",
            "Import root: UNAVAILABLE",
            "Supported surfaces: UNAVAILABLE",
            "historical assertions are not executable evidence",
        ):
            self.assertIn(phrase, audit_scenario)
        for phrase in (
            "focus.element",
            "input.touch-migration.unknown",
            "input.voice.unknown",
            "historical assertions are not executable evidence",
        ):
            self.assertIn(phrase, implementation_scenario)

    def test_authority_section_pins_stable_and_current_version_boundaries(self) -> None:
        authority = section_after_heading(
            self.reference, "Authority and version boundary"
        )
        self.assertIn("88e70bb0382525c1a93ef077c2401dcc31a273ce", authority)
        self.assertIn("63bb5f5efa2f0c11a2defca35bc00777150f43d2", authority)
        self.assertRegex(
            authority,
            r"(?is)reuse its general testing discipline, not its feature availability",
        )
        self.assertRegex(
            authority,
            r"(?is)0\.17 target.*(?:widgets|agent workers).*gated",
        )

    def test_reference_emits_machine_parseable_source_roles_and_claim_schema(self) -> None:
        authority = section_after_heading(
            self.reference, "Authority and version boundary"
        )
        self.assertIn(
            '{"schemaVersion":1,"scopeClosed":true,"claims":[{"family":"<family>",'
            '"surface":"<surface>","description":"<description>"}]}',
            authority,
        )
        self.assertIn("do not wrap the role marker in backticks", self.reference.lower())
        self.assertNotRegex(
            self.reference,
            r"`(?:DOC|SAMPLE|SEARCH-SCOPE|DECLARATION-SNIPPET)=`?\[",
        )

    def test_reference_copies_every_validator_capability_behavior_contract(self) -> None:
        namespace = runpy.run_path(str(AUDIT_VALIDATOR_SCRIPT))
        contracts = namespace["CAPABILITY_BEHAVIOR_CONTRACTS"]
        tokens = namespace["CAPABILITY_CONTRACT_TOKENS"]
        self.assertEqual(set(contracts), set(tokens))
        for family, descriptions in contracts.items():
            with self.subTest(family=family):
                self.assertIn(f"| `{family}` |", self.reference)
                for path, description in zip(
                    ("positive", "negative-fallback", "lifecycle-cleanup"),
                    descriptions,
                ):
                    self.assertIn(
                        f"`{{contract={tokens[family]}}} {{path={path}}} "
                        f"{description}`",
                        self.reference,
                    )

    def test_scanner_and_audit_validator_policy_registries_stay_in_lockstep(self) -> None:
        scripts_directory = str(SKILL_ROOT / "scripts")
        sys.path.insert(0, scripts_directory)
        try:
            scanner = runpy.run_path(str(INVENTORY_SCRIPT))
        finally:
            sys.path.remove(scripts_directory)
        validator = runpy.run_path(str(AUDIT_VALIDATOR_SCRIPT))

        self.assertEqual(
            set(scanner["REGISTERED_POLICY_FAMILIES"]) | {"project.unregistered"},
            set(validator["CAPABILITY_POLICIES"]),
        )
        self.assertEqual(
            scanner["INPUT_KIND_BY_FAMILY"],
            validator["INPUT_KIND_BY_FAMILY"],
        )
        self.assertEqual(
            set(validator["INPUT_KIND_BY_FAMILY"]),
            set(validator["INPUT_FAMILIES"]),
        )
        self.assertTrue(
            set(validator["INPUT_KIND_BY_FAMILY"].values()).issubset(
                validator["INPUT_KINDS"]
            )
        )

    def test_reference_exposes_closed_ux_and_trust_contracts(self) -> None:
        for family in UX_FAMILIES:
            token = "ux-" + family.removeprefix("UX-").lower() + "-v1"
            self.assertIn(f"{{contract={token}}}", self.reference)
        for phrase in (
            "Inputs: none",
            "canonical SubjectPublicKeyInfo DER",
            "never executes it",
            "Exit `0` alone",
            "exit `2`",
            "exit `1`",
        ):
            self.assertIn(phrase, self.reference)
        for sentinel in ("HOST-MANAGED:", "HOST-DEFAULT:", "FRAMEWORK-MANAGED:"):
            self.assertNotIn(sentinel, self.reference)

    def test_implementation_change_evaluation_requires_current_reruns_and_failures(self) -> None:
        evaluation = self.implementation_forward_evaluation
        self.assertIn("Project revision: UNAVAILABLE", evaluation)
        self.assertIn("Final status: BLOCKED", evaluation)
        self.assertIn("Release-ready: NO", evaluation)
        self.assertGreaterEqual(
            evaluation.count("current-revision evidence not supplied"),
            10,
            "the blind audit must reject pre-change execution evidence instead of "
            "silently reusing it",
        )
        for pattern in (
            r"(?i)LOGIC",
            r"(?i)\bAIX\b",
            r"(?i)STUDIO",
            r"(?i)(?:DEVICE|GLASSES|真机)",
            r"(?i)(?:offline|离线)",
            r"(?i)(?:timeout|超时)",
            r"(?i)(?:malformed|畸形|异常)",
            r"(?i)(?:partial|部分)",
            r"(?i)(?:no[- ]match|无匹配)",
            r"(?i)(?:unavailable|不可用)",
            r"(?i)(?:repeated|重复)",
            r"(?i)fallback",
        ):
            with self.subTest(pattern=pattern):
                self.assertRegex(evaluation, pattern)


if __name__ == "__main__":
    unittest.main()
