#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
DELIVERY_GUARD="$SCRIPT_DIR/aix_delivery_guard.py"
PROJECT_DIR="${1:-$SKILL_ROOT/assets/studio-importable-minimal}"
DELIVERY_PATH="${2:-}"
REPOSITORY_ROOT="${3:-}"
AIX_PACKAGE="${AIX_PACKAGE:-@yodaos-pkg/aix-cli@0.8.2}"

fail() {
  printf 'ERROR: %s\n' "$1" >&2
  exit 1
}

[[ -d "$PROJECT_DIR" ]] || fail "AIUI project directory not found: $PROJECT_DIR"
[[ -f "$PROJECT_DIR/app.json" ]] || fail "app.json not found: $PROJECT_DIR/app.json"
[[ "$#" -le 3 ]] || fail "usage: smoke_aix.sh [PROJECT_DIR [OUTPUT.aix REPOSITORY_ROOT]]"

delivery_artifact=""
delivery_created=0
delivery_identity=""
completed=0
stage_dir=""
source_fingerprint=""
package_source="$PROJECT_DIR"

if [[ -n "$DELIVERY_PATH" ]]; then
  [[ -n "$REPOSITORY_ROOT" ]] \
    || fail "persistent AIX delivery requires an explicit repository root"
  [[ -f "$DELIVERY_GUARD" ]] || fail "AIX delivery guard not found: $DELIVERY_GUARD"
  if ! validated_paths="$(python3 "$DELIVERY_GUARD" validate \
    "$PROJECT_DIR" "$DELIVERY_PATH" "$REPOSITORY_ROOT" 2>&1)"; then
    fail "$validated_paths"
  fi
  IFS=$'\t' read -r PROJECT_DIR REPOSITORY_ROOT delivery_artifact \
    <<<"$validated_paths"
  [[ -n "$PROJECT_DIR" && -n "$REPOSITORY_ROOT" && -n "$delivery_artifact" ]] \
    || fail "AIX delivery guard returned invalid canonical paths"
  package_source="$PROJECT_DIR"
fi

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

cleanup() {
  if [[ "$delivery_created" == "1" && "$completed" != "1" \
    && -n "$delivery_identity" ]]; then
    if ! python3 "$DELIVERY_GUARD" cleanup \
      "$delivery_artifact" "$delivery_identity" >/dev/null 2>&1; then
      printf 'WARNING: could not safely clean the failed AIX delivery\n' >&2
    fi
  fi
  if [[ -n "${stage_dir:-}" && -d "$stage_dir" ]]; then
    stage_name="$(basename -- "$stage_dir")"
    if [[ "$stage_name" == rokid-aiui-aix-smoke.* \
      || "$stage_name" == .rokid-aiui-aix-stage.* ]]; then
      rm -rf -- "$stage_dir"
    fi
  fi
}
trap cleanup EXIT

if [[ -n "$delivery_artifact" ]]; then
  delivery_parent="$(dirname -- "$delivery_artifact")"
  mkdir -p -- "$delivery_parent"
  previous_delivery="$delivery_artifact"
  if ! validated_paths="$(python3 "$DELIVERY_GUARD" validate \
    "$PROJECT_DIR" "$delivery_artifact" "$REPOSITORY_ROOT" 2>&1)"; then
    fail "$validated_paths"
  fi
  IFS=$'\t' read -r PROJECT_DIR REPOSITORY_ROOT delivery_artifact \
    <<<"$validated_paths"
  [[ "$delivery_artifact" == "$previous_delivery" ]] \
    || fail "AIX delivery parent changed after initial validation"
  stage_dir="$(mktemp -d "$delivery_parent/.rokid-aiui-aix-stage.XXXXXX")"
  package_source="$stage_dir/source"
  if ! source_fingerprint="$(python3 "$DELIVERY_GUARD" snapshot \
    "$PROJECT_DIR" "$REPOSITORY_ROOT" "$package_source" 2>&1)"; then
    fail "cannot create a verified AIX source snapshot: $source_fingerprint"
  fi
else
  stage_dir="$(mktemp -d "${TMPDIR:-/tmp}/rokid-aiui-aix-smoke.XXXXXX")"
fi

expected_entries=()
if ! expected_output="$(python3 -c '
import json
import pathlib
import sys

root = pathlib.Path(sys.argv[1])
manifest = json.loads((root / "app.json").read_text(encoding="utf-8"))
if not isinstance(manifest, dict):
    raise SystemExit("app.json must contain an object")
routes = manifest.get("pages")
if not isinstance(routes, list) or not routes:
    raise SystemExit("app.json pages must be a non-empty array")
if any(not isinstance(route, str) or not route for route in routes):
    raise SystemExit("every app.json page route must be a non-empty string")
entries = [candidate for candidate in (root / "app.js", root / "app.ink") if candidate.is_file()]
if len(entries) != 1:
    raise SystemExit("expected exactly one application entry: app.js or app.ink")
