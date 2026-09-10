#!/usr/bin/env python3
"""Fail-closed validator for a completed ROKID AIUI release audit.

The Markdown report is deliberately treated as untrusted input.  This command
re-inventories the Studio import root, checks the two closed matrices, and only
accepts executed evidence that is content-addressed below ``.aiui-evidence``.
Physical-device outcomes additionally require an externally supplied public key.
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unicodedata
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Optional


SCRIPT_DIRECTORY = Path(__file__).resolve().parent
INVENTORY_SCRIPT = SCRIPT_DIRECTORY / "inventory_aiui_capabilities.py"
FINGERPRINT_SCRIPT = SCRIPT_DIRECTORY / "fingerprint_aiui_project.py"
PROJECT_VALIDATOR_SCRIPT = SCRIPT_DIRECTORY / "validate_aiui_project.py"
EVIDENCE_DIRECTORY = ".aiui-evidence"
STABLE_AIUI_REVISION = "88e70bb0382525c1a93ef077c2401dcc31a273ce"
PREVIEW_AIUI_REVISION = "8b19a87b4ba8b486c0dd4dd3fd32290d27891069"
PROJECT_BINDING_UNRESOLVED = "PROJECT-BINDING:UNRESOLVED"

UX_HEADERS = (
    "ID",
    "Surface/state",
    "Risk",
    "Test",
    "Evidence layer",
    "Result",
    "Evidence",
)
CAPABILITY_HEADERS = (
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
HEADINGS = (
    "Project UX evidence matrix",
    "Per-capability matrix",
    "Final release decision",
)
METADATA_LABELS = (
    "Project revision",
    "Canonical version",
    "Import root",
    "Device/host",
    "Supported surfaces",
    "Inputs",
    "Claimed capabilities",
)
EVIDENCE_LAYERS = frozenset(
    {"SOURCE", "STATIC", "LOGIC", "AIX", "STUDIO", "DEVICE"}
)
INPUT_KINDS = frozenset(
    {
        "tap",
        "enter",
        "back",
        "key",
        "directional-scroll",
        "component-scroll",
        "scroll",
        "voice-wakeup",
        "speech",
        "voice",
        "head-gesture",
        "fallback",
        "touch-migration",
        "gesture-fallback",
    }
)
INPUT_FAMILIES = frozenset(
    {
        "event.bindtap",
        "input.enter",
        "input.back",
        "input.key.unknown",
        "input.scroll.host",
        "component.scroll-view",
        "input.scroll.unknown",
        "input.voice-wakeup",
        "ai.speech-recognition",
        "input.voice.unknown",
        "input.head-gesture",
        "input.fallback.unknown",
        "input.touch-migration.unknown",
        "input.gesture-fallback.unknown",
    }
)
INPUT_KIND_BY_FAMILY = {
    "event.bindtap": "tap",
    "input.enter": "enter",
    "input.back": "back",
    "input.key.unknown": "key",
    "input.scroll.host": "directional-scroll",
    "component.scroll-view": "component-scroll",
    "input.scroll.unknown": "scroll",
    "input.voice-wakeup": "voice-wakeup",
    "ai.speech-recognition": "speech",
    "input.voice.unknown": "voice",
    "input.head-gesture": "head-gesture",
    "input.fallback.unknown": "fallback",
    "input.touch-migration.unknown": "touch-migration",
    "input.gesture-fallback.unknown": "gesture-fallback",
}
SUPPORTED_SURFACES = frozenset(
    {"_current", "_blank", "Page", "Widget", "Agent Worker", "App"}
)
ALLOWED_RESULTS = frozenset({"PASS", "FAIL", "BLOCKED", "N/A"})
LAYER_ALLOWED_KINDS = {
    "SOURCE": frozenset({"source"}),
    "STATIC": frozenset({"source", "command", "log", "artifact"}),
    "LOGIC": frozenset({"command", "log", "artifact"}),
    "AIX": frozenset({"command", "screenshot", "recording"}),
    "STUDIO": frozenset({"log", "screenshot", "recording", "artifact"}),
    "DEVICE": frozenset({"log", "screenshot", "recording", "artifact"}),
}
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
UX_CONTRACT_TOKENS = {
    family: "ux-" + family.removeprefix("UX-").lower() + "-v1"
    for family in UX_REQUIRED_LAYERS
}
UX_APPLICABILITY_MODES = {
    "UX-TARGET": "declared-surface",
    "UX-STATE": "ui-surface",
    "UX-TEXT": "ui-surface",
    "UX-FOCUS": "focus-or-actionable",
    "UX-INPUT": "scanner-input",
    "UX-RECOVERY": "failure-capability",
    "UX-LIFECYCLE": "always",
    "UX-VISUAL": "ui-surface",
    "UX-ENVIRONMENT": "ui-surface",
    "UX-MOTION": "scope-conditional",
}
if set(UX_APPLICABILITY_MODES) != set(UX_REQUIRED_LAYERS):
    raise RuntimeError("UX applicability registry must equal UX layer policies")
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

PROVISIONAL_BEHAVIOR = (
    "The declared capability performs its claimed outcome once",
    "Unavailable, rejected, or ignored delivery preserves an explicit fallback",
    "Hide/show and unload do not retain stale capability work",
)
UNRESOLVED_BEHAVIOR = {
    "input.key.unknown": (
        "The intended key input performs exactly one owned action",
        "Unknown, ignored, or repeated key delivery preserves host defaults and a non-key fallback",
        "Hide/show and unload do not retain stale key handling",
    ),
    "input.scroll.unknown": (
        "The declared product intent affects only its owned target",
        "Unsupported or ignored scrolling preserves host behavior",
        "Repeated open does not duplicate scroll handling",
    ),
    "input.voice.unknown": (
        "The declared product intent is delivered once",
        "No-match, unavailable, repeated, and ignored input use a non-voice fallback",
        "Hide/show and unload do not retain stale voice work",
    ),
    "voice.declaration.unknown": (
        "The required declaration matches the inspected voice mechanism",
        "Missing, denied, or revoked access preserves a non-voice fallback",
        "Reopen reconciles the current declaration and access state",
    ),
    "input.fallback.unknown": (
        "The core task remains usable without the primary sensor",
        "Fallback failure leaves a clear exit without duplicate action",
        "Fallback remains available after hide/show and reopen",
    ),
    "input.touch-migration.unknown": (
        "The intended primary input performs exactly one owned action",
        "No stale touch binding, duplicate action, or dead end remains",
        "Repeated open does not restore obsolete bindings",
    ),
    "input.gesture-fallback.unknown": (
        "The core task remains usable without the gesture sensor",
        "Fallback failure leaves a clear exit without duplicate action",
        "Fallback remains available after hide/show and reopen",
    ),
    "network.unknown": (
        "The declared product outcome is delivered without stale updates",
        "Offline, timeout, malformed, and partial results recover with bounded retry",
        "Hide/show and unload cancel or reconcile retained network work",
    ),
}


@dataclass(frozen=True)
class CapabilityPolicy:
    base_id: str
    layers: frozenset[str]
    provisional: bool = False


ALL_LAYERS = frozenset(EVIDENCE_LAYERS)
SOURCE_STATIC_LOGIC_AIX_STUDIO = frozenset(
    {"SOURCE", "STATIC", "LOGIC", "AIX", "STUDIO"}
)
SOURCE_STATIC_LOGIC_STUDIO_DEVICE = frozenset(
    {"SOURCE", "STATIC", "LOGIC", "STUDIO", "DEVICE"}
)
SOURCE_STATIC_STUDIO_DEVICE = frozenset({"SOURCE", "STATIC", "STUDIO", "DEVICE"})

CAPABILITY_POLICIES = {
    "page.route": CapabilityPolicy("CAP-PAGE-ROUTE", SOURCE_STATIC_LOGIC_AIX_STUDIO),
    "page.target": CapabilityPolicy("CAP-PAGE-TARGET", ALL_LAYERS),
    "focus.host": CapabilityPolicy("CAP-HOST-FOCUS", SOURCE_STATIC_STUDIO_DEVICE),
    "focus.element": CapabilityPolicy("CAP-ELEMENT-FOCUS", SOURCE_STATIC_STUDIO_DEVICE),
    "ui.button": CapabilityPolicy(
        "CAP-BUTTON", frozenset({"SOURCE", "STATIC", "AIX", "STUDIO", "DEVICE"})
    ),
    "event.bindtap": CapabilityPolicy("CAP-BINDTAP", ALL_LAYERS),
    "input.enter": CapabilityPolicy("CAP-INPUT-ENTER", SOURCE_STATIC_LOGIC_STUDIO_DEVICE),
    "input.back": CapabilityPolicy("CAP-INPUT-BACK", SOURCE_STATIC_LOGIC_STUDIO_DEVICE),
    "input.key.unknown": CapabilityPolicy(
        "CAP-INPUT-KEY", SOURCE_STATIC_LOGIC_STUDIO_DEVICE, True
    ),
    "input.scroll.unknown": CapabilityPolicy(
        "CAP-INPUT-SCROLL", SOURCE_STATIC_LOGIC_STUDIO_DEVICE, True
    ),
    "input.voice.unknown": CapabilityPolicy(
        "CAP-VOICE", SOURCE_STATIC_LOGIC_STUDIO_DEVICE, True
    ),
    "voice.declaration.unknown": CapabilityPolicy(
        "CAP-VOICE-DECLARATION", SOURCE_STATIC_STUDIO_DEVICE, True
    ),
    "input.scroll.host": CapabilityPolicy(
        "CAP-INPUT-SCROLL-HOST", SOURCE_STATIC_LOGIC_STUDIO_DEVICE
    ),
    "component.scroll-view": CapabilityPolicy("CAP-SCROLL-VIEW", ALL_LAYERS),
    "input.voice-wakeup": CapabilityPolicy(
        "CAP-VOICE-WAKEUP", SOURCE_STATIC_LOGIC_STUDIO_DEVICE
    ),
    "ai.speech-recognition": CapabilityPolicy(
        "CAP-SPEECH-RECOGNITION", SOURCE_STATIC_LOGIC_STUDIO_DEVICE
    ),
    "input.fallback.unknown": CapabilityPolicy(
        "CAP-INPUT-FALLBACK", SOURCE_STATIC_LOGIC_STUDIO_DEVICE, True
    ),
    "input.touch-migration.unknown": CapabilityPolicy(
        "CAP-INPUT-TOUCH-MIGRATION", ALL_LAYERS, True
    ),
    "page.world-awareness": CapabilityPolicy(
        "CAP-WORLD-AWARENESS", SOURCE_STATIC_LOGIC_STUDIO_DEVICE
    ),
    "input.head-gesture": CapabilityPolicy(
        "CAP-HEAD-GESTURE", SOURCE_STATIC_LOGIC_STUDIO_DEVICE
    ),
    "input.gesture-fallback.unknown": CapabilityPolicy(
        "CAP-GESTURE-FALLBACK", SOURCE_STATIC_LOGIC_STUDIO_DEVICE, True
    ),
    "media.camera.permission": CapabilityPolicy(
        "CAP-CAMERA-PERMISSION", SOURCE_STATIC_STUDIO_DEVICE
    ),
    "media.camera.runtime": CapabilityPolicy(
        "CAP-CAMERA-RUNTIME", SOURCE_STATIC_LOGIC_STUDIO_DEVICE
    ),
    "media.camera.lifecycle": CapabilityPolicy(
        "CAP-CAMERA-LIFECYCLE", SOURCE_STATIC_LOGIC_STUDIO_DEVICE
    ),
    "network.unknown": CapabilityPolicy("CAP-NETWORK", ALL_LAYERS, True),
    "network.https": CapabilityPolicy("CAP-NETWORK-HTTPS", ALL_LAYERS),
    "network.sse": CapabilityPolicy("CAP-NETWORK-SSE", ALL_LAYERS),
    "network.websocket": CapabilityPolicy("CAP-NETWORK-WEBSOCKET", ALL_LAYERS),
    "page.lifecycle": CapabilityPolicy("CAP-PAGE-LIFECYCLE", ALL_LAYERS),
    "project.unregistered": CapabilityPolicy("CAP-UNREGISTERED", ALL_LAYERS, True),
    # AIUI 0.18 is inventory-only until a separate policy is published.  Fixed
    # IDs still prevent these preview shapes from being relabelled as 0.17 APIs.
    "widget.declaration": CapabilityPolicy("CAP-WIDGET-DECLARATION", ALL_LAYERS, True),
    "widget.lifecycle": CapabilityPolicy("CAP-WIDGET-LIFECYCLE", ALL_LAYERS, True),
    "agent-worker.declaration": CapabilityPolicy(
        "CAP-AGENT-WORKER-DECLARATION", ALL_LAYERS, True
    ),
    "agent-worker.capability": CapabilityPolicy(
        "CAP-AGENT-WORKER-CAPABILITY", ALL_LAYERS, True
    ),
    "agent-worker.on-open": CapabilityPolicy(
        "CAP-AGENT-WORKER-ON-OPEN", ALL_LAYERS, True
    ),
    "agent-worker.wait-until": CapabilityPolicy(
        "CAP-AGENT-WORKER-WAIT-UNTIL", ALL_LAYERS, True
    ),
}
FAILURE_CAPABILITY_FAMILIES = frozenset(
    {
        "ai.speech-recognition",
        "input.voice-wakeup",
        "input.voice.unknown",
        "voice.declaration.unknown",
        "input.fallback.unknown",
        "input.touch-migration.unknown",
        "page.world-awareness",
        "input.head-gesture",
        "input.gesture-fallback.unknown",
    }
)
if not FAILURE_CAPABILITY_FAMILIES.issubset(CAPABILITY_POLICIES):
    raise RuntimeError("failure capability registry must stay within capability policies")
CAPABILITY_CONTRACT_TOKENS = {
    family: "cap-" + family.replace(".", "-") + "-v1"
    for family in CAPABILITY_POLICIES
}
CAPABILITY_BEHAVIOR_CONTRACTS = {
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
    "focus.host": (
        "Host focus enters and leaves the Page at the documented boundaries",
        "Blurred or unavailable host focus cannot trigger an unfocused action and preserves a usable return",
        "Hide/show and unload reconcile host focus without stale callbacks",
    ),
    "focus.element": (
        "Each actionable element exposes focus and activation in the intended order",
        "Missing, trapped, or blurred element focus preserves a visible recovery path",
        "Repeated render and reopen do not retain stale element focus handlers",
    ),
    "ui.button": (
        "The button exposes and performs its intended action",
        "Disabled, unavailable, or repeated activation remains explicit and recoverable",
        "Repeated render and reopen preserve one current button action",
    ),
    "event.bindtap": (
        "One owned tap invokes the bound action exactly once",
        "Ignored, repeated, or unavailable tap delivery does not duplicate or dead-end the action",
        "Hide/show and unload do not retain stale tap handlers or work",
    ),
    "input.enter": (
        "One owned Enter input invokes the intended action exactly once",
        "Ignored or repeated Enter input preserves host defaults and a non-key fallback",
        "Hide/show and unload do not retain stale Enter handling",
    ),
    "input.back": (
        "One owned Back input performs the intended navigation or dismissal",
        "Ignored or repeated Back input preserves host defaults and a usable exit",
        "Hide/show and unload do not retain stale Back handling",
    ),
    "input.key.unknown": UNRESOLVED_BEHAVIOR["input.key.unknown"],
    "input.scroll.unknown": UNRESOLVED_BEHAVIOR["input.scroll.unknown"],
    "input.voice.unknown": UNRESOLVED_BEHAVIOR["input.voice.unknown"],
    "voice.declaration.unknown": UNRESOLVED_BEHAVIOR["voice.declaration.unknown"],
    "input.scroll.host": (
        "Owned directional input scrolls only the intended content by a bounded amount",
        "Boundary, ignored, and repeated scrolling preserve host behavior without trapping input",
        "Hide/show and unload do not retain stale directional scroll handling",
    ),
    "component.scroll-view": (
        "The scroll-view reveals intended overflow while preserving fixed actions",
        "Empty, short, boundary, and excessive content remain readable and recoverable",
        "Repeated render and reopen restore a valid bounded scroll state",
    ),
    "input.voice-wakeup": (
        "One voice-wakeup delivery invokes the owned action exactly once",
        "No-match, unavailable, repeated, and ignored delivery preserve a non-voice fallback",
        "Hide/show and unload do not retain stale voice-wakeup work",
    ),
    "ai.speech-recognition": (
        "A started recognition session delivers one current transcript outcome",
        "No-match, denial, unavailability, error, and repeated delivery preserve a non-voice fallback",
        "Hide/show and unload stop or reconcile every recognition session and listener",
    ),
    "input.fallback.unknown": UNRESOLVED_BEHAVIOR["input.fallback.unknown"],
    "input.touch-migration.unknown": UNRESOLVED_BEHAVIOR[
        "input.touch-migration.unknown"
    ],
    "page.world-awareness": (
        "World awareness enables only for the owned Page and intended interaction",
        "Unsupported, denied, or unavailable awareness preserves a non-sensor fallback",
        "Hide/show and unload disable or reconcile every awareness subscription",
    ),
    "input.head-gesture": (
        "One supported head gesture invokes the owned action exactly once",
        "Ignored, unavailable, repeated, and unsupported gestures preserve a non-sensor fallback",
        "Hide/show and unload remove or reconcile gesture subscriptions and awareness state",
    ),
    "input.gesture-fallback.unknown": UNRESOLVED_BEHAVIOR[
        "input.gesture-fallback.unknown"
    ],
    "media.camera.permission": (
        "The declared CAMERA permission matches the camera behavior used by the project",
        "Missing, denied, or revoked permission preserves an explicit non-camera fallback",
        "Reopen reconciles the current permission state without assuming prior access",
    ),
    "media.camera.runtime": (
        "A granted camera request yields only the intended current video stream",
        "Denial, unavailability, constraint failure, and runtime error preserve an explicit fallback",
        "Hide/show and unload stop or reconcile every acquired camera track",
    ),
    "media.camera.lifecycle": (
        "Every acquired camera track is owned by one current Page lifecycle",
        "Partial setup, revocation, and stop failure preserve explicit cleanup and recovery",
        "Hide/show and unload stop all tracks without retaining camera resources",
    ),
    "network.unknown": UNRESOLVED_BEHAVIOR["network.unknown"],
    "network.https": (
        "A successful HTTPS request updates only the current intended state",
        "Offline, timeout, malformed, partial, and rejected responses use bounded retry and recovery",
        "Hide/show and unload cancel or reconcile every retained HTTPS request",
    ),
    "network.sse": (
        "A connected event stream applies each current event exactly once and in order",
        "Offline, timeout, malformed, partial, and disconnected streams use bounded recovery",
        "Hide/show and unload close or reconcile every EventSource and listener",
    ),
    "network.websocket": (
        "A connected socket sends and applies only messages for the current session",
        "Offline, timeout, malformed, partial, rejected, and closed sockets use bounded recovery",
        "Hide/show and unload close or reconcile every socket and listener",
    ),
    "page.lifecycle": (
        "Page callbacks establish the intended state once in documented lifecycle order",
        "Repeated, interrupted, and out-of-date work cannot overwrite the current Page state",
        "Hide/show and unload reconcile or release all Page-owned retained work",
    ),
    "project.unregistered": PROVISIONAL_BEHAVIOR,
    "widget.declaration": (
        "The declared Widget path and family resolve to the intended Widget definition",
        "Missing, invalid, unsupported, or mismatched declarations remain blocked with an explicit fallback",
        "Repeated host attach and reopen resolve one current Widget declaration",
    ),
    "widget.lifecycle": (
        "Widget create and attach establish the intended glanceable state once",
        "Interrupted, repeated, detached, and unavailable Widget states remain recoverable",
        "Detach and destroy release all Widget-owned retained work",
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
if set(CAPABILITY_BEHAVIOR_CONTRACTS) != set(CAPABILITY_POLICIES):
    raise RuntimeError("capability behavior registry must equal capability policies")


def stable_blob(path: str) -> str:
    return f"https://github.com/yodaos-project/AIUI/blob/{STABLE_AIUI_REVISION}/{path}"


def stable_tree(path: str) -> str:
    return f"https://github.com/yodaos-project/AIUI/tree/{STABLE_AIUI_REVISION}/{path}"


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

CAPABILITY_SOURCE_POLICIES = {
    "page.route": frozenset({("DOC", stable_blob(APP_JSON_DOC))}),
    "page.target": frozenset({("DOC", stable_blob(TARGET_DOC))}),
    "focus.host": frozenset({("DOC", stable_blob(FOCUS_DOC))}),
    "focus.element": frozenset({("DOC", stable_blob(FOCUS_DOC))}),
    "ui.button": frozenset(
        {("DOC", stable_blob(BUTTON_DOC)), ("SAMPLE", stable_blob(BUTTON_SAMPLE))}
    ),
    "event.bindtap": frozenset(
        {("DOC", stable_blob(BUTTON_DOC)), ("SAMPLE", stable_blob(BUTTON_SAMPLE))}
    ),
    "input.enter": frozenset({("DOC", stable_blob(PAGE_EVENTS_DOC))}),
    "input.back": frozenset({("DOC", stable_blob(PAGE_EVENTS_DOC))}),
    "input.key.unknown": frozenset({("DOC", stable_blob(PAGE_EVENTS_DOC))}),
    "input.scroll.host": frozenset({("DOC", stable_blob(PAGE_EVENTS_DOC))}),
    "input.scroll.unknown": frozenset(
        {
            ("SEARCH-SCOPE", stable_tree(OPEN_AGENT_INDEX)),
            ("SEARCH-SCOPE", stable_tree(COMPONENT_INDEX)),
        }
    ),
    "input.voice.unknown": frozenset(
        {
            ("SEARCH-SCOPE", stable_tree(OPEN_AGENT_INDEX)),
            ("SEARCH-SCOPE", stable_tree(AI_INDEX)),
        }
    ),
    "voice.declaration.unknown": frozenset(
        {
            ("SEARCH-SCOPE", stable_tree(OPEN_AGENT_INDEX)),
            ("SEARCH-SCOPE", stable_tree(AI_INDEX)),
        }
    ),
    "input.fallback.unknown": frozenset(
        {
            ("SEARCH-SCOPE", stable_tree(OPEN_AGENT_INDEX)),
            ("SEARCH-SCOPE", stable_tree(COMPONENT_INDEX)),
        }
    ),
    "input.touch-migration.unknown": frozenset(
        {("SEARCH-SCOPE", stable_tree(COMPONENT_INDEX))}
    ),
    "input.gesture-fallback.unknown": frozenset(
        {
            ("SEARCH-SCOPE", stable_tree(OPEN_AGENT_INDEX)),
            ("SEARCH-SCOPE", stable_tree(COMPONENT_INDEX)),
        }
    ),
    "component.scroll-view": frozenset({("DOC", stable_blob(SCROLL_VIEW_DOC))}),
    "page.lifecycle": frozenset({("DOC", stable_blob(PAGE_API_DOC))}),
    "input.voice-wakeup": frozenset(
        {("DOC", stable_blob(PAGE_EVENTS_DOC)), ("SAMPLE", stable_blob(VOICE_SAMPLE))}
    ),
    "ai.speech-recognition": frozenset(
        {("DOC", stable_blob(SPEECH_DOC)), ("SAMPLE", stable_blob(SPEECH_SAMPLE))}
    ),
    "page.world-awareness": frozenset(
        {("DOC", stable_blob(PAGE_API_DOC)), ("SAMPLE", stable_blob(HEAD_SAMPLE))}
    ),
    "input.head-gesture": frozenset(
        {("DOC", stable_blob(PAGE_API_DOC)), ("SAMPLE", stable_blob(HEAD_SAMPLE))}
    ),
    "media.camera.permission": frozenset(
        {
            ("DOC", stable_blob(MEDIA_DOC)),
            ("DECLARATION-SNIPPET", stable_blob(PERMISSION_MANIFEST) + "#L57"),
        }
    ),
    "media.camera.runtime": frozenset(
        {
            ("DOC", stable_blob(MEDIA_DOC)),
            ("SAMPLE", stable_blob(MEDIA_SAMPLE)),
            ("DECLARATION-SNIPPET", stable_blob(PERMISSION_MANIFEST) + "#L57"),
        }
    ),
    "media.camera.lifecycle": frozenset(
        {
            ("DOC", stable_blob(MEDIA_DOC)),
            ("SAMPLE", stable_blob(MEDIA_SAMPLE)),
            ("DECLARATION-SNIPPET", stable_blob(PERMISSION_MANIFEST) + "#L57"),
        }
    ),
    "network.unknown": frozenset({("SEARCH-SCOPE", stable_tree(NETWORK_INDEX))}),
    "network.https": frozenset(
        {("DOC", stable_blob(HTTPS_DOC)), ("SAMPLE", stable_blob(HTTPS_SAMPLE))}
    ),
    "network.sse": frozenset(
        {("DOC", stable_blob(SSE_DOC)), ("SAMPLE", stable_blob(SSE_SAMPLE))}
    ),
    "network.websocket": frozenset(
        {
            ("DOC", stable_blob(WEBSOCKET_DOC)),
            ("SAMPLE", stable_blob(WEBSOCKET_SAMPLE)),
        }
    ),
    "project.unregistered": frozenset(
        {
            ("SEARCH-SCOPE", stable_tree("documentation")),
            ("SEARCH-SCOPE", stable_tree("samples")),
        }
    ),
}

UX_ID_RE = re.compile(
    r"^`?\[(?P<identifier>UX-[A-Z0-9-]+)\]`?\s+"
    r"\{gate=(?P<gate>[a-z0-9][a-z0-9_.-]*)\}`?$"
)
CAPABILITY_ID_RE = re.compile(
    r"^`?\[(?P<identifier>CAP-[A-Z0-9-]+)\]`?\s+"
    r"\{family=(?P<family>[a-z0-9][a-z0-9_.-]*)\}\s+"
    r"\{gate=(?P<gate>[a-z0-9][a-z0-9_.-]*)\}`?\s+(?P<label>.+)$"
)
EVIDENCE_ENTRY_RE = re.compile(
    r"^(?P<layer>SOURCE|STATIC|LOGIC|AIX|STUDIO|DEVICE)="
    r"(?P<kind>source|command|log|screenshot|recording|artifact|blocked):"
    r"(?P<locator>\S.*)$"
)
MANIFEST_LOCATOR_RE = re.compile(
    r"^manifest:(?P<path>[^\s#]+)@sha256=(?P<digest>[0-9a-f]{64})#"
    r"(?P<entry>[A-Za-z0-9][A-Za-z0-9._-]*)$"
)
SOURCE_ENTRY_RE = re.compile(
    r"^(?P<role>DOC|SAMPLE|DECLARATION-SNIPPET|SEARCH-SCOPE)="
    r"\[(?P<label>[^\]]+)\]\((?P<url>https://[^)\s]+)\)$"
)
PINNED_SOURCE_RE = re.compile(
    r"^https://github\.com/yodaos-project/AIUI/(?P<kind>blob|tree)/"
    r"(?P<revision>[0-9a-f]{40})/(?P<path>[^?#\s]+)(?:#(?P<fragment>[^?\s]+))?$"
)
INVALID_EXECUTED_RE = re.compile(
    r"(?is)(?:^|\b)(?:none|n/?a|missing|unverified|not tested|not provided|"
    r"not executed|fake|fabricated|made[- ]?up|blocked)(?:\b|$)|"
    r"无真机|无设备|无证据|未提供|未执行|未测试|未验证|伪造|虚构|"
    r"仅(?:口头|声称|陈述)|待(?:执行|验证|补充|检查|核对)"
)
RELEASE_CLAIM_RE = re.compile(
    r"(?is)\*\*PASS\*\*|release[- ]?ready|ready to release|"
    r"approved for release|ship now|production[- ]?ready|\bLGTM\b|"
    r"开发完成|已完成|可以发布|可发布|可以上线|可上线|可交付"
)


class AuditValidationError(ValueError):
    """One closed-contract rule failed."""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AuditValidationError(message)


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def normalized(value: str) -> str:
    return " ".join(value.split())


def capability_contract_cell(family: str, path: str, description: str) -> str:
    token = CAPABILITY_CONTRACT_TOKENS[family]
    return f"{{contract={token}}} {{path={path}}} {description}"


def is_provisional_capability_id(identifier: str, base_id: str) -> bool:
    """Allow a stable instance discriminator before the final marker."""

    return (
        re.fullmatch(
            re.escape(base_id)
            + r"(?:-(?!PROVISIONAL(?:-|$))[A-Z0-9]+)*-PROVISIONAL",
            identifier,
        )
        is not None
    )


def strict_json(data: bytes, description: str) -> dict[str, Any]:
    def reject_duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in pairs:
            if key in result:
                raise AuditValidationError(
                    f"{description} contains duplicate JSON key {key!r}"
                )
            result[key] = value
        return result

    try:
        value = json.loads(data.decode("utf-8"), object_pairs_hook=reject_duplicates)
    except AuditValidationError:
        raise
    except (UnicodeError, json.JSONDecodeError, ValueError) as error:
        raise AuditValidationError(f"invalid {description}: {error}") from error
    require(isinstance(value, dict), f"{description} root must be an object")
    return value


def split_markdown_row(line: str) -> list[str]:
    stripped = line.strip()
    require(
        stripped.startswith("|") and stripped.endswith("|"),
        f"table line must start and end with |: {line}",
    )
    cells: list[str] = []
    current: list[str] = []
    escaped = False
    for character in stripped[1:-1]:
        if escaped:
            current.append(character)
            escaped = False
        elif character == "\\":
            escaped = True
        elif character == "|":
            cells.append("".join(current).strip())
            current = []
        else:
            current.append(character)
    require(not escaped, "table row ends with an invalid escape")
    cells.append("".join(current).strip())
    return cells


def parse_table(section: str, expected_headers: tuple[str, ...], name: str) -> list[list[str]]:
    lines = [line.strip() for line in section.splitlines() if line.strip()]
    require(len(lines) >= 3, f"{name} must contain one complete Markdown table")
    require(all(line.startswith("|") for line in lines), f"prose is not allowed in {name}")
    header = split_markdown_row(lines[0])
    require(tuple(header) == expected_headers, f"{name} headers must be exact")
    separator = split_markdown_row(lines[1])
    require(len(separator) == len(header), f"{name} separator width is invalid")
    require(
        all(re.fullmatch(r":?-{3,}:?", cell) for cell in separator),
        f"{name} separator row is invalid",
    )
    rows = [split_markdown_row(line) for line in lines[2:]]
    require(rows, f"{name} must contain at least one row")
    for row in rows:
        require(len(row) == len(header), f"{name} row has the wrong number of cells")
        require(all(cell.strip() for cell in row), f"{name} contains an empty cell")
    return rows


def parse_layers(value: str, description: str) -> tuple[str, ...]:
    layers = tuple(part.strip() for part in value.split(","))
    require(all(layers), f"{description} contains an empty evidence layer")
    require(len(layers) == len(set(layers)), f"{description} repeats an evidence layer")
    require(set(layers).issubset(EVIDENCE_LAYERS), f"{description} names an unknown layer")
    return layers


def parse_sorted_ledger(value: str, pattern: str, description: str) -> list[str]:
    if value == "":
        return []
    entries = value.split(",")
    require(entries == sorted(entries), f"{description} must use ASCII sort order")
    require(len(entries) == len(set(entries)), f"{description} contains duplicates")
    for entry in entries:
        require(re.fullmatch(pattern, entry) is not None, f"invalid {description} entry: {entry}")
    return entries


def resolve_relative_directory(repository_root: Path, value: str, description: str) -> Path:
    require(value.strip() == value and value, f"{description} must be a non-empty relative path")
    require(not Path(value).is_absolute(), f"{description} must be repository-relative")
    require("\\" not in value, f"{description} must use POSIX separators")
    require(re.search(r"(?i)%2e|[\x00-\x1f\x7f]", value) is None, f"unsafe {description}")
    require(".." not in Path(value).parts, f"{description} cannot traverse the repository")
    candidate = repository_root / value
    current = repository_root
    for part in Path(value).parts:
        current = current / part
        require(not current.is_symlink(), f"{description} contains a symlink: {value}")
    try:
        resolved = candidate.resolve(strict=True)
        resolved.relative_to(repository_root.resolve())
    except (OSError, ValueError) as error:
        raise AuditValidationError(f"invalid {description}: {value}") from error
    require(resolved.is_dir(), f"{description} is not a directory: {value}")
    return resolved


def resolve_evidence_file(repository_root: Path, value: Any, description: str) -> Path:
    require(isinstance(value, str) and value, f"{description} path must be a string")
    require(not Path(value).is_absolute(), f"{description} path must be repository-relative")
    require("\\" not in value, f"{description} path must use POSIX separators")
    require(re.search(r"(?i)%2e|[\x00-\x1f\x7f]", value) is None, f"unsafe {description} path")
    parts = Path(value).parts
    require(parts and parts[0] == EVIDENCE_DIRECTORY, f"{description} must stay under {EVIDENCE_DIRECTORY}/")
    require("." not in parts and ".." not in parts, f"unsafe {description} path")
    current = repository_root
    for part in parts:
        current = current / part
        require(not current.is_symlink(), f"{description} path contains a symlink: {value}")
    try:
        resolved = (repository_root / value).resolve(strict=True)
        resolved.relative_to(repository_root.resolve())
    except (OSError, ValueError) as error:
        raise AuditValidationError(f"{description} path does not exist safely: {value}") from error
    require(resolved.is_file(), f"{description} is not a regular file: {value}")
    require(resolved.stat().st_size > 0, f"{description} is empty: {value}")
    return resolved


def stable_read(path: Path, description: str) -> bytes:
    before = path.stat()
    data = path.read_bytes()
    after = path.stat()
    identity_before = (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns)
    identity_after = (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns)
    require(identity_before == identity_after, f"{description} changed while being read")
    return data


def run_json_tool(arguments: list[str], cwd: Path, description: str) -> dict[str, Any]:
    completed = subprocess.run(
        arguments,
        cwd=cwd,
        text=True,
        capture_output=True,
        check=False,
    )
    require(
        completed.returncode == 0,
        f"{description} failed: {completed.stderr.strip() or completed.stdout.strip()}",
    )
    return strict_json(completed.stdout.encode("utf-8"), description)


def current_inventory(repository_root: Path, import_path: Path, version: str) -> dict[str, Any]:
    report = run_json_tool(
        [
            sys.executable,
            str(INVENTORY_SCRIPT),
            str(import_path),
            "--target-version",
            version,
            "--repository-root",
            str(repository_root),
        ],
        repository_root,
        "AIUI capability inventory",
    )
    require(type(report.get("schemaVersion")) is int, "inventory schemaVersion must be integer 2")
    require(report.get("schemaVersion") == 2, "inventory schemaVersion must be 2")
    require(
        set(report)
        == {
            "schemaVersion",
            "targetVersion",
            "policyVersion",
            "projectRevision",
            "items",
            "claimedCapabilities",
            "unmatchedSymbols",
            "versionViolations",
            "claimsLedger",
            "supportedSurfaces",
            "inputGates",
        },
        "inventory schema-2 fields are not exact",
    )
    require(report.get("targetVersion") == version, "inventory targetVersion changed")
    for field in ("items", "claimedCapabilities", "unmatchedSymbols", "versionViolations"):
        require(isinstance(report.get(field), list), f"inventory {field} must be an array")
    require(report["versionViolations"] == [], "inventory versionViolations must be empty")
    surfaces = report["supportedSurfaces"]
    require(isinstance(surfaces, list), "inventory supportedSurfaces must be an array")
    require(surfaces == sorted(set(surfaces)), "inventory supportedSurfaces must be sorted and unique")
    require(
        all(
            isinstance(surface, str)
            and surface == surface.strip()
            and surface in SUPPORTED_SURFACES
            for surface in surfaces
        ),
        "inventory supportedSurfaces contains an invalid token",
    )
    claims_ledger = report["claimsLedger"]
    require(
        isinstance(claims_ledger, dict)
        and set(claims_ledger)
        == {"path", "present", "scopeClosed", "sha256", "claimCount"},
        "inventory claims ledger schema is not exact",
    )
    require(
        claims_ledger.get("path") == "aiui-audit-claims.json"
        and claims_ledger.get("present") is True
        and claims_ledger.get("scopeClosed") is True,
        "a present, scope-closed claims ledger is required",
    )
    claims_path = import_path / "aiui-audit-claims.json"
    require(claims_path.is_file() and not claims_path.is_symlink(), "claims ledger is not a regular file")
    claims_bytes = stable_read(claims_path, "claims ledger")
    require(
        re.fullmatch(r"[0-9a-f]{64}", str(claims_ledger.get("sha256", "")))
        is not None
        and claims_ledger["sha256"] == sha256(claims_bytes),
        "claims ledger SHA-256 does not match source",
    )
    claims_document = strict_json(claims_bytes, "claims ledger")
    require(
        set(claims_document) == {"schemaVersion", "scopeClosed", "claims"}
        and type(claims_document.get("schemaVersion")) is int
        and claims_document["schemaVersion"] == 1
        and claims_document.get("scopeClosed") is True
        and isinstance(claims_document.get("claims"), list)
        and type(claims_ledger.get("claimCount")) is int
        and claims_ledger["claimCount"] == len(claims_document["claims"]),
        "claims ledger content does not match the closed inventory summary",
    )
    claims = report["claimedCapabilities"]
    require(claims == sorted(claims), "inventory claimedCapabilities is not sorted")
    require(len(claims) == len(set(claims)), "inventory claimedCapabilities contains duplicates")
    item_claims: list[str] = []
    item_by_claim: dict[str, dict[str, Any]] = {}
    for item in report["items"]:
        require(isinstance(item, dict), "inventory item must be an object")
        require(
            set(item)
            == {
                "family",
                "gate",
                "mechanism",
                "apiBinding",
                "declarationBinding",
                "policyState",
                "versionFeature",
                "locations",
            },
            "inventory item fields are not exact",
        )
        family, gate = item.get("family"), item.get("gate")
        require(
            isinstance(family, str)
            and isinstance(gate, str)
            and re.fullmatch(r"[a-z0-9][a-z0-9_.-]*", family) is not None
            and re.fullmatch(r"[a-z0-9][a-z0-9_.-]*", gate) is not None,
            "inventory item has an invalid family/gate",
        )
        for binding in ("apiBinding", "declarationBinding", "policyState"):
            require(
                isinstance(item.get(binding), str) and item[binding],
                f"inventory item lacks {binding}",
            )
        claim = f"{family}@{gate}"
        item_claims.append(claim)
        item_by_claim[claim] = item
    require(
        sorted(item_claims) == claims,
        "inventory claimedCapabilities must equal all and only inventory items",
    )
    claim_set = set(claims)
    input_gates = report["inputGates"]
    require(isinstance(input_gates, list), "inventory inputGates must be an array")
    input_identities: list[tuple[str, str, str]] = []
    input_selectors: list[str] = []
    for entry in input_gates:
        require(
            isinstance(entry, dict) and set(entry) == {"family", "kind", "gate"},
            "inventory input gate fields are not exact",
        )
        family, kind, gate = entry.get("family"), entry.get("kind"), entry.get("gate")
        require(kind in INPUT_KINDS and kind != "combined", "inventory contains an invalid or combined input kind")
        selector = f"{family}@{gate}"
        require(selector in claim_set and family in INPUT_FAMILIES, "inventory input gate lacks its capability item")
        require(
            kind == INPUT_KIND_BY_FAMILY[family],
            "inventory input kind does not match its family",
        )
        input_identities.append((str(kind), str(gate), str(family)))
        input_selectors.append(selector)
    require(
        input_identities == sorted(set(input_identities)),
        "inventory inputGates must be sorted and unique",
    )
    require(len(input_selectors) == len(set(input_selectors)), "one capability item cannot back multiple input gates")
    expected_input_selectors = sorted(
        selector
        for selector, item in item_by_claim.items()
        if item.get("family") in INPUT_FAMILIES
    )
    require(
        sorted(input_selectors) == expected_input_selectors,
        "inventory inputGates must equal all and only input capability items",
    )
    unmatched_by_gate: dict[str, dict[str, Any]] = {}
    for unmatched in report["unmatchedSymbols"]:
        require(isinstance(unmatched, dict), "inventory unmatchedSymbols item must be an object")
        require(
            set(unmatched) == {"symbol", "family", "gate", "path", "line", "column"},
            "inventory unmatched symbol fields are not exact",
        )
        selector = f"{unmatched.get('family')}@{unmatched.get('gate')}"
        require(selector in claim_set, "unmatched inventory symbol lacks a quarantined capability item")
        require(unmatched.get("family") == "project.unregistered", "unmatched symbol must be quarantined")
        require(str(unmatched.get("gate")) not in unmatched_by_gate, "duplicate unmatched symbol gate")
        unmatched_by_gate[str(unmatched.get("gate"))] = unmatched
    unregistered_items = {
        str(item["gate"]): item
        for item in report["items"]
        if item.get("family") == "project.unregistered"
    }
    require(
        set(unmatched_by_gate) == set(unregistered_items),
        "unmatched symbols and project.unregistered items must map one-to-one",
    )
    for gate, unmatched in unmatched_by_gate.items():
        item = unregistered_items[gate]
        locations = item.get("locations")
        require(isinstance(locations, list) and len(locations) == 1, "quarantine item must have one source location")
        location = locations[0]
        mechanism = str(item.get("mechanism"))
        expected_symbol = mechanism[:-5] if mechanism.endswith("(...)") else mechanism
        require(
            isinstance(location, dict)
            and unmatched.get("symbol") == expected_symbol
            and unmatched.get("path") == location.get("path")
            and unmatched.get("line") == location.get("line")
            and unmatched.get("column") == location.get("column"),
            "unmatched symbol does not exactly bind its quarantine item",
        )
    return report


def validate_project_structure(
    repository_root: Path, import_path: Path, version: str
) -> None:
    completed = subprocess.run(
        [
            sys.executable,
            str(PROJECT_VALIDATOR_SCRIPT),
            str(import_path),
            "--repository-root",
            str(repository_root),
            "--target-version",
            version,
            "--strict",
            "--json",
        ],
        cwd=repository_root,
        text=True,
        capture_output=True,
        check=False,
    )
    payload = strict_json(
        completed.stdout.encode("utf-8"), "strict AIUI project validation"
    )
    require(
        set(payload)
        == {
            "valid",
            "strict",
            "targetVersion",
            "errorCount",
            "warningCount",
            "diagnostics",
        },
        "strict AIUI project validation schema is not exact",
    )
    require(payload.get("strict") is True, "AIUI project validator did not run in strict mode")
    require(
        payload.get("targetVersion") == version,
        "AIUI project validator targetVersion changed",
    )
    diagnostics = payload.get("diagnostics")
    require(
        isinstance(diagnostics, list),
        "strict AIUI project validation diagnostics must be an array",
    )
    diagnostic_codes = [
        str(item.get("code", "UNKNOWN"))
        for item in diagnostics
        if isinstance(item, dict)
    ]
    detail = ",".join(diagnostic_codes) or completed.stderr.strip() or "unknown failure"
    require(
        completed.returncode == 0 and payload.get("valid") is True,
        f"strict AIUI project validation failed: {detail}",
    )


def verify_commit_tree(repository_root: Path, import_path: Path, revision: str) -> None:
    repository = repository_root.resolve()

    def is_reserved(path: Path) -> bool:
        try:
            relative = path.relative_to(repository)
        except ValueError:
            return False
        return bool(
            relative.parts
            and relative.parts[0].lower() in {".git", EVIDENCE_DIRECTORY}
        )

    def git(*arguments: str) -> subprocess.CompletedProcess[bytes]:
        return subprocess.run(
            ["git", *arguments], cwd=repository_root, capture_output=True, check=False
        )

    commit = git("cat-file", "-e", f"{revision}^{{commit}}")
    require(commit.returncode == 0, f"unresolvable project commit: {revision}")
    try:
        relative_root = import_path.relative_to(repository_root.resolve()).as_posix()
    except ValueError as error:
        raise AuditValidationError("import root escapes repository") from error
    tree = git("ls-tree", "-r", "-z", revision, "--", relative_root)
    require(tree.returncode == 0, "cannot inspect project commit tree")
    prefix = "" if relative_root == "." else relative_root.rstrip("/") + "/"
    expected: dict[str, tuple[str, str]] = {}
    for raw_entry in tree.stdout.split(b"\0"):
        if not raw_entry:
            continue
        metadata, raw_path = raw_entry.split(b"\t", 1)
        mode, object_type, object_id = metadata.decode("ascii").split()
        repository_path = raw_path.decode("utf-8")
        require(repository_path.startswith(prefix), "commit tree escaped import root")
        relative = repository_path[len(prefix) :]
        if is_reserved(repository / repository_path):
            continue
        require(object_type == "blob", f"unsupported git object: {repository_path}")
        require(mode in {"100644", "100755"}, f"unsupported git mode: {repository_path}")
        expected[relative] = (mode, object_id)
    actual: dict[str, tuple[str, bytes]] = {}
    for candidate in import_path.rglob("*"):
        relative_path = candidate.relative_to(import_path)
        if is_reserved(candidate):
            continue
        require(not candidate.is_symlink(), f"symlink in import root: {relative_path}")
        if candidate.is_dir():
            continue
        require(candidate.is_file(), f"unsupported import-root entry: {relative_path}")
        mode = "100755" if candidate.stat().st_mode & 0o111 else "100644"
        actual[relative_path.as_posix()] = (mode, candidate.read_bytes())
    require(set(expected) == set(actual), "current import-root paths differ from commit")
    for relative, (expected_mode, object_id) in expected.items():
        mode, data = actual[relative]
        require(mode == expected_mode, f"file mode differs from commit: {relative}")
        blob = git("cat-file", "blob", object_id)
        require(blob.returncode == 0 and blob.stdout == data, f"file differs from commit: {relative}")


def parse_time(value: Any, description: str) -> datetime:
    require(isinstance(value, str), f"{description} must be an ISO timestamp")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as error:
        raise AuditValidationError(f"invalid {description}: {error}") from error
    require(parsed.tzinfo is not None, f"{description} must include a timezone")
    require(
        parsed.astimezone(timezone.utc) <= datetime.now(timezone.utc) + timedelta(minutes=5),
        f"{description} is in the future",
    )
    return parsed


@dataclass
class ParsedRow:
    identifier: str
    family: str
    gate: str
    layers: tuple[str, ...]
    result: str
    evidence: str
    criterion: str
    source_urls: tuple[str, ...]
    capability_binding: Optional[dict[str, Any]]


@dataclass(frozen=True)
class CaptureAuthority:
    public_key_path: Path
    public_key_bytes: bytes
    public_key_sha256: str


def is_below(path: Path, directory: Path) -> bool:
    current = path
    while True:
        try:
            if os.path.samefile(current, directory):
                return True
        except OSError:
            return False
        parent = current.parent
        if parent == current:
            return False
        current = parent


def canonical_public_key_sha256(public_key: bytes) -> str:
    openssl = shutil.which("openssl")
    require(openssl is not None, "OpenSSL is required to load a trust policy")
    completed = subprocess.run(
        [openssl, "pkey", "-pubin", "-outform", "DER"],
        input=public_key,
        capture_output=True,
        check=False,
    )
    require(completed.returncode == 0 and completed.stdout, "invalid authority public key")
    return sha256(completed.stdout)


def load_trust_policy(
    policy_path: Optional[Path], repository_root: Path
) -> dict[str, CaptureAuthority]:
    if policy_path is None:
        return {}
    require(policy_path.is_absolute(), "trust policy path must be absolute")
    require(not policy_path.is_symlink(), "trust policy cannot be a symlink")
    try:
        resolved_policy = policy_path.resolve(strict=True)
    except OSError as error:
        raise AuditValidationError(f"cannot resolve trust policy: {error}") from error
    require(
        not is_below(resolved_policy, repository_root),
        "trust policy must be outside the audited repository",
    )
    require(resolved_policy.is_file(), "trust policy is not a regular file")
    document = strict_json(stable_read(resolved_policy, "trust policy"), "trust policy")
    require(
        set(document) == {"schemaVersion", "authorities"},
        "trust policy must contain exactly schemaVersion and authorities",
    )
    require(
        type(document.get("schemaVersion")) is int and document["schemaVersion"] == 1,
        "trust policy schemaVersion must be integer 1",
    )
    raw_authorities = document.get("authorities")
    require(isinstance(raw_authorities, dict), "trust policy authorities must be an object")
    require(
        set(raw_authorities).issubset({"RUNNER", "STUDIO", "DEVICE", "SCOPE"}),
        "trust policy contains an unknown authority role",
    )
    authorities: dict[str, CaptureAuthority] = {}
    authority_fingerprints: set[str] = set()
    for role, raw in raw_authorities.items():
        require(
            isinstance(raw, dict)
            and set(raw) == {"publicKeyPath", "publicKeySha256"},
            f"invalid {role} authority policy",
        )
        key_value = raw.get("publicKeyPath")
        digest = raw.get("publicKeySha256")
        require(isinstance(key_value, str) and Path(key_value).is_absolute(), f"{role} public key path must be absolute")
        key_path = Path(key_value)
        require(not key_path.is_symlink(), f"{role} public key cannot be a symlink")
        try:
            resolved_key = key_path.resolve(strict=True)
        except OSError as error:
            raise AuditValidationError(f"cannot resolve {role} public key: {error}") from error
        require(
            not is_below(resolved_key, repository_root),
            f"{role} public key must be outside the audited repository",
        )
        require(resolved_key.is_file(), f"{role} public key is not a regular file")
        key_bytes = stable_read(resolved_key, f"{role} public key")
        canonical_digest = canonical_public_key_sha256(key_bytes)
        require(
            isinstance(digest, str)
            and re.fullmatch(r"[0-9a-f]{64}", digest) is not None
            and canonical_digest == digest,
            f"{role} canonical public-key fingerprint is not pinned correctly",
        )
        require(
            digest not in authority_fingerprints,
            "each trust-policy authority role must use a distinct pinned key",
        )
        authority_fingerprints.add(digest)
        authorities[role] = CaptureAuthority(resolved_key, key_bytes, digest)
    return authorities


class AuditValidator:
    def __init__(
        self,
        *,
        repository_root: Path,
        import_root: str,
        request_prompt: str = "",
        trusted_device_public_key: Optional[Path] = None,
        trust_policy_path: Optional[Path] = None,
    ) -> None:
        self.repository_root = repository_root.resolve()
        require(self.repository_root.is_dir(), "repository root is not a directory")
        self.import_root_value = import_root
        self.source_unavailable = import_root == "UNAVAILABLE"
        self.import_path: Optional[Path] = (
            None
            if self.source_unavailable
            else resolve_relative_directory(self.repository_root, import_root, "import root")
        )
        self.request_prompt = request_prompt
        require(
            trusted_device_public_key is None,
            "a standalone public key is not a trust policy; use --trust-policy",
        )
        self.capture_authorities = load_trust_policy(
            trust_policy_path, self.repository_root
        )
        self.inventory: dict[str, Any] = {}
        self.project_revision = ""
        self.canonical_runtime = ""
        self.device_host_value = ""
        self.device_environment: Optional[dict[str, str]] = None
        self.supported_surfaces: tuple[str, ...] = ()
        self.input_gates: frozenset[str] = frozenset()
        self.artifact_registry: dict[str, tuple[str, str, str]] = {}
        self.manifest_cache: dict[tuple[str, str], dict[str, Any]] = {}
        self.final_status = ""
        self.release_ready = ""

    def validate(self, markdown: str) -> tuple[str, str]:
        require("\r" not in markdown.replace("\r\n", ""), "audit contains a bare carriage return")
        markdown = markdown.replace("\r\n", "\n")
        headings = re.findall(r"(?m)^## (.+?)\s*$", markdown)
        require(tuple(headings) == HEADINGS, "audit must contain exactly the three required H2 sections")
        first_heading = markdown.find("## Project UX evidence matrix")
        require(first_heading >= 0, "missing Project UX evidence matrix")
        metadata_lines = [
            line for line in markdown[:first_heading].splitlines() if line.strip()
        ]
        require(len(metadata_lines) == 7, "audit must begin with exactly seven metadata lines")
        metadata: dict[str, str] = {}
        for index, (line, label) in enumerate(zip(metadata_lines, METADATA_LABELS), start=1):
            match = re.fullmatch(rf"{re.escape(label)}: (?P<value>.*)", line)
            require(match is not None, f"metadata line {index} must be {label!r}")
            metadata[label] = match.group("value")
        require(metadata["Import root"] == self.import_root_value, "Import root metadata disagrees with CLI")
        version_match = re.fullmatch(r"AIUI (0\.17\.0|0\.18\.0)", metadata["Canonical version"])
        require(version_match is not None, "Canonical version must be exact AIUI 0.17.0 or AIUI 0.18.0")
        version = version_match.group(1)
        self.canonical_runtime = f"AIUI {version}"
        if self.source_unavailable:
            require(
                metadata["Project revision"] == "UNAVAILABLE",
                "source-unavailable mode requires Project revision: UNAVAILABLE",
            )
            self.project_revision = "UNAVAILABLE"
        else:
            assert self.import_path is not None
            validate_project_structure(
                self.repository_root, self.import_path, version
            )
            self.inventory = current_inventory(self.repository_root, self.import_path, version)
            self._validate_revision(metadata["Project revision"])
        self.device_host_value = metadata["Device/host"]
        self.device_environment = self._parse_device_host(self.device_host_value, version)
        require(metadata["Supported surfaces"].strip(), "Supported surfaces must not be empty")
        if self.source_unavailable:
            require(
                metadata["Device/host"] == "UNAVAILABLE"
                and metadata["Supported surfaces"] == "UNAVAILABLE",
                "source-unavailable mode requires unavailable device and surfaces",
            )
            self.supported_surfaces = ()
        else:
            inventory_surfaces = tuple(self.inventory["supportedSurfaces"])
            expected_surfaces = ",".join(inventory_surfaces) or "UNAVAILABLE"
            require(
                metadata["Supported surfaces"] == expected_surfaces,
                "Supported surfaces must equal the fresh scanner ledger exactly",
            )
            self.supported_surfaces = inventory_surfaces
        input_entries = (
            []
            if metadata["Inputs"] == "none"
            else parse_sorted_ledger(
                metadata["Inputs"],
                r"[a-z0-9][a-z0-9.-]*@[a-z0-9][a-z0-9.-]*",
                "Inputs",
            )
        )
        for entry in input_entries:
            kind = entry.split("@", 1)[0]
            require(
                kind in INPUT_KINDS and kind != "combined",
                f"Inputs contains an invalid or combined kind: {kind}",
            )
        input_gates = [entry.split("@", 1)[1] for entry in input_entries]
        require(len(input_gates) == len(set(input_gates)), "each Inputs kind needs a distinct gate")
        self.input_gates = frozenset(input_gates)
        if not self.source_unavailable:
            expected_inputs = sorted(
                f"{entry['kind']}@{entry['gate']}"
                for entry in self.inventory["inputGates"]
            )
            require(
                input_entries == expected_inputs,
                "Inputs must equal the fresh scanner input gates exactly",
            )
        claimed = parse_sorted_ledger(
            metadata["Claimed capabilities"],
            r"[a-z0-9][a-z0-9_.-]*@[a-z0-9][a-z0-9_.-]*",
            "Claimed capabilities",
        )
        if self.source_unavailable:
            disclosed_inputs = sorted(
                f"{INPUT_KIND_BY_FAMILY[family]}@{gate}"
                for family, gate in (claim.split("@", 1) for claim in claimed)
                if family in INPUT_KIND_BY_FAMILY
            )
            require(
                input_entries == disclosed_inputs,
                "source-unavailable Inputs must equal all and only disclosed input capability gates",
            )
        else:
            require(
                claimed == self.inventory["claimedCapabilities"],
                "Claimed capabilities must equal the fresh inventory exactly",
            )

        sections = self._sections(markdown)
        ux_rows = parse_table(sections[HEADINGS[0]], UX_HEADERS, HEADINGS[0])
        capability_rows = parse_table(
            sections[HEADINGS[1]], CAPABILITY_HEADERS, HEADINGS[1]
        )
        parsed_ux = self._validate_ux_rows(ux_rows, set(input_gates))
        parsed_capability = (
            self._validate_unavailable_capability_rows(capability_rows, version, set(claimed))
            if self.source_unavailable
            else self._validate_capability_rows(capability_rows, version, set(claimed))
        )
        all_rows = parsed_ux + parsed_capability
        identifiers = [row.identifier for row in all_rows]
        require(len(identifiers) == len(set(identifiers)), "matrix row IDs must be globally unique")
        for row in all_rows:
            self._validate_result_evidence(row)
        if self.source_unavailable:
            require(
                all(row.result == "BLOCKED" for row in all_rows),
                "source-unavailable audits may contain only BLOCKED rows",
            )
        self._validate_final(markdown, sections[HEADINGS[2]], all_rows)
        if not self.source_unavailable:
            assert self.import_path is not None
            validate_project_structure(
                self.repository_root, self.import_path, version
            )
            completion_inventory = current_inventory(
                self.repository_root, self.import_path, version
            )
            require(
                completion_inventory == self.inventory,
                "project or capability inventory changed while the audit was validated",
            )
        return self.final_status, self.release_ready

    def _sections(self, markdown: str) -> dict[str, str]:
        positions = []
        for heading in HEADINGS:
            match = re.search(rf"(?m)^## {re.escape(heading)}\s*$", markdown)
            require(match is not None, f"missing heading {heading}")
            positions.append((heading, match.start(), match.end()))
        result: dict[str, str] = {}
        for index, (heading, _, end) in enumerate(positions):
            next_start = positions[index + 1][1] if index + 1 < len(positions) else len(markdown)
            result[heading] = markdown[end:next_start]
        return result

    def _validate_revision(self, revision: str) -> None:
        require(
            re.fullmatch(r"WORKTREE:[0-9a-f]{64}|[0-9a-f]{40}", revision) is not None,
            "Project revision must be a verified commit or WORKTREE fingerprint",
        )
        current_fingerprint = self.inventory.get("projectRevision")
        require(
            isinstance(current_fingerprint, str)
            and re.fullmatch(r"WORKTREE:[0-9a-f]{64}", current_fingerprint) is not None,
            "fresh inventory lacks a project fingerprint",
        )
        if revision.startswith("WORKTREE:"):
            require(revision == current_fingerprint, "Project revision is stale")
        else:
            verify_commit_tree(self.repository_root, self.import_path, revision)
        self.project_revision = revision

    def _parse_device_host(self, value: str, version: str) -> Optional[dict[str, str]]:
        if value == "UNAVAILABLE":
            return None
        match = re.fullmatch(
            r"device=(?P<device>[^;]+); host=(?P<host>[^;]+); runtime=(?P<runtime>[^;]+)",
            value,
        )
        require(match is not None, "Device/host must be UNAVAILABLE or an exact device tuple")
        environment = {
            "deviceModel": match.group("device").strip(),
            "hostBuild": match.group("host").strip(),
            "runtimeVersion": match.group("runtime").strip(),
        }
        forbidden = re.compile(
            r"(?i)\b(?:simulator|emulator|browser|chrome|safari|firefox|edge|"
            r"mock|fixture|test|tbd|placeholder|fake)\b|模拟器|浏览器|测试|占位|伪造"
        )
        for name, field in environment.items():
            require(len(field) >= 3 and forbidden.search(field) is None, f"invalid physical-device {name}")
        require(re.search(r"(?i)\brokid\b", environment["deviceModel"]) is not None, "device must name Rokid hardware")
        require(environment["runtimeVersion"] == f"AIUI {version}", "device runtime differs from canonical version")
        return environment

    def _capability_surfaces(self, item: dict[str, Any]) -> str:
        mechanism = str(item.get("mechanism", ""))
        if mechanism.startswith("CLAIM:") and "@" in mechanism:
            surface = mechanism.split("@", 1)[1].split(":", 1)[0]
            require(surface in self.supported_surfaces, "claim surface is absent from scanner surfaces")
            return surface
        if mechanism.startswith("target:"):
            surface = mechanism.split(":", 1)[1]
            require(surface in self.supported_surfaces, "target surface is absent from scanner surfaces")
            return surface
        return ",".join(self.supported_surfaces) or "UNAVAILABLE"

    def _validate_capability_target(
        self, value: str, version: str, item: dict[str, Any], identifier: str
    ) -> None:
        expected_surface = self._capability_surfaces(item)
        if self.device_host_value == "UNAVAILABLE":
            expected = f"AIUI {version}; device=UNAVAILABLE; surface={expected_surface}"
        else:
            expected = f"AIUI {version}; {self.device_host_value}; surface={expected_surface}"
        require(
            value == expected,
            f"capability target tuple is not exact for {identifier}",
        )

    def _validate_capability_contract(
        self,
        row: list[str],
        family: str,
        identifier: str,
        policy_state: str,
        *,
        source_unavailable: bool = False,
    ) -> None:
        paths = ("positive", "negative-fallback", "lifecycle-cleanup")
        cells = tuple(row[index] for index in (5, 6, 7))
        for path, cell in zip(paths, cells):
            prefix = capability_contract_cell(family, path, "")
            require(
                cell.startswith(prefix) and len(cell[len(prefix) :].strip()) >= 8,
                f"capability {path} contract is invalid for {identifier}",
            )

        policy = CAPABILITY_POLICIES[family]
        if family == "project.unregistered":
            if not source_unavailable:
                expected_id = "CAP-UNREGISTERED-" + row[0].split("{gate=", 1)[1].split("}", 1)[0].removeprefix("unregistered-").upper()
                require(
                    identifier == expected_id,
                    f"quarantine capability ID is not exact for {identifier}",
                )
            expected_behavior = PROVISIONAL_BEHAVIOR
        else:
            if policy_state == "binding-unresolved":
                require(
                    is_provisional_capability_id(identifier, policy.base_id)
                    and row[2] == PROJECT_BINDING_UNRESOLVED
                    and row[3] == PROJECT_BINDING_UNRESOLVED,
                    f"project-binding provisional contract is not exact for {identifier}",
                )
            expected_behavior = CAPABILITY_BEHAVIOR_CONTRACTS[family]

        if expected_behavior is not None:
            expected_cells = tuple(
                capability_contract_cell(family, path, description)
                for path, description in zip(paths, expected_behavior)
            )
            require(
                cells == expected_cells,
                f"capability behavior contract is not exact for {identifier}",
            )

    def _has_ui_surface(self) -> bool:
        inventory_families = {
            str(item.get("family")) for item in self.inventory.get("items", [])
        }
        ui_surfaces = {"_current", "_blank", "Page", "Widget"}
        surfaces = set(self.supported_surfaces)
        if surfaces.intersection(ui_surfaces):
            return True
        if any(
            candidate.startswith(
                ("page.", "widget.", "focus.", "ui.", "event.", "input.", "component.")
            )
            for candidate in inventory_families
        ):
            return True
        return False

    def _has_target_surface(self) -> bool:
        return bool({"_current", "_blank"}.intersection(self.supported_surfaces))

    def _ux_is_applicable(self, family: str) -> bool:
        mode = UX_APPLICABILITY_MODES[family]
        inventory_families = {
            str(item.get("family")) for item in self.inventory.get("items", [])
        }
        has_ui = self._has_ui_surface()
        if mode == "always":
            return True
        if mode == "declared-surface":
            return has_ui
        if mode == "ui-surface":
            return has_ui
        if mode == "focus-or-actionable":
            return has_ui and bool(
                inventory_families.intersection(
                    {"focus.host", "focus.element", "ui.button", "event.bindtap"}
                    | INPUT_FAMILIES
                )
            )
        if mode == "scanner-input":
            return bool(self.input_gates)
        if mode == "failure-capability":
            return any(
                candidate == "project.unregistered"
                or candidate.startswith(("network.", "media.camera.", "agent-worker."))
                or candidate in FAILURE_CAPABILITY_FAMILIES
                for candidate in inventory_families
            )
        require(mode == "scope-conditional", f"unknown UX applicability mode: {mode}")
        return any(
            str(item.get("mechanism", "")).startswith("MOTION:")
            for item in self.inventory.get("items", [])
            if isinstance(item, dict)
        )

    def _validate_ux_rows(self, rows: list[list[str]], input_gates: set[str]) -> list[ParsedRow]:
        parsed_rows: list[ParsedRow] = []
        family_gates: dict[str, dict[str, set[str]]] = {
            family: {} for family in UX_REQUIRED_LAYERS
        }
        signatures: dict[tuple[str, str], tuple[str, str, str]] = {}
        outcomes: dict[tuple[str, str], list[tuple[str, str]]] = {}
        for row in rows:
            match = UX_ID_RE.fullmatch(row[0])
            require(match is not None, f"invalid UX ID: {row[0]}")
            identifier, gate = match.group("identifier"), match.group("gate")
            matching = [
                family
                for family in UX_REQUIRED_LAYERS
                if identifier == family or identifier.startswith(family + "-")
            ]
            require(len(matching) == 1, f"UX ID does not resolve to one family: {identifier}")
            family = matching[0]
            require(
                re.fullmatch(re.escape(family) + r"(?:-[A-Z0-9]+)*", identifier) is not None,
                f"non-canonical UX ID: {identifier}",
            )
            contract_prefix = f"{{contract={UX_CONTRACT_TOKENS[family]}}} "
            canonical_surface, canonical_risk, canonical_test = UX_CONTRACTS[family]
            require(
                normalized(row[3])
                == normalized(contract_prefix + canonical_test),
                f"UX Test contract token or criterion is invalid for {family}",
            )
            require(
                normalized(row[1]) == normalized(canonical_surface)
                and normalized(row[2]) == normalized(canonical_risk),
                f"UX surface/state or risk contract is not canonical for {family}",
            )
            layers = parse_layers(row[4], identifier)
            result = row[5]
            require(result in ALLOWED_RESULTS, f"invalid result on {identifier}: {result}")
            gate_layers = family_gates[family].setdefault(gate, set())
            require(not gate_layers.intersection(layers), f"duplicate UX layer in {family}@{gate}")
            gate_layers.update(layers)
            key = (family, gate)
            signature = (normalized(row[1]), normalized(row[2]), normalized(row[3]))
            if key in signatures:
                require(signatures[key] == signature, f"split UX rows changed the contract for {family}@{gate}")
            signatures[key] = signature
            outcomes.setdefault(key, []).append((identifier, result))
            parsed_rows.append(
                ParsedRow(identifier, family, gate, layers, result, row[6], row[3], (), None)
            )
        for family, gates in family_gates.items():
            require(gates, f"missing required UX family {family}")
            for gate, layers in gates.items():
                require(layers == UX_REQUIRED_LAYERS[family], f"wrong fixed layers for {family}@{gate}")
        observed_input_gates = set(family_gates["UX-INPUT"])
        expected_ux_input_gates = input_gates or {"no-input"}
        require(
            observed_input_gates == expected_ux_input_gates,
            "Inputs gates must equal all UX-INPUT gates, using no-input only for an empty scanner ledger",
        )
        require(
            any(row.result != "N/A" for row in parsed_rows),
            "all UX contract families cannot be N/A",
        )
        for parsed in parsed_rows:
            if self.source_unavailable:
                continue
            mode = UX_APPLICABILITY_MODES[parsed.family]
            applicable = self._ux_is_applicable(parsed.family)
            if parsed.family == "UX-TARGET" and not self._has_target_surface():
                require(
                    parsed.result == "BLOCKED",
                    "UX-TARGET must remain BLOCKED when target surfaces are unavailable",
                )
            elif (
                parsed.family == "UX-INPUT"
                and self._has_ui_surface()
                and not input_gates
            ):
                require(
                    parsed.gate == "no-input" and parsed.result == "N/A",
                    "an empty scanner input ledger requires the signed no-input N/A gate",
                )
            elif applicable:
                require(
                    parsed.result != "N/A",
                    f"applicable {parsed.family} cannot be N/A",
                )
            elif mode in {
                "declared-surface",
                "ui-surface",
                "focus-or-actionable",
                "scanner-input",
            }:
                require(
                    parsed.result in {"N/A", "BLOCKED"},
                    f"non-applicable {parsed.family} cannot claim an executed result",
                )
        self._validate_split_ids(outcomes)
        return parsed_rows

    def _validate_capability_rows(
        self, rows: list[list[str]], version: str, claimed: set[str]
    ) -> list[ParsedRow]:
        inventory_items = {
            (str(item.get("family")), str(item.get("gate"))): item
            for item in self.inventory["items"]
            if isinstance(item, dict)
        }
        require(len(inventory_items) == len(self.inventory["items"]), "inventory contains duplicate capability gates")
        parsed_rows: list[ParsedRow] = []
        observed: set[str] = set()
        gate_layers: dict[tuple[str, str], set[str]] = {}
        signatures: dict[tuple[str, str], tuple[str, ...]] = {}
        outcomes: dict[tuple[str, str], list[tuple[str, str]]] = {}
        speech_companions: dict[tuple[str, str], set[str]] = {}
        surfaces: dict[tuple[str, str], str] = {}
        for row in rows:
            match = CAPABILITY_ID_RE.fullmatch(row[0])
            require(match is not None, f"invalid capability ID: {row[0]}")
            identifier = match.group("identifier")
            family, gate = match.group("family"), match.group("gate")
            key = (family, gate)
            claim = f"{family}@{gate}"
            require(claim in claimed, f"capability row is not in fresh inventory: {claim}")
            require(key in inventory_items, f"missing fresh inventory binding for {claim}")
            policy = CAPABILITY_POLICIES.get(family)
            require(policy is not None, f"no validator policy for inventory family {family}")
            require(
                re.fullmatch(re.escape(policy.base_id) + r"(?:-[A-Z0-9]+)*", identifier) is not None,
                f"non-canonical capability ID for {family}: {identifier}",
            )
            layers = parse_layers(row[8], identifier)
            prior_layers = gate_layers.setdefault(key, set())
            require(not prior_layers.intersection(layers), f"duplicate capability layer for {claim}")
            prior_layers.update(layers)
            result = row[9]
            require(result in ALLOWED_RESULTS - {"N/A"}, "inventoried capabilities cannot be N/A")
            item = inventory_items[key]
            require(row[2] == item.get("apiBinding"), f"matrix changed inventory API binding for {claim}")
            require(
                row[3] == item.get("declarationBinding"),
                f"matrix changed inventory declaration binding for {claim}",
            )
            self._validate_capability_contract(
                row, family, identifier, str(item.get("policyState"))
            )
            self._validate_capability_target(row[1], version, item, identifier)
            source_urls = self._parse_source_cell(row[4], version, family)
            if version == "0.18.0" or item.get("policyState") != "registered" or policy.provisional:
                require(result == "BLOCKED", f"{claim} has no PASS/FAIL policy and must remain BLOCKED")
            signature = tuple(normalized(cell) for cell in row[1:8])
            if key in signatures:
                require(signatures[key] == signature, f"split capability rows changed the contract for {claim}")
            signatures[key] = signature
            surfaces[key] = row[1]
            outcomes.setdefault(key, []).append((identifier, result))
            observed.add(claim)
            criterion = (
                f"Positive={row[5]}; Negative={row[6]}; Lifecycle={row[7]}"
            )
            binding = {
                "target": row[1],
                "apiBinding": row[2],
                "declarationBinding": row[3],
                "sourceUrls": list(source_urls),
            }
            parsed_rows.append(
                ParsedRow(
                    identifier,
                    family,
                    gate,
                    layers,
                    result,
                    row[10],
                    criterion,
                    source_urls,
                    binding,
                )
            )
            if family == "ai.speech-recognition":
                companion = re.fullmatch(r"COMPANION:(voice\.declaration\.unknown)@([a-z0-9_.-]+)", row[3])
                require(companion is not None, "speech recognition requires an exact declaration companion")
                companion_key = (companion.group(1), companion.group(2))
                speech_companions.setdefault(companion_key, set()).add(claim)
        require(observed == claimed, "capability matrix gates must equal fresh inventory exactly")
        for key, layers in gate_layers.items():
            policy = CAPABILITY_POLICIES[key[0]]
            require(layers == policy.layers, f"wrong fixed capability layers for {key[0]}@{key[1]}")
        self._validate_split_ids(outcomes)
        for companion, parents in speech_companions.items():
            require(companion in inventory_items, f"missing speech declaration companion {companion[0]}@{companion[1]}")
            require(len(parents) == 1, "one declaration companion cannot serve multiple speech gates")
            parent_key = tuple(next(iter(parents)).split("@", 1))
            require(surfaces.get(companion) == surfaces.get(parent_key), "speech companion surface/version differs")
        return parsed_rows

    def _validate_unavailable_capability_rows(
        self, rows: list[list[str]], version: str, claimed: set[str]
    ) -> list[ParsedRow]:
        """Validate disclosed capability scope when there is no inspectable source.

        This mode deliberately cannot establish a project binding or executed
        outcome.  It exists so a useful, structurally honest BLOCKED audit can be
        exchanged before a Studio import root is supplied.
        """

        parsed_rows: list[ParsedRow] = []
        observed: set[str] = set()
        for row in rows:
            match = CAPABILITY_ID_RE.fullmatch(row[0])
            require(match is not None, f"invalid capability ID: {row[0]}")
            identifier = match.group("identifier")
            family, gate = match.group("family"), match.group("gate")
            claim = f"{family}@{gate}"
            require(claim in claimed, f"source-unavailable row is not disclosed: {claim}")
            require(claim not in observed, f"duplicate source-unavailable capability: {claim}")
            policy = CAPABILITY_POLICIES.get(family)
            require(policy is not None, f"no validator policy for disclosed family {family}")
            require(
                re.fullmatch(re.escape(policy.base_id) + r"(?:-[A-Z0-9]+)*", identifier)
                is not None,
                f"non-canonical capability ID for {family}: {identifier}",
            )
            layers = parse_layers(row[8], identifier)
            require(layers and set(layers) == set(policy.layers), f"wrong fixed capability layers for {claim}")
            require(row[9] == "BLOCKED", "source-unavailable capabilities must remain BLOCKED")
            require(
                row[1] == f"AIUI {version}; device=UNAVAILABLE; surface=UNAVAILABLE",
                f"source-unavailable target tuple is not exact on {identifier}",
            )
            if family == "project.unregistered":
                require(
                    row[2] == PROJECT_BINDING_UNRESOLVED
                    and row[3] == "UNKNOWN — source policy not registered",
                    f"unavailable quarantine bindings are not exact on {identifier}",
                )
            else:
                require(
                    is_provisional_capability_id(identifier, policy.base_id)
                    and row[2] == PROJECT_BINDING_UNRESOLVED
                    and row[3] == PROJECT_BINDING_UNRESOLVED,
                    f"unavailable registered family must use its provisional contract: {identifier}",
                )
            self._validate_capability_contract(
                row,
                family,
                identifier,
                "unregistered" if family == "project.unregistered" else "binding-unresolved",
                source_unavailable=True,
            )
            source_urls = self._parse_source_cell(row[4], version, family)
            criterion = f"Positive={row[5]}; Negative={row[6]}; Lifecycle={row[7]}"
            parsed_rows.append(
                ParsedRow(
                    identifier,
                    family,
                    gate,
                    layers,
                    row[9],
                    row[10],
                    criterion,
                    source_urls,
                    None,
                )
            )
            observed.add(claim)
        require(observed == claimed, "source-unavailable capability ledger is not closed")
        return parsed_rows

    def _validate_split_ids(
        self, outcomes: dict[tuple[str, str], list[tuple[str, str]]]
    ) -> None:
        for key, values in outcomes.items():
            if len(values) < 2:
                continue
            for identifier, result in values:
                require(
                    re.search(rf"-{re.escape(result)}(?:-|$)", identifier) is not None,
                    f"split row ID must expose {result} for {key[0]}@{key[1]}",
                )

    def _parse_source_cell(
        self, value: str, version: str, family: str
    ) -> tuple[str, ...]:
        entries = [part.strip() for part in value.split(";")]
        require(entries and all(entries), "Official source/sample must contain machine-readable links")
        urls: list[str] = []
        identities: set[tuple[str, str]] = set()
        for entry in entries:
            match = SOURCE_ENTRY_RE.fullmatch(entry)
            require(match is not None, f"invalid Official source/sample entry: {entry}")
            role, url = match.group("role"), match.group("url")
            source = PINNED_SOURCE_RE.fullmatch(url)
            require(source is not None, f"official source must be a commit-pinned AIUI URL: {url}")
            require(
                (role == "SEARCH-SCOPE") == (source.group("kind") == "tree"),
                f"source role/path kind mismatch: {entry}",
            )
            expected_revision = (
                STABLE_AIUI_REVISION if version == "0.17.0" else PREVIEW_AIUI_REVISION
            )
            require(
                source.group("revision") == expected_revision,
                f"AIUI {version} capability source uses the wrong pinned revision",
            )
            identity = (role, url)
            require(identity not in identities, "Official source/sample contains duplicates")
            identities.add(identity)
            urls.append(url)
        if version == "0.17.0":
            expected_sources = CAPABILITY_SOURCE_POLICIES.get(family)
            require(
                expected_sources is not None,
                f"AIUI 0.17 has no registered official source set for {family}",
            )
            require(
                identities == expected_sources,
                f"Official source/sample set is not exact for {family}",
            )
        return tuple(urls)

    def _validate_result_evidence(self, row: ParsedRow) -> None:
        if row.result == "N/A":
            self._validate_na(row)
            return
        mappings: dict[str, tuple[str, str]] = {}
        for part in (piece.strip() for piece in row.evidence.split(";")):
            match = EVIDENCE_ENTRY_RE.fullmatch(part)
            require(match is not None, f"invalid {row.result} evidence mapping on {row.identifier}: {part}")
            layer, kind, locator = match.group("layer"), match.group("kind"), match.group("locator")
            require(layer not in mappings, f"duplicate evidence mapping for {row.identifier}@{layer}")
            if row.result == "BLOCKED":
                require(kind == "blocked", f"BLOCKED {row.identifier}@{layer} must use blocked:reason")
                require(len(locator.strip()) >= 6, f"blocked reason is too weak on {row.identifier}@{layer}")
            else:
                require(kind in LAYER_ALLOWED_KINDS[layer], f"{kind} cannot prove {layer}")
                self._validate_executed(row, layer, kind, locator)
            mappings[layer] = (kind, locator)
        require(set(mappings) == set(row.layers), f"evidence mappings do not equal declared layers on {row.identifier}")

    def _validate_executed(self, row: ParsedRow, layer: str, kind: str, locator: str) -> None:
        require(INVALID_EXECUTED_RE.search(locator) is None, f"placeholder executed locator on {row.identifier}")
        if kind == "source" and re.fullmatch(r"https://\S+", locator):
            require(layer == "SOURCE", "official URL can prove only SOURCE")
            require(len(row.source_urls) == 1 and locator == row.source_urls[0], "direct SOURCE URL must be the row's sole URL")
            return
        if kind == "source" and locator.startswith("request://current#"):
            claim = locator.split("#", 1)[1]
            require(row.result == "FAIL", "request facts can establish only FAIL")
            require(len(claim) >= 8 and claim in self.request_prompt, "request evidence is not verbatim current prompt text")
            return
        entry, artifact = self._manifest_entry(locator, row)
        require(entry.get("layer") == layer, f"manifest layer mismatch on {row.identifier}")
        require(entry.get("gate") == row.gate, f"manifest gate mismatch on {row.identifier}")
        require(entry.get("kind") == kind, f"manifest kind mismatch on {row.identifier}")
        require(entry.get("result") == row.result, f"manifest result mismatch on {row.identifier}")
        require(normalized(str(entry.get("criterion", ""))) == normalized(row.criterion), f"manifest criterion mismatch on {row.identifier}")
        if row.capability_binding is not None:
            for field, expected in row.capability_binding.items():
                require(entry.get(field) == expected, f"manifest capability {field} mismatch on {row.identifier}")
            if layer == "SOURCE":
                require(entry.get("inspectedSourceUrls") == list(row.source_urls), "SOURCE manifest did not inspect the full source set")
        environment = entry.get("environment")
        if isinstance(environment, dict):
            for runtime_field in ("hostRuntime", "runtimeVersion"):
                if runtime_field in environment:
                    require(
                        environment[runtime_field] == self.canonical_runtime,
                        f"{layer} {runtime_field} differs from audit canonical version",
                    )
        if layer == "AIX":
            require(isinstance(environment, dict), "AIX evidence lacks environment")
            require(set(environment) == {"tool", "toolVersion", "host"}, "invalid AIX environment")
            require(environment.get("tool") == "aix", "AIX environment tool must be aix")
            require(kind not in {"log", "artifact"}, "naked AIX logs/artifacts cannot prove a gate")
        elif layer == "STUDIO":
            require(isinstance(environment, dict), "STUDIO evidence lacks environment")
            require(set(environment) == {"studioVersion", "hostRuntime"}, "invalid STUDIO environment")
        elif layer == "DEVICE":
            self._validate_device_entry(entry)
        if kind in {"command", "log", "artifact"}:
            self._validate_command(entry, artifact, layer, row.result)
        required_authorities: set[str] = set()
        if kind in {"command", "log", "artifact"} or layer == "AIX":
            required_authorities.add("RUNNER")
        if layer in {"STUDIO", "DEVICE"}:
            required_authorities.add(layer)
        self._validate_capture_attestations(entry, required_authorities)
        self._validate_media_signature(kind, artifact)

    def _manifest_entry(self, locator: str, row: ParsedRow) -> tuple[dict[str, Any], Path]:
        match = MANIFEST_LOCATOR_RE.fullmatch(locator)
        require(match is not None, f"executed evidence requires a schema-2 manifest locator: {locator}")
        manifest_path = resolve_evidence_file(
            self.repository_root, match.group("path"), "evidence manifest"
        )
        manifest_bytes = stable_read(manifest_path, "evidence manifest")
        require(sha256(manifest_bytes) == match.group("digest"), "manifest locator SHA-256 mismatch")
        cache_key = (match.group("path"), match.group("digest"))
        manifest = self.manifest_cache.get(cache_key)
        if manifest is None:
            manifest = strict_json(manifest_bytes, "evidence manifest")
            self._validate_manifest_envelope(manifest)
            self.manifest_cache[cache_key] = manifest
        entries = manifest.get("entries")
        matches = [
            entry for entry in entries if isinstance(entry, dict) and entry.get("id") == match.group("entry")
        ]
        require(len(matches) == 1, f"manifest entry is missing or duplicated: {match.group('entry')}")
        entry = matches[0]
        require(entry.get("row") == row.identifier, f"manifest row mismatch for {row.identifier}")
        require(entry.get("projectRevision") == self.project_revision, "manifest entry revision mismatch")
        self._validate_entry_core(entry)
        artifact_path = resolve_evidence_file(self.repository_root, entry.get("path"), "evidence artifact")
        require(artifact_path != manifest_path, "manifest cannot be its own evidence artifact")
        artifact = stable_read(artifact_path, "evidence artifact")
        require(sha256(artifact) == entry.get("sha256"), "evidence artifact SHA-256 mismatch")
        require(type(entry.get("bytes")) is int and entry["bytes"] == len(artifact), "evidence artifact byte count mismatch")
        require(len(artifact) > 0, "evidence artifact must be non-empty")
        if artifact_path.suffix.lower() in {".txt", ".log", ".json", ".md", ".html", ".xml"}:
            try:
                text = artifact.decode("utf-8")
            except UnicodeDecodeError as error:
                raise AuditValidationError("text evidence must be UTF-8") from error
            require(INVALID_EXECUTED_RE.search(text) is None, "text evidence contains a placeholder assertion")
        identity = (str(manifest_path), str(entry.get("id")), str(entry.get("layer") or entry.get("scopeAspect")))
        capture_id = str(entry.get("captureId"))
        for registry_key, description in (
            ("artifact:" + str(entry.get("sha256")), "artifact SHA-256"),
            ("capture:" + capture_id, "capture ID"),
        ):
            prior = self.artifact_registry.get(registry_key)
            require(prior is None or prior == identity, f"one {description} cannot prove multiple entries")
            self.artifact_registry[registry_key] = identity
        return entry, artifact_path

    def _validate_manifest_envelope(self, manifest: dict[str, Any]) -> None:
        require(type(manifest.get("schemaVersion")) is int and manifest["schemaVersion"] == 2, "manifest schemaVersion must be integer 2")
        require(manifest.get("projectRevision") == self.project_revision, "manifest projectRevision mismatch")
        subject = manifest.get("subject")
        require(isinstance(subject, dict) and set(subject) == {"projectRevision", "importRoot"}, "manifest subject must bind only revision and import root")
        require(subject.get("projectRevision") == self.project_revision, "manifest subject revision mismatch")
        require(subject.get("importRoot") == self.import_root_value, "manifest subject import root mismatch")
        source = manifest.get("sourceSnapshot")
        completion = manifest.get("completionSnapshot")
        require(
            isinstance(source, dict)
            and set(source) == {"fingerprint", "inventoryPath", "inventorySha256", "capturedAt"},
            "sourceSnapshot must bind fingerprint, inventory path/hash, and capture time",
        )
        require(
            isinstance(completion, dict) and set(completion) == {"fingerprint", "capturedAt"},
            "completionSnapshot must bind fingerprint and capture time",
        )
        current_fingerprint = self.inventory["projectRevision"]
        require(source.get("fingerprint") == current_fingerprint, "sourceSnapshot fingerprint is stale")
        require(completion.get("fingerprint") == current_fingerprint, "completionSnapshot fingerprint is stale")
        source_time = parse_time(source.get("capturedAt"), "sourceSnapshot.capturedAt")
        completion_time = parse_time(completion.get("capturedAt"), "completionSnapshot.capturedAt")
        require(source_time <= completion_time, "completionSnapshot predates sourceSnapshot")
        inventory_path = resolve_evidence_file(self.repository_root, source.get("inventoryPath"), "source inventory")
        inventory_bytes = stable_read(inventory_path, "source inventory")
        require(source.get("inventorySha256") == sha256(inventory_bytes), "source inventory SHA-256 mismatch")
        snapshot_inventory = strict_json(inventory_bytes, "source inventory")
        require(snapshot_inventory == self.inventory, "sourceSnapshot inventory differs from the fresh inventory")
        entries = manifest.get("entries")
        require(isinstance(entries, list) and entries, "manifest entries must be a non-empty array")
        entry_ids: set[str] = set()
        capture_ids: set[str] = set()
        artifact_hashes: set[str] = set()
        for entry in entries:
            require(isinstance(entry, dict), "every manifest entry must be an object")
            entry_id = entry.get("id")
            require(isinstance(entry_id, str) and re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]*", entry_id) is not None, "invalid manifest entry ID")
            require(entry_id not in entry_ids, "duplicate manifest entry ID")
            entry_ids.add(entry_id)
            capture_id = entry.get("captureId")
            require(isinstance(capture_id, str) and re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{15,127}", capture_id) is not None, "invalid capture ID")
            require(capture_id not in capture_ids, "duplicate capture ID inside manifest")
            capture_ids.add(capture_id)
            digest = entry.get("sha256")
            require(isinstance(digest, str) and re.fullmatch(r"[0-9a-f]{64}", digest) is not None, "invalid artifact SHA-256")
            require(digest not in artifact_hashes, "one artifact hash cannot back multiple manifest entries")
            artifact_hashes.add(digest)
            started = parse_time(entry.get("startedAt"), "entry.startedAt")
            captured = parse_time(entry.get("capturedAt"), "entry.capturedAt")
            require(source_time <= started <= captured <= completion_time, "entry capture lies outside source/completion snapshots")

    def _validate_entry_core(self, entry: dict[str, Any]) -> None:
        capture_id = entry.get("captureId")
        require(isinstance(capture_id, str), "manifest entry lacks captureId")
        collector = entry.get("collector")
        require(isinstance(collector, dict) and set(collector) == {"name", "version"}, "manifest collector must bind name/version")
        for value in collector.values():
            require(isinstance(value, str) and len(value.strip()) >= 2, "invalid collector provenance")
            require(INVALID_EXECUTED_RE.search(value) is None, "placeholder collector provenance")
        for field in ("criterion", "observed"):
            value = entry.get(field)
            require(isinstance(value, str) and len(value.strip()) >= 8, f"weak manifest {field}")
        require(INVALID_EXECUTED_RE.search(str(entry.get("observed"))) is None, "placeholder observed outcome")
        for field in ("artifactRole", "mediaType"):
            value = entry.get(field)
            require(isinstance(value, str) and len(value.strip()) >= 3, f"invalid {field}")

    def _validate_command(self, entry: dict[str, Any], artifact: Path, layer: str, result: str) -> None:
        fields = {"operation", "argv", "cwd", "tool", "exitCode", "stdoutSha256", "stderrSha256"}
        missing = fields - set(entry)
        require(not missing, f"{layer} command evidence lacks provenance: {sorted(missing)}")
        operation = entry.get("operation")
        require(isinstance(operation, str) and re.fullmatch(r"[a-z][a-z0-9.-]{2,63}", operation) is not None, "invalid command operation")
        require(INVALID_EXECUTED_RE.search(operation) is None, "placeholder command operation")
        argv = entry.get("argv")
        require(isinstance(argv, list) and argv, "command argv must be a non-empty token array")
        require(all(isinstance(arg, str) and arg and re.search(r"[\x00\r\n]", arg) is None for arg in argv), "invalid command argv token")
        require(entry.get("cwd") == self.import_root_value, "command cwd must equal the audited import root")
        tool = entry.get("tool")
        require(isinstance(tool, dict) and set(tool) == {"name", "version"}, "command tool must bind name/version")
        require(all(isinstance(value, str) and len(value.strip()) >= 2 for value in tool.values()), "invalid command tool provenance")
        exit_code = entry.get("exitCode")
        require(type(exit_code) is int, "command exitCode must be an integer, not boolean")
        if result == "PASS":
            require(exit_code == 0, "PASS command must exit zero")
        for field in ("stdoutSha256", "stderrSha256"):
            require(re.fullmatch(r"[0-9a-f]{64}", str(entry.get(field, ""))) is not None, f"invalid {field}")
        digest = sha256(artifact.read_bytes())
        require(digest in {entry.get("stdoutSha256"), entry.get("stderrSha256")}, "command artifact is neither captured stdout nor stderr")
        if layer == "AIX":
            require(tool.get("name") == "aix", "AIX command tool must be aix")
            require(re.fullmatch(r"aix-(preview|pack|list|validate)", operation) is not None, "unsupported AIX operation")
            require(Path(argv[0]).name == "aix", "AIX argv must execute aix")

    def _validate_media_signature(self, kind: str, artifact: Path) -> None:
        if kind == "screenshot":
            suffix = artifact.suffix.lower()
            data = artifact.read_bytes()
            require(suffix in {".png", ".jpg", ".jpeg", ".webp"}, "unsupported screenshot extension")
            valid = (
                (suffix == ".png" and data.startswith(b"\x89PNG\r\n\x1a\n"))
                or (suffix in {".jpg", ".jpeg"} and data.startswith(b"\xff\xd8\xff"))
                or (suffix == ".webp" and len(data) >= 12 and data.startswith(b"RIFF") and data[8:12] == b"WEBP")
            )
            require(valid, "screenshot bytes do not match its media type")
        elif kind == "recording":
            suffix = artifact.suffix.lower()
            data = artifact.read_bytes()
            require(suffix in {".mp4", ".mov", ".webm"}, "unsupported recording extension")
            valid = data.startswith(b"\x1a\x45\xdf\xa3") if suffix == ".webm" else len(data) >= 12 and data[4:8] == b"ftyp"
            require(valid, "recording bytes do not match its media type")

    def _validate_device_entry(self, entry: dict[str, Any]) -> None:
        require(self.device_environment is not None, "DEVICE PASS/FAIL requires concrete physical Device/host metadata")
        environment = entry.get("environment")
        expected_fields = {
            "deviceModel",
            "hostBuild",
            "runtimeVersion",
            "physicalDevice",
            "deviceIdHash",
            "captureTool",
            "captureSessionId",
        }
        require(isinstance(environment, dict) and set(environment) == expected_fields, "invalid DEVICE environment")
        for field, expected in self.device_environment.items():
            require(environment.get(field) == expected, f"DEVICE {field} differs from audit metadata")
        require(environment.get("physicalDevice") is True, "DEVICE evidence must assert physicalDevice=true")
        require(re.fullmatch(r"[0-9a-f]{64}", str(environment.get("deviceIdHash", ""))) is not None, "invalid deviceIdHash")
        for field in ("captureTool", "captureSessionId"):
            value = environment.get(field)
            require(isinstance(value, str) and len(value.strip()) >= 8, f"invalid DEVICE {field}")
            require(INVALID_EXECUTED_RE.search(value) is None, f"placeholder DEVICE {field}")

    def _validate_capture_attestations(
        self, entry: dict[str, Any], required_roles: set[str]
    ) -> None:
        attestations = entry.get("attestations")
        if not required_roles:
            require(
                "attestations" not in entry,
                "non-capture evidence cannot carry unrequested attestations",
            )
            return
        require(
            isinstance(attestations, dict)
            and set(attestations) == required_roles,
            "capture attestations must equal the required authority roles: "
            + ",".join(sorted(required_roles)),
        )
        for role in sorted(required_roles):
            self._validate_capture_attestation(entry, role)

    def _validate_capture_attestation(self, entry: dict[str, Any], role: str) -> None:
        authority = self.capture_authorities.get(role)
        require(
            authority is not None,
            f"{role} PASS/FAIL requires an independent capture authority in the trust policy",
        )
        attestations = entry.get("attestations")
        require(isinstance(attestations, dict), f"{role} capture lacks attestations")
        attestation = attestations.get(role)
        require(isinstance(attestation, dict), f"{role} capture lacks a signed attestation")
        require(set(attestation) == {"algorithm", "keyId", "signature"}, f"invalid {role} attestation fields")
        require(
            attestation.get("keyId") == authority.public_key_sha256,
            f"{role} attestation keyId does not match the pinned authority",
        )
        try:
            signature = base64.b64decode(attestation.get("signature", ""), validate=True)
        except (ValueError, TypeError) as error:
            raise AuditValidationError(f"invalid {role} signature encoding") from error
        require(signature, f"{role} signature is empty")
        unsigned_entry = dict(entry)
        unsigned_entry.pop("attestations", None)
        # These exact fields bind the capture to both source snapshots and the
        # manifest subject, without signing mutable JSON formatting.
        manifest = self._manifest_for_entry(entry)
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
        self._verify_public_key_signature(
            str(attestation.get("algorithm")),
            authority.public_key_bytes,
            signature,
            canonical,
        )

    def _manifest_for_entry(self, entry: dict[str, Any]) -> dict[str, Any]:
        matches = [
            manifest
            for manifest in self.manifest_cache.values()
            if any(candidate is entry for candidate in manifest.get("entries", []))
        ]
        require(len(matches) == 1, "cannot resolve DEVICE entry envelope")
        return matches[0]

    def _verify_public_key_signature(
        self, algorithm: str, public_key: bytes, signature: bytes, payload: bytes
    ) -> None:
        openssl = shutil.which("openssl")
        require(openssl is not None, "OpenSSL is required to verify DEVICE evidence")
        with tempfile.NamedTemporaryFile(
            prefix="aiui-capture-", suffix=".sig"
        ) as signature_handle, tempfile.NamedTemporaryFile(
            prefix="aiui-authority-", suffix=".pem"
        ) as key_handle:
            signature_handle.write(signature)
            signature_handle.flush()
            key_handle.write(public_key)
            key_handle.flush()
            if algorithm in {"rsa-sha256", "ecdsa-sha256"}:
                command = [
                    openssl,
                    "dgst",
                    "-sha256",
                    "-verify",
                    key_handle.name,
                    "-signature",
                    signature_handle.name,
                ]
            elif algorithm == "ed25519":
                command = [
                    openssl,
                    "pkeyutl",
                    "-verify",
                    "-pubin",
                    "-inkey",
                    key_handle.name,
                    "-sigfile",
                    signature_handle.name,
                    "-rawin",
                ]
            else:
                raise AuditValidationError(f"unsupported DEVICE signature algorithm: {algorithm}")
            completed = subprocess.run(command, input=payload, capture_output=True, check=False)
        require(completed.returncode == 0, "DEVICE signature does not verify against the trusted public key")

    def _validate_na(self, row: ParsedRow) -> None:
        require(row.capability_binding is None, "inventoried capabilities cannot be N/A")
        require(not self.source_unavailable, "source-unavailable rows cannot be N/A")
        require(
            not (row.family == "UX-TARGET" and not self._has_target_surface()),
            "UX-TARGET cannot be N/A when target surfaces are unavailable",
        )
        if row.family == "UX-INPUT":
            if self._has_ui_surface():
                require(
                    row.gate == "no-input" and self.inventory.get("inputGates") == [],
                    "a scanner-discovered UI input gate cannot be N/A",
                )
            else:
                require(
                    not self._ux_is_applicable(row.family),
                    "applicable UX-INPUT cannot be scoped to N/A",
                )
        else:
            require(
                not self._ux_is_applicable(row.family),
                f"applicable {row.family} cannot be scoped to N/A",
            )
        match = re.fullmatch(
            r"SCOPE: source=(?P<source>manifest:[^;\s]+@sha256=[0-9a-f]{64}#[A-Za-z0-9._-]+); "
            r"claim=(?P<claim>manifest:[^;\s]+@sha256=[0-9a-f]{64}#[A-Za-z0-9._-]+)",
            row.evidence,
        )
        require(match is not None, "N/A requires source and claim schema-2 manifest locators")
        require(match.group("source") != match.group("claim"), "N/A source and claim entries must differ")
        self._validate_scope_entry(row, match.group("source"), "source")
        self._validate_scope_entry(row, match.group("claim"), "claim")

    def _validate_scope_entry(self, row: ParsedRow, locator: str, aspect: str) -> None:
        entry, _ = self._manifest_entry(locator, row)
        self._validate_capture_attestations(entry, {"SCOPE"})
        require(entry.get("kind") == "scope" and entry.get("result") == "N/A", "invalid N/A scope entry")
        require(entry.get("gate") == row.gate, "N/A scope gate mismatch")
        require(entry.get("scopeAspect") == aspect, "N/A scopeAspect mismatch")
        require(normalized(str(entry.get("criterion", ""))) == normalized(row.criterion), "N/A criterion mismatch")
        proof = entry.get("scopeProof")
        require(isinstance(proof, dict), "N/A scope entry lacks scopeProof")
        expected_family = ".".join(row.identifier.lower().split("-")[:2])
        query = {"family": expected_family, "gate": row.gate}
        require(proof.get("query") == query and proof.get("matches") == [], "N/A scope query must replay to no matches")
        if aspect == "source":
            require(set(proof) == {"inventoryPath", "inventorySha256", "query", "matches"}, "invalid source absence proof")
            path = resolve_evidence_file(self.repository_root, proof.get("inventoryPath"), "N/A inventory")
            data = stable_read(path, "N/A inventory")
            require(sha256(data) == proof.get("inventorySha256"), "N/A inventory hash mismatch")
            inventory = strict_json(data, "N/A inventory")
            require(inventory == self.inventory, "N/A source proof does not use fresh inventory")
            selector = f"{expected_family}@{row.gate}"
            actual = sorted(value for value in inventory["claimedCapabilities"] if value == selector)
            require(actual == proof["matches"], "N/A source query replay found a match")
        else:
            require(
                set(proof)
                == {"scopeManifestPath", "scopeManifestSha256", "query", "matches", "universeClosed"},
                "invalid claim absence proof",
            )
            require(proof.get("universeClosed") is True, "N/A claim universe must be closed")
            scope_path = self._resolve_scope_file(proof.get("scopeManifestPath"))
            data = stable_read(scope_path, "UX scope universe")
            require(sha256(data) == proof.get("scopeManifestSha256"), "UX scope universe hash mismatch")
            scope = strict_json(data, "UX scope universe")
            require(set(scope) == {"schemaVersion", "closed", "uxCriteria"}, "invalid UX scope universe schema")
            require(type(scope.get("schemaVersion")) is int and scope["schemaVersion"] == 1, "UX scope schemaVersion must be 1")
            require(scope.get("closed") is True, "UX scope universe must declare closed=true")
            require(isinstance(scope.get("uxCriteria"), list), "UX scope uxCriteria must be an array")
            actual = sorted(
                f"{criterion.get('family')}@{criterion.get('gate')}"
                for criterion in scope["uxCriteria"]
                if isinstance(criterion, dict)
                and criterion.get("family") == expected_family
                and criterion.get("gate") == row.gate
            )
            require(actual == proof["matches"], "N/A product-scope query replay found a match")

    def _resolve_scope_file(self, value: Any) -> Path:
        require(self.import_path is not None, "N/A scope cannot be resolved without source")
        require(isinstance(value, str) and value, "UX scope universe path must be a string")
        require(not Path(value).is_absolute() and "\\" not in value and ".." not in Path(value).parts, "unsafe UX scope universe path")
        unresolved = self.repository_root / value
        current = self.repository_root
        for part in Path(value).parts:
            current = current / part
            require(not current.is_symlink(), "UX scope universe path contains a symlink")
        candidate = unresolved.resolve(strict=True)
        try:
            relative = candidate.relative_to(self.import_path)
        except ValueError as error:
            raise AuditValidationError("UX scope universe must stay inside the fingerprinted import root") from error
        require(relative.parts and relative.parts[0] != EVIDENCE_DIRECTORY, "UX scope universe cannot be mutable evidence")
        require(candidate.is_file() and not candidate.is_symlink(), "UX scope universe is not a regular file")
        expected = (self.import_path / "aiui-audit-scope.json").resolve()
        require(
            candidate == expected,
            "UX scope universe must be import-root aiui-audit-scope.json",
        )
        return candidate

    def _validate_final(self, markdown: str, section: str, rows: list[ParsedRow]) -> None:
        for label in ("Final status", "Release-ready", "Reason", "Required gates"):
            require(len(re.findall(rf"(?m)^{re.escape(label)}:", markdown)) == 1, f"{label} must appear exactly once")
        lines = [line.strip() for line in section.splitlines() if line.strip()]
        require(len(lines) == 4, "Final release decision must contain exactly four fields")
        fields: dict[str, str] = {}
        expected_labels = ("Final status", "Release-ready", "Reason", "Required gates")
        for line, label in zip(lines, expected_labels):
            match = re.fullmatch(rf"{re.escape(label)}: (?P<value>.+)", line)
            require(match is not None, f"invalid or out-of-order final field {label}")
            fields[label] = match.group("value")
        fail_ids = sorted(row.identifier for row in rows if row.result == "FAIL")
        blocked_ids = sorted(row.identifier for row in rows if row.result == "BLOCKED")
        reason = re.fullmatch(
            r"FAIL=\[(?P<fail>none|[A-Z0-9,-]+)\]; BLOCKED=\[(?P<blocked>none|[A-Z0-9,-]+)\]",
            fields["Reason"],
        )
        require(reason is not None, "Reason must be an exact FAIL/BLOCKED ledger")
        stated_fail = [] if reason.group("fail") == "none" else reason.group("fail").split(",")
        stated_blocked = [] if reason.group("blocked") == "none" else reason.group("blocked").split(",")
        require(stated_fail == sorted(set(stated_fail)) == fail_ids, "Reason FAIL ledger is not exact")
        require(stated_blocked == sorted(set(stated_blocked)) == blocked_ids, "Reason BLOCKED ledger is not exact")
        required_gates = sorted(
            f"{row.identifier}@{layer}"
            for row in rows
            if row.result in {"FAIL", "BLOCKED"}
            for layer in row.layers
        )
        stated_gates = [] if fields["Required gates"] == "none" else fields["Required gates"].split(",")
        require(stated_gates == sorted(set(stated_gates)) == required_gates, "Required gates ledger is not exact")
        expected_status = "FAIL" if fail_ids else "BLOCKED" if blocked_ids else "PASS"
        require(fields["Final status"] == expected_status, "Final status violates FAIL > BLOCKED > PASS precedence")
        require(fields["Release-ready"] == ("YES" if expected_status == "PASS" else "NO"), "Release-ready conflicts with matrix outcomes")
        self.final_status = fields["Final status"]
        self.release_ready = fields["Release-ready"]
        pre_final = unicodedata.normalize("NFKC", markdown.split("## Final release decision", 1)[0])
        require(RELEASE_CLAIM_RE.search(pre_final) is None, "release/completion claims are allowed only in the structured final decision")


def load_request_prompt(value: Optional[str], repository_root: Path) -> str:
    if value is None:
        return ""
    path_value = value[1:] if value.startswith("@") else value
    candidate = Path(path_value)
    if not candidate.is_absolute():
        candidate = repository_root / candidate
    if candidate.is_file():
        try:
            return candidate.read_text(encoding="utf-8")
        except (OSError, UnicodeError) as error:
            raise AuditValidationError(f"cannot read request prompt: {error}") from error
    return value


def validate_audit(
    audit_path: Path,
    *,
    repository_root: Path,
    import_root: str,
    request_prompt: str = "",
    trusted_device_public_key: Optional[Path] = None,
    trust_policy_path: Optional[Path] = None,
) -> tuple[str, str]:
    try:
        markdown = audit_path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as error:
        raise AuditValidationError(f"cannot read audit Markdown: {error}") from error
    return AuditValidator(
        repository_root=repository_root,
        import_root=import_root,
        request_prompt=request_prompt,
        trusted_device_public_key=trusted_device_public_key,
        trust_policy_path=trust_policy_path,
    ).validate(markdown)


class AuditArgumentParser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        self.print_usage(sys.stderr)
        self.exit(1, f"{self.prog}: error: {message}\n")


def build_parser() -> argparse.ArgumentParser:
    parser = AuditArgumentParser(
        description="Validate a completed AIUI UX/capability audit against fresh source and signed evidence."
    )
    parser.add_argument("audit_markdown", type=Path, help="completed audit Markdown")
    parser.add_argument(
        "--repository-root",
        "--repo-root",
        dest="repository_root",
        type=Path,
        required=True,
        help="repository containing the import root and .aiui-evidence",
    )
    parser.add_argument(
        "--import-root",
        required=True,
        help="repository-relative AIUI Studio import root",
    )
    parser.add_argument(
        "--request-prompt",
        help="literal request text, a prompt file, or @prompt-file for request:// FAIL evidence",
    )
    parser.add_argument(
        "--trusted-device-public-key",
        type=Path,
        help="deprecated and rejected; use an external --trust-policy",
    )
    parser.add_argument(
        "--trust-policy",
        type=Path,
        help="absolute repository-external JSON policy pinning capture authority keys",
    )
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    try:
        repository_root = args.repository_root.resolve(strict=True)
        prompt = load_request_prompt(args.request_prompt, repository_root)
        final_status, release_ready = validate_audit(
            args.audit_markdown,
            repository_root=repository_root,
            import_root=args.import_root,
            request_prompt=prompt,
            trusted_device_public_key=(
                args.trusted_device_public_key
            ),
            trust_policy_path=args.trust_policy,
        )
    except (AuditValidationError, OSError, ValueError) as error:
        print(f"AIUI audit invalid: {error}", file=sys.stderr)
        return 1
    print(
        "AIUI audit structurally valid: "
        f"Final status={final_status}; Release-ready={release_ready}"
    )
    return 0 if final_status == "PASS" and release_ready == "YES" else 2


if __name__ == "__main__":
    raise SystemExit(main())
