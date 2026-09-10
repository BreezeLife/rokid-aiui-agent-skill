#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
PROJECT_DIR="${1:-$SKILL_ROOT/assets/studio-importable-minimal}"
AIX_PACKAGE="${AIX_PACKAGE:-@yodaos-pkg/aix-cli@0.8.2}"

fail() {
  printf 'ERROR: %s\n' "$1" >&2
  exit 1
}

[[ -d "$PROJECT_DIR" ]] || fail "AIUI project directory not found: $PROJECT_DIR"
[[ -f "$PROJECT_DIR/app.json" ]] || fail "app.json not found: $PROJECT_DIR/app.json"

runner=()
if [[ "${AIX_FORCE_PACKAGE:-0}" == "1" ]]; then
  if command -v pnpm >/dev/null 2>&1; then
    runner=(pnpm --package "$AIX_PACKAGE" dlx aix)
  elif command -v npx >/dev/null 2>&1; then
    runner=(npx --yes --package "$AIX_PACKAGE" aix)
  else
    fail "AIX_FORCE_PACKAGE=1 requires pnpm or npx"
  fi
elif [[ -n "${AIX_BIN:-}" ]]; then
  [[ -x "$AIX_BIN" ]] || fail "AIX_BIN is not executable: $AIX_BIN"
  runner=("$AIX_BIN")
elif command -v aix >/dev/null 2>&1; then
  runner=(aix)
elif command -v pnpm >/dev/null 2>&1; then
  runner=(pnpm --package "$AIX_PACKAGE" dlx aix)
elif command -v npx >/dev/null 2>&1; then
  runner=(npx --yes --package "$AIX_PACKAGE" aix)
else
  fail "no aix, pnpm, or npx executable is available"
fi

if ! help_output="$("${runner[@]}" --help 2>&1)"; then
  printf '%s\n' "$help_output" >&2
  fail "the selected AIX executable failed its --help capability probe"
fi

if ! grep -Eq '(^|[[:space:]])pack([[:space:]<]|$)' <<<"$help_output"; then
  fail "the selected AIX release does not advertise pack"
fi

list_command=""
if grep -Eq '(^|[[:space:]])list([[:space:]<]|$)' <<<"$help_output"; then
  list_command="list"
elif grep -Eq '(^|[[:space:]])ls([[:space:]<]|$)' <<<"$help_output"; then
  list_command="ls"
else
  fail "the selected AIX release does not advertise list or ls"
fi

expected_entry="${AIX_EXPECTED_ENTRY:-}"
if [[ -z "$expected_entry" ]]; then
  if ! expected_entry="$(python3 -c '
import json
import pathlib
import sys

root = pathlib.Path(sys.argv[1])
manifest = json.loads((root / "app.json").read_text(encoding="utf-8"))
route = manifest["pages"][0]
for suffix in (".ink", ".wxml"):
    candidate = root / f"{route}{suffix}"
    if candidate.is_file():
        print(candidate.relative_to(root).as_posix())
        break
else:
    raise SystemExit("first declared page has no .ink or .wxml entry")
' "$PROJECT_DIR" 2>&1)"; then
    fail "cannot determine the first declared page entry: $expected_entry"
  fi
fi

smoke_tmp="$(mktemp -d "${TMPDIR:-/tmp}/rokid-aiui-aix-smoke.XXXXXX")"
cleanup() {
  if [[ -n "${smoke_tmp:-}" && -d "$smoke_tmp" ]]; then
    smoke_name="$(basename -- "$smoke_tmp")"
    if [[ "$smoke_name" == rokid-aiui-aix-smoke.* ]]; then
      rm -rf -- "$smoke_tmp"
    fi
  fi
}
trap cleanup EXIT

artifact="$smoke_tmp/fixture.aix"
"${runner[@]}" pack "$PROJECT_DIR" -o "$artifact"
[[ -s "$artifact" ]] || fail "pack did not create a non-empty AIX artifact"

if ! listing="$("${runner[@]}" "$list_command" "$artifact" 2>&1)"; then
  printf '%s\n' "$listing" >&2
  fail "AIX artifact listing failed"
fi

listing_has_entry() {
  local expected="$1"
  local line
  while IFS= read -r line; do
    if [[ "$line" == "$expected" || "$line" == "$expected":\ * ]]; then
      return 0
    fi
  done <<<"$listing"
  return 1
}

listing_has_reserved_entry() {
  local line
  local entry
  local normalized_entry
  while IFS= read -r line; do
    entry="${line%%: *}"
    while [[ "$entry" == ./* ]]; do
      entry="${entry#./}"
    done
    entry="${entry%/}"
    normalized_entry="$(LC_ALL=C printf '%s' "$entry" | tr '[:upper:]' '[:lower:]')"
    case "$normalized_entry" in
      .aiui-evidence|.aiui-evidence/*|.git|.git/*)
        return 0
        ;;
    esac
  done <<<"$listing"
  return 1
}

listing_has_entry "META-INF/aix/manifest.json" \
  || fail "AIX listing does not contain META-INF/aix/manifest.json"
listing_has_entry "app.json" || fail "AIX listing does not contain app.json"
listing_has_entry "$expected_entry" \
  || fail "AIX listing does not contain $expected_entry"
if listing_has_reserved_entry; then
  fail "AIX listing contains reserved .aiui-evidence or .git content"
fi

printf '%s\n' "$listing"
printf 'AIX smoke passed: pack + %s verified app.json and %s\n' \
  "$list_command" "$expected_entry"
