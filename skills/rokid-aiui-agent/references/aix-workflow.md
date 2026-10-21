# AIX CLI workflow

Read this when installing the AIX CLI, previewing, packaging, inspecting, or deciding whether a requested command exists.

## Keep three layers separate

1. **AIUI source project**: authored/imported in Studio; creation is not an AIX command.
2. **Local AIX tooling**: browser preview, package, optimize, and inspect only when the installed CLI advertises them.
3. **ROKID platform flow**: cloud synchronization, device resource download, review, and store release in Studio/Rokid AI App.

`aix preview` is not physical-device debugging, and `aix pack` is not store deployment.

## Version facts inspected 2026-09-07

- The AIX `main` snapshot is [`8e5f5b1ba60691291f99d14ea9516995f2af55e4`](https://github.com/yodaos-project/aix/tree/8e5f5b1ba60691291f99d14ea9516995f2af55e4). Its [CLI manifest](https://github.com/yodaos-project/aix/blob/8e5f5b1ba60691291f99d14ea9516995f2af55e4/packages/cli/package.json#L1-L31) says `0.9.0`, Node `>=20`, and its [README](https://github.com/yodaos-project/aix/blob/8e5f5b1ba60691291f99d14ea9516995f2af55e4/packages/cli/README.md) includes runtime-version commands.
- The npm registry's published latest observed that day was **`@yodaos-pkg/aix-cli@0.8.2`**. Its source is tag commit [`19e6133f1984ee4455e6de9167b582864b528252`](https://github.com/yodaos-project/aix/tree/19e6133f1984ee4455e6de9167b582864b528252); verify immutable release metadata at the [versioned registry endpoint](https://registry.npmjs.org/@yodaos-pkg%2Faix-cli/0.8.2).

Repository `main` is not proof that a released installation has the same commands or preview dimensions. In particular, do not assume `aix runtime ...` from 0.9.0-era `main` is available in 0.8.2.

## Capability probe first

Require Node 20 or newer for the npm CLI, then capture evidence:

```bash
node --version
command -v aix
aix --help
```

Do not assume `aix --version` reports a version: published 0.8.2 prints its general help for that option. Record the resolved executable and package-manager version/lock evidence when the CLI does not expose a version command.

If using an isolated published npm release:

```bash
npx --yes --package @yodaos-pkg/aix-cli@0.8.2 aix --help
```

Branch only on the printed help. The tagged 0.8.2 source/release documents `pack`, `list`/`ls`, `optimize`, and `preview`; still probe because another executable may be on `PATH`.

Never invent or prescribe:

```text
aix create
aix dev
aix build
aix deploy
```

Do not prescribe `aix runtime versions/current/select` unless the installed help advertises them.

## Preview branch

If `aix preview` is advertised, use it for fast browser iteration:

```bash
aix preview ./agent-app
```

If the root `aix --help` advertises `preview` with `--dev`, it can provide browser live reload. Do not rely on `aix preview --help`: published 0.8.2 rejects that subcommand option.

```bash
aix preview ./agent-app --dev --launch
```

The published 0.8.2 and inspected main documentation differ in preview details; never hard-code a viewport assumption from the wrong CLI version. Preview uses a browser Ink runtime and cannot validate physical optics, actual host focus, hardware keys, sensors, permissions, or continuous device performance.

## Package and inspect

Validate the source tree first, then use commands present in help:

```bash
aix pack ./agent-app -o ./artifacts/agent.aix
aix list ./artifacts/agent.aix
```

For creation and implementation work, source is always the primary output. If
the selected CLI advertises both operations and they succeed, deliver the
verified archive as an additional output. Keep that output outside the Studio
import root; a sibling such as `/work/agent-app.aix` for
`/work/agent-app/` prevents the archive from changing the source fingerprint or
being packed into itself.

The packaged script has a backward-compatible delivery mode. Pass only the
project to run a disposable smoke test. Pass an output and explicit repository
root to preserve a verified package:

```bash
AIUI_REPOSITORY_ROOT="/absolute/path/to/repository"
AIUI_IMPORT_ROOT="$AIUI_REPOSITORY_ROOT/agent-app"
AIUI_AIX_OUTPUT="${AIUI_IMPORT_ROOT%/}.aix"
bash skills/rokid-aiui-agent/scripts/smoke_aix.sh \
  "$AIUI_IMPORT_ROOT" "$AIUI_AIX_OUTPUT" "$AIUI_REPOSITORY_ROOT"
```

The delivery mode refuses to overwrite any file or symlink and rejects an
output inside the Studio import root. It resolves containment by filesystem identity,
including case aliases, rather than trusting path spelling. It makes
a verified source snapshot beside the destination and packages that snapshot,
so a temporary live-source change cannot create an archive from an unreported
revision. After inspecting the staged package, it publishes with an exclusive no-clobber copy
through a fixed parent-directory descriptor, then lists the
exact final archive. It checks the same artifact identity and SHA-256 before
and after that listing and cleans a failed output only while its filesystem
identity still belongs to this run. The live source fingerprint must match the
snapshot before and after packaging. Successful output includes:

```text
AIUI source fingerprint: WORKTREE:<sha256>
AIX artifact: /absolute/path/to/repository/agent-app.aix
AIX bytes: <integer>
AIX SHA-256: <sha256>
AIX inspect command: list
```

The source fingerprint binds the run to the audited project. The published
AIX `0.8.2` [CLI reference](https://github.com/yodaos-project/aix/blob/19e6133f1984ee4455e6de9167b582864b528252/packages/cli/README.md#L14-L20)
defines `VERSION` as a unique UUID v4. This random build ID means two valid
builds from the same source need not share the same package SHA-256;
`AIX SHA-256` identifies the exact bytes handed off.

The wrapper output proves the local delivery flow but does not by itself satisfy signed AIX audit evidence.
To mark the audit's AIX layer `PASS`, capture
the underlying `aix pack` and `aix list` (or `aix ls`) executions separately as
schema-2 command evidence signed by the configured `RUNNER` authority; the
audit validator does not treat a wrapper command as the underlying AIX argv.

Published AIX 0.8.2 does not implicitly exclude the import root's top-level
`.aiui-evidence/` or `.git/` directories. If the repository root is also the
Studio import root, a repository-root `.aiui-evidence/` directory will be
packaged and can leak audit captures. Prefer keeping evidence outside the
import root, for example by making the importable project a repository
subdirectory. If the repository root must also be the import root, place these
exact directory exclusions in the import-root `.aixignore`:

```gitignore
.aiui-evidence/
.git/
```

Treat the exact `aix list` result as a privacy and consistency gate. Normalize
ASCII case before comparison and fail the package if any entry is
`.aiui-evidence`, starts with `.aiui-evidence/`, is `.git`, or starts with
`.git/`; mixed-case aliases are equally reserved, and required application
entries do not compensate for reserved content. The packaged
[`smoke_aix.sh`](../scripts/smoke_aix.sh) enforces this check.

The current AIX specification describes `.aix` as a structured package with entries, metadata, optional signatures, Page definitions, schemas, target hints, and derived tools: [AIX contents](https://github.com/yodaos-project/aix/blob/8e5f5b1ba60691291f99d14ea9516995f2af55e4/README.md#L34-L46). Packing creates package metadata, including `META-INF/aix/manifest.json`; listing should show `app.json` and expected Page/asset entries: [typical shape](https://github.com/yodaos-project/aix/blob/8e5f5b1ba60691291f99d14ea9516995f2af55e4/README.md#L104-L132).

If help advertises `--engine`, select a version/range that matches the target host rather than copying an example blindly. If help advertises `--optimize`, treat it as packaging optimization, not correctness validation. `.aixignore` can keep development-only files out of the artifact, but the exact final listing remains the delivery gate.

## Package result semantics

Keep source delivery and AIX delivery as separate results:

- `PASS`: the final archive was packed and listed, required entries and privacy checks passed, the source fingerprint stayed unchanged, and path/bytes/SHA-256 were reported.
- `BLOCKED`: Node or AIX is unavailable, installation cannot be completed, or help does not advertise `pack` plus `list`/`ls`.
- `FAIL`: an attempted pack/list failed, the archive was empty, required entries were absent, reserved content appeared, the destination was unsafe, or the source changed during packaging.
- `N/A`: only for a review or diagnosis whose agreed scope excludes packaging; it is not a fallback for missing tooling.

Do not claim an archive was delivered unless the final-path checks passed. A
source project can still be delivered when its AIX gate is `BLOCKED` or
`FAIL`, but the separate package result must remain visible.

## Safe execution

- Write generated deliverables outside the Studio import root or use a temporary directory for disposable checks.
- Never overwrite an existing `.aix` file; the packaged delivery script refuses to overwrite.
- Run `list` on the exact artifact that will be handed off.
- Record CLI version, commands, exit codes, source fingerprint, artifact path, byte size, SHA-256, and relevant listing.
- Keep the importable source project in Git; do not replace it with only the generated archive.

For cloud/device/review steps, continue with [debugging-and-release.md](debugging-and-release.md).
