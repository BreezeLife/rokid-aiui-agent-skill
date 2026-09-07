#!/usr/bin/env python3
"""Verify local Markdown links and pin mutable canonical source links."""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from urllib.parse import unquote, urlparse


LINK_RE = re.compile(r"!?\[[^\]]*\]\((?P<target><[^>]+>|[^)\s]+)")
REFERENCE_DEFINITION_RE = re.compile(
    r"^[ \t]{0,3}\[[^\]\n]+\]:[ \t]*(?P<target><[^>]+>|\S+)"
)
AUTOLINK_RE = re.compile(r"<(?P<target>https?://[^<>\s]+)>", flags=re.IGNORECASE)
PINNED_SOURCE_RE = re.compile(
    r"^https://github\.com/yodaos-project/(?:AIUI|aix|awesome-aiui)/"
    r"(?:blob|tree)/(?P<revision>[^/]+)(?:/|$)",
    flags=re.IGNORECASE,
)
FULL_COMMIT_RE = re.compile(r"^[0-9a-f]{40}$", flags=re.IGNORECASE)
STALE_AIX_HOST = "jsar-project.github.io"


@dataclass(frozen=True, order=True)
class Diagnostic:
    path: str
    line: int
    code: str
    message: str

    def text(self) -> str:
        return f"ERROR {self.code} {self.path}:{self.line}: {self.message}"


def markdown_files(root: Path) -> list[Path]:
    return sorted(
        path
        for path in root.rglob("*.md")
        if path.is_file() and ".git" not in path.relative_to(root).parts
    )


def normalize_target(raw_target: str) -> str:
    target = raw_target.strip()
    if target.startswith("<") and target.endswith(">"):
        target = target[1:-1]
    return target


def link_targets(line: str) -> list[str]:
    targets = [match.group("target") for match in LINK_RE.finditer(line)]
    definition = REFERENCE_DEFINITION_RE.match(line)
    if definition:
        targets.append(definition.group("target"))
    targets.extend(match.group("target") for match in AUTOLINK_RE.finditer(line))
    return targets


def is_within_root(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
    except ValueError:
        return False
    return True


def verify(root: Path) -> list[Diagnostic]:
    root = root.resolve()
    if not root.is_dir():
        return [
            Diagnostic(
                ".",
                0,
                "ROOT_NOT_DIRECTORY",
                "scan root does not exist or is not a directory",
            )
        ]

    diagnostics: list[Diagnostic] = []
    for markdown_path in markdown_files(root):
        relative = markdown_path.relative_to(root).as_posix()
        for line_number, line in enumerate(
            markdown_path.read_text(encoding="utf-8").splitlines(), start=1
        ):
            for raw_target in link_targets(line):
                target = normalize_target(raw_target)
                parsed = urlparse(target)

                if parsed.netloc.lower() == STALE_AIX_HOST:
                    is_source_of_truth = (
                        relative == "references/source-of-truth.md"
                        or relative.endswith("/references/source-of-truth.md")
                    )
                    is_labeled_history = is_source_of_truth and (
                        "stale" in line.lower() or "失效" in line
                    )
                    if not is_labeled_history:
                        diagnostics.append(
                            Diagnostic(
                                relative,
                                line_number,
                                "STALE_AIX_HOST",
                                "use the current yodaos-project AIX sources; the old site is stale",
                            )
                        )

                source_match = PINNED_SOURCE_RE.match(target)
                if source_match and not FULL_COMMIT_RE.fullmatch(
                    source_match.group("revision")
                ):
                    diagnostics.append(
                        Diagnostic(
                            relative,
                            line_number,
                            "SOURCE_LINK_UNPINNED",
                            "canonical GitHub file/tree links must use a full 40-character commit",
                        )
                    )

                if parsed.scheme or target.startswith("#"):
                    continue

                local_part = unquote(target.split("#", 1)[0].split("?", 1)[0])
                if not local_part:
                    continue
                if local_part.startswith("/"):
                    resolved = root / local_part.lstrip("/")
                else:
                    resolved = markdown_path.parent / local_part
                resolved = resolved.resolve()
                if not is_within_root(resolved, root):
                    diagnostics.append(
                        Diagnostic(
                            relative,
                            line_number,
                            "LOCAL_LINK_OUTSIDE_ROOT",
                            f"local target escapes the scan root: {local_part}",
                        )
                    )
                    continue
                if not resolved.exists():
                    diagnostics.append(
                        Diagnostic(
                            relative,
                            line_number,
                            "LOCAL_LINK_MISSING",
                            f"local target does not exist: {local_part}",
                        )
                    )

    return sorted(set(diagnostics))


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", nargs="?", default=".", help="repository root")
    parser.add_argument("--json", action="store_true", help="emit machine-readable JSON")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv if argv is not None else sys.argv[1:])
    root = Path(args.root).resolve()
    diagnostics = verify(root)
    if args.json:
        print(
            json.dumps(
                {
                    "root": str(root),
                    "diagnostics": [asdict(item) for item in diagnostics],
                },
                ensure_ascii=False,
                indent=2,
                sort_keys=True,
            )
        )
    else:
        for diagnostic in diagnostics:
            print(diagnostic.text())
        if not diagnostics:
            print(f"OK: verified Markdown references under {root}")
    return 1 if diagnostics else 0


if __name__ == "__main__":
    raise SystemExit(main())
