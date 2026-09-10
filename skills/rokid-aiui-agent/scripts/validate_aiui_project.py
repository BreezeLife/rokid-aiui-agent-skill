#!/usr/bin/env python3
"""Dependency-free structural validator for ROKID AIUI projects."""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path, PurePosixPath
from typing import Any, Dict, List, Optional, Sequence


CLOSED_MARKUP_COMMENT_RE = re.compile(r"<!--.*?-->", re.DOTALL)
MUSTACHE_RE = re.compile(r"{{.*?}}", re.DOTALL)
SCRIPT_OPEN_RE = re.compile(r"<script\b([^>]*)>", re.IGNORECASE)
SCRIPT_BLOCK_RE = re.compile(
    r"<script\b([^>]*)>(.*?)</script\s*>", re.IGNORECASE | re.DOTALL
)
STYLE_OPEN_RE = re.compile(r"<style\b[^>]*>", re.IGNORECASE)
STYLE_BLOCK_RE = re.compile(r"<style\b[^>]*>.*?</style\s*>", re.IGNORECASE | re.DOTALL)
TARGET_VERSION_RE = re.compile(r"^(?P<major>\d+)\.(?P<minor>\d+)\.(?P<patch>\d+)$")
WX_TEMPLATE_CONTROL_RE = re.compile(
    r"wx:(?:if|elif|else|for|for-item|for-index|key)",
    re.IGNORECASE,
)
RESERVED_PATH_NAMES = frozenset({".git", ".aiui-evidence"})
RESERVED_SOURCE_REFERENCE_RE = re.compile(
    r"(?<![A-Za-z0-9_.-])(?:\.git|\.aiui-evidence)"
    r"(?:[\\/]|(?![A-Za-z0-9_.-]))",
    re.IGNORECASE,
)
RUNTIME_RESERVED_PATH_RE = re.compile(
    r"(?P<path>(?:(?:\.\.?)[\\/])*(?P<segment>\.git|\.aiui-evidence)"
    r"(?:[\\/][A-Za-z0-9_.-]+)*)",
    re.IGNORECASE,
)
JS_ASCII_ESCAPE_RE = re.compile(
    r"\\x(?P<hex>[0-9A-Fa-f]{2})|"
    r"\\u(?P<unicode>[0-9A-Fa-f]{4})|"
    r"\\u\{(?P<braced>[0-9A-Fa-f]{1,6})\}"
)


def mask_code_comments(source: str) -> str:
    """Blank JS-style comments while retaining strings and line boundaries."""

    output = list(source)
    state = "code"
    index = 0
    while index < len(source):
        character = source[index]
        following = source[index + 1] if index + 1 < len(source) else ""
        if state == "code":
            if character == "'":
                state = "single"
            elif character == '"':
                state = "double"
            elif character == "`":
                state = "template"
            elif character == "/" and following == "/":
                output[index] = output[index + 1] = " "
                state = "line-comment"
                index += 1
            elif character == "/" and following == "*":
                output[index] = output[index + 1] = " "
                state = "block-comment"
                index += 1
        elif state == "line-comment":
            if character == "\n":
                state = "code"
            else:
                output[index] = " "
        elif state == "block-comment":
            if character == "*" and following == "/":
                output[index] = output[index + 1] = " "
                state = "code"
                index += 1
            elif character != "\n":
                output[index] = " "
        elif character == "\\":
            index += 1
        elif (
            (state == "single" and character == "'")
            or (state == "double" and character == '"')
            or (state == "template" and character == "`")
        ):
            state = "code"
        index += 1
    return "".join(output)


def mask_javascript_regex_literals(source: str) -> str:
    """Mask regex literals without changing strings, offsets, or newlines."""

    structure = list(source)
    state = "code"
    index = 0
    while index < len(source):
        character = source[index]
        following = source[index + 1] if index + 1 < len(source) else ""
        if state == "code":
            if character == "'":
                structure[index] = " "
                state = "single"
            elif character == '"':
                structure[index] = " "
                state = "double"
            elif character == "`":
                structure[index] = " "
                state = "template"
            elif character == "/" and following == "/":
                structure[index] = structure[index + 1] = " "
                state = "line-comment"
                index += 1
            elif character == "/" and following == "*":
                structure[index] = structure[index + 1] = " "
                state = "block-comment"
                index += 1
        elif state == "line-comment":
            if character == "\n":
                state = "code"
            else:
                structure[index] = " "
        elif state == "block-comment":
            if character == "*" and following == "/":
                structure[index] = structure[index + 1] = " "
                state = "code"
                index += 1
            elif character != "\n":
                structure[index] = " "
        else:
            structure[index] = "\n" if character == "\n" else " "
            if character == "\\":
                index += 1
                if index < len(source) and source[index] != "\n":
                    structure[index] = " "
            elif (
                (state == "single" and character == "'")
                or (state == "double" and character == '"')
                or (state == "template" and character == "`")
            ):
                state = "code"
        index += 1

    code = "".join(structure)
    output = list(source)
    regex_literal = re.compile(
        r"/(?:\\[^\r\n]|\[(?:\\[^\r\n]|[^\]\\\r\n])*\]|[^/\\\[\r\n])+/[A-Za-z]*"
    )
    expression_punctuation = frozenset("([{:,;=!?&|+-*%^~<>")
    expression_prefixes = re.compile(
        r"(?:^|[^A-Za-z0-9_$])(?:await|case|delete|do|else|in|instanceof|new|"
        r"of|return|throw|typeof|void|yield)\s*$"
    )
    for match in regex_literal.finditer(code):
        previous = match.start() - 1
        while previous >= 0 and code[previous].isspace():
            previous -= 1
        if not (
            previous < 0
            or code[previous] in expression_punctuation
            or expression_prefixes.search(code[: match.start()]) is not None
        ):
            continue
        for offset in range(match.start(), match.end()):
            if output[offset] != "\n":
                output[offset] = " "
    return "".join(output)


