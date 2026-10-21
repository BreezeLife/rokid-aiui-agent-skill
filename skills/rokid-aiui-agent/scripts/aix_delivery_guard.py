#!/usr/bin/env python3
"""Prepare, publish, and verify a source-bound AIX delivery safely."""

from __future__ import annotations

import argparse
import hashlib
import os
from pathlib import Path
import shutil
import stat
import sys

from fingerprint_aiui_project import fingerprint_project


RESERVED_REPOSITORY_ROOTS = frozenset({".git", ".aiui-evidence"})
COPY_CHUNK_SIZE = 1024 * 1024


def _reject_control_characters(value: str, label: str) -> None:
    if any(ord(character) < 32 or ord(character) == 127 for character in value):
        raise ValueError(f"{label} contains an unsupported control character")


def _absolute(path: Path) -> Path:
    expanded = path.expanduser()
    if not expanded.is_absolute():
        expanded = Path.cwd() / expanded
    return expanded


def _canonical_directory(path: Path, label: str) -> Path:
    _reject_control_characters(str(path), label)
    resolved = _absolute(path).resolve(strict=True)
    if not resolved.is_dir():
        raise ValueError(f"{label} is not a directory: {path}")
    return resolved


def _same_identity(left: os.stat_result, right: os.stat_result) -> bool:
    return left.st_dev == right.st_dev and left.st_ino == right.st_ino


def _is_within_by_identity(candidate: Path, root: Path) -> bool:
    """Return true when an existing candidate ancestor is the physical root."""

    root_stat = root.stat()
    current = _absolute(candidate)
    while True:
        try:
            current_stat = current.stat()
        except (FileNotFoundError, NotADirectoryError):
            pass
        else:
            if _same_identity(current_stat, root_stat):
                return True
        parent = current.parent
        if parent == current:
            return False
        current = parent


def _validate_output_path(
    project: Path, output: Path, *, require_missing: bool
) -> Path:
    _reject_control_characters(str(output), "AIX delivery path")
    raw_output = _absolute(output)
    if raw_output.name == "" or not raw_output.name.endswith(".aix"):
        raise ValueError("AIX delivery path must use the lowercase .aix suffix")
    if require_missing and os.path.lexists(raw_output):
        raise FileExistsError(f"AIX delivery path already exists: {raw_output}")
    if _is_within_by_identity(raw_output, project):
        raise ValueError("AIX delivery path must be outside the Studio import root")

    resolved = Path(os.path.realpath(raw_output))
    if require_missing and os.path.lexists(resolved):
        raise FileExistsError(f"AIX delivery path already exists: {resolved}")
    if _is_within_by_identity(resolved, project):
        raise ValueError("AIX delivery path must be outside the Studio import root")
    return resolved


def validate_paths(project_arg: Path, output_arg: Path, repository_arg: Path) -> tuple[Path, Path, Path]:
    project = _canonical_directory(project_arg, "AIUI project root")
    repository = _canonical_directory(repository_arg, "repository root")
    if not _is_within_by_identity(project, repository):
        raise ValueError("AIUI project root is outside the explicit repository root")
    output = _validate_output_path(project, output_arg, require_missing=True)
    return project, repository, output


def _copy_regular_file(source: Path, destination: Path, expected: os.stat_result) -> None:
    nofollow = getattr(os, "O_NOFOLLOW", 0)
    source_fd = os.open(source, os.O_RDONLY | nofollow)
    destination_fd = -1
    try:
        opened = os.fstat(source_fd)
        if not stat.S_ISREG(opened.st_mode) or not _same_identity(opened, expected):
            raise ValueError(f"source changed while snapshotting: {source}")
        mode = stat.S_IMODE(opened.st_mode) & 0o666
        destination_fd = os.open(
            destination,
            os.O_WRONLY | os.O_CREAT | os.O_EXCL | nofollow,
            mode or 0o600,
        )
        while True:
            chunk = os.read(source_fd, COPY_CHUNK_SIZE)
            if not chunk:
                break
            view = memoryview(chunk)
            while view:
                written = os.write(destination_fd, view)
                view = view[written:]
    finally:
        if destination_fd >= 0:
            os.close(destination_fd)
        os.close(source_fd)


def _copy_source_tree(project: Path, repository: Path, snapshot: Path) -> None:
    if os.path.lexists(snapshot):
        raise FileExistsError(f"source snapshot path already exists: {snapshot}")
    snapshot.mkdir(mode=0o700)
    project_is_repository = os.path.samefile(project, repository)

    for current_text, directory_names, file_names in os.walk(
        project, topdown=True, followlinks=False
    ):
        current = Path(current_text)
        relative = current.relative_to(project)
        target_directory = snapshot / relative

        retained_directories: list[str] = []
        for name in sorted(directory_names):
            if (
                project_is_repository
                and relative == Path(".")
                and name.lower() in RESERVED_REPOSITORY_ROOTS
            ):
                continue
            source_entry = current / name
            entry_stat = source_entry.lstat()
            if stat.S_ISLNK(entry_stat.st_mode):
                raise ValueError(f"symlink is not allowed in source snapshot: {source_entry}")
            if not stat.S_ISDIR(entry_stat.st_mode):
                raise ValueError(f"unsupported source entry: {source_entry}")
            (target_directory / name).mkdir(mode=0o700)
            retained_directories.append(name)
        directory_names[:] = retained_directories

        for name in sorted(file_names):
            if (
                project_is_repository
                and relative == Path(".")
                and name.lower() in RESERVED_REPOSITORY_ROOTS
            ):
                continue
            source_entry = current / name
            entry_stat = source_entry.lstat()
            if stat.S_ISLNK(entry_stat.st_mode):
                raise ValueError(f"symlink is not allowed in source snapshot: {source_entry}")
            if not stat.S_ISREG(entry_stat.st_mode):
                raise ValueError(f"unsupported source entry: {source_entry}")
            _copy_regular_file(source_entry, target_directory / name, entry_stat)


