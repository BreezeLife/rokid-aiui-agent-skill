# Third-Party Notices

This repository contains independently written guidance, tests, and validation code. It does not vendor the referenced courseware, videos, design document, AIUI repository, AIX implementation, samples, or DeepSeek Harness toolkit.

## ROKID / YodaOS AIUI

- Stable compatibility snapshot inspected: [AIUI `v0.17.0` at `88e70bb0382525c1a93ef077c2401dcc31a273ce`](https://github.com/yodaos-project/AIUI/tree/88e70bb0382525c1a93ef077c2401dcc31a273ce).
- Source snapshot inspected: [yodaos-project/AIUI at `8b19a87b4ba8b486c0dd4dd3fd32290d27891069`](https://github.com/yodaos-project/AIUI/commit/8b19a87b4ba8b486c0dd4dd3fd32290d27891069).
- The new Skill is based on the upstream `skills/aiui-dev` workflow and official samples, with current documentation and implementation evidence layered over stale conflicting statements.
- The upstream root package metadata declares `Apache-2.0`.
- No upstream source or manual is copied wholesale. Short names, API identifiers, facts, and links are used for compatibility guidance.

## AIX

- Source snapshot inspected: [yodaos-project/aix at `8e5f5b1ba60691291f99d14ea9516995f2af55e4`](https://github.com/yodaos-project/aix/commit/8e5f5b1ba60691291f99d14ea9516995f2af55e4).
- Published npm CLI verified independently: `@yodaos-pkg/aix-cli@0.8.2`; its package metadata declares `MIT`.
- This repository invokes the external CLI for an integration smoke test but does not redistribute it.

## Awesome AIUI

- Discovery index inspected: [yodaos-project/awesome-aiui at `98049c58e31e25abcf6c4b9d93e469346a7c88a9`](https://github.com/yodaos-project/awesome-aiui/commit/98049c58e31e25abcf6c4b9d93e469346a7c88a9).
- It is used only to discover candidate resources; it is not treated as API or runtime authority.

## Official ROKID learning and design materials

- [乐奇学院 AIUI 课程](https://t.rokid.com/n2w8u2o)
- [Rokid Glasses 推荐设计规范](https://custom.rokid.com/prod/rokid_web/57e35cd3ae294d16b1b8fc8dcbb1b7c7/pc/cn/5a71b66dbc1e4689886c7aa437299f2b.html)

No redistribution license was identified for the videos, PDF courseware, or dynamically served design document. This repository links to them and records limited factual summaries; it does not bundle those assets.

## DeepSeek Harness ROKID AIUI toolkit

- Community source inspected: [twinkle10010/dsh-rokid-aiui at `ddf012da7d3b488b5edf5b77faff71a1663f5342`](https://github.com/twinkle10010/dsh-rokid-aiui/commit/ddf012da7d3b488b5edf5b77faff71a1663f5342).
- Its package metadata declares `MIT`; the inspected Git snapshot and npm package are not reproducibly identical.
- Only high-level workflow observations informed this project. No toolkit code or bundled Skill file is included here.