def mask_javascript_comments_and_regex_literals(source: str) -> str:
    """Mask comments and context-recognizable regex while preserving strings."""

    output = list(source)
    regex_literal = re.compile(
        r"/(?:\\[^\r\n]|\[(?:\\[^\r\n]|[^\]\\\r\n])*\]|[^/\\\[\r\n])+/[A-Za-z]*"
    )
    expression_punctuation = frozenset("([{:,;=!?&|+-*%^~<>")
    expression_prefixes = re.compile(
        r"(?:^|[^A-Za-z0-9_$])(?:await|case|delete|do|else|in|instanceof|new|"
        r"of|return|throw|typeof|void|yield)\s*$"
    )

    def regex_can_start(offset: int) -> bool:
        previous = offset - 1
        while previous >= 0 and source[previous].isspace():
            previous -= 1
        return bool(
            previous < 0
            or source[previous] in expression_punctuation
            or expression_prefixes.search(source[:offset]) is not None
        )

    state = "code"
    index = 0
    while index < len(source):
        character = source[index]
        following = source[index + 1] if index + 1 < len(source) else ""
        if state == "code":
            if character == "'":
                state = "single"
            elif character == '"':
                state = "double"
            elif character == "`":
                state = "template"
            elif character == "/" and following == "/":
                output[index] = output[index + 1] = " "
                state = "line-comment"
                index += 1
            elif character == "/" and following == "*":
                output[index] = output[index + 1] = " "
                state = "block-comment"
                index += 1
            elif character == "/" and regex_can_start(index):
                match = regex_literal.match(source, index)
                if match is not None:
                    for offset in range(match.start(), match.end()):
                        if output[offset] != "\n":
                            output[offset] = " "
                    index = match.end() - 1
        elif state == "line-comment":
            if character == "\n":
                state = "code"
            else:
                output[index] = " "
        elif state == "block-comment":
            if character == "*" and following == "/":
                output[index] = output[index + 1] = " "
                state = "code"
                index += 1
            elif character != "\n":
                output[index] = " "
        elif character == "\\":
            index += 1
        elif (
            (state == "single" and character == "'")
            or (state == "double" and character == '"')
            or (state == "template" and character == "`")
        ):
            state = "code"
        index += 1
    return "".join(output)


def normalize_runtime_reference_text(
    source: str, *, compose_javascript_literals: bool = True
) -> str:
    """Expose simple runtime path spellings without executing JavaScript."""

    if not compose_javascript_literals:
        return source

    def decode_escape(match: re.Match[str]) -> str:
        digits = next(value for value in match.groupdict().values() if value is not None)
        codepoint = int(digits, 16)
        return chr(codepoint) if codepoint <= 0x7F else match.group(0)

    normalized = re.sub(r"\\(?:\r\n|\r|\n)", "", source)
    normalized = JS_ASCII_ESCAPE_RE.sub(decode_escape, normalized)

    simple_string_concatenation = re.compile(
        r"(?P<left_quote>['\"`])(?P<left>[^'\"`\\$]*)(?P=left_quote)"
        r"\s*\)*\s*\+\s*\(*\s*"
        r"(?P<right_quote>['\"`])(?P<right>[^'\"`\\$]*)(?P=right_quote)"
    )

    def compose_simple_strings(match: re.Match[str]) -> str:
        return json.dumps(match.group("left") + match.group("right"))

    previous = None
    while normalized != previous:
        previous = normalized
        normalized = simple_string_concatenation.sub(
            compose_simple_strings, normalized
        )

    simple_template_interpolation = re.compile(
        r"\$\{\s*\(*\s*(?P<quote>['\"`])"
        r"(?P<value>[^'\"`\\$]*)(?P=quote)\s*\)*\s*\}"
    )
    normalized = simple_template_interpolation.sub(
        lambda match: match.group("value"), normalized
    )
    previous = None
    while normalized != previous:
        previous = normalized
        normalized = re.sub(
            r"['\"`]\s*\)*\s*\+\s*\(*\s*['\"`]", "", normalized
        )
    return normalized


@dataclass(frozen=True)
class Diagnostic:
    severity: str
    code: str
    path: str
    message: str

    def text(self) -> str:
        return f"{self.severity} {self.code} {self.path}: {self.message}"


