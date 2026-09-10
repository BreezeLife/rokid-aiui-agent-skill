#!/usr/bin/env python3
"""Create a deterministic content fingerprint for an AIUI Studio import root."""

from __future__ import annotations

import argparse
import hashlib
from pathlib import Path


FORMAT_PREFIX = b"ROKID-AIUI-WORKTREE-v1\0"
REPOSITORY_ROOT_EXCLUSIONS = frozenset({".git", ".aiui-evidence"})
AIUI_RUNTIME_SOURCE_SUFFIXES = frozenset({".ink", ".js", ".ts", ".wxml", ".wxss"})


def fingerprint_project(
    project_root: Path, repository_root: Path | None = None
) -> str:
    root = project_root.resolve()
    if not root.is_dir():
        raise ValueError(f"project root is not a directory: {project_root}")
    repository: Path | None = None
    evidence_directories: tuple[Path, ...] = ()
    if repository_root is not None:
        repository = repository_root.resolve()
        if not repository.is_dir():
            raise ValueError(f"repository root is not a directory: {repository_root}")
        try:
            repository_relative_root = root.relative_to(repository)
        except ValueError as error:
            raise ValueError("project root is outside repository root") from error
        if (
            repository_relative_root.parts
            and repository_relative_root.parts[0].lower()
            in REPOSITORY_ROOT_EXCLUSIONS
        ):
            raise ValueError(
                "project root cannot be inside a reserved repository directory"
            )
        evidence_directories = tuple(
            candidate
            for candidate in repository.iterdir()
            if candidate.name.lower() == ".aiui-evidence"
        )
        for candidate in evidence_directories:
            if candidate.is_symlink():
                raise ValueError("reserved evidence directory cannot be a symlink")
            if not candidate.is_dir():
                raise ValueError("reserved evidence path must be a directory")
            for evidence_entry in candidate.rglob("*"):
                evidence_relative = evidence_entry.relative_to(repository)
                if evidence_entry.is_symlink():
                    raise ValueError(
                        "symlink is not allowed in reserved evidence directory: "
                        f"{evidence_relative}"
                    )
                if evidence_entry.is_dir():
                    continue
                if not evidence_entry.is_file():
                    raise ValueError(
                        f"unsupported reserved evidence entry: {evidence_relative}"
                    )
                if evidence_entry.suffix.lower() in AIUI_RUNTIME_SOURCE_SUFFIXES:
                    raise ValueError(
                        "AIUI runtime source is not allowed in reserved evidence "
                        f"directory: {evidence_relative}"
                    )

    files: list[tuple[str, Path]] = []
    for candidate in root.rglob("*"):
        relative = candidate.relative_to(root)
        reserved_root = None
        if repository is not None:
            repository_relative = candidate.relative_to(repository)
            if repository_relative.parts:
                reserved_root = repository_relative.parts[0].lower()
        if reserved_root == ".aiui-evidence":
            if candidate.is_symlink():
                raise ValueError(
                    f"symlink is not allowed in reserved evidence directory: {relative}"
                )
            if candidate.is_dir():
                continue
            if not candidate.is_file():
                raise ValueError(
                    f"unsupported reserved evidence entry: {relative}"
                )
            if candidate.suffix.lower() in AIUI_RUNTIME_SOURCE_SUFFIXES:
                raise ValueError(
                    f"AIUI runtime source is not allowed in reserved evidence "
                    f"directory: {relative}"
                )
            continue
        if reserved_root == ".git":
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
            "file contents and rejects symlinks. With an explicit repository "
            "root, only that root's .git/ and .aiui-evidence/ are excluded; "
            "runtime source and symlinks are forbidden in reserved evidence."
        )
    )
    parser.add_argument("project_root", type=Path, help="AIUI Studio import root")
    parser.add_argument(
        "--repository-root",
        type=Path,
        help="audit repository root that owns the reserved evidence directory",
    )
    args = parser.parse_args()
    try:
        print(fingerprint_project(args.project_root, args.repository_root))
    except (OSError, UnicodeError, ValueError) as error:
        parser.error(str(error))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
