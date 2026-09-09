#!/usr/bin/env python3
"""Create a deterministic content fingerprint for an AIUI Studio import root."""

from __future__ import annotations

import argparse
import hashlib
from pathlib import Path


FORMAT_PREFIX = b"ROKID-AIUI-WORKTREE-v1\0"
EXCLUDED_TOP_LEVEL_DIRECTORIES = frozenset({".git", ".aiui-evidence"})


def fingerprint_project(project_root: Path) -> str:
    root = project_root.resolve()
    if not root.is_dir():
        raise ValueError(f"project root is not a directory: {project_root}")

    files: list[tuple[str, Path]] = []
    for candidate in root.rglob("*"):
        relative = candidate.relative_to(root)
        if (
            relative.parts
            and relative.parts[0] in EXCLUDED_TOP_LEVEL_DIRECTORIES
        ):
            continue
        if candidate.is_symlink():
            raise ValueError(f"symlink is not allowed in import root: {relative}")
        if candidate.is_dir():
            continue
        if not candidate.is_file():
            raise ValueError(f"unsupported filesystem entry: {relative}")
        files.append((relative.as_posix(), candidate))

    digest = hashlib.sha256(FORMAT_PREFIX)
    for relative, candidate in sorted(files):
        content = candidate.read_bytes()
        relative_bytes = relative.encode("utf-8")
        digest.update(len(relative_bytes).to_bytes(8, "big"))
        digest.update(relative_bytes)
        digest.update(len(content).to_bytes(8, "big"))
        digest.update(content)
    return f"WORKTREE:{digest.hexdigest()}"


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Hash the exact AIUI Studio import directory and print a canonical "
            "WORKTREE:SHA-256 revision. The format includes relative paths and "
            "file contents, excludes only top-level .git/ and .aiui-evidence/, "
            "and rejects symlinks."
        )
    )
    parser.add_argument("project_root", type=Path, help="AIUI Studio import root")
    args = parser.parse_args()
    try:
        print(fingerprint_project(args.project_root))
    except (OSError, UnicodeError, ValueError) as error:
        parser.error(str(error))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
