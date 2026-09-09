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


COMMENT_RE = re.compile(r"<!--.*?-->", re.DOTALL)
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


@dataclass(frozen=True)
class Diagnostic:
    severity: str
    code: str
    path: str
    message: str

    def text(self) -> str:
        return f"{self.severity} {self.code} {self.path}: {self.message}"


class AIUIProjectValidator:
    def __init__(self, project_dir: Path, target_version: str = "0.17.0") -> None:
        self.project_dir = project_dir
        self.target_version = target_version
        self.target_version_tuple = parse_version_tuple(target_version)
        self.diagnostics: List[Diagnostic] = []

    def error(self, code: str, path: str, message: str) -> None:
        self.diagnostics.append(Diagnostic("ERROR", code, path, message))

    def warning(self, code: str, path: str, message: str) -> None:
        self.diagnostics.append(Diagnostic("WARNING", code, path, message))

    def validate(self) -> List[Diagnostic]:
        if not self.project_dir.is_dir():
            self.error("PROJECT_DIR_NOT_FOUND", ".", "project directory does not exist.")
            return self.diagnostics

        self._validate_recommended_files()
        self._validate_reserved_paths()
        manifest = self._load_manifest()
        if manifest is None:
            return self.diagnostics

        self._validate_target_features(manifest)
        self._validate_pages(manifest)
        self._validate_widgets(manifest)
        self._validate_workers(manifest)
        return self.diagnostics

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
                source = COMMENT_RE.sub("", app_ink.read_text(encoding="utf-8"))
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

        source = COMMENT_RE.sub("", source)
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
            source = COMMENT_RE.sub("", path.read_text(encoding="utf-8"))
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
    validator = AIUIProjectValidator(args.PROJECT_DIR, args.target_version)
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