class AIUIProjectValidator:
    def __init__(
        self,
        project_dir: Path,
        target_version: str = "0.17.0",
        repository_root: Optional[Path] = None,
    ) -> None:
        self.project_dir = project_dir.resolve()
        self.target_version = target_version
        self.target_version_tuple = parse_version_tuple(target_version)
        self.repository_root_was_explicit = repository_root is not None
        self.repository_root = (
            repository_root.resolve()
            if repository_root is not None
            else self.project_dir
        )
        self.diagnostics: List[Diagnostic] = []

    def error(self, code: str, path: str, message: str) -> None:
        self.diagnostics.append(Diagnostic("ERROR", code, path, message))

    def warning(self, code: str, path: str, message: str) -> None:
        self.diagnostics.append(Diagnostic("WARNING", code, path, message))

    def validate(self) -> List[Diagnostic]:
        if not self.project_dir.is_dir():
            self.error("PROJECT_DIR_NOT_FOUND", ".", "project directory does not exist.")
            return self.diagnostics
        if not self.repository_root.is_dir():
            self.error(
                "REPOSITORY_ROOT_NOT_FOUND",
                ".",
                "repository root is not a directory.",
            )
            return self.diagnostics
        try:
            repository_relative_root = self.project_dir.relative_to(self.repository_root)
        except ValueError:
            self.error(
                "PROJECT_OUTSIDE_REPOSITORY",
                ".",
                "project directory must stay inside the repository root.",
            )
            return self.diagnostics
        root_is_reserved = bool(
            repository_relative_root.parts
            and repository_relative_root.parts[0].lower() in RESERVED_PATH_NAMES
        )
        if not self.repository_root_was_explicit:
            root_is_reserved = any(
                part.lower() in RESERVED_PATH_NAMES
                for part in self.project_dir.parts
            )
        if root_is_reserved:
            self.error(
                "RESERVED_PROJECT_ROOT",
                ".",
                "project directory cannot be inside reserved repository or audit paths.",
            )
            return self.diagnostics

        self._validate_recommended_files()
        self._validate_reserved_paths()
        manifest = self._load_manifest()
        if manifest is None:
            return self.diagnostics

        self._validate_manifest_reserved_references(manifest)
        self._validate_target_features(manifest)
        self._validate_pages(manifest)
        self._validate_widgets(manifest)
        self._validate_workers(manifest)
        return self.diagnostics

    def _is_reserved_repository_path(self, path: Path) -> bool:
        try:
            relative = path.resolve().relative_to(self.repository_root)
        except (OSError, ValueError):
            return False
        return bool(
            relative.parts and relative.parts[0].lower() in RESERVED_PATH_NAMES
        )

    def _manifest_value_enters_reserved_path(self, value: str) -> bool:
        if RESERVED_SOURCE_REFERENCE_RE.search(value) is None:
            return False
        normalized_value = value.replace("\\", "/")
        unresolved = Path(normalized_value)
        candidate = unresolved if unresolved.is_absolute() else self.project_dir / unresolved
        return self._is_reserved_repository_path(candidate)

    def _runtime_text_enters_reserved_path(self, value: str, source: Path) -> bool:
        for match in RUNTIME_RESERVED_PATH_RE.finditer(value):
            literal_start = max(
                value.rfind(quote, 0, match.start()) for quote in ("'", '"', "`")
            )
            if literal_start >= 0:
                quote = value[literal_start]
                literal_end = value.find(quote, match.end())
                if literal_end >= 0:
                    literal_value = value[literal_start + 1 : literal_end]
                    literal_path = Path(literal_value)
                    if literal_path.is_absolute():
                        return True
            unresolved = Path(match.group("path").replace("\\", "/"))
            candidates = (
                unresolved
                if unresolved.is_absolute()
                else self.project_dir / unresolved,
                unresolved if unresolved.is_absolute() else source.parent / unresolved,
            )
            for candidate in candidates:
                resolved = candidate.resolve()
                try:
                    resolved.relative_to(self.repository_root)
                except ValueError:
                    return True
                if self._is_reserved_repository_path(resolved):
                    return True
        return False

    def _validate_target_features(self, manifest: Dict[str, Any]) -> None:
        if self.target_version_tuple >= (0, 18, 0):
            return
        if "widgets" in manifest:
            self.error(
                "WIDGETS_UNSUPPORTED_TARGET",
                "app.json",
                f"widgets require AIUI 0.18.0 or newer; target is {self.target_version}.",
            )
        if "agentWorkers" in manifest:
            self.error(
                "AGENT_WORKERS_UNSUPPORTED_TARGET",
                "app.json",
                "agentWorkers require AIUI 0.18.0 or newer; "
                f"target is {self.target_version}.",
            )

    def _validate_manifest_reserved_references(
        self, value: Any, pointer: str = "app.json"
    ) -> None:
        if isinstance(value, dict):
            for key, child in value.items():
                self._validate_manifest_reserved_references(
                    child, f"{pointer}.{key}"
                )
            return
        if isinstance(value, list):
            for index, child in enumerate(value):
                self._validate_manifest_reserved_references(
                    child, f"{pointer}[{index}]"
                )
            return
        if isinstance(value, str) and self._manifest_value_enters_reserved_path(value):
            self.error(
                "RESERVED_AUDIT_REFERENCE",
                "app.json",
                f"{pointer} cannot reference a reserved repository or audit path.",
            )

    def _validate_recommended_files(self) -> None:
        if not (self.project_dir / "AGENTS.md").is_file():
            self.warning(
                "AGENTS_MD_MISSING",
                "AGENTS.md",
                "recommended agent description file is missing.",
            )
        app_js = self.project_dir / "app.js"
        app_ink = self.project_dir / "app.ink"
        present_entries = [path for path in (app_js, app_ink) if path.is_file()]
        if not present_entries:
            self.warning(
                "APP_ENTRY_MISSING",
                ".",
                "application logic entry is missing; expected app.js or app.ink.",
            )
            return
        if len(present_entries) > 1:
            self.warning(
                "APP_ENTRY_MULTIPLE",
                ".",
                "both app.js and app.ink exist; keep one unambiguous application entry.",
            )

        valid_entry = False
        if app_js.is_file():
            try:
                valid_entry = bool(app_js.read_text(encoding="utf-8").strip())
            except (OSError, UnicodeError):
                pass
        if app_ink.is_file():
            try:
                source = strip_closed_markup_comments(
                    app_ink.read_text(encoding="utf-8")
                )
            except (OSError, UnicodeError):
                source = ""
            openings = len(SCRIPT_OPEN_RE.findall(source))
            matched_blocks = SCRIPT_BLOCK_RE.findall(source)
            has_setup_logic = any(
                has_script_attribute(attributes, "setup") and content.strip()
                for attributes, content in matched_blocks
            )
            valid_entry = valid_entry or bool(
                source.strip()
                and openings
                and openings == len(matched_blocks)
                and has_setup_logic
            )
        if not valid_entry:
            self.warning(
                "APP_ENTRY_INVALID",
                relative_path(present_entries[0], self.project_dir),
                "application entry must be readable, non-empty, and app.ink script blocks must close.",
            )

    def _validate_reserved_paths(self) -> None:
        for name in ("VERSION", "META-INF"):
            if (self.project_dir / name).exists():
                self.warning(
                    "RESERVED_PACKAGE_PATH",
                    name,
                    "path is reserved for generated AIX package metadata.",
                )

        runtime_suffixes = {".ink", ".js", ".ts", ".wxml", ".wxss"}
        evidence_roots = [
            candidate
            for candidate in self.repository_root.iterdir()
            if candidate.name.lower() == ".aiui-evidence"
        ]
        for evidence_root in evidence_roots:
            if evidence_root.is_symlink():
                self.error(
                    "RESERVED_AUDIT_SOURCE",
                    evidence_root.name,
                    "the audit evidence root cannot be a symlink.",
                )
                continue
            if not evidence_root.is_dir():
                self.error(
                    "RESERVED_AUDIT_SOURCE",
                    evidence_root.name,
                    "the audit evidence root must be a directory.",
                )
                continue
            for candidate in evidence_root.rglob("*"):
                if candidate.is_symlink():
                    self.error(
                        "RESERVED_AUDIT_SOURCE",
                        relative_path(candidate, self.repository_root),
                        "the audit evidence directory cannot contain symlinks or runtime source.",
                    )
                elif candidate.is_file() and candidate.suffix.lower() in runtime_suffixes:
                    self.error(
                        "RESERVED_AUDIT_SOURCE",
                        relative_path(candidate, self.repository_root),
                        "the audit evidence directory cannot contain AIUI runtime source.",
                    )

        for candidate in self.project_dir.rglob("*"):
            if not candidate.is_file() or candidate.suffix.lower() not in runtime_suffixes:
                continue
            relative = candidate.relative_to(self.project_dir)
            if self._is_reserved_repository_path(candidate):
                continue
            try:
                source = candidate.read_text(encoding="utf-8")
            except (OSError, UnicodeError):
                continue
            source_without_markup_comments = COMMENT_RE.sub("", source)
            suffix = candidate.suffix.lower()
            if suffix in {".js", ".ts"}:
                javascript = mask_javascript_comments_and_regex_literals(
                    source_without_markup_comments
                )
                reference_views = [normalize_runtime_reference_text(javascript)]
            elif suffix == ".ink":
                markup = list(source_without_markup_comments)
                scripts = SCRIPT_BLOCK_RE.findall(source_without_markup_comments)
                for match in SCRIPT_BLOCK_RE.finditer(source_without_markup_comments):
                    body_start, body_end = match.span(2)
                    markup[body_start:body_end] = [
                        "\n" if character == "\n" else " "
                        for character in source_without_markup_comments[body_start:body_end]
                    ]
                reference_views = [mask_code_comments("".join(markup))]
                reference_views.extend(
                    normalize_runtime_reference_text(
                        mask_javascript_comments_and_regex_literals(content)
                    )
                    for _, content in scripts
                )
            else:
                reference_views = [mask_code_comments(source_without_markup_comments)]
            if any(
                RESERVED_SOURCE_REFERENCE_RE.search(reference_text)
                and self._runtime_text_enters_reserved_path(reference_text, candidate)
                for reference_text in reference_views
            ):
                self.error(
                    "RESERVED_AUDIT_REFERENCE",
                    relative.as_posix(),
                    "AIUI runtime source cannot reference reserved repository or audit paths.",
                )

    def _load_manifest(self) -> Optional[Dict[str, Any]]:
        path = self.project_dir / "app.json"
        if not path.is_file():
            self.error("APP_JSON_MISSING", "app.json", "required manifest is missing.")
            return None
        try:
            content = path.read_text(encoding="utf-8")
        except (OSError, UnicodeError):
            self.error("APP_JSON_MALFORMED", "app.json", "manifest is not readable UTF-8 JSON.")
            return None
        try:
            manifest = json.loads(content)
        except json.JSONDecodeError as exc:
            self.error(
                "APP_JSON_MALFORMED",
                "app.json",
                f"manifest is invalid JSON at line {exc.lineno}, column {exc.colno}.",
            )
            return None
        if not isinstance(manifest, dict):
            self.error("APP_JSON_NOT_OBJECT", "app.json", "manifest root must be a JSON object.")
            return None
        return manifest

    def _validate_pages(self, manifest: Dict[str, Any]) -> None:
        if "pages" not in manifest:
            self.error("PAGES_MISSING", "app.json", "pages field is required.")
            return
        pages = manifest["pages"]
        if not isinstance(pages, list):
            self.error("PAGES_NOT_LIST", "app.json", "pages must be a JSON array.")
            return
        if not pages:
            self.error("PAGES_EMPTY", "app.json", "pages must contain at least one route.")
            return

        seen = set()
        has_ink = False
        has_wxml = False
        for index, route in enumerate(pages):
            if not isinstance(route, str):
                self.error(
                    "PAGE_ROUTE_NOT_STRING",
                    "app.json",
                    f"pages[{index}] must be a string.",
                )
                continue
            if route in seen:
                self.error(
                    "PAGE_ROUTE_DUPLICATE",
                    "app.json",
                    f"page route {route!r} is declared more than once.",
                )
                continue
            seen.add(route)
            if not is_safe_relative_path(route, extensionless=True):
                self.error(
                    "PAGE_ROUTE_UNSAFE",
                    "app.json",
                    f"page route {route!r} must be a safe extensionless relative path.",
                )
                continue

            if self._is_reserved_repository_path(self.project_dir / route):
                self.error(
                    "PAGE_ROUTE_UNSAFE",
                    "app.json",
                    f"page route {route!r} cannot enter a reserved repository path.",
                )
                continue

            ink_path = self.project_dir / f"{route}.ink"
            wxml_path = self.project_dir / f"{route}.wxml"
            ink_exists = ink_path.is_file()
            wxml_exists = wxml_path.is_file()
            has_ink = has_ink or ink_exists
            has_wxml = has_wxml or wxml_exists

            if not ink_exists and not wxml_exists:
                self.error(
                    "PAGE_ROUTE_NOT_FOUND",
                    "app.json",
                    f"page route {route!r} resolves to neither {route}.ink nor {route}.wxml.",
                )
                continue
            if ink_exists and wxml_exists:
                self.warning(
                    "MIXED_PAGE_DEFINITION",
                    relative_path(ink_path, self.project_dir),
                    f"route {route!r} has both .ink and .wxml definitions.",
                )
            if ink_exists:
                self._validate_ink(ink_path, root_kind="page")
            if wxml_exists:
                self._validate_wxml(wxml_path)

        if has_ink and has_wxml:
            self.warning(
                "MIXED_AUTHORING_MODES",
                "app.json",
                "declared pages mix single-file .ink and multi-file .wxml authoring modes.",
            )

    def _validate_widgets(self, manifest: Dict[str, Any]) -> None:
        if "widgets" not in manifest:
            return
        widgets = manifest["widgets"]
        if not isinstance(widgets, list):
            self.error("WIDGETS_NOT_LIST", "app.json", "widgets must be a JSON array.")
            return

        for index, widget in enumerate(widgets):
            if not isinstance(widget, dict):
                self.error(
                    "WIDGET_ENTRY_NOT_OBJECT",
                    "app.json",
                    f"widgets[{index}] must be an object.",
                )
                continue
            route = widget.get("path")
            family = widget.get("family")
            route_valid = isinstance(route, str) and bool(route)
            if not route_valid:
                self.error(
                    "WIDGET_PATH_INVALID",
                    "app.json",
                    f"widgets[{index}].path must be a non-empty string.",
                )
            elif not is_safe_relative_path(route, extensionless=True):
                route_valid = False
                self.error(
                    "WIDGET_PATH_UNSAFE",
                    "app.json",
                    f"widget path {route!r} must be a safe extensionless relative path.",
                )
            elif self._is_reserved_repository_path(self.project_dir / route):
                route_valid = False
                self.error(
                    "WIDGET_PATH_UNSAFE",
                    "app.json",
                    f"widget path {route!r} cannot enter a reserved repository path.",
                )

            if family not in ("1x1", "1x2"):
                self.error(
                    "WIDGET_FAMILY_INVALID",
                    "app.json",
                    f"widgets[{index}].family must be '1x1' or '1x2'.",
                )

            if not route_valid:
                continue
            ink_path = self.project_dir / f"{route}.ink"
            if not ink_path.is_file():
                self.error(
                    "WIDGET_NOT_FOUND",
                    "app.json",
                    f"widget path {route!r} does not resolve to {route}.ink.",
                )
                continue
            self._validate_ink(
                ink_path,
                root_kind="widget",
                expected_widget_family=family if family in ("1x1", "1x2") else None,
            )

    def _validate_workers(self, manifest: Dict[str, Any]) -> None:
        if "agentWorkers" not in manifest:
            return
        workers = manifest["agentWorkers"]
        if not isinstance(workers, list):
            self.error(
                "AGENT_WORKERS_NOT_LIST", "app.json", "agentWorkers must be a JSON array."
            )
            return

        names = set()
        open_workers = 0
        for index, worker in enumerate(workers):
            if not isinstance(worker, dict):
                self.error(
                    "WORKER_ENTRY_NOT_OBJECT",
                    "app.json",
                    f"agentWorkers[{index}] must be an object.",
                )
                continue

            name = worker.get("name")
            if not isinstance(name, str) or not name.strip():
                self.error(
                    "WORKER_NAME_INVALID",
                    "app.json",
                    f"agentWorkers[{index}].name must be a non-empty string.",
                )
            elif name in names:
                self.error(
                    "WORKER_NAME_DUPLICATE",
                    "app.json",
                    f"Agent Worker name {name!r} is declared more than once.",
                )
            else:
                names.add(name)

            script = worker.get("script")
            script_valid = isinstance(script, str) and bool(script)
            if not script_valid:
                self.error(
                    "WORKER_SCRIPT_INVALID",
                    "app.json",
                    f"agentWorkers[{index}].script must be a non-empty string.",
                )
            else:
                if not is_safe_relative_path(script):
                    script_valid = False
                    self.error(
                        "WORKER_SCRIPT_UNSAFE",
                        "app.json",
                        f"worker script {script!r} must be a safe relative path.",
                    )
                elif self._is_reserved_repository_path(self.project_dir / script):
                    script_valid = False
                    self.error(
                        "WORKER_SCRIPT_UNSAFE",
                        "app.json",
                        f"worker script {script!r} cannot enter a reserved repository path.",
                    )
                if PurePosixPath(script).suffix not in (".js", ".ts"):
                    script_valid = False
                    self.error(
                        "WORKER_SCRIPT_EXTENSION",
                        "app.json",
                        f"worker script {script!r} must end in .js or .ts.",
                    )
                if script_valid and not (self.project_dir / script).is_file():
                    self.error(
                        "WORKER_SCRIPT_NOT_FOUND",
                        "app.json",
                        f"worker script {script!r} does not exist.",
                    )

            trigger = worker.get("trigger")
            trigger_valid = (
                isinstance(trigger, dict)
                and trigger.get("type") == "open"
                and set(trigger) == {"type"}
            )
            if not trigger_valid:
                self.error(
                    "WORKER_TRIGGER_INVALID",
                    "app.json",
                    f"agentWorkers[{index}].trigger must be exactly {{\"type\": \"open\"}}.",
                )
            else:
                open_workers += 1

            lifetime = worker.get("lifetime")
            if lifetime not in ("instant", "foreground"):
                self.error(
                    "WORKER_LIFETIME_INVALID",
                    "app.json",
                    f"agentWorkers[{index}].lifetime must be 'instant' or 'foreground'.",
                )

            capabilities = worker.get("capabilities", [])
            if not isinstance(capabilities, list):
                self.error(
                    "WORKER_CAPABILITIES_NOT_LIST",
                    "app.json",
                    f"agentWorkers[{index}].capabilities must be a string array.",
                )
                capabilities = []
            else:
                for capability in capabilities:
                    if capability != "bluetooth-peripheral":
                        self.error(
                            "WORKER_CAPABILITY_UNSUPPORTED",
                            "app.json",
                            f"unsupported Agent Worker capability {capability!r}.",
                        )
            if "bluetooth-peripheral" in capabilities and lifetime != "foreground":
                self.error(
                    "WORKER_BLUETOOTH_REQUIRES_FOREGROUND",
                    "app.json",
                    "bluetooth-peripheral capability requires foreground lifetime.",
                )

        if open_workers > 1:
            self.error(
                "WORKER_OPEN_LIMIT",
                "app.json",
                "at most one Agent Worker may use the open trigger.",
            )

    def _validate_ink(
        self,
        path: Path,
        root_kind: str,
        expected_widget_family: Optional[str] = None,
    ) -> None:
        display_path = relative_path(path, self.project_dir)
        try:
            source = path.read_text(encoding="utf-8")
        except (OSError, UnicodeError):
            self.error("INK_READ_ERROR", display_path, "file is not readable UTF-8 text.")
            return

        source = strip_closed_markup_comments(source)
        script_openings = SCRIPT_OPEN_RE.findall(source)
        def_count = sum(has_script_attribute(attrs, "def") for attrs in script_openings)
        setup_count = sum(has_script_attribute(attrs, "setup") for attrs in script_openings)
        style_count = len(STYLE_OPEN_RE.findall(source))
        matched_scripts = SCRIPT_BLOCK_RE.findall(source)
        matched_setup_count = sum(
            has_script_attribute(attrs, "setup") for attrs, _ in matched_scripts
        )
        matched_style_count = len(STYLE_BLOCK_RE.findall(source))

        if def_count > 1:
            self.error(
                "INK_DUPLICATE_SCRIPT_DEF",
                display_path,
                "an .ink file may contain at most one script def block.",
            )
        if setup_count > 1:
            self.error(
                "INK_DUPLICATE_SCRIPT_SETUP",
                display_path,
                "an .ink file may contain at most one script setup block.",
            )
        if matched_setup_count < setup_count:
            self.error(
                "INK_SETUP_UNCLOSED",
                display_path,
                "script setup block must have a closing script tag.",
            )
        if style_count > 1:
            self.error(
                "INK_DUPLICATE_STYLE",
                display_path,
                "an .ink file may contain at most one style block.",
            )
        if matched_style_count < style_count:
            self.error(
                "INK_STYLE_UNCLOSED",
                display_path,
                "style block must have a closing style tag.",
            )

        definitions: List[Dict[str, Any]] = []
        matched_def_count = 0
        for attrs, content in matched_scripts:
            if not has_script_attribute(attrs, "def"):
                continue
            matched_def_count += 1
            try:
                definition = json.loads(content)
            except json.JSONDecodeError:
                self.error(
                    "INK_DEF_MALFORMED",
                    display_path,
                    "script def must contain valid JSON.",
                )
                continue
            if not isinstance(definition, dict):
                self.error(
                    "INK_DEF_NOT_OBJECT",
                    display_path,
                    "script def JSON root must be an object.",
                )
                continue
            definitions.append(definition)
        if matched_def_count < def_count:
            self.error(
                "INK_DEF_MALFORMED",
                display_path,
                "script def block must have a closing script tag and valid JSON.",
            )

        markup = SCRIPT_BLOCK_RE.sub("", source)
        markup = STYLE_BLOCK_RE.sub("", markup)
        self._validate_template_control_directives(markup, display_path)
        markup_error = find_markup_nesting_error(markup)
        if markup_error is not None:
            self.error("INK_MARKUP_INVALID", display_path, markup_error)
        page_count = count_opening_tag(markup, "page")
        widget_count = count_opening_tag(markup, "widget")
        page_close_count = count_closing_tag(markup, "page")
        widget_close_count = count_closing_tag(markup, "widget")

        if root_kind == "page":
            if page_count != 1:
                self.error(
                    "PAGE_ROOT_COUNT",
                    display_path,
                    f"page .ink must contain exactly one page root; found {page_count}.",
                )
            if page_count != page_close_count:
                self.error(
                    "PAGE_ROOT_UNBALANCED",
                    display_path,
                    "page root opening and closing tags must be balanced.",
                )
            if widget_count:
                self.error(
                    "PAGE_HAS_WIDGET_ROOT",
                    display_path,
                    "page .ink must not contain a widget root.",
                )
            if widget_count != widget_close_count:
                self.error(
                    "WIDGET_ROOT_UNBALANCED",
                    display_path,
                    "widget opening and closing tags must be balanced.",
                )
            return

        if widget_count != 1:
            self.error(
                "WIDGET_ROOT_COUNT",
                display_path,
                f"widget .ink must contain exactly one widget root; found {widget_count}.",
            )
        if widget_count != widget_close_count:
            self.error(
                "WIDGET_ROOT_UNBALANCED",
                display_path,
                "widget root opening and closing tags must be balanced.",
            )
        if page_count:
            self.error(
                "WIDGET_HAS_PAGE_ROOT",
                display_path,
                "widget .ink must not contain a page root.",
            )
        if page_count != page_close_count:
            self.error(
                "PAGE_ROOT_UNBALANCED",
                display_path,
                "page opening and closing tags must be balanced.",
            )
        if expected_widget_family is not None:
            family_found = False
            for definition in definitions:
                widget_definition = definition.get("widget")
                if not isinstance(widget_definition, dict) or "family" not in widget_definition:
                    continue
                family_found = True
                if widget_definition["family"] != expected_widget_family:
                    self.error(
                        "WIDGET_DEF_FAMILY_MISMATCH",
                        display_path,
                        "script def widget family must match app.json.",
                    )
                break
            if not family_found:
                self.error(
                    "WIDGET_DEF_FAMILY_MISSING",
                    display_path,
                    "script def must declare widget.family matching app.json.",
                )

    def _validate_wxml(self, path: Path) -> None:
        display_path = relative_path(path, self.project_dir)
        try:
            source = strip_closed_markup_comments(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError):
            self.error("WXML_READ_ERROR", display_path, "file is not readable UTF-8 text.")
            return
        if not source.strip():
            self.error("WXML_EMPTY", display_path, "declared WXML page must not be empty.")
            return
        self._validate_template_control_directives(source, display_path)
        markup_error = find_markup_nesting_error(source)
        if markup_error is not None:
            self.error("WXML_MARKUP_INVALID", display_path, markup_error)

    def _validate_template_control_directives(
        self, source: str, display_path: str
    ) -> None:
        directives = find_wechat_template_control_directives(source)
        if not directives:
            return
        replacements = ", ".join(
            f"{directive} with {directive.replace('wx:', 'ink:')}"
            for directive in directives
        )
        self.warning(
            "WX_TEMPLATE_CONTROL_DIRECTIVE",
            display_path,
            "AIUI template control attributes use the ink:* namespace; replace "
            f"{replacements}.",
        )


