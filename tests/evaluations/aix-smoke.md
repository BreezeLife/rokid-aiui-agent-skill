# Published AIX CLI Smoke Evidence

- Captured: 2026-09-07
- Package: `@yodaos-pkg/aix-cli@0.8.2`
- Runtime: Node.js `v24.19.0`, pnpm `11.19.0`
- Capability gate: the selected executable's `--help` advertised `pack` and `list`
- Upload/deployment: not attempted

## Studio-importable example

Command:

```bash
bash skills/rokid-aiui-agent/scripts/smoke_aix.sh \
  skills/rokid-aiui-agent/assets/studio-importable-minimal
```

Result: passed after the final package relocation. AIX created a non-empty 2.54 KB archive and `list` reported `AGENTS.md`, generated `META-INF/aix/manifest.json`, generated `VERSION`, `app.js`, `app.json`, and `pages/index/index.ink`.

The advertised `preview --html-out` path was also exercised again on the same relocated directory. It produced a non-empty 17,260-byte static preview document whose embedded project state contained `app.json` and the declared `.ink` page. The document was served locally and opened in a browser: AIX reached `Preview ready` and visibly rendered “AIUI project ready” plus the import instruction on the preview canvas. This proves the browser preview path, not AIUI Studio import or physical-glasses rendering.

## Minimal validator fixture

Command:

```bash
bash skills/rokid-aiui-agent/scripts/smoke_aix.sh tests/fixtures/valid-minimal
```

Result: passed. AIX created a non-empty 1.67 KB archive and `list` reported `app.json` plus the declared `pages/index/index.ink` entry. Both smoke runs used isolated temporary directories that the script removed on exit.

These results establish source packaging and archive inspection only. They do not establish successful AIUI Studio import, cloud upload, or behavior on physical glasses; those remain separate platform/device gates.
