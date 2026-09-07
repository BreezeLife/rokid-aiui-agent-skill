# Runtime capability index and no-guess rule

Read this before using any component, JavaScript API, permission, device capability, Widget, or Agent Worker.

## The rule

Never infer AIUI support from a browser, WeChat Mini Program, TypeScript type, or similarly named API. The upstream `aiui-dev` Skill's strongest reusable rule is to route each capability to a narrow official reference and not guess. This reference preserves that discipline while applying a 0.17-stable default and a separately gated 0.18 layer.

For every capability:

1. Name the target AIUI version and host/device.
2. Find the exact entry in version-matched official docs.
3. Verify required `app.json` permission or capability declarations.
4. Check a runnable official sample or implementation when docs are ambiguous.
5. Add a fallback for absent/denied capability.
6. Verify in Studio simulation, then on the physical device.

If any step is unknown, say so. Do not fabricate an API signature, event, permission name, or polyfill guarantee.

## 0.17 stable lookup map

Use commit `88e70bb0382525c1a93ef077c2401dcc31a273ce` for default-compatible work:

| Need | Authoritative starting point |
| --- | --- |
| Page/App lifecycle and data | [Framework APIs](https://github.com/yodaos-project/AIUI/tree/88e70bb0382525c1a93ef077c2401dcc31a273ce/documentation/3-api/framework) |
| UI elements and their exact events/properties | [Component index](https://github.com/yodaos-project/AIUI/tree/88e70bb0382525c1a93ef077c2401dcc31a273ce/documentation/2-components) |
| Routing/navigation | [Route API](https://github.com/yodaos-project/AIUI/blob/88e70bb0382525c1a93ef077c2401dcc31a273ce/documentation/3-api/route.en-US.md) |
| HTTPS, WebSocket, streams | [Network guide](https://github.com/yodaos-project/AIUI/tree/88e70bb0382525c1a93ef077c2401dcc31a273ce/documentation/0-guide/basic/network) and [network APIs](https://github.com/yodaos-project/AIUI/tree/88e70bb0382525c1a93ef077c2401dcc31a273ce/documentation/3-api/network) |
| Speech recognition, synthesis, language model | [AI APIs](https://github.com/yodaos-project/AIUI/tree/88e70bb0382525c1a93ef077c2401dcc31a273ce/documentation/3-api/ai) |
| Audio, camera, recording | [Media APIs](https://github.com/yodaos-project/AIUI/tree/88e70bb0382525c1a93ef077c2401dcc31a273ce/documentation/3-api/media) |
| Sensor/Bluetooth/device access | [Device APIs](https://github.com/yodaos-project/AIUI/tree/88e70bb0382525c1a93ef077c2401dcc31a273ce/documentation/3-api/device) |
| Storage | [Storage APIs](https://github.com/yodaos-project/AIUI/tree/88e70bb0382525c1a93ef077c2401dcc31a273ce/documentation/3-api/storage) |
| Canvas | [Canvas API](https://github.com/yodaos-project/AIUI/tree/88e70bb0382525c1a93ef077c2401dcc31a273ce/documentation/3-api/canvas) |
| `wx.*` compatibility | [Explicit compatibility list](https://github.com/yodaos-project/AIUI/blob/88e70bb0382525c1a93ef077c2401dcc31a273ce/documentation/3-api/weixin-compatible-apis.en-US.md) |

The upstream bundled component/API summaries are useful indexes, but not exhaustive runtime contracts. Follow their links into version-matched documentation instead of relying on memory.

## Permissions

Declare only exact, documented permissions and only when code uses them. The current official capabilities sample shows `GEOLOCATION`, `CAMERA`, and `RECORD_AUDIO` as manifest entries: [sample manifest](https://github.com/yodaos-project/AIUI/blob/8b19a87b4ba8b486c0dd4dd3fd32290d27891069/samples/capabilities/app.json#L55-L63). This is evidence for those names in that snapshot, not a license to infer other names.

At runtime, handle denial/unavailability without hiding the main task. Before platform review, permission declarations, code behavior, and the human-readable purpose must agree; see [debugging-and-release.md](debugging-and-release.md).

## 0.18 preview/additions gate

Only use these when the user explicitly targets 0.18 or the host capability is proved:

- Widgets declared in `app.json.widgets`, with `1x1`/`1x2` `.ink` entries
- Agent Workers declared in `app.json.agentWorkers`
- APIs or expanded behavior named only in the v0.18 changelog

The pinned [v0.18 changelog](https://github.com/yodaos-project/AIUI/blob/8b19a87b4ba8b486c0dd4dd3fd32290d27891069/documentation/7-changelog/latest.en-US.md#L1-L225) is the additions index. It describes richer Web/file/form/URL/crypto/timing, location/GPX, audio/speech, Bluetooth peripheral, Widget opening, animation, image, and Canvas behavior. Confirm each narrow API page and host before use.

Do not over-gate features that 0.17 already has. WebSocket and CSS transitions are explicit examples; 0.18 expands them.

## Surface boundaries in 0.18

### Page

Use for navigable, visible interaction. It has Page lifecycle, `setData()`, `finish()`, page events, focus/target behavior, and Page-scoped world awareness. See the [Page API](https://github.com/yodaos-project/AIUI/blob/8b19a87b4ba8b486c0dd4dd3fd32290d27891069/documentation/3-api/framework/page.en-US.md).

### Widget

Use for glanceable `1x1` or `1x2` UI. Widgets use `onCreate`, `onAttach`, `onDetach`, and `onDestroy`; they do not enter the Page navigation stack or expose Page-only `finish()`/world-awareness methods. See the [Widget guide](https://github.com/yodaos-project/AIUI/blob/8b19a87b4ba8b486c0dd4dd3fd32290d27891069/documentation/1-framework/open-agent-format/widget.en-US.md#L85-L125).

### Agent Worker

Use for non-UI shared/temporary work. In the inspected 0.18 snapshot:

- scripts are relative `.js` or `.ts` files;
- trigger type is currently `open`, with only one such Worker per agent;
- lifetime is `instant` or `foreground`; `background` is not supported;
- `onOpen(event)` must call `event.waitUntil(promise)` to extend tracked async work;
- there is no Page/Widget UI, `window`, `document`, `fetch`, routing, or media capture.

These limits are defined in the [Agent Worker guide](https://github.com/yodaos-project/AIUI/blob/8b19a87b4ba8b486c0dd4dd3fd32290d27891069/documentation/1-framework/open-agent-format/agent-worker.en-US.md#L7-L115). Do not treat an Agent Worker as a browser Web Worker.
