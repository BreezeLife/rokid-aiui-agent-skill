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

The current AIX specification describes `.aix` as a structured package with entries, metadata, optional signatures, Page definitions, schemas, target hints, and derived tools: [AIX contents](https://github.com/yodaos-project/aix/blob/8e5f5b1ba60691291f99d14ea9516995f2af55e4/README.md#L34-L46). Packing creates package metadata, including `META-INF/aix/manifest.json`; listing should show `app.json` and expected Page/asset entries: [typical shape](https://github.com/yodaos-project/aix/blob/8e5f5b1ba60691291f99d14ea9516995f2af55e4/README.md#L104-L132).

If help advertises `--engine`, select a version/range that matches the target host rather than copying an example blindly. If help advertises `--optimize`, treat it as packaging optimization, not correctness validation. `.aixignore` can keep development-only files out of the artifact.

## Safe execution

- Write generated artifacts to a dedicated project `artifacts/` directory or a temporary directory.
- Never overwrite the only copy of a user-supplied `.aix` file.
- Run `list` on the exact artifact that will be handed off.
- Record CLI version, command, exit code, artifact path, byte size, and relevant listing.
- Keep the importable source project in Git; do not replace it with only the generated archive.

For cloud/device/review steps, continue with [debugging-and-release.md](debugging-and-release.md).