def has_script_attribute(attributes: str, name: str) -> bool:
    return re.search(rf"(?:^|\s){re.escape(name)}(?:\s*=\s*[^\s]+)?(?=\s|$)", attributes) is not None


def strip_closed_markup_comments(source: str) -> str:
    """Remove only explicitly closed XML/HTML comments.

    Unterminated comments stay visible to later conservative markup and
    template-directive checks, so malformed source cannot hide live-looking
    attributes from validation.
    """
    return CLOSED_MARKUP_COMMENT_RE.sub("", source)


def find_wechat_template_control_directives(source: str) -> List[str]:
    masked = MUSTACHE_RE.sub("", source)
    directives = set()
    position = 0
    while True:
        start = masked.find("<", position)
        if start < 0:
            break
        cursor = start + 1
        if cursor >= len(masked) or not masked[cursor].isalpha():
            position = cursor
            continue

        while cursor < len(masked) and (
            masked[cursor].isalnum() or masked[cursor] in "_:.-"
        ):
            cursor += 1

        while cursor < len(masked):
            while cursor < len(masked) and masked[cursor].isspace():
                cursor += 1
            if cursor >= len(masked):
                break
            if masked[cursor] == ">":
                cursor += 1
                break
            if masked[cursor] == "/" and masked[cursor : cursor + 2] == "/>":
                cursor += 2
                break

            name_start = cursor
            while cursor < len(masked) and (
                not masked[cursor].isspace() and masked[cursor] not in "=/>"
            ):
                cursor += 1
            if cursor == name_start:
                cursor += 1
                continue

            attribute_name = masked[name_start:cursor]
            if WX_TEMPLATE_CONTROL_RE.fullmatch(attribute_name):
                directives.add(attribute_name.lower())

            while cursor < len(masked) and masked[cursor].isspace():
                cursor += 1
            if cursor >= len(masked) or masked[cursor] != "=":
                continue
            cursor += 1
            while cursor < len(masked) and masked[cursor].isspace():
                cursor += 1
            if cursor >= len(masked):
                break
            quote = masked[cursor] if masked[cursor] in "\"'" else None
            if quote is not None:
                cursor += 1
                while cursor < len(masked) and masked[cursor] != quote:
                    cursor += 1
                if cursor < len(masked):
                    cursor += 1
            else:
                while cursor < len(masked) and (
                    not masked[cursor].isspace() and masked[cursor] != ">"
                ):
                    cursor += 1

        position = max(cursor, start + 1)
    return sorted(directives)