def create_verified_snapshot(project: Path, repository: Path, snapshot: Path) -> str:
    before = fingerprint_project(project, repository)
    _copy_source_tree(project, repository, snapshot)
    snapshot_fingerprint = fingerprint_project(snapshot)
    after = fingerprint_project(project, repository)
    if snapshot_fingerprint != before or after != before:
        raise ValueError("AIUI source changed while creating the AIX source snapshot")
    return before


def _metadata_from_fd(file_descriptor: int) -> tuple[int, int, int, str]:
    file_stat = os.fstat(file_descriptor)
    if not stat.S_ISREG(file_stat.st_mode):
        raise ValueError("AIX artifact is not a regular file")
    digest = hashlib.sha256()
    offset = 0
    while True:
        chunk = os.pread(file_descriptor, COPY_CHUNK_SIZE, offset)
        if not chunk:
            break
        digest.update(chunk)
        offset += len(chunk)
    final_stat = os.fstat(file_descriptor)
    if not _same_identity(file_stat, final_stat) or file_stat.st_size != final_stat.st_size:
        raise ValueError("AIX artifact changed while hashing")
    return file_stat.st_dev, file_stat.st_ino, file_stat.st_size, digest.hexdigest()


def _format_identity(metadata: tuple[int, int, int, str]) -> str:
    return ":".join(str(part) for part in metadata)


def _parse_identity(value: str) -> tuple[int, int, int, str]:
    parts = value.split(":")
    if len(parts) != 4 or not all(part.isdigit() for part in parts[:3]):
        raise ValueError("invalid AIX delivery identity")
    if len(parts[3]) != 64 or any(character not in "0123456789abcdef" for character in parts[3]):
        raise ValueError("invalid AIX delivery digest")
    return int(parts[0]), int(parts[1]), int(parts[2]), parts[3]


def _open_stable_parent(output: Path, project: Path) -> tuple[int, Path]:
    resolved_output = _validate_output_path(project, output, require_missing=False)
    if resolved_output != output:
        raise ValueError("AIX delivery parent changed after path validation")
    parent = output.parent
    if _is_within_by_identity(parent, project):
        raise ValueError("AIX delivery path must be outside the Studio import root")
    flags = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0) | getattr(os, "O_NOFOLLOW", 0)
    parent_fd = os.open(parent, flags)
    opened = os.fstat(parent_fd)
    named = os.stat(parent, follow_symlinks=False)
    if not stat.S_ISDIR(named.st_mode) or not _same_identity(opened, named):
        os.close(parent_fd)
        raise ValueError("AIX delivery parent changed while opening")
    return parent_fd, output.name


def _unlink_created(parent_fd: int, name: Path | str, identity: tuple[int, int, int, str]) -> bool:
    try:
        current = os.stat(name, dir_fd=parent_fd, follow_symlinks=False)
    except FileNotFoundError:
        return False
    if current.st_dev != identity[0] or current.st_ino != identity[1]:
        return False
    os.unlink(name, dir_fd=parent_fd)
    return True


def publish_artifact(staged: Path, output: Path, project: Path) -> str:
    project = _canonical_directory(project, "AIUI project root")
    output = _validate_output_path(project, output, require_missing=True)
    staged = staged.resolve(strict=True)
    source_fd = os.open(staged, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0))
    parent_fd = -1
    destination_fd = -1
    created_identity: tuple[int, int, int, str] | None = None
    try:
        source_metadata = _metadata_from_fd(source_fd)
        parent_fd, name = _open_stable_parent(output, project)
        flags = os.O_RDWR | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0)
        destination_fd = os.open(
            name,
            flags,
            stat.S_IMODE(os.fstat(source_fd).st_mode) & 0o666 or 0o600,
            dir_fd=parent_fd,
        )
        initial_destination = os.fstat(destination_fd)
        created_identity = (
            initial_destination.st_dev,
            initial_destination.st_ino,
            initial_destination.st_size,
            hashlib.sha256(b"").hexdigest(),
        )
        while True:
            chunk = os.read(source_fd, COPY_CHUNK_SIZE)
            if not chunk:
                break
            view = memoryview(chunk)
            while view:
                written = os.write(destination_fd, view)
                view = view[written:]
        os.fsync(destination_fd)
        destination_metadata = _metadata_from_fd(destination_fd)
        created_identity = destination_metadata
        if destination_metadata[2:] != source_metadata[2:]:
            raise ValueError("published AIX bytes differ from the staged artifact")
        named_parent = os.stat(output.parent, follow_symlinks=False)
        if not _same_identity(os.fstat(parent_fd), named_parent):
            raise ValueError("AIX delivery parent changed during publication")
        named_output = os.stat(name, dir_fd=parent_fd, follow_symlinks=False)
        if named_output.st_dev != destination_metadata[0] or named_output.st_ino != destination_metadata[1]:
            raise ValueError("AIX delivery path changed during publication")
        return _format_identity(destination_metadata)
    except Exception:
        if parent_fd >= 0 and created_identity is not None:
            try:
                _unlink_created(parent_fd, output.name, created_identity)
            except OSError:
                pass
        raise
    finally:
        if destination_fd >= 0:
            os.close(destination_fd)
        if parent_fd >= 0:
            os.close(parent_fd)
        os.close(source_fd)


