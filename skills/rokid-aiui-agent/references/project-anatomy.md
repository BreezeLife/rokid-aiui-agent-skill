# Project anatomy and Studio import contract

Read this when creating a project, reviewing its tree, adding routes, or preparing a GitHub repository for AIUI Studio.

## Default deliverable

Produce a **complete AIUI source project directory**, not an isolated `.ink` fragment. The directory must be selectable by AIUI Studio local import. If the result is hosted on GitHub, either the repository root or one clearly named subdirectory must itself be the importable AIUI project root.

The official Studio quickstart documents three creation paths—conversation creation, local-folder import, and GitHub import by repository URL, branch/tag, and specified directory—in the [0.17 stable snapshot](https://github.com/yodaos-project/AIUI/blob/88e70bb0382525c1a93ef077c2401dcc31a273ce/documentation/0-guide/quickstart/quickstart.md) and [0.18 preview snapshot](https://github.com/yodaos-project/AIUI/blob/8b19a87b4ba8b486c0dd4dd3fd32290d27891069/documentation/0-guide/quickstart/quickstart.md#L16-L58).

For a GitHub handoff, report all three coordinates explicitly:

```text
Repository: https://github.com/OWNER/REPOSITORY
Ref: BRANCH_OR_TAG
AIUI project directory: /              # or e.g. samples/my-agent
```

The selected directory—not merely its parent repository—must contain `app.json` and the paths referenced by it. Do not require Studio to infer a nested project root.

## Conservative 0.17 project root

Start from the official [0.17 project structure](https://github.com/yodaos-project/AIUI/blob/88e70bb0382525c1a93ef077c2401dcc31a273ce/documentation/0-guide/structure.md) and runnable [0.17 samples](https://github.com/yodaos-project/AIUI/tree/88e70bb0382525c1a93ef077c2401dcc31a273ce/samples):

```text
agent-app/
├── AGENTS.md
├── app.json
├── app.js
├── app.wxss
├── pages/
│   └── home/
│       └── index.ink
├── components/          # optional
└── assets/              # optional
```

- `AGENTS.md` records agent identity, behavior, and capability boundaries; [the official OAF guidance separates it from UI configuration](https://github.com/yodaos-project/AIUI/blob/88e70bb0382525c1a93ef077c2401dcc31a273ce/documentation/1-framework/open-agent-format/agents.en-US.md).
- `app.json` declares page entries and global configuration; `app.js` carries application lifecycle and shared data. See the [0.17 app definition](https://github.com/yodaos-project/AIUI/blob/88e70bb0382525c1a93ef077c2401dcc31a273ce/documentation/1-framework/open-agent-format/app-json.en-US.md).
- `app.wxss` holds styles shared by Pages. Page-local styles belong beside the page or in its `.ink` file.
- A Page may be a single `.ink` file or a multi-file page. Choose one authoring mode per route; see [ink-authoring.md](ink-authoring.md).

A minimal manifest is intentionally small:

```json
{
  "pages": ["pages/home/index"],
  "window": {
    "navigationBarTitleText": "Agent"
  }
}
```

## Routes: validate declarations, do not invent a registry rule

For each string in `app.json.pages`, verify that the corresponding source exists as either:

- `<route>.ink`, or
- a multi-file entry with at least `<route>.wxml` and its matching logic/style/config as needed.

Reject empty, duplicate, or unresolved declared routes. Do **not** assert that every file below `pages/` must be present in `app.json.pages`; current official samples demonstrate dynamic navigation to files not all listed in the manifest: [manifest](https://github.com/yodaos-project/AIUI/blob/8b19a87b4ba8b486c0dd4dd3fd32290d27891069/samples/capabilities/app.json#L1-L4), [navigation](https://github.com/yodaos-project/AIUI/blob/8b19a87b4ba8b486c0dd4dd3fd32290d27891069/samples/capabilities/pages/index/index.js#L12-L21).

## 0.18-gated entries

Add these only when 0.18 is an explicit target or the host has proved support. The [0.18 changelog](https://github.com/yodaos-project/AIUI/blob/8b19a87b4ba8b486c0dd4dd3fd32290d27891069/documentation/7-changelog/latest.en-US.md#L1-L40) introduces them as development additions.

```text
agent-app/
├── widgets/weather/index.ink
└── workers/sync.js
```

```json
{
  "pages": ["pages/home/index"],
  "widgets": [
    { "path": "widgets/weather/index", "family": "1x2" }
  ],
  "agentWorkers": [
    {
      "name": "sync",
      "script": "workers/sync.js",
      "trigger": { "type": "open" },
      "lifetime": "instant"
    }
  ]
}
```

For Widgets, require an existing `.ink` path and matching `1x1` or `1x2` family. For Agent Workers, require a relative `.js` or `.ts` path and version-supported fields. See [runtime-capabilities.md](runtime-capabilities.md).

## Scaffold and package scripts

Project creation belongs to the official AIUI initializer or Studio, not to AIX. AIX packages an existing source tree. Do not invent `aix create`.

Do not assume that a scaffold has `npm start`. Inspect `package.json.scripts` and use only scripts that exist. The inspected preview initializer's output mentions `npm start`, while its [template manifest contains no scripts](https://github.com/yodaos-project/AIUI/blob/8b19a87b4ba8b486c0dd4dd3fd32290d27891069/packages/create-aiui-agent/template/package.json).

## Import handoff checklist

- `app.json` parses from the selected root.
- Every declared Page, Widget, component, and Worker entry resolves relative to that root.
- No absolute local paths, secrets, generated `.aix` files, or unrelated monorepo files are required to import.
- The target AIUI version is stated; default is 0.17 stable.
- Repository URL, exact branch/tag, and project subdirectory are stated for GitHub import.
- Local validation passes before asking the developer to import into Studio.