def count_opening_tag(source: str, name: str) -> int:
    return len(re.findall(rf"<{re.escape(name)}(?:\s|/?>)", source, re.IGNORECASE))


def count_closing_tag(source: str, name: str) -> int:
    return len(re.findall(rf"</{re.escape(name)}\s*>", source, re.IGNORECASE))


def find_markup_nesting_error(source: str) -> Optional[str]:
    """Return a basic XML-like tag ordering error without parsing WXML attributes."""
    masked = MUSTACHE_RE.sub("", source)
    stack: List[str] = []
    position = 0
    while True:
        start = masked.find("<", position)
        if start < 0:
            break
        cursor = start + 1
        if cursor >= len(masked):
            return "markup ends with an incomplete tag opener."
        if masked[cursor] in ("!", "?"):
            end = masked.find(">", cursor + 1)
            if end < 0:
                return "markup declaration is not closed."
            position = end + 1
            continue

        closing = masked[cursor] == "/"
        if closing:
            cursor += 1
        if cursor >= len(masked) or not masked[cursor].isalpha():
            position = start + 1
            continue

        name_start = cursor
        while cursor < len(masked) and (
            masked[cursor].isalnum() or masked[cursor] in "_:-."
        ):
            cursor += 1
        name = masked[name_start:cursor]

        quote: Optional[str] = None
        end = cursor
        while end < len(masked):
            character = masked[end]
            if quote is not None:
                if character == quote:
                    quote = None
            elif character in ("'", '"'):
                quote = character
            elif character == ">":
                break
            end += 1
        if end >= len(masked):
            return f"tag <{'/' if closing else ''}{name}> is not closed."

        raw_tag = masked[start : end + 1]
        self_closing = not closing and raw_tag.rstrip().endswith("/>")
        if closing:
            if not stack:
                return f"unexpected closing tag </{name}>."
            expected = stack.pop()
            if name != expected:
                return f"closing tag </{name}> does not match open <{expected}>."
        elif not self_closing:
            stack.append(name)
        position = end + 1

    if stack:
        return f"unclosed tag <{stack[-1]}>."
    return None


