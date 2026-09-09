#!/usr/bin/env python3
"""Inventory release-sensitive AIUI capabilities without guessing support."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any

from fingerprint_aiui_project import fingerprint_project


SOURCE_SUFFIXES = frozenset({".ink", ".js", ".ts", ".wxml", ".wxss", ".json"})
EXCLUDED_TOP_LEVEL_DIRECTORIES = frozenset({".git", ".aiui-evidence"})
KNOWN_MANIFEST_KEYS = frozenset(
    {
        "pages",
        "window",
        "permissions",
        "widgets",
        "agentWorkers",
        "usingComponents",
        "fonts",
    }
)
KNOWN_TEMPLATE_BINDINGS = frozenset({"bindtap", "bindfocus", "bindblur"})
STRUCTURAL_TAGS = frozenset(
    {"page", "widget", "view", "text", "script", "style", "template", "block"}
)
KNOWN_PLATFORM_CALLBACKS = frozenset(
    {
        "onLoad",
        "onShow",
        "onReady",
        "onHide",
        "onUnload",
        "onHostFocus",
        "onHostBlur",
        "onTargetChanged",
        "onVoiceWakeup",
        "onHeadGesture",
        "onHeadGestureStateChange",
        "onKeyDown",
        "onKeyUp",
        "onOpen",
        "onCreate",
        "onAttach",
        "onDetach",
        "onDestroy",
        "onLaunch",
        "onError",
    }
)
KNOWN_WX_CALLS = {
    "wx.request": ("network.https", "wx.request(...)"),
    "wx.createEventSource": ("network.sse", "wx.createEventSource(...)"),
    "wx.connectSocket": ("network.websocket", "wx.connectSocket(...)"),
}
GLOBAL_CALLS_TO_QUARANTINE = frozenset(
    {
        "setInterval",
        "clearInterval",
        "setTimeout",
        "clearTimeout",
        "requestAnimationFrame",
        "cancelAnimationFrame",
        "WebSocket",
        "EventSource",
        "MediaRecorder",
        "ImageCapture",
        "Worker",
    }
)
REGISTERED_POLICY_FAMILIES = frozenset(
    {
        "page.route",
        "page.target",
        "focus.host",
        "focus.element",
        "ui.button",
        "event.bindtap",
        "input.enter",
        "input.back",
        "input.scroll.unknown",
        "input.scroll.host",
        "component.scroll-view",
        "input.voice.unknown",
        "input.voice-wakeup",
        "ai.speech-recognition",
        "voice.declaration.unknown",
        "input.fallback.unknown",
        "input.touch-migration.unknown",
        "page.world-awareness",
        "input.head-gesture",
        "input.gesture-fallback.unknown",
        "media.camera.permission",
        "media.camera.runtime",
        "media.camera.lifecycle",
        "network.unknown",
        "network.https",
        "network.sse",
        "network.websocket",
        "page.lifecycle",
        "widget.declaration",
        "widget.lifecycle",
        "agent-worker.declaration",
        "agent-worker.capability",
        "agent-worker.on-open",
        "agent-worker.wait-until",
    }
)
PAGE_CALLBACKS = frozenset(
    {
        "onLoad",
        "onShow",
        "onReady",
        "onHide",
        "onUnload",
        "onHostFocus",
        "onHostBlur",
        "onTargetChanged",
        "onVoiceWakeup",
        "onHeadGesture",
        "onHeadGestureStateChange",
        "onKeyDown",
        "onKeyUp",
    }
)
WIDGET_CALLBACKS = frozenset({"onCreate", "onAttach", "onDetach", "onDestroy"})
WORKER_CALLBACKS = frozenset({"onOpen"})
SURFACE_LABELS = {
    "app": "App",
    "page": "Page",
    "widget": "Widget",
    "worker": "AgentWorker",
    "shared": "Shared",
}
DECLARED_SURFACE_BY_FAMILY = {
    "widget.declaration": "Widget",
    "agent-worker.declaration": "Agent Worker",
}
CANONICAL_SURFACES = frozenset(
    {"_current", "_blank", "Page", "Widget", "Agent Worker", "App"}
)
AUDIT_SURFACE_BY_SOURCE_KIND = {
    "app": "App",
    "page": "Page",
    "widget": "Widget",
    "worker": "Agent Worker",
}
REFERENCE_GLOBALS = frozenset(
    set(GLOBAL_CALLS_TO_QUARANTINE)
    | {"localStorage", "sessionStorage", "SpeechRecognition"}
)
CLAIMS_FILENAME = "aiui-audit-claims.json"
PROJECT_BINDING_UNRESOLVED = "PROJECT-BINDING:UNRESOLVED"
NO_DECLARATION = "NONE REQUIRED"
UNREGISTERED_DECLARATION = "UNKNOWN — source policy not registered"
INPUT_KIND_BY_FAMILY = {
    "event.bindtap": "tap",
    "input.enter": "enter",
    "input.back": "back",
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


def line_number(text: str, offset: int) -> int:
    return text.count("\n", 0, offset) + 1


def line_and_column(text: str, offset: int) -> tuple[int, int]:
    line = line_number(text, offset)
    preceding_newline = text.rfind("\n", 0, offset)
    return line, offset - preceding_newline


def reject_duplicate_json_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def mask_comments(text: str) -> str:
    """Replace comments with spaces while preserving offsets and string literals."""
    output = list(text)
    state = "code"
    index = 0
    while index < len(text):
        char = text[index]
        next_char = text[index + 1] if index + 1 < len(text) else ""
        if state == "code":
            if char == "'":
                state = "single"
            elif char == '"':
                state = "double"
            elif char == "`":
                state = "template"
            elif char == "/" and next_char == "/":
                output[index] = output[index + 1] = " "
                state = "line-comment"
                index += 1
            elif char == "/" and next_char == "*":
                output[index] = output[index + 1] = " "
                state = "block-comment"
                index += 1
        elif state == "line-comment":
            if char == "\n":
                state = "code"
            else:
                output[index] = " "
        elif state == "block-comment":
            if char == "*" and next_char == "/":
                output[index] = output[index + 1] = " "
                state = "code"
                index += 1
            elif char != "\n":
                output[index] = " "
        elif char == "\\":
            index += 1
        elif (
            (state == "single" and char == "'")
            or (state == "double" and char == '"')
            or (state == "template" and char == "`")
        ):
            state = "code"
        index += 1
    return "".join(output)


def mask_literals_and_comments(text: str) -> str:
    """Mask comments and JavaScript string literals without changing offsets."""
    output = list(text)
    state = "code"
    expression_depth = 0
    template_parents: list[int] = []
    index = 0
    while index < len(text):
        char = text[index]
        next_char = text[index + 1] if index + 1 < len(text) else ""
        if state == "code":
            if char == "'":
                output[index] = " "
                state = "single"
            elif char == '"':
                output[index] = " "
                state = "double"
            elif char == "`":
                output[index] = " "
                template_parents.append(expression_depth)
                expression_depth = 0
                state = "template"
            elif char == "/" and next_char == "/":
                output[index] = output[index + 1] = " "
                state = "line-comment"
                index += 1
            elif char == "/" and next_char == "*":
                output[index] = output[index + 1] = " "
                state = "block-comment"
                index += 1
            elif expression_depth and char == "{":
                expression_depth += 1
            elif expression_depth and char == "}":
                expression_depth -= 1
                if expression_depth == 0:
                    output[index] = " "
                    state = "template"
        elif state == "line-comment":
            if char == "\n":
                state = "code"
            else:
                output[index] = " "
        elif state == "block-comment":
            if char == "*" and next_char == "/":
                output[index] = output[index + 1] = " "
                state = "code"
                index += 1
            elif char != "\n":
                output[index] = " "
        elif state in {"single", "double"}:
            if char == "\\":
                output[index] = " "
                if index + 1 < len(text):
                    index += 1
                    if text[index] != "\n":
                        output[index] = " "
            elif (
                (state == "single" and char == "'")
                or (state == "double" and char == '"')
            ):
                output[index] = " "
                state = "code"
            elif char != "\n":
                output[index] = " "
        else:
            if char == "\\":
                output[index] = " "
                if index + 1 < len(text):
                    index += 1
                    if text[index] != "\n":
                        output[index] = " "
            elif char == "`":
                output[index] = " "
                state = "code"
                expression_depth = template_parents.pop()
            elif char == "$" and next_char == "{":
                output[index] = output[index + 1] = " "
                state = "code"
                expression_depth = 1
                index += 1
            elif char != "\n":
                output[index] = " "
        index += 1
    return "".join(output)


def mask_regex_literals(code_text: str) -> str:
    """Mask JavaScript regex literals in already-masked executable code.

    `code_text` must already have comments and string/template literal text
    replaced by spaces.  The result preserves every offset and newline so it
    can safely drive brace matching without treating regex contents as syntax.
    """
    output = list(code_text)
    expression_prefixes = frozenset(
        {
            "await",
            "case",
            "delete",
            "in",
            "instanceof",
            "new",
            "of",
            "return",
            "throw",
            "typeof",
            "void",
            "yield",
        }
    )
    expression_punctuation = frozenset("([{:,;=!?&|+-*%^~<>")
    index = 0
    while index < len(code_text):
        if code_text[index] != "/" or (
            index + 1 < len(code_text) and code_text[index + 1] == "="
        ):
            index += 1
            continue

        previous = index - 1
        while previous >= 0 and code_text[previous].isspace():
            previous -= 1
        starts_expression = previous < 0 or code_text[previous] in expression_punctuation
        if not starts_expression:
            preceding_identifier = re.search(
                r"[A-Za-z_$][A-Za-z0-9_$]*$", code_text[: previous + 1]
            )
            starts_expression = bool(
                preceding_identifier
                and preceding_identifier.group() in expression_prefixes
            )
        if not starts_expression:
            index += 1
            continue

        cursor = index + 1
        in_character_class = False
        closing: int | None = None
        while cursor < len(code_text):
            char = code_text[cursor]
            if char == "\n":
                break
            if char == "\\":
                cursor += 2
                continue
            if char == "[":
                in_character_class = True
            elif char == "]":
                in_character_class = False
            elif char == "/" and not in_character_class:
                closing = cursor
                break
            cursor += 1
        if closing is None:
            index += 1
            continue

        end = closing + 1
        while end < len(code_text) and code_text[end].isalpha():
            end += 1
        for masked_index in range(index, end):
            if output[masked_index] != "\n":
                output[masked_index] = " "
        index = end
    return "".join(output)


def executable_code_text(text: str, relative: str) -> str:
    """Return offset-preserving executable code, excluding `.ink` markup."""
    suffix = Path(relative).suffix.lower()
    if suffix in {".js", ".ts"}:
        return mask_literals_and_comments(text)
    if suffix != ".ink":
        return "".join("\n" if char == "\n" else " " for char in text)

    output = ["\n" if char == "\n" else " " for char in text]
    for match in re.finditer(
        r"<script\b[^>]*>(?P<body>.*?)</script\s*>",
        text,
        re.IGNORECASE | re.DOTALL,
    ):
        body_start, body_end = match.span("body")
        masked_body = mask_literals_and_comments(text[body_start:body_end])
        output[body_start:body_end] = masked_body
    return "".join(output)


def blank_preserving_lines(text: str) -> str:
    return "".join("\n" if char == "\n" else " " for char in text)


def mask_markup_comments(text: str) -> str:
    """Mask HTML comments without changing offsets."""
    output = list(text)
    for match in re.finditer(r"<!--.*?-->", text, re.DOTALL):
        for index in range(match.start(), match.end()):
            if output[index] != "\n":
                output[index] = " "
    return "".join(output)


def markup_scan_text(text: str, relative: str) -> str:
    """Return offset-preserving declarative markup, never executable JS text."""
    suffix = Path(relative).suffix.lower()
    if suffix in {".js", ".ts", ".json"}:
        return blank_preserving_lines(text)
    if suffix == ".wxss":
        return mask_comments(text)
    if suffix == ".wxml":
        return mask_markup_comments(text)
    if suffix != ".ink":
        return blank_preserving_lines(text)

    output = list(mask_markup_comments(text))
    for match in re.finditer(
        r"<script\b[^>]*>(?P<body>.*?)</script\s*>",
        text,
        re.IGNORECASE | re.DOTALL,
    ):
        body_start, body_end = match.span("body")
        output[body_start:body_end] = blank_preserving_lines(
            text[body_start:body_end]
        )
    return mask_comments("".join(output))


def mask_css_strings_and_comments(text: str) -> str:
    """Mask CSS strings and block comments while preserving source offsets."""
    output = list(text)
    state = "code"
    index = 0
    while index < len(text):
        char = text[index]
        next_char = text[index + 1] if index + 1 < len(text) else ""
        if state == "code":
            if char == "'":
                output[index] = " "
                state = "single"
            elif char == '"':
                output[index] = " "
                state = "double"
            elif char == "/" and next_char == "*":
                output[index] = output[index + 1] = " "
                state = "comment"
                index += 1
        elif state == "comment":
            if char == "*" and next_char == "/":
                output[index] = output[index + 1] = " "
                state = "code"
                index += 1
            elif char != "\n":
                output[index] = " "
        elif char == "\\":
            output[index] = " "
            if index + 1 < len(text):
                index += 1
                if text[index] != "\n":
                    output[index] = " "
        elif (state == "single" and char == "'") or (
            state == "double" and char == '"'
        ):
            output[index] = " "
            state = "code"
        elif char != "\n":
            output[index] = " "
        index += 1
    return "".join(output)


def style_scan_text(text: str, relative: str) -> str:
    """Return offset-preserving CSS source without comments or string content."""
    suffix = Path(relative).suffix.lower()
    if suffix == ".wxss":
        return mask_css_strings_and_comments(text)
    if suffix != ".ink":
        return blank_preserving_lines(text)

    output = ["\n" if char == "\n" else " " for char in text]
    for match in re.finditer(
        r"<style\b[^>]*>(?P<body>.*?)</style\s*>",
        text,
        re.IGNORECASE | re.DOTALL,
    ):
        body_start, body_end = match.span("body")
        output[body_start:body_end] = mask_css_strings_and_comments(
            text[body_start:body_end]
        )
    return "".join(output)


def lexical_scopes(code_text: str) -> list[dict[str, int | None]]:
    """Build conservative brace scopes over already-masked executable code."""
    scopes: list[dict[str, int | None]] = [
        {"start": 0, "end": len(code_text), "parent": None, "opening": None}
    ]
    stack = [0]
    for offset, char in enumerate(code_text):
        if char == "{":
            scopes.append(
                {
                    "start": offset + 1,
                    "end": len(code_text),
                    "parent": stack[-1],
                    "opening": offset,
                }
            )
            stack.append(len(scopes) - 1)
        elif char == "}" and len(stack) > 1:
            scopes[stack.pop()]["end"] = offset
    return scopes


def scope_at(scopes: list[dict[str, int | None]], offset: int) -> int:
    selected = 0
    for index, scope in enumerate(scopes[1:], start=1):
        start = int(scope["start"])
        end = int(scope["end"])
        if start <= offset <= end and start >= int(scopes[selected]["start"]):
            selected = index
    return selected


def child_scope_for_opening(
    scopes: list[dict[str, int | None]], opening: int
) -> int | None:
    for index, scope in enumerate(scopes):
        if scope["opening"] == opening:
            return index
    return None


def identifier_tokens(text: str) -> set[str]:
    return set(re.findall(r"[A-Za-z_$][A-Za-z0-9_$]*", text))


def declaration_scopes(
    code_text: str,
    scopes: list[dict[str, int | None]],
    names: set[str],
) -> dict[tuple[int, str], set[int]]:
    """Locate lexical declarations for selected identifiers.

    This is intentionally conservative: a declaration makes the containing
    lexical scope local even when a full JavaScript parser would distinguish
    hoisting details. That prevents platform globals from being guessed.
    """
    declarations: dict[tuple[int, str], set[int]] = {}
    callable_parameter_patterns = (
        re.compile(
            r"\bfunction(?:\s+[A-Za-z_$][A-Za-z0-9_$]*)?\s*"
            r"\((?P<parameters>[^()]*)\)\s*\{"
        ),
        re.compile(
            r"(?P<method>[A-Za-z_$][A-Za-z0-9_$]*)\s*"
            r"\((?P<parameters>[^()]*)\)\s*\{"
        ),
        re.compile(r"\((?P<parameters>[^()]*)\)\s*=>\s*\{"),
        re.compile(r"(?P<parameters>[A-Za-z_$][A-Za-z0-9_$]*)\s*=>\s*\{"),
    )
    control_words = {"if", "for", "while", "switch", "catch", "with"}
    function_scopes = {0}
    for pattern in callable_parameter_patterns:
        for match in pattern.finditer(code_text):
            if "method" in match.groupdict() and match.group("method") in control_words:
                continue
            opening = code_text.rfind("{", match.start(), match.end())
            child = child_scope_for_opening(scopes, opening)
            if child is not None:
                function_scopes.add(child)

    def declare(
        name: str,
        offset: int,
        scope_id: int | None = None,
        declaration_kind: str | None = None,
    ) -> None:
        if name not in names:
            return
        owner = scope_at(scopes, offset) if scope_id is None else scope_id
        if declaration_kind == "var":
            while owner not in function_scopes:
                parent = scopes[owner]["parent"]
                if parent is None:
                    break
                owner = int(parent)
        declarations.setdefault((owner, name), set()).add(offset)

    for match in re.finditer(
        r"\b(?P<kind>const|let|var|class|function)\s+"
        r"(?P<name>[A-Za-z_$][A-Za-z0-9_$]*)\b",
        code_text,
    ):
        declare(
            match.group("name"),
            match.start("name"),
            declaration_kind=match.group("kind"),
        )

    for match in re.finditer(
        r"\b(?P<kind>const|let|var)\s*(?P<opening>[{\[])", code_text
    ):
        opening = match.start("opening")
        opener = match.group("opening")
        closer = "}" if opener == "{" else "]"
        closing = matching_delimiter(code_text, opening, opener, closer)
        if closing is None:
            continue
        binding = code_text[opening : closing + 1]
        for name in names:
            binding_match = re.search(
                rf"(?:^|[,{{]|\[|:|\.\.\.)\s*"
                rf"(?P<name>{re.escape(name)})\b"
                r"(?=\s*(?:[,}\]]|=))",
                binding,
            )
            if binding_match:
                declare(
                    name,
                    opening + binding_match.start("name"),
                    scope_id=scope_at(scopes, match.start()),
                    declaration_kind=match.group("kind"),
                )

    for match in re.finditer(r"(?m)^\s*import\b(?P<body>[^;\n]*)", code_text):
        body = match.group("body")
        for name in names & identifier_tokens(body):
            declare(name, match.start("body") + body.find(name), 0)

    parameter_patterns = callable_parameter_patterns + (
        re.compile(r"\bcatch\s*\((?P<parameters>[^()]*)\)\s*\{"),
    )
    seen_parameter_blocks: set[tuple[int, str]] = set()
    for pattern in parameter_patterns:
        for match in pattern.finditer(code_text):
            if "method" in match.groupdict() and match.group("method") in control_words:
                continue
            opening = code_text.rfind("{", match.start(), match.end())
            child = child_scope_for_opening(scopes, opening)
            if child is None:
                continue
            parameters = match.group("parameters")
            for name in names & identifier_tokens(parameters):
                identity = (child, name)
                if identity in seen_parameter_blocks:
                    continue
                seen_parameter_blocks.add(identity)
                relative_offset = parameters.find(name)
                declare(name, match.start("parameters") + relative_offset, child)
    return declarations


def resolved_declaration_scope(
    name: str,
    offset: int,
    scopes: list[dict[str, int | None]],
    declarations: dict[tuple[int, str], set[int]],
) -> int | None:
    current: int | None = scope_at(scopes, offset)
    while current is not None:
        if (current, name) in declarations:
            return current
        current = scopes[current]["parent"]
    return None


def matching_delimiter(text: str, opening: int, opener: str, closer: str) -> int | None:
    depth = 0
    state = "code"
    index = opening
    while index < len(text):
        char = text[index]
        next_char = text[index + 1] if index + 1 < len(text) else ""
        if state == "code":
            if char == "'":
                state = "single"
            elif char == '"':
                state = "double"
            elif char == "`":
                state = "template"
            elif char == "/" and next_char == "/":
                state = "line-comment"
                index += 1
            elif char == "/" and next_char == "*":
                state = "block-comment"
                index += 1
            elif char == opener:
                depth += 1
            elif char == closer:
                depth -= 1
                if depth == 0:
                    return index
        elif state == "line-comment":
            if char == "\n":
                state = "code"
        elif state == "block-comment":
            if char == "*" and next_char == "/":
                state = "code"
                index += 1
        elif char == "\\":
            index += 1
        elif (
            (state == "single" and char == "'")
            or (state == "double" and char == '"')
            or (state == "template" and char == "`")
        ):
            state = "code"
        index += 1
    return None


def method_bodies(
    text: str, method_pattern: str
) -> list[tuple[re.Match[str], str, int]]:
    bodies: list[tuple[re.Match[str], str, int]] = []
    for match in re.finditer(method_pattern, text):
        opening = text.find("{", match.start(), match.end())
        if opening < 0:
            continue
        closing = matching_delimiter(text, opening, "{", "}")
        if closing is not None:
            bodies.append((match, text[opening + 1 : closing], opening + 1))
    return bodies


def is_method_declaration(structure_text: str, name_offset: int) -> bool:
    """Return whether `name(` at the offset is method syntax rather than a call."""
    opening = structure_text.find("(", name_offset)
    if opening < 0:
        return False
    closing = matching_delimiter(structure_text, opening, "(", ")")
    if closing is None:
        return False
    cursor = closing + 1
    while cursor < len(structure_text) and structure_text[cursor].isspace():
        cursor += 1
    return cursor < len(structure_text) and structure_text[cursor] == "{"


def direct_case_literals(
    structure_body: str, source_body: str
) -> list[tuple[str, int]]:
    """Return direct string-literal cases from one switch body with offsets."""
    cases: list[tuple[str, int]] = []
    depth = 0
    for token in re.finditer(r"[{}]|\bcase\b", structure_body):
        value = token.group()
        if value == "{":
            depth += 1
        elif value == "}":
            depth = max(0, depth - 1)
        elif depth == 0:
            literal = re.match(
                r"case\s*(?P<quote>[\"'])(?P<code>[A-Za-z0-9_-]+)"
                r"(?P=quote)\s*:",
                source_body[token.start() :],
            )
            if literal:
                cases.append((literal.group("code"), token.start()))
    return cases


def object_member_offsets(
    text: str, opening: int, *, include_methods: bool = True
) -> dict[str, set[int]]:
    """Return identifier members owned directly by one object literal.

    The special `methods` object is also an owner surface because AIUI components
    place template handlers there. Other nested objects are deliberately ignored.
    """
    closing = matching_delimiter(text, opening, "{", "}")
    if closing is None:
        return {}
    masked = mask_literals_and_comments(text)
    members: dict[str, set[int]] = {}
    cursor = opening + 1
    while cursor < closing:
        while cursor < closing and (masked[cursor].isspace() or masked[cursor] == ","):
            cursor += 1
        if cursor >= closing:
            break
        candidate = re.match(
            r"(?:(?:async|get|set)\s+)?(?P<name>[A-Za-z_$][A-Za-z0-9_$]*)",
            masked[cursor:closing],
        )
        if candidate:
            name = candidate.group("name")
            name_offset = cursor + candidate.start("name")
            after = cursor + candidate.end()
            while after < closing and masked[after].isspace():
                after += 1
            if after == closing or masked[after] in "(:,":
                members.setdefault(name, set()).add(name_offset)
                if (
                    include_methods
                    and name == "methods"
                    and after < closing
                    and masked[after] == ":"
                ):
                    nested_opening = after + 1
                    while nested_opening < closing and masked[nested_opening].isspace():
                        nested_opening += 1
                    if nested_opening < closing and masked[nested_opening] == "{":
                        for nested_name, offsets in object_member_offsets(
                            text, nested_opening
                        ).items():
                            members.setdefault(nested_name, set()).update(offsets)

        braces = brackets = parentheses = 0
        while cursor < closing:
            char = masked[cursor]
            if char == "{":
                braces += 1
            elif char == "}" and braces:
                braces -= 1
            elif char == "[":
                brackets += 1
            elif char == "]" and brackets:
                brackets -= 1
            elif char == "(":
                parentheses += 1
            elif char == ")" and parentheses:
                parentheses -= 1
            elif char == "," and not (braces or brackets or parentheses):
                cursor += 1
                break
            cursor += 1
    return members


def exported_object_members(
    text: str, *, include_methods: bool = True
) -> dict[str, set[int]]:
    members: dict[str, set[int]] = {}
    for export_match in re.finditer(r"\bexport\s+default\s*\{", text):
        opening = text.find("{", export_match.start(), export_match.end())
        for name, offsets in object_member_offsets(
            text, opening, include_methods=include_methods
        ).items():
            members.setdefault(name, set()).update(offsets)
    return members


def owner_key(relative: str) -> str:
    path = Path(relative)
    if path.suffix.lower() in SOURCE_SUFFIXES:
        return path.with_suffix("").as_posix()
    return relative


def semantic_gate(
    family: str,
    api_binding: str,
    declaration_binding: str,
    relative: str,
    line: int,
    column: int,
    gate_salt: str = "",
) -> str:
    identity_text = (
        f"{family}\0{api_binding}\0{declaration_binding}\0"
        f"{relative}\0{line}\0{column}"
    )
    if gate_salt:
        identity_text += f"\0{gate_salt}"
    identity = identity_text.encode("utf-8")
    digest = hashlib.sha256(identity).hexdigest()[:12]
    if family == "project.unregistered":
        return f"unregistered-{digest}"
    return f"{family.replace('.', '-')}-{digest}"


def make_item(
    family: str,
    mechanism: str,
    api_binding: str,
    declaration_binding: str,
    relative: str,
    line: int,
    column: int = 1,
    *,
    policy_state: str = "registered",
    version_feature: str = "stable-0.17",
    gate_salt: str = "",
) -> dict[str, object]:
    return {
        "family": family,
        "gate": semantic_gate(
            family,
            api_binding,
            declaration_binding,
            relative,
            line,
            column,
            gate_salt,
        ),
        "mechanism": mechanism,
        "apiBinding": api_binding,
        "declarationBinding": declaration_binding,
        "policyState": policy_state,
        "versionFeature": version_feature,
        "locations": [{"path": relative, "line": line, "column": column}],
    }


def make_unregistered_item(
    token: str,
    relative: str,
    line: int,
    column: int = 1,
) -> dict[str, object]:
    return make_item(
        "project.unregistered",
        token,
        f"PROJECT-SYMBOL:{token}",
        UNREGISTERED_DECLARATION,
        relative,
        line,
        column,
        policy_state="unregistered",
        version_feature="unresolved",
    )


def unmatched_entry(item: dict[str, object]) -> dict[str, object]:
    location = item["locations"][0]
    symbol = str(item["mechanism"])
    if symbol.endswith("(...)"):
        symbol = symbol[:-5]
    return {
        "symbol": symbol,
        "family": item["family"],
        "gate": item["gate"],
        "path": location["path"],
        "line": location["line"],
        "column": location["column"],
    }


def add_unregistered(
    items: list[dict[str, object]],
    unmatched_symbols: list[dict[str, object]],
    token: str,
    relative: str,
    line: int,
    column: int = 1,
) -> None:
    item = make_unregistered_item(token, relative, line, column)
    items.append(item)
    unmatched_symbols.append(unmatched_entry(item))


def json_leaf_tokens(value: Any, prefix: str) -> list[str]:
    if isinstance(value, dict):
        if not value:
            return [f"{prefix}={{}}"]
        tokens: list[str] = []
        for key in sorted(value):
            tokens.extend(json_leaf_tokens(value[key], f"{prefix}.{key}"))
        return tokens
    if isinstance(value, list):
        if not value:
            return [f"{prefix}=[]"]
        tokens = []
        for index, member in enumerate(value):
            tokens.extend(json_leaf_tokens(member, f"{prefix}[{index}]"))
        return tokens
    scalar = value if isinstance(value, str) else json.dumps(value, ensure_ascii=False)
    return [f"{prefix}={scalar}"]


def claims_items(
    claims_document: dict[str, Any],
) -> list[dict[str, str]]:
    relative = CLAIMS_FILENAME
    if set(claims_document) != {"schemaVersion", "scopeClosed", "claims"}:
        raise ValueError(
            f"{relative} root must contain exactly schemaVersion, scopeClosed, "
            "and claims"
        )
    if type(claims_document["schemaVersion"]) is not int or claims_document[
        "schemaVersion"
    ] != 1:
        raise ValueError(f"{relative} schemaVersion must be integer 1")
    if type(claims_document["scopeClosed"]) is not bool:
        raise ValueError(f"{relative} scopeClosed must be a boolean")
    claims = claims_document["claims"]
    if not isinstance(claims, list):
        raise ValueError(f"{relative} claims must be a JSON array")

    normalized: list[dict[str, str]] = []
    seen: set[tuple[str, str, str]] = set()
    for index, claim in enumerate(claims):
        if not isinstance(claim, dict) or set(claim) != {
            "family",
            "surface",
            "description",
        }:
            raise ValueError(
                f"{relative} claims[{index}] must contain exactly "
                "family, surface, and description"
            )
        family = claim["family"]
        surface = claim["surface"]
        description = claim["description"]
        values = {"family": family, "surface": surface, "description": description}
        for field, value in values.items():
            if not isinstance(value, str) or not value.strip() or value != value.strip():
                raise ValueError(
                    f"{relative} claims[{index}].{field} must be a "
                    "trimmed non-empty string"
                )
        if re.fullmatch(r"[a-z][a-z0-9_.-]*", family) is None:
            raise ValueError(
                f"{relative} claims[{index}].family has an invalid token"
            )
        if surface not in CANONICAL_SURFACES:
            raise ValueError(
                f"{relative} claims[{index}].surface has an invalid token"
            )
        identity = (family, surface, description)
        if identity in seen:
            raise ValueError(f"{relative} contains a duplicate claim at index {index}")
        seen.add(identity)
        normalized.append(
            {
                "family": family,
                "surface": surface,
                "description": description,
            }
        )
    return normalized


def unresolved_claim_item(
    claim: dict[str, str], index: int
) -> tuple[dict[str, object], dict[str, object] | None]:
    family = claim["family"]
    surface = claim["surface"]
    description = claim["description"]
    identity = (family, surface, description)
    token = f"CLAIM:{family}@{surface}:{description}"
    salt = json.dumps(identity, ensure_ascii=False, separators=(",", ":"))
    if family in REGISTERED_POLICY_FAMILIES:
        version_feature = (
            "preview-0.18"
            if family.startswith(("widget.", "agent-worker."))
            else "stable-0.17"
        )
        return (
            make_item(
                family,
                token,
                PROJECT_BINDING_UNRESOLVED,
                PROJECT_BINDING_UNRESOLVED,
                CLAIMS_FILENAME,
                index,
                policy_state="binding-unresolved",
                version_feature=version_feature,
                gate_salt=salt,
            ),
            None,
        )
    item = make_item(
        "project.unregistered",
        token,
        PROJECT_BINDING_UNRESOLVED,
        UNREGISTERED_DECLARATION,
        CLAIMS_FILENAME,
        index,
        policy_state="unregistered",
        version_feature="unresolved",
        gate_salt=salt,
    )
    return item, unmatched_entry(item)


def manifest_items(
    manifest: dict[str, Any],
) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    items: list[dict[str, object]] = []
    unmatched: list[dict[str, object]] = []
    relative = "app.json"

    if "pages" not in manifest or not isinstance(manifest["pages"], list):
        raise ValueError("app.json pages must be a JSON array")
    pages = manifest["pages"]
    for index, route in enumerate(pages, start=1):
        if not isinstance(route, str) or not route:
            raise ValueError("app.json pages entries must be non-empty strings")
        items.append(
            make_item(
                "page.route",
                f"app.json#pages:{route}",
                f"app.json#pages:{route}",
                "pages",
                relative,
                index,
            )
        )

    if "window" in manifest:
        window = manifest["window"]
        if not isinstance(window, dict):
            raise ValueError("app.json window must be a JSON object")
        for token in json_leaf_tokens(window, "app.json#window"):
            add_unregistered(items, unmatched, token, relative, 1)

    components = manifest.get("usingComponents", {})
    if not isinstance(components, dict):
        raise ValueError("app.json usingComponents must be a JSON object")
    for index, (name, path) in enumerate(sorted(components.items()), start=1):
        if not name or not isinstance(path, str) or not path:
            raise ValueError(
                "app.json usingComponents entries must map non-empty names to "
                "non-empty string paths"
            )
        add_unregistered(
            items,
            unmatched,
            f"app.json#usingComponents:{name}={path}",
            relative,
            index,
        )

    fonts = manifest.get("fonts", [])
    if not isinstance(fonts, list):
        raise ValueError("app.json fonts must be a JSON array")
    required_font_keys = {"family", "src", "weight", "style"}
    for index, font in enumerate(fonts, start=1):
        if not isinstance(font, dict) or not required_font_keys.issubset(font):
            raise ValueError(
                "app.json fonts entries must contain family, src, weight, and style"
            )
        family = font["family"]
        source = font["src"]
        weight = font["weight"]
        style = font["style"]
        if not isinstance(family, str) or not family:
            raise ValueError("app.json fonts family must be a non-empty string")
        if not isinstance(source, str) or not source:
            raise ValueError("app.json fonts src must be a non-empty string")
        if (type(weight) is not int and not isinstance(weight, str)) or (
            isinstance(weight, str) and not weight
        ):
            raise ValueError("app.json fonts weight must be an integer or string")
        if not isinstance(style, str) or not style:
            raise ValueError("app.json fonts style must be a non-empty string")
        add_unregistered(
            items,
            unmatched,
            f"app.json#fonts:{family}@{source}#{weight}/{style}",
            relative,
            index,
        )
        for key in sorted(set(font) - required_font_keys):
            for token in json_leaf_tokens(font[key], f"app.json#fonts[{index - 1}].{key}"):
                add_unregistered(items, unmatched, token, relative, index)

    permissions = manifest.get("permissions", [])
    if not isinstance(permissions, list):
        raise ValueError("app.json permissions must be a JSON array")
    for index, permission in enumerate(permissions, start=1):
        if not isinstance(permission, str) or not permission:
            raise ValueError("app.json permissions entries must be non-empty strings")
        if permission == "CAMERA":
            items.append(
                make_item(
                    "media.camera.permission",
                    "app.json#permissions:CAMERA",
                    "app.json#permissions",
                    "CAMERA",
                    relative,
                    index,
                )
            )
        else:
            add_unregistered(
                items,
                unmatched,
                f"app.json#permissions:{permission}",
                relative,
                index,
            )

    widgets = manifest.get("widgets", [])
    if not isinstance(widgets, list):
        raise ValueError("app.json widgets must be a JSON array")
    for index, widget in enumerate(widgets, start=1):
        if not isinstance(widget, dict):
            raise ValueError("app.json widgets entries must be JSON objects")
        path = widget.get("path")
        family = widget.get("family")
        if not isinstance(path, str) or not path:
            raise ValueError("app.json widgets path must be a non-empty string")
        if family not in {"1x1", "1x2"}:
            raise ValueError("app.json widgets family must be 1x1 or 1x2")
        items.append(
            make_item(
                "widget.declaration",
                f"app.json#widgets:{path}",
                f"app.json#widgets:{path}",
                f"family:{family}",
                relative,
                index,
                policy_state="version-gated",
                version_feature="preview-0.18",
            )
        )
        for key in sorted(set(widget) - {"path", "family"}):
            for token in json_leaf_tokens(widget[key], f"app.json#widgets[{index - 1}].{key}"):
                add_unregistered(items, unmatched, token, relative, index)

    workers = manifest.get("agentWorkers", [])
    if not isinstance(workers, list):
        raise ValueError("app.json agentWorkers must be a JSON array")
    for index, worker in enumerate(workers, start=1):
        if not isinstance(worker, dict):
            raise ValueError("app.json agentWorkers entries must be JSON objects")
        name = worker.get("name")
        if not isinstance(name, str) or not name:
            raise ValueError("app.json agentWorkers name must be a non-empty string")
        script = worker.get("script")
        if not isinstance(script, str) or not script:
            raise ValueError("app.json agentWorkers script must be a non-empty string")
        trigger = worker.get("trigger")
        if not isinstance(trigger, dict) or trigger != {"type": "open"}:
            raise ValueError(
                'app.json agentWorkers trigger must be exactly {"type":"open"}'
            )
        trigger_type = trigger["type"]
        lifetime = worker.get("lifetime")
        if lifetime not in {"instant", "foreground"}:
            raise ValueError(
                "app.json agentWorkers lifetime must be instant or foreground"
            )
        items.append(
            make_item(
                "agent-worker.declaration",
                f"app.json#agentWorkers:{name}",
                f"app.json#agentWorkers:{name}",
                f"script={script};trigger={trigger_type};lifetime={lifetime}",
                relative,
                index,
                policy_state="version-gated",
                version_feature="preview-0.18",
            )
        )
        capabilities = worker.get("capabilities", [])
        if not isinstance(capabilities, list):
            raise ValueError(
                "app.json agentWorkers capabilities must be a string array"
            )
        for capability in capabilities:
            if not isinstance(capability, str) or not capability:
                raise ValueError(
                    "app.json agentWorkers capabilities entries must be "
                    "non-empty strings"
                )
            items.append(
                make_item(
                    "agent-worker.capability",
                    capability,
                    f"app.json#agentWorkers:{name}.capabilities",
                    capability,
                    relative,
                    index,
                    policy_state="version-gated",
                    version_feature="preview-0.18",
                )
            )
        known_worker_keys = {"name", "script", "trigger", "lifetime", "capabilities"}
        for key in sorted(set(worker) - known_worker_keys):
            for token in json_leaf_tokens(
                worker[key], f"app.json#agentWorkers[{index - 1}].{key}"
            ):
                add_unregistered(items, unmatched, token, relative, index)

    for key in sorted(set(manifest) - KNOWN_MANIFEST_KEYS):
        add_unregistered(items, unmatched, f"app.json#{key}", relative, 1)
    return items, unmatched


def add_registered_source_items(
    markup_text: str,
    code_text: str,
    source_text: str,
    relative: str,
    surface_kind: str,
    items: list[dict[str, object]],
    unmatched_symbols: list[dict[str, object]],
    owned_handler_names: set[str],
    local_owner_offsets: dict[str, set[int]],
) -> None:
    common_patterns = (
        ("ui.button", r"<button\b", "<button>", "<button ...>"),
        ("component.scroll-view", r"<scroll-view\b", "<scroll-view>", "<scroll-view ...>"),
    )
    simple_patterns = common_patterns
    for family, expression, mechanism, api_binding in simple_patterns:
        for match in re.finditer(expression, markup_text, re.IGNORECASE):
            items.append(
                make_item(
                    family,
                    mechanism,
                    api_binding,
                    NO_DECLARATION,
                    relative,
                    *line_and_column(source_text, match.start()),
                )
            )

    for match in re.finditer(
        r":host-focus(?![A-Za-z0-9_-])", style_scan_text(source_text, relative)
    ):
        items.append(
            make_item(
                "focus.host",
                ":host-focus",
                ":host-focus",
                NO_DECLARATION,
                relative,
                *line_and_column(source_text, match.start()),
            )
        )

    structure_code_text = mask_regex_literals(code_text)
    scopes = lexical_scopes(structure_code_text)
    global_declarations = declaration_scopes(
        structure_code_text, scopes, {"fetch", "document"}
    )
    for match in re.finditer(r"(?<![\w.$])fetch\s*\(", structure_code_text):
        if resolved_declaration_scope(
            "fetch", match.start(), scopes, global_declarations
        ) is None:
            items.append(
                make_item(
                    "network.https",
                    "fetch",
                    "fetch(...)",
                    NO_DECLARATION,
                    relative,
                    *line_and_column(source_text, match.start()),
                )
            )

    fetch_aliases: list[tuple[str, int, int]] = []
    for match in re.finditer(
        r"\bconst\s+(?P<alias>[A-Za-z_$][A-Za-z0-9_$]*)\s*=\s*fetch\b",
        structure_code_text,
    ):
        if resolved_declaration_scope(
            "fetch", match.start(), scopes, global_declarations
        ) is None:
            fetch_aliases.append(
                (match.group("alias"), scope_at(scopes, match.start()), match.end())
            )
    if fetch_aliases:
        alias_declarations = declaration_scopes(
            structure_code_text, scopes, {alias for alias, _, _ in fetch_aliases}
        )
        for alias, alias_scope, declaration_end in fetch_aliases:
            for call in re.finditer(
                rf"(?<![A-Za-z0-9_$.]){re.escape(alias)}\s*\(",
                structure_code_text,
            ):
                if call.start() <= declaration_end:
                    continue
                if is_method_declaration(structure_code_text, call.start()):
                    continue
                if (
                    resolved_declaration_scope(
                        alias, call.start(), scopes, alias_declarations
                    )
                    != alias_scope
                ):
                    continue
                items.append(
                    make_item(
                        "network.https",
                        f"fetch-alias:{alias}",
                        "fetch(...)",
                        NO_DECLARATION,
                        relative,
                        *line_and_column(source_text, call.start()),
                    )
                )

    for binding in ("bindtap", "bindfocus", "bindblur"):
        family = "event.bindtap" if binding == "bindtap" else "focus.element"
        pattern = re.compile(
            rf"\b{binding}\s*=\s*[\"'](?P<handler>[A-Za-z_$][A-Za-z0-9_$]*)[\"']"
        )
        for match in pattern.finditer(markup_text):
            handler = match.group("handler")
            resolved = handler in owned_handler_names
            items.append(
                make_item(
                    family,
                    f"{binding}={handler}",
                    f"{binding}={handler}" if resolved else PROJECT_BINDING_UNRESOLVED,
                    NO_DECLARATION if resolved else PROJECT_BINDING_UNRESOLVED,
                    relative,
                    *line_and_column(source_text, match.start()),
                    policy_state="registered" if resolved else "binding-unresolved",
                )
            )

    for symbol, (family, api_binding) in KNOWN_WX_CALLS.items():
        for match in re.finditer(
            rf"(?<![A-Za-z0-9_$.]){re.escape(symbol)}\s*\(", code_text
        ):
            items.append(
                make_item(
                    family,
                    symbol,
                    api_binding,
                    NO_DECLARATION,
                    relative,
                    *line_and_column(source_text, match.start()),
                )
            )

    if surface_kind == "page":
        for callback in ("onLoad", "onShow", "onReady", "onHide", "onUnload"):
            for offset in sorted(local_owner_offsets.get(callback, set())):
                items.append(
                    make_item(
                        "page.lifecycle",
                        f"CALLBACK:{callback}",
                        f"CALLBACK:{callback}",
                        NO_DECLARATION,
                        relative,
                        *line_and_column(source_text, offset),
                    )
                )

        callback_bindings = (
            (
                "onTargetChanged",
                "page.target",
                "onTargetChanged",
                "onTargetChanged(target,previousTarget)",
            ),
            ("onHostFocus", "focus.host", "onHostFocus", "onHostFocus()"),
            ("onHostBlur", "focus.host", "onHostBlur", "onHostBlur()"),
            (
                "onVoiceWakeup",
                "input.voice-wakeup",
                "onVoiceWakeup",
                "onVoiceWakeup(event)",
            ),
        )
        for callback, family, mechanism, api_binding in callback_bindings:
            for offset in sorted(local_owner_offsets.get(callback, set())):
                items.append(
                    make_item(
                        family,
                        mechanism,
                        api_binding,
                        NO_DECLARATION,
                        relative,
                        *line_and_column(source_text, offset),
                    )
                )

        for match in re.finditer(
            r"(?<![A-Za-z0-9_$])(?:this\.)?enableWorldAwareness\s*\(",
            code_text,
        ):
            items.append(
                make_item(
                    "page.world-awareness",
                    "enableWorldAwareness",
                    "enableWorldAwareness(...)",
                    NO_DECLARATION,
                    relative,
                    *line_and_column(source_text, match.start()),
                )
            )

        for match in re.finditer(
            r"@media\s*\(\s*target\s*:\s*(?P<target>_current|_blank)\s*\)",
            markup_text,
            re.IGNORECASE,
        ):
            target = match.group("target")
            target_offset = match.start("target")
            items.append(
                make_item(
                    "page.target",
                    f"target:{target}",
                    f"target:{target}",
                    NO_DECLARATION,
                    relative,
                    *line_and_column(source_text, target_offset),
                )
            )

        def record_key_event(
            callback_name: str, code: str, absolute_offset: int
        ) -> None:
            family = {
                "Enter": "input.enter",
                "Backspace": "input.back",
                "ArrowUp": "input.scroll.host",
                "ArrowDown": "input.scroll.host",
            }.get(code)
            api_binding = f"{callback_name}(event.code={code})"
            if family:
                items.append(
                    make_item(
                        family,
                        api_binding,
                        api_binding,
                        NO_DECLARATION,
                        relative,
                        *line_and_column(source_text, absolute_offset),
                    )
                )
            else:
                add_unregistered(
                    items,
                    unmatched_symbols,
                    api_binding,
                    relative,
                    *line_and_column(source_text, absolute_offset),
                )

        callback_text = mask_comments(source_text)
        for method_match, body, body_offset in method_bodies(
            callback_text,
            r"\b(?P<callback>onKey(?:Down|Up))\s*\([^)]*\)\s*\{",
        ):
            callback_name = method_match.group("callback")
            if method_match.start("callback") not in local_owner_offsets.get(
                callback_name, set()
            ):
                continue
            for match in re.finditer(
                r"event\.code\s*(?:===|!==|==|!=)\s*[\"']"
                r"(?P<code>[A-Za-z0-9_-]+)[\"']",
                body,
            ):
                record_key_event(
                    callback_name, match.group("code"), body_offset + match.start()
                )

        for method_match, body, body_offset in method_bodies(
            structure_code_text,
            r"\b(?P<callback>onKey(?:Down|Up))\s*\([^)]*\)\s*\{",
        ):
            callback_name = method_match.group("callback")
            if method_match.start("callback") not in local_owner_offsets.get(
                callback_name, set()
            ):
                continue
            for _, switch_body, switch_body_offset in method_bodies(
                body, r"\bswitch\s*\(\s*event\.code\s*\)\s*\{"
            ):
                absolute_body_offset = body_offset + switch_body_offset
                source_switch_body = source_text[
                    absolute_body_offset : absolute_body_offset + len(switch_body)
                ]
                for code, case_offset in direct_case_literals(
                    switch_body, source_switch_body
                ):
                    record_key_event(
                        callback_name, code, absolute_body_offset + case_offset
                    )


def add_speech_inventory(
    text: str,
    code_text: str,
    relative: str,
    items: list[dict[str, object]],
    unmatched_symbols: list[dict[str, object]],
) -> None:
    scopes = lexical_scopes(code_text)
    constructor_pattern = re.compile(
        r"(?:"
        r"(?:(?:const|let|var)\s+(?P<variable>[A-Za-z_$][A-Za-z0-9_$]*)\s*=\s*)"
        r"|(?:this\.(?P<property>[A-Za-z_$][A-Za-z0-9_$]*)\s*=\s*)"
        r")?\bnew\s+SpeechRecognition\s*\("
    )
    speech_global_declarations = declaration_scopes(
        code_text, scopes, {"SpeechRecognition"}
    )
    constructors: list[dict[str, object]] = []
    for match in constructor_pattern.finditer(code_text):
        new_offset = code_text.find("new", match.start(), match.end())
        speech_name_offset = code_text.find(
            "SpeechRecognition", new_offset, match.end()
        )
        if resolved_declaration_scope(
            "SpeechRecognition",
            speech_name_offset,
            scopes,
            speech_global_declarations,
        ) is not None:
            continue
        opening = code_text.find("(", new_offset, match.end())
        closing = matching_delimiter(code_text, opening, "(", ")")
        constructors.append(
            {
                "variable": match.group("variable"),
                "property": match.group("property"),
                "offset": new_offset,
                "closing": closing,
                "scope": scope_at(scopes, new_offset),
            }
        )

    candidate_names = {
        str(constructor["variable"])
        for constructor in constructors
        if constructor["variable"] is not None
    }
    declarations = declaration_scopes(code_text, scopes, candidate_names)
    speech_by_scope_name: dict[tuple[int, str], list[int]] = {}
    for constructor_id, constructor in enumerate(constructors):
        variable = constructor["variable"]
        if variable is not None:
            speech_by_scope_name.setdefault(
                (int(constructor["scope"]), str(variable)), []
            ).append(constructor_id)

    def resolve_identifier(name: str, offset: int) -> tuple[str, int | None]:
        declaration_scope = resolved_declaration_scope(
            name, offset, scopes, declarations
        )
        if declaration_scope is None:
            return "unknown", None
        candidates = speech_by_scope_name.get((declaration_scope, name), [])
        if len(candidates) == 1:
            return "speech", candidates[0]
        if candidates:
            return "ambiguous", None
        return "non-speech", None

    property_history: dict[tuple[int, str], list[tuple[int, int | None]]] = {}
    speech_properties: set[str] = set()
    for constructor_id, constructor in enumerate(constructors):
        property_name = constructor["property"]
        if property_name is not None:
            property_history.setdefault(
                (int(constructor["scope"]), str(property_name)), []
            ).append((int(constructor["offset"]), constructor_id))
            speech_properties.add(str(property_name))

    for assignment in re.finditer(
        r"\bthis\.(?P<property>[A-Za-z_$][A-Za-z0-9_$]*)\s*=\s*"
        r"(?P<source>[A-Za-z_$][A-Za-z0-9_$]*)\b",
        code_text,
    ):
        source = assignment.group("source")
        if source == "new":
            continue
        assignment_scope = scope_at(scopes, assignment.start())
        status, constructor_id = resolve_identifier(source, assignment.start())
        property_name = assignment.group("property")
        if status == "speech":
            speech_properties.add(property_name)
        property_history.setdefault((assignment_scope, property_name), []).append(
            (assignment.start(), constructor_id if status == "speech" else None)
        )
    for history in property_history.values():
        history.sort()

    started: set[int] = set()
    for constructor_id, constructor in enumerate(constructors):
        closing = constructor["closing"]
        if closing is not None and re.match(
            r"\s*\.\s*start\s*\(", code_text[int(closing) + 1 :]
        ):
            started.add(constructor_id)

    for call in re.finditer(
        r"(?<![A-Za-z0-9_$.])(?P<variable>[A-Za-z_$][A-Za-z0-9_$]*)"
        r"\.(?P<method>start|stop)\s*\(",
        code_text,
    ):
        variable = call.group("variable")
        status, constructor_id = resolve_identifier(variable, call.start())
        if status == "speech" and constructor_id is not None:
            if call.group("method") == "start":
                started.add(constructor_id)
        elif status == "ambiguous":
            add_unregistered(
                items,
                unmatched_symbols,
                f"SpeechRecognition.{call.group('method')}:instance-association",
                relative,
                *line_and_column(text, call.start()),
            )

    for call in re.finditer(
        r"\bthis\.(?P<property>[A-Za-z_$][A-Za-z0-9_$]*)"
        r"\.(?P<method>start|stop)\s*\(",
        code_text,
    ):
        property_name = call.group("property")
        call_scope = scope_at(scopes, call.start())
        preceding = [
            entry
            for entry in property_history.get((call_scope, property_name), [])
            if entry[0] < call.start()
        ]
        constructor_id = preceding[-1][1] if preceding else None
        if constructor_id is not None:
            if call.group("method") == "start":
                started.add(constructor_id)
        elif property_name in speech_properties:
            add_unregistered(
                items,
                unmatched_symbols,
                f"SpeechRecognition.{call.group('method')}:instance-association",
                relative,
                *line_and_column(text, call.start()),
            )

    for constructor_id, constructor in enumerate(constructors):
        constructor_offset = int(constructor["offset"])
        if constructor_id not in started:
            add_unregistered(
                items,
                unmatched_symbols,
                "new SpeechRecognition:instance-start-association",
                relative,
                *line_and_column(text, constructor_offset),
            )
            continue
        line, column = line_and_column(text, constructor_offset)
        companion = make_item(
            "voice.declaration.unknown",
            "SpeechRecognition declaration",
            PROJECT_BINDING_UNRESOLVED,
            PROJECT_BINDING_UNRESOLVED,
            relative,
            line,
            column,
            policy_state="binding-unresolved",
        )
        items.append(companion)
        items.append(
            make_item(
                "ai.speech-recognition",
                "new SpeechRecognition",
                "new SpeechRecognition()->recognition.start()",
                f"COMPANION:voice.declaration.unknown@{companion['gate']}",
                relative,
                line,
                column,
            )
        )


def is_import_binding(code_text: str, offset: int) -> bool:
    line_start = code_text.rfind("\n", 0, offset) + 1
    return re.search(r"\bimport\b", code_text[line_start:offset]) is not None


def add_platform_quarantines(
    text: str,
    code_text: str,
    relative: str,
    items: list[dict[str, object]],
    unmatched_symbols: list[dict[str, object]],
) -> None:
    def quarantine(token: str, offset: int) -> None:
        add_unregistered(
            items,
            unmatched_symbols,
            token,
            relative,
            *line_and_column(text, offset),
        )

    scopes = lexical_scopes(code_text)
    global_declarations = declaration_scopes(
        code_text, scopes, {"fetch", "document", "SpeechRecognition"}
    )

    namespace_pattern = re.compile(
        r"(?<![A-Za-z0-9_$.])(?P<symbol>(?:window|globalThis)"
        r"(?:\.[A-Za-z_$][A-Za-z0-9_$]*)*)"
    )
    for match in namespace_pattern.finditer(code_text):
        symbol = match.group("symbol")
        remainder = code_text[match.end() :]
        if re.match(r"\s*\(", remainder):
            quarantine(f"{symbol}(...)", match.start())
        else:
            quarantine(f"REFERENCE:{symbol}", match.start())

    for match in re.finditer(
        r"(?<![A-Za-z0-9_$.])(?P<symbol>document"
        r"(?:\.[A-Za-z_$][A-Za-z0-9_$]*)*)",
        code_text,
    ):
        if any(
            match.start() in offsets
            for (scope_id, name), offsets in global_declarations.items()
            if name == "document"
        ):
            continue
        if resolved_declaration_scope(
            "document", match.start(), scopes, global_declarations
        ) is not None:
            continue
        symbol = match.group("symbol")
        if re.match(r"\s*\(", code_text[match.end() :]):
            quarantine(f"{symbol}(...)", match.start())
        else:
            quarantine(f"REFERENCE:{symbol}", match.start())

    for match in re.finditer(
        r"(?<![A-Za-z0-9_$.])(?P<symbol>wx(?:\.[A-Za-z_$][A-Za-z0-9_$]*)*)"
        r"\s*\(",
        code_text,
    ):
        symbol = match.group("symbol")
        if symbol not in KNOWN_WX_CALLS:
            quarantine(f"{symbol}(...)", match.start())

    for match in re.finditer(
        r"(?<![A-Za-z0-9_$.])(?P<symbol>wx(?:\.[A-Za-z_$][A-Za-z0-9_$]*)*)",
        code_text,
    ):
        if is_import_binding(code_text, match.start()):
            continue
        if re.match(r"\s*\(", code_text[match.end() :]):
            continue
        quarantine(f"REFERENCE:{match.group('symbol')}", match.start())

    for match in re.finditer(
        r"(?<![A-Za-z0-9_$.])(?P<symbol>navigator"
        r"(?:\.[A-Za-z_$][A-Za-z0-9_$]*)*)\s*\(",
        code_text,
    ):
        symbol = match.group("symbol")
        if symbol != "navigator.mediaDevices.getUserMedia":
            quarantine(f"{symbol}(...)", match.start())

    for match in re.finditer(
        r"(?<![A-Za-z0-9_$.])(?P<symbol>navigator"
        r"(?:\.[A-Za-z_$][A-Za-z0-9_$]*)*)",
        code_text,
    ):
        if re.match(r"\s*\(", code_text[match.end() :]):
            continue
        quarantine(f"REFERENCE:{match.group('symbol')}", match.start())

    for match in re.finditer(
        r"(?<![A-Za-z0-9_$.])(?P<symbol>(?:localStorage|sessionStorage)"
        r"(?:\.[A-Za-z_$][A-Za-z0-9_$]*)*)",
        code_text,
    ):
        symbol = match.group("symbol")
        if re.match(r"\s*\(", code_text[match.end() :]):
            quarantine(f"{symbol}(...)", match.start())
        else:
            quarantine(f"REFERENCE:{symbol}", match.start())

    for symbol in sorted(REFERENCE_GLOBALS - {"localStorage", "sessionStorage"}):
        for match in re.finditer(
            rf"(?<![A-Za-z0-9_$.]){re.escape(symbol)}\b", code_text
        ):
            if symbol == "SpeechRecognition":
                if any(
                    match.start() in offsets
                    for (scope_id, name), offsets in global_declarations.items()
                    if name == symbol
                ):
                    continue
                if resolved_declaration_scope(
                    symbol, match.start(), scopes, global_declarations
                ) is not None:
                    continue
                prefix = code_text[max(0, match.start() - 16) : match.start()]
                if re.search(r"\b(?:new|typeof)\s*$", prefix):
                    continue
            if is_import_binding(code_text, match.start()):
                continue
            if re.match(r"\s*\(", code_text[match.end() :]):
                if symbol in GLOBAL_CALLS_TO_QUARANTINE:
                    quarantine(f"{symbol}(...)", match.start())
                continue
            quarantine(f"REFERENCE:{symbol}", match.start())


def add_callback_surface_inventory(
    text: str,
    relative: str,
    surface_kind: str,
    all_owner_offsets: dict[str, set[int]],
    direct_owner_offsets: dict[str, set[int]],
    bound_handler_names: set[str],
    items: list[dict[str, object]],
    unmatched_symbols: list[dict[str, object]],
) -> None:
    allowed = {
        "page": PAGE_CALLBACKS,
        "widget": WIDGET_CALLBACKS,
        "worker": WORKER_CALLBACKS,
    }.get(surface_kind, frozenset())
    label = SURFACE_LABELS[surface_kind]
    for callback, offsets in all_owner_offsets.items():
        if re.fullmatch(r"on[A-Z][A-Za-z0-9_$]*", callback) is None:
            continue
        if callback in bound_handler_names:
            continue
        for offset in sorted(offsets):
            if offset not in direct_owner_offsets.get(callback, set()):
                token = f"{label}.{callback}:owner-unresolved"
            elif callback in KNOWN_PLATFORM_CALLBACKS:
                if callback in allowed:
                    continue
                token = f"{label}.{callback}"
            else:
                token = callback
            add_unregistered(
                items,
                unmatched_symbols,
                token,
                relative,
                *line_and_column(text, offset),
            )


def item_declared_surfaces(
    item: dict[str, object], source_surface_kinds: dict[str, str]
) -> set[str]:
    location = item["locations"][0]
    path = str(location["path"])
    family = str(item["family"])
    surfaces: set[str] = set()
    source_surface = source_surface_kinds.get(owner_key(path))
    if source_surface:
        surfaces.add(source_surface)
    if path == "app.json":
        if family == "page.route":
            surfaces.add("Page")
        elif family.startswith("widget."):
            surfaces.add("Widget")
        elif family.startswith("agent-worker."):
            surfaces.add("Agent Worker")
        else:
            surfaces.add("App")
    mechanism = str(item["mechanism"])
    if family == "page.target" and mechanism.startswith("target:"):
        surfaces.add(mechanism.removeprefix("target:"))
    return surfaces


def reconcile_claims(
    claims: list[dict[str, str]],
    items: list[dict[str, object]],
    unmatched_symbols: list[dict[str, object]],
    _source_surface_kinds: dict[str, str],
) -> None:
    """Keep every product claim distinct until source binds it explicitly.

    Family and surface equality cannot prove that a discovered source call
    implements the behavior described by the claim.  The closed ledger
    therefore emits one unresolved gate per claim instead of borrowing an
    arbitrary same-family source item.
    """
    for claim_index, claim in enumerate(claims, start=1):
        item, unmatched = unresolved_claim_item(claim, claim_index)
        items.append(item)
        if unmatched is not None:
            unmatched_symbols.append(unmatched)


def inventory_project(project_root: Path, target_version: str) -> dict[str, object]:
    root = project_root.resolve()
    revision_before = fingerprint_project(root)
    items: list[dict[str, object]] = []
    unmatched_symbols: list[dict[str, object]] = []
    claims: list[dict[str, str]] = []
    claims_ledger: dict[str, object] = {
        "path": CLAIMS_FILENAME,
        "present": False,
        "scopeClosed": False,
        "sha256": None,
        "claimCount": 0,
    }

    app_json_path = root / "app.json"
    worker_scripts: set[str] = set()
    if app_json_path.is_file():
        manifest = json.loads(
            app_json_path.read_text(encoding="utf-8"),
            object_pairs_hook=reject_duplicate_json_keys,
        )
        if not isinstance(manifest, dict):
            raise ValueError("app.json root must be an object")
        manifest_entries, manifest_unmatched = manifest_items(manifest)
        items.extend(manifest_entries)
        unmatched_symbols.extend(manifest_unmatched)
        workers = manifest.get("agentWorkers", [])
        worker_scripts = {worker["script"] for worker in workers}
        camera_permission_declared = "CAMERA" in manifest.get("permissions", [])
    else:
        raise ValueError("app.json is required for capability inventory")

    claims_path = root / CLAIMS_FILENAME
    if claims_path.is_file():
        claims_bytes = claims_path.read_bytes()
        claims_document = json.loads(
            claims_bytes.decode("utf-8"),
            object_pairs_hook=reject_duplicate_json_keys,
        )
        if not isinstance(claims_document, dict):
            raise ValueError(f"{CLAIMS_FILENAME} root must be an object")
        claims = claims_items(claims_document)
        claims_ledger = {
            "path": CLAIMS_FILENAME,
            "present": True,
            "scopeClosed": claims_document["scopeClosed"],
            "sha256": hashlib.sha256(claims_bytes).hexdigest(),
            "claimCount": len(claims),
        }

    source_units: list[
        tuple[
            str,
            str,
            str,
            str,
            str,
            dict[str, set[int]],
            dict[str, set[int]],
        ]
    ] = []
    owner_handlers: dict[str, set[str]] = {}
    owner_bound_handlers: dict[str, set[str]] = {}
    source_surface_kinds: dict[str, str] = {}
    for candidate in sorted(root.rglob("*")):
        relative_path = candidate.relative_to(root)
        if relative_path.parts and relative_path.parts[0] in EXCLUDED_TOP_LEVEL_DIRECTORIES:
            continue
        if not candidate.is_file() or candidate.suffix.lower() not in SOURCE_SUFFIXES:
            continue
        relative = relative_path.as_posix()
        if relative in {"app.json", CLAIMS_FILENAME}:
            continue
        text = candidate.read_text(encoding="utf-8")
        scan_text = markup_scan_text(text, relative)
        code_text = executable_code_text(text, relative)
        if relative in worker_scripts:
            surface_kind = "worker"
        elif relative.startswith("widgets/"):
            surface_kind = "widget"
        elif relative in {"app.js", "app.ts", "app.ink"}:
            surface_kind = "app"
        elif relative.startswith("pages/"):
            surface_kind = "page"
        else:
            surface_kind = "shared"
        all_members = exported_object_members(code_text)
        direct_members = exported_object_members(code_text, include_methods=False)
        key = owner_key(relative)
        audit_surface = AUDIT_SURFACE_BY_SOURCE_KIND.get(surface_kind)
        if audit_surface is not None:
            source_surface_kinds[key] = audit_surface
        owner_handlers.setdefault(key, set()).update(all_members)
        owner_bound_handlers.setdefault(key, set()).update(
            match.group("handler")
            for match in re.finditer(
                r"\b(?:bind|catch)[A-Za-z0-9_-]+\s*=\s*[\"']"
                r"(?P<handler>[A-Za-z_$][A-Za-z0-9_$]*)[\"']",
                scan_text,
            )
        )
        source_units.append(
            (
                relative,
                text,
                scan_text,
                code_text,
                surface_kind,
                all_members,
                direct_members,
            )
        )

    for (
        relative,
        text,
        scan_text,
        code_text,
        surface_kind,
        all_members,
        direct_members,
    ) in source_units:
        key = owner_key(relative)
        bound_handler_names = owner_bound_handlers.get(key, set())
        add_registered_source_items(
            scan_text,
            code_text,
            text,
            relative,
            surface_kind,
            items,
            unmatched_symbols,
            owner_handlers.get(key, set()),
            direct_members,
        )

        if surface_kind == "widget":
            for callback in sorted(WIDGET_CALLBACKS):
                for offset in sorted(direct_members.get(callback, set())):
                    items.append(
                        make_item(
                            "widget.lifecycle",
                            f"{callback}()",
                            f"{callback}()",
                            NO_DECLARATION,
                            relative,
                            *line_and_column(text, offset),
                            policy_state="version-gated",
                            version_feature="preview-0.18",
                        )
                    )

        wait_until_consumed: set[int] = set()
        if relative in worker_scripts:
            for offset in sorted(direct_members.get("onOpen", set())):
                items.append(
                    make_item(
                        "agent-worker.on-open",
                        "onOpen(event)",
                        "onOpen(event)",
                        NO_DECLARATION,
                        relative,
                        *line_and_column(text, offset),
                        policy_state="version-gated",
                        version_feature="preview-0.18",
                    )
                )
            for method_match, body, body_offset in method_bodies(
                code_text, r"\b(?P<callback>onOpen)\s*\([^)]*\)\s*\{"
            ):
                if method_match.start("callback") not in direct_members.get(
                    "onOpen", set()
                ):
                    continue
                for match in re.finditer(r"\bevent\.waitUntil\s*\(", body):
                    absolute_offset = body_offset + match.start()
                    wait_until_consumed.add(absolute_offset)
                    items.append(
                        make_item(
                            "agent-worker.wait-until",
                            "event.waitUntil(promise)",
                            "event.waitUntil(promise)",
                            NO_DECLARATION,
                            relative,
                            *line_and_column(text, absolute_offset),
                            policy_state="version-gated",
                            version_feature="preview-0.18",
                        )
                    )
        for match in re.finditer(r"\bevent\.waitUntil\s*\(", code_text):
            if match.start() in wait_until_consumed:
                continue
            add_unregistered(
                items,
                unmatched_symbols,
                f"{SURFACE_LABELS[surface_kind]}.event.waitUntil",
                relative,
                *line_and_column(text, match.start()),
            )

        cleanup_match = re.search(
            r"\b(?P<stream>[A-Za-z_$][A-Za-z0-9_$]*)\.getTracks\(\)"
            r"\.forEach\(\s*\(?\s*(?P<track>[A-Za-z_$][A-Za-z0-9_$]*)"
            r"\s*\)?\s*=>\s*(?:\{\s*)?(?P=track)\.stop\(\)",
            code_text,
        )
        camera_stream_variables: set[str] = set()
        media_runtime_matches = list(
            re.finditer(
                r"(?<![A-Za-z0-9_$.])navigator\.mediaDevices\.getUserMedia\s*\(",
                code_text,
            )
        )
        media_runtime_details: list[tuple[re.Match[str], bool]] = []
        for media_match in media_runtime_matches:
            opening = code_text.find("(", media_match.start(), media_match.end())
            closing = matching_delimiter(code_text, opening, "(", ")")
            arguments = code_text[opening + 1 : closing] if closing is not None else ""
            has_video_true = re.search(
                r"(?:^|[{,])\s*video\s*:\s*true\s*(?:[,}])", arguments
            ) is not None
            media_runtime_details.append((media_match, has_video_true))
            prefix = code_text[max(0, media_match.start() - 160) : media_match.start()]
            assignment = re.search(
                r"(?:const|let|var)\s+(?P<stream>[A-Za-z_$][A-Za-z0-9_$]*)"
                r"\s*=\s*(?:await\s*)?$",
                prefix,
            )
            if assignment and has_video_true and camera_permission_declared:
                camera_stream_variables.add(assignment.group("stream"))
        get_tracks = re.search(
            r"\b[A-Za-z_$][A-Za-z0-9_$]*\.getTracks\s*\(", code_text
        )
        stop_call = re.search(
            r"\b[A-Za-z_$][A-Za-z0-9_$]*\.stop\s*\(", code_text
        )
        if cleanup_match and cleanup_match.group("stream") in camera_stream_variables:
            items.append(
                make_item(
                    "media.camera.lifecycle",
                    "MediaStream.getTracks()->MediaStreamTrack.stop()",
                    "MediaStream.getTracks()->MediaStreamTrack.stop()",
                    "CAMERA",
                    relative,
                    *line_and_column(text, cleanup_match.start()),
                )
            )
        elif cleanup_match or get_tracks or stop_call:
            candidate = cleanup_match or get_tracks or stop_call
            add_unregistered(
                items,
                unmatched_symbols,
                "media-cleanup-association",
                relative,
                *line_and_column(text, candidate.start()),
            )

        for match, has_video_true in media_runtime_details:
            if has_video_true and camera_permission_declared:
                api_binding = "navigator.mediaDevices.getUserMedia(video=true)"
                policy_state = "registered"
            else:
                api_binding = PROJECT_BINDING_UNRESOLVED
                policy_state = "binding-unresolved"
            items.append(
                make_item(
                    "media.camera.runtime",
                    "navigator.mediaDevices.getUserMedia",
                    api_binding,
                    "CAMERA" if policy_state == "registered" else PROJECT_BINDING_UNRESOLVED,
                    relative,
                    *line_and_column(text, match.start()),
                    policy_state=policy_state,
                )
            )

        if surface_kind == "page":
            has_world_awareness = re.search(
                r"(?<![A-Za-z0-9_$])(?:this\.)?enableWorldAwareness\s*\(",
                code_text,
            ) is not None
            for callback_name in ("onHeadGesture", "onHeadGestureStateChange"):
                for offset in sorted(direct_members.get(callback_name, set())):
                    callback = f"{callback_name}(event)"
                    if has_world_awareness:
                        api_binding = f"enableWorldAwareness(...)+{callback}"
                        declaration_binding = NO_DECLARATION
                        policy_state = "registered"
                    else:
                        api_binding = PROJECT_BINDING_UNRESOLVED
                        declaration_binding = PROJECT_BINDING_UNRESOLVED
                        policy_state = "binding-unresolved"
                    items.append(
                        make_item(
                            "input.head-gesture",
                            callback,
                            api_binding,
                            declaration_binding,
                            relative,
                            *line_and_column(text, offset),
                            policy_state=policy_state,
                        )
                    )

        add_speech_inventory(
            text, code_text, relative, items, unmatched_symbols
        )
        add_platform_quarantines(
            text, code_text, relative, items, unmatched_symbols
        )

        for match in re.finditer(
            r"\b(?P<binding>(?:bind|catch)[A-Za-z0-9_-]+)\s*=\s*"
            r"[\"'](?P<value>[^\"']*)[\"']",
            scan_text,
        ):
            binding = match.group("binding")
            value = match.group("value")
            static_known_binding = (
                binding in KNOWN_TEMPLATE_BINDINGS
                and re.fullmatch(r"[A-Za-z_$][A-Za-z0-9_$]*", value) is not None
            )
            if not static_known_binding:
                add_unregistered(
                    items,
                    unmatched_symbols,
                    f"{binding}={value}",
                    relative,
                    *line_and_column(text, match.start()),
                )

        for match in re.finditer(
            r"<(?P<tag>[a-z][a-z0-9-]*)\b", scan_text, re.IGNORECASE
        ):
            tag = match.group("tag").lower()
            if tag not in STRUCTURAL_TAGS | {"button", "scroll-view"}:
                add_unregistered(
                    items,
                    unmatched_symbols,
                    f"<{tag}>",
                    relative,
                    *line_and_column(text, match.start()),
                )

        add_callback_surface_inventory(
            text,
            relative,
            surface_kind,
            all_members,
            direct_members,
            bound_handler_names,
            items,
            unmatched_symbols,
        )

    reconcile_claims(
        claims,
        items,
        unmatched_symbols,
        source_surface_kinds,
    )

    unique_items = {(item["family"], item["gate"]): item for item in items}
    ordered_items = [unique_items[key] for key in sorted(unique_items)]
    unique_unmatched = {
        (
            entry["gate"],
            entry["symbol"],
            entry["path"],
            entry["line"],
            entry.get("column", 1),
        ): entry
        for entry in unmatched_symbols
    }
    ordered_unmatched = [unique_unmatched[key] for key in sorted(unique_unmatched)]
    revision_after = fingerprint_project(root)
    if revision_before != revision_after:
        raise ValueError("project changed while capability inventory was running")
    version_violations = []
    if target_version == "0.17.0" and app_json_path.is_file():
        for feature in ("widgets", "agentWorkers"):
            if feature in manifest:
                version_violations.append(
                    {
                        "feature": feature,
                        "minimumVersion": "0.18.0",
                        "targetVersion": target_version,
                    }
                )
    supported_surfaces = {claim["surface"] for claim in claims}
    for item in ordered_items:
        declared_surface = DECLARED_SURFACE_BY_FAMILY.get(str(item["family"]))
        if declared_surface:
            supported_surfaces.add(declared_surface)
        if item["family"] == "page.target" and str(item["mechanism"]).startswith(
            "target:"
        ):
            supported_surfaces.add(str(item["mechanism"]).removeprefix("target:"))
    input_gates = sorted(
        (
            {
                "family": str(item["family"]),
                "kind": INPUT_KIND_BY_FAMILY[str(item["family"])],
                "gate": str(item["gate"]),
            }
            for item in ordered_items
            if str(item["family"]) in INPUT_KIND_BY_FAMILY
        ),
        key=lambda entry: (entry["kind"], entry["gate"], entry["family"]),
    )
    return {
        "schemaVersion": 2,
        "targetVersion": target_version,
        "policyVersion": (
            "aiui-0.17-policy-v1"
            if target_version == "0.17.0"
            else "aiui-0.18-inventory-v1"
        ),
        "projectRevision": revision_after,
        "claimsLedger": claims_ledger,
        "supportedSurfaces": sorted(supported_surfaces),
        "inputGates": input_gates,
        "items": ordered_items,
        "claimedCapabilities": sorted(
            f"{item['family']}@{item['gate']}" for item in ordered_items
        ),
        "unmatchedSymbols": ordered_unmatched,
        "versionViolations": version_violations,
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Scan an AIUI Studio import root for release-sensitive symbols and "
            "emit a deterministic, source-bound capability ledger. Unregistered "
            "symbols are quarantined instead of guessed or silently dropped."
        )
    )
    parser.add_argument("project_root", type=Path, help="AIUI Studio import root")
    parser.add_argument(
        "--target-version",
        required=True,
        choices=("0.17.0", "0.18.0"),
        help="canonical AIUI target version",
    )
    args = parser.parse_args()
    try:
        report = inventory_project(args.project_root, args.target_version)
    except (OSError, UnicodeError, ValueError, json.JSONDecodeError) as error:
        parser.error(str(error))
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