print(entries[0].relative_to(root).as_posix())
for route in routes:
    pages = [candidate for suffix in (".ink", ".wxml") if (candidate := root / f"{route}{suffix}").is_file()]
    if len(pages) != 1:
        raise SystemExit(f"declared page must resolve to exactly one .ink or .wxml entry: {route}")
    print(pages[0].relative_to(root).as_posix())
' "$package_source" 2>&1)"; then
  fail "cannot determine required AIX entries: $expected_output"
fi
while IFS= read -r expected_entry; do
  [[ -n "$expected_entry" ]] && expected_entries+=("$expected_entry")
done <<<"$expected_output"
if [[ -n "${AIX_EXPECTED_ENTRY:-}" ]]; then
  expected_entries+=("$AIX_EXPECTED_ENTRY")
fi

artifact="$stage_dir/fixture.aix"
if ! "${runner[@]}" pack "$package_source" -o "$artifact"; then
  fail "AIX pack execution failed"
fi
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
for expected_entry in "${expected_entries[@]}"; do
  listing_has_entry "$expected_entry" \
    || fail "AIX listing does not contain $expected_entry"
done
if listing_has_reserved_entry; then
  fail "AIX listing contains reserved .aiui-evidence or .git content"
fi

if [[ -n "$delivery_artifact" ]]; then
  if ! source_fingerprint_after="$(python3 "$SCRIPT_DIR/fingerprint_aiui_project.py" \
    "$PROJECT_DIR" --repository-root "$REPOSITORY_ROOT" 2>&1)"; then
    fail "cannot fingerprint the AIUI source after packaging: $source_fingerprint_after"
  fi
  [[ "$source_fingerprint_after" == "$source_fingerprint" ]] \
    || fail "AIUI source fingerprint changed during AIX packaging"

  if ! delivery_identity="$(python3 "$DELIVERY_GUARD" publish \
    "$artifact" "$delivery_artifact" "$PROJECT_DIR" 2>&1)"; then
    fail "cannot publish the verified AIX artifact: $delivery_identity"
  fi
  delivery_created=1
  if ! listing="$("${runner[@]}" "$list_command" "$delivery_artifact" 2>&1)"; then
    printf '%s\n' "$listing" >&2
    fail "final AIX artifact listing failed"
  fi
  listing_has_entry "META-INF/aix/manifest.json" \
    || fail "final AIX listing does not contain META-INF/aix/manifest.json"
  listing_has_entry "app.json" || fail "final AIX listing does not contain app.json"
  for expected_entry in "${expected_entries[@]}"; do
    listing_has_entry "$expected_entry" \
      || fail "final AIX listing does not contain $expected_entry"
  done
  if listing_has_reserved_entry; then
    fail "final AIX listing contains reserved .aiui-evidence or .git content"
  fi
  if ! artifact_metadata="$(python3 "$DELIVERY_GUARD" verify \
    "$artifact" "$delivery_artifact" "$PROJECT_DIR" \
    "$delivery_identity" 2>&1)"; then
    fail "final AIX artifact changed during listing: $artifact_metadata"
  fi
  IFS=$'\t' read -r artifact_bytes artifact_sha256 <<<"$artifact_metadata"
  [[ -n "$artifact_bytes" && -n "$artifact_sha256" ]] \
    || fail "AIX delivery guard returned invalid artifact metadata"
  if ! source_fingerprint_after="$(python3 "$SCRIPT_DIR/fingerprint_aiui_project.py" \
    "$PROJECT_DIR" --repository-root "$REPOSITORY_ROOT" 2>&1)"; then
    fail "cannot fingerprint the AIUI source after AIX handoff: $source_fingerprint_after"
  fi
  [[ "$source_fingerprint_after" == "$source_fingerprint" ]] \
    || fail "AIUI source fingerprint changed during AIX handoff"
  if ! artifact_metadata_after="$(python3 "$DELIVERY_GUARD" verify \
    "$artifact" "$delivery_artifact" "$PROJECT_DIR" \
    "$delivery_identity" 2>&1)"; then
    fail "final AIX artifact changed during source verification: $artifact_metadata_after"
  fi
  [[ "$artifact_metadata_after" == "$artifact_metadata" ]] \
    || fail "final AIX artifact metadata changed during handoff"
fi

printf '%s\n' "$listing"
printf 'AIX smoke passed: pack + %s verified app.json and %s required source entries\n' \
  "$list_command" "${#expected_entries[@]}"
if [[ -n "$delivery_artifact" ]]; then
  printf 'AIUI source fingerprint: %s\n' "$source_fingerprint"
  printf 'AIX artifact: %s\n' "$delivery_artifact"
  printf 'AIX bytes: %s\n' "$artifact_bytes"
  printf 'AIX SHA-256: %s\n' "$artifact_sha256"
  printf 'AIX inspect command: %s\n' "$list_command"
fi
completed=1
