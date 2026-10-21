# Source of truth and version policy

Read this first when a request does not name an AIUI runtime version, when two upstream pages disagree, or before adding a component, API, permission, or AIX command.

## Default and reproducible snapshot

Sources were rechecked on **2026-10-21**.

- Default to **AIUI 0.19.0** for new work. Read [aiui-0.19.md](aiui-0.19.md) for its source map, new capabilities, compatibility changes, and functional/UX scenarios. The pinned official snapshot is [`7d62c2d9ac1cdc1389ba06ed0651b395903accff`](https://github.com/yodaos-project/AIUI/tree/7d62c2d9ac1cdc1389ba06ed0651b395903accff), observed on both `main` and `v0.19.x`; no `v0.19.0` tag was published at inspection. The [versioned runtime changelog](https://github.com/yodaos-project/AIUI/blob/7d62c2d9ac1cdc1389ba06ed0651b395903accff/documentation/8-changelog/latest.en-US.md) explicitly describes v0.19.0.
- The official website selector labeled **0.19.0 Stable** and `latest` **0.20.0 Preview** at inspection. Its [TOC API](https://open.rokid.com/aiui/-/api/docs/toc?version=latest&locale=en-US) resolves `latest` to `main`, `0.19.0` to `v0.19.x`, and `0.18.0` to `v0.18.x`. The deployed selector bundle (`AIUIDetail-CJWBgXx8.js`) supplied those labels; they are an observation, not an immutable release guarantee. Use explicit `version=0.19.0` and the full source commit for repeatable decisions. Never equate `latest` permanently with 0.19.0.
- Keep the user-provided [0.19 introduction](https://open.rokid.com/aiui/guide/quickstart/intro?lang=en-US&version=0.19.0), [0.18 quickstart](https://js.rokid.com/AIUI/guide/quickstart/quickstart?version=0.18.0&lang=en-US), and [latest quickstart](https://js.rokid.com/AIUI/guide/quickstart/quickstart?version=latest&lang=en-US) as navigation entrypoints. Website content is mutable; a query parameter alone does not prove the served runtime contract.
- Preserve an existing project's explicit 0.17/0.18 target until a migration is requested. Bundled 0.17 examples and signed evidence remain 0.17-specific. For 0.19, the local audit currently inventories capabilities but keeps every capability `BLOCKED` until a separate 0.19 source policy and version-matched evidence are implemented. Changing a source SHA or replaying a 0.17 `PASS` cannot authorize 0.19 release readiness.
- The canonical repositories are now under `yodaos-project`; the user-provided `jsar-project` URLs redirect there.

## Explicit older targets

- **0.17.0**: tag `v0.17.0`, commit [`88e70bb0382525c1a93ef077c2401dcc31a273ce`](https://github.com/yodaos-project/AIUI/tree/88e70bb0382525c1a93ef077c2401dcc31a273ce). Retain its [quickstart](https://github.com/yodaos-project/AIUI/blob/88e70bb0382525c1a93ef077c2401dcc31a273ce/documentation/0-guide/quickstart/quickstart.md), [project structure](https://github.com/yodaos-project/AIUI/blob/88e70bb0382525c1a93ef077c2401dcc31a273ce/documentation/0-guide/structure.md), and version-matched APIs for explicit compatibility work.
- **0.18.0**: released tag `v0.18.0`, commit [`cfa902ba2732121808ddf07a4e71465545977742`](https://github.com/yodaos-project/AIUI/tree/cfa902ba2732121808ddf07a4e71465545977742). Earlier references in this package also retain the dated pre-tag snapshot `8b19a87b4ba8b486c0dd4dd3fd32290d27891069`; its historical “preview” label describes that snapshot, not the present release status. The tag's [changelog](https://github.com/yodaos-project/AIUI/blob/cfa902ba2732121808ddf07a4e71465545977742/documentation/8-changelog/latest.en-US.md) documents Widgets and Agent Workers. Do not apply 0.19-only changes to an explicit 0.18 project without migration evidence.

Do not label whole technology families as 0.18-only. For example, the 0.17 baseline already documents [networking including WebSocket](https://github.com/yodaos-project/AIUI/blob/88e70bb0382525c1a93ef077c2401dcc31a273ce/documentation/0-guide/basic/network/index.md) and [CSS transitions](https://github.com/yodaos-project/AIUI/blob/88e70bb0382525c1a93ef077c2401dcc31a273ce/documentation/1-framework/wxss/property.md#L104-L115). The 0.18 changelog describes broader or improved support, including more animatable properties and `@keyframes`, rather than the first existence of all networking or motion.

## Conflict order

Within one target version, use this order:

1. Current official changelog and version-matched framework/API documentation.
2. Runtime/source behavior and runnable official samples.
3. The bundled upstream `skills/aiui-dev` summaries.

This Skill is deliberately derived from the official [AIUI `aiui-dev` Skill](https://github.com/yodaos-project/AIUI/tree/7d62c2d9ac1cdc1389ba06ed0651b395903accff/skills/aiui-dev) and [official samples](https://github.com/yodaos-project/AIUI/tree/7d62c2d9ac1cdc1389ba06ed0651b395903accff/samples). Retain its useful project, `.ink`, event, component/API routing, and no-guess discipline; do not copy its manuals wholesale. Where a bundled summary conflicts with newer docs or a runnable sample, prefer the latter and record the target version.

Important resolved conflicts:

- `_current` pages can be interactive in current documentation, but the exact focus and activation behavior is host/runtime-sensitive. Do not repeat the older blanket “display-only” claim or promise universal interaction.
- The 0.19 [Monochrome documentation](https://github.com/yodaos-project/AIUI/blob/7d62c2d9ac1cdc1389ba06ed0651b395903accff/documentation/6-design/visual/monochrome.en-US.md) still summarizes the old 2px/12px card grammar, while its linked [design source](https://github.com/yodaos-project/AIUI/blob/7d62c2d9ac1cdc1389ba06ed0651b395903accff/design/monochrome/design-system-green.md) explicitly migrates it to beta 1px/4px/6px/12% guidance. Use the latter for the named monochrome devices and record device results; see [interaction-and-design.md](interaction-and-design.md).
- Validate every route that `app.json.pages` declares. Do not infer that every page file in a source tree must be listed: the official [capabilities manifest declares only its index page](https://github.com/yodaos-project/AIUI/blob/8b19a87b4ba8b486c0dd4dd3fd32290d27891069/samples/capabilities/app.json#L1-L4), while its [index navigates to other paths](https://github.com/yodaos-project/AIUI/blob/8b19a87b4ba8b486c0dd4dd3fd32290d27891069/samples/capabilities/pages/index/index.js#L12-L21).
- Animation is supported. The 0.17 baseline documents transitions; 0.18 explicitly expands transitions and `@keyframes` support and ships an [animation sample](https://github.com/yodaos-project/AIUI/blob/8b19a87b4ba8b486c0dd4dd3fd32290d27891069/samples/capabilities/pages/transition_animation/index.ink#L169-L390).
- A generated scaffold is not evidence for `npm start`. At the inspected 0.18 snapshot the initializer [prints that instruction](https://github.com/yodaos-project/AIUI/blob/8b19a87b4ba8b486c0dd4dd3fd32290d27891069/packages/create-aiui-agent/index.js#L50-L54), but its [template package has no scripts](https://github.com/yodaos-project/AIUI/blob/8b19a87b4ba8b486c0dd4dd3fd32290d27891069/packages/create-aiui-agent/template/package.json). Inspect `package.json` before running a script.

## AIX version split

- AIX repository `main` was inspected at [`8e5f5b1ba60691291f99d14ea9516995f2af55e4`](https://github.com/yodaos-project/aix/tree/8e5f5b1ba60691291f99d14ea9516995f2af55e4). Its npm CLI manifest says `0.9.0` and Node `>=20` at that snapshot: [package.json](https://github.com/yodaos-project/aix/blob/8e5f5b1ba60691291f99d14ea9516995f2af55e4/packages/cli/package.json#L1-L31).
- The npm registry's published `latest` observed on 2026-09-07 was **`@yodaos-pkg/aix-cli@0.8.2`**, whose tagged source is commit [`19e6133f1984ee4455e6de9167b582864b528252`](https://github.com/yodaos-project/aix/tree/19e6133f1984ee4455e6de9167b582864b528252). Verify live metadata at the [versioned npm registry endpoint](https://registry.npmjs.org/@yodaos-pkg%2Faix-cli/0.8.2).
- Never promote a command found only on repository `main` to released guidance. Probe the installed CLI first; see [aix-workflow.md](aix-workflow.md).

## Other source classes

- The [official ROKID course](https://t.rokid.com/n2w8u2o) and [official optical design guideline](https://custom.rokid.com/prod/rokid_web/57e35cd3ae294d16b1b8fc8dcbb1b7c7/pc/cn/5a71b66dbc1e4689886c7aa437299f2b.html) are useful but mutable, non-Git sources. Record the inspection date and device-test interpretations.
- [Awesome AIUI at `98049c58e31e25abcf6c4b9d93e469346a7c88a9`](https://github.com/yodaos-project/awesome-aiui/blob/98049c58e31e25abcf6c4b9d93e469346a7c88a9/README.zh-CN.md) is a discovery index, not an API specification.
- [DeepSeek Harness ROKID AIUI kit at `ddf012da7d3b488b5edf5b77faff71a1663f5342`](https://github.com/twinkle10010/dsh-rokid-aiui/tree/ddf012da7d3b488b5edf5b77faff71a1663f5342) is a third-party, non-normative observation only. Do not copy it or let it override official behavior.