def is_safe_relative_path(value: str, extensionless: bool = False) -> bool:
    if not value or value != value.strip() or "\\" in value:
        return False
    if value.startswith("/") or re.match(r"^[A-Za-z]:", value) or "://" in value:
        return False
    parts = value.split("/")
    if any(part in ("", ".", "..") for part in parts):
        return False
    if extensionless and PurePosixPath(value).suffix:
        return False
    return True


def relative_path(path: Path, root: Path) -> str:
    return path.relative_to(root).as_posix()


def parse_version_tuple(value: str) -> tuple[int, int, int]:
    match = TARGET_VERSION_RE.fullmatch(value)
    if match is None:
        raise ValueError("target version must use MAJOR.MINOR.PATCH")
    return tuple(int(match.group(name)) for name in ("major", "minor", "patch"))


def parse_target_version(value: str) -> str:
    try:
        parse_version_tuple(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(str(exc)) from exc
    return value


def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("PROJECT_DIR", type=Path, help="AIUI project directory")
    parser.add_argument(
        "--repository-root",
        type=Path,
        help=(
            "repository boundary that owns top-level .git and .aiui-evidence; "
            "defaults to PROJECT_DIR"
        ),
    )
    parser.add_argument(
        "--strict", action="store_true", help="return exit status 1 when warnings exist"
    )
    parser.add_argument("--json", action="store_true", help="emit JSON diagnostics")
    parser.add_argument(
        "--target-version",
        type=parse_target_version,
        default="0.17.0",
        metavar="VERSION",
        help="AIUI compatibility target (default: 0.17.0 stable)",
    )
    return parser.parse_args(argv)


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = parse_args(argv)
    validator = AIUIProjectValidator(
        args.PROJECT_DIR,
        args.target_version,
        repository_root=args.repository_root,
    )
    diagnostics = validator.validate()
    error_count = sum(item.severity == "ERROR" for item in diagnostics)
    warning_count = sum(item.severity == "WARNING" for item in diagnostics)
    exit_code = 1 if error_count or (args.strict and warning_count) else 0

    if args.json:
        payload = {
            "valid": exit_code == 0,
            "strict": args.strict,
            "targetVersion": args.target_version,
            "errorCount": error_count,
            "warningCount": warning_count,
            "diagnostics": [asdict(item) for item in diagnostics],
        }
        print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        for diagnostic in diagnostics:
            print(diagnostic.text())
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