def verify_artifact(staged: Path, output: Path, project: Path, identity_text: str) -> tuple[int, str]:
    expected = _parse_identity(identity_text)
    project = _canonical_directory(project, "AIUI project root")
    output = _validate_output_path(project, output, require_missing=False)
    staged = staged.resolve(strict=True)
    parent_fd, name = _open_stable_parent(output, project)
    staged_fd = os.open(staged, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0))
    output_fd = -1
    try:
        output_fd = os.open(
            name,
            os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0),
            dir_fd=parent_fd,
        )
        output_metadata = _metadata_from_fd(output_fd)
        staged_metadata = _metadata_from_fd(staged_fd)
        if output_metadata != expected:
            raise ValueError("final AIX artifact identity or digest changed")
        if staged_metadata[2:] != expected[2:]:
            raise ValueError("staged AIX artifact changed after publication")
        named_parent = os.stat(output.parent, follow_symlinks=False)
        if not _same_identity(os.fstat(parent_fd), named_parent):
            raise ValueError("AIX delivery parent changed during verification")
        return output_metadata[2], output_metadata[3]
    finally:
        if output_fd >= 0:
            os.close(output_fd)
        os.close(staged_fd)
        os.close(parent_fd)


def cleanup_artifact(output: Path, identity_text: str) -> None:
    expected = _parse_identity(identity_text)
    _reject_control_characters(str(output), "AIX delivery path")
    output = _absolute(output)
    try:
        flags = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0) | getattr(os, "O_NOFOLLOW", 0)
        parent_fd = os.open(output.parent, flags)
    except OSError:
        return
    output_fd = -1
    try:
        output_fd = os.open(
            output.name,
            os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_NONBLOCK", 0),
            dir_fd=parent_fd,
        )
        # Publication has closed its descriptor. An unlinked inode may have
        # been recycled, so device/inode alone no longer proves ownership.
        # Keep this descriptor open through unlink to prevent another reuse.
        if _metadata_from_fd(output_fd) != expected:
            return
        _unlink_created(parent_fd, output.name, expected)
    except (OSError, ValueError):
        # A missing, replaced, unreadable, or changing file is not ours to delete.
        return
    finally:
        if output_fd >= 0:
            os.close(output_fd)
        os.close(parent_fd)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    validate_parser = subparsers.add_parser("validate")
    validate_parser.add_argument("project", type=Path)
    validate_parser.add_argument("output", type=Path)
    validate_parser.add_argument("repository", type=Path)

    snapshot_parser = subparsers.add_parser("snapshot")
    snapshot_parser.add_argument("project", type=Path)
    snapshot_parser.add_argument("repository", type=Path)
    snapshot_parser.add_argument("destination", type=Path)

    publish_parser = subparsers.add_parser("publish")
    publish_parser.add_argument("staged", type=Path)
    publish_parser.add_argument("output", type=Path)
    publish_parser.add_argument("project", type=Path)

    verify_parser = subparsers.add_parser("verify")
    verify_parser.add_argument("staged", type=Path)
    verify_parser.add_argument("output", type=Path)
    verify_parser.add_argument("project", type=Path)
    verify_parser.add_argument("identity")

    cleanup_parser = subparsers.add_parser("cleanup")
    cleanup_parser.add_argument("output", type=Path)
    cleanup_parser.add_argument("identity")

    args = parser.parse_args()
    try:
        if args.command == "validate":
            project, repository, output = validate_paths(
                args.project, args.output, args.repository
            )
            print(f"{project}\t{repository}\t{output}")
        elif args.command == "snapshot":
            project = _canonical_directory(args.project, "AIUI project root")
            repository = _canonical_directory(args.repository, "repository root")
            print(create_verified_snapshot(project, repository, args.destination))
        elif args.command == "publish":
            print(publish_artifact(args.staged, args.output, args.project))
        elif args.command == "verify":
            size, digest = verify_artifact(
                args.staged, args.output, args.project, args.identity
            )
            print(f"{size}\t{digest}")
        else:
            cleanup_artifact(args.output, args.identity)
    except (OSError, UnicodeError, ValueError) as error:
        parser.error(str(error))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
