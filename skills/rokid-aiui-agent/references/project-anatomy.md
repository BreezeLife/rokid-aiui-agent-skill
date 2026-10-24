# Project anatomy and Studio import contract

Read this when creating a project, configuring `app.json`, reviewing its tree, adding routes, or preparing a GitHub repository for AIUI Studio.

Default new projects to **0.19.0** and read [aiui-0.19.md](aiui-0.19.md). The 0.17/0.18 sources below remain compatibility evidence for explicit older targets; an existing fixture keeps its stated version.

## Default deliverable

Produce a **complete AIUI source project directory**, not an isolated `.ink` fragment. The directory must be selectable by AIUI Studio local import. If the result is hosted on GitHub, either the repository root or one clearly named subdirectory must itself be the importable AIUI project root.

The official Studio quickstart documents three creation paths—conversation creation, local-folder import, and GitHub import by repository URL, branch/tag, and specified directory—in the [0.19 snapshot](https://github.com/yodaos-project/AIUI/blob/7d62c2d9ac1cdc1389ba06ed0651b395903accff/documentation/0-guide/quickstart/quickstart.en-US.md), [0.17 snapshot](https://github.com/yodaos-project/AIUI/blob/88e70bb0382525c1a93ef077c2401dcc31a273ce/documentation/0-guide/quickstart/quickstart.md), and historical [0.18 preview snapshot](https://github.com/yodaos-project/AIUI/blob/8b19a87b4ba8b486c0dd4dd3fd32290d27891069/documentation/0-guide/quickstart/quickstart.md#L16-L58).

For a GitHub handoff, report all three coordinates explicitly:

```text
Repository: https://github.com/OWNER/REPOSITORY
Ref: BRANCH_OR_TAG
AIUI project directory: /              # or e.g. samples/my-agent
```

The selected directory—not merely its parent repository—must contain `app.json` and the paths referenced by it. Do not require Studio to infer a nested project root.

## Minimal Page root

The basic tree is shared with the explicit 0.17 examples. For new work use the [0.19 structure](https://github.com/yodaos-project/AIUI/blob/7d62c2d9ac1cdc1389ba06ed0651b395903accff/documentation/0-guide/structure.en-US.md); the following [0.17 structure](https://github.com/yodaos-project/AIUI/blob/88e70bb0382525c1a93ef077c2401dcc31a273ce/documentation/0-guide/structure.md) and runnable [samples](https://github.com/yodaos-project/AIUI/tree/88e70bb0382525c1a93ef077c2401dcc31a273ce/samples) preserve the earlier compatibility evidence:

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

## Configure app.json from actual features

Use the user's [0.18 app.json documentation](https://js.rokid.com/AIUI/framework/open-agent-format-app-json?version=0.18.0&lang=zh-CN) as the navigation entrypoint. The official [0.18 release source](https://github.com/yodaos-project/AIUI/blob/cfa902ba2732121808ddf07a4e71465545977742/documentation/1-framework/open-agent-format/app-json.md) and [0.19 source](https://github.com/yodaos-project/AIUI/blob/7d62c2d9ac1cdc1389ba06ed0651b395903accff/documentation/1-framework/open-agent-format/app-json.md) were checked on 2026-10-25. Preserve the project's selected version; do not downgrade new work because a reference URL selects 0.18.

Configure the selected import root, then explain each field in terms of the shipped feature:

| Field | Configuration decision |
| --- | --- |
| `pages` | List real route entries without source extensions; resolve every declared path as described below. |
| `window` | Set shared window configuration such as `navigationBarTitleText`; keep Page-specific UI in the Page. |
| `permissions` | Use exact, case-sensitive strings for APIs actually used. A declaration does not grant OS authorization or execute the API. |
| `usingComponents` | Declare actual component entries when needed; 0.19 requires a concrete entry path. |
| `widgets` / `agentWorkers` | Add only required, version-supported surfaces with the contracts below. Do not add a Worker merely to enable a camera. |
| `app.<locale>.json` | Optional Widget text overrides keyed by Widget path; retain default text and runtime configuration in `app.json`. |

For a Page that **only takes photos**, this manifest is sufficient configuration for the declared route and camera permission; it is not a complete camera implementation:

```json
{
  "pages": ["pages/camera/index"],
  "window": { "navigationBarTitleText": "Photo Agent" },
  "permissions": ["CAMERA"]
}
```

Create the corresponding Page and application entry. Do not copy all permissions from an upstream demo:

| Actual operation | Manifest permission |
| --- | --- |
| Camera photos or video input | `CAMERA` |
| Microphone input or audio recording | `RECORD_AUDIO` |
| Location access | `GEOLOCATION` |
| Read / add images in the system media library | `READ_MEDIA_IMAGES` / `CREATE_MEDIA_IMAGES`, respectively |
| Read / add audio in the system media library | `READ_MEDIA_AUDIO` / `CREATE_MEDIA_AUDIO`, respectively |

Taking a photo does not itself request system-library storage, and playing supplied audio does not itself open a microphone. Add library or recording permissions only for those actual operations. Missing declarations, denied authorization, and unavailable devices need separate recovery paths. For 0.19, do not add the removed `SPEECH_RECOGNITION` permission.

For camera or other multimedia features, also read [media implementation and testing](media-implementation-and-testing.md). In particular, `"CAMERA"`, `getUserMedia()` and `new ImageCapture(...)` do not take a still photo: the selected interaction must reach and await `capture.takePhoto()` (or the documented wx equivalent). `_blank` is a runtime target requirement, not an invented `app.json` permission or target field.

## Routes: validate declarations, do not invent a registry rule

For each string in `app.json.pages`, verify that the corresponding source exists as either:

- `<route>.ink`, or
- a multi-file entry with at least `<route>.wxml` and its matching logic/style/config as needed.

Reject empty, duplicate, or unresolved declared routes. Do **not** assert that every file below `pages/` must be present in `app.json.pages`; current official samples demonstrate dynamic navigation to files not all listed in the manifest: [manifest](https://github.com/yodaos-project/AIUI/blob/8b19a87b4ba8b486c0dd4dd3fd32290d27891069/samples/capabilities/app.json#L1-L4), [navigation](https://github.com/yodaos-project/AIUI/blob/8b19a87b4ba8b486c0dd4dd3fd32290d27891069/samples/capabilities/pages/index/index.js#L12-L21).

## Widget and Agent Worker entries in 0.19

These entries are supported by the default 0.19 target, with exact [Widget](https://github.com/yodaos-project/AIUI/blob/7d62c2d9ac1cdc1389ba06ed0651b395903accff/documentation/1-framework/open-agent-format/widget.en-US.md) and [Agent Worker](https://github.com/yodaos-project/AIUI/blob/7d62c2d9ac1cdc1389ba06ed0651b395903accff/documentation/1-framework/open-agent-format/agent-worker.en-US.md) contracts. They originated in 0.18 and remain unavailable to an explicit 0.17 project.

```text
agent-app/
├── widgets/weather/index.ink
└── workers/sync.js
```

```json
{
  "pages": ["pages/home/index"],
  "widgets": [
    {
      "path": "widgets/weather/index",
      "family": "1x2",
      "placement": "overlay",
      "displayName": "Weather",
      "description": "Shows current weather."
    }
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

For Widgets, require an existing `.ink` path, matching `1x1`/`1x2` family, default `displayName`/`description`, and relative layout. `placement` defaults to `persistent`; use `overlay` for `window.open()` and keep placement in the manifest. For Agent Workers, require a safe relative `.js`/`.ts` path, one `open` trigger, and `instant`/`foreground` lifetime. The directory is still named `workers/`, but its manifest field is `agentWorkers`, never the removed `workers`. See [runtime-capabilities.md](runtime-capabilities.md).

In 0.19, `usingComponents` must name the concrete entry, such as `/components/card/index`; a directory path alone does not search for `index`. Test unresolved and nested component paths as loading failures.

## Scaffold and package scripts

Project creation belongs to the official AIUI initializer or Studio, not to AIX. AIX packages an existing source tree. Do not invent `aix create`.

Do not assume that a scaffold has `npm start`. Inspect `package.json.scripts` and use only scripts that exist. The inspected preview initializer's output mentions `npm start`, while its [template manifest contains no scripts](https://github.com/yodaos-project/AIUI/blob/8b19a87b4ba8b486c0dd4dd3fd32290d27891069/packages/create-aiui-agent/template/package.json).

## Import handoff checklist

- `app.json` parses from the selected root.
- Every declared Page, Widget, component, and Worker entry resolves relative to that root.
- No absolute local paths, secrets, generated `.aix` files, or unrelated monorepo files are required to import.
- The target AIUI version is stated; default new work is 0.19.0. Retain explicit older fixture targets.
- Repository URL, exact branch/tag, and project subdirectory are stated for GitHub import.
- Local validation passes before asking the developer to import into Studio.
