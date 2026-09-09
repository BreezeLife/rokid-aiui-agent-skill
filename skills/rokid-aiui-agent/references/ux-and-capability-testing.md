# Mandatory AIUI UX and capability testing

Read this for every AIUI project creation, implementation, code change, or review. The output is a project-specific UX matrix and a per-capability matrix, not a reference to a generic checklist. Keep the record beside the Studio import root or in the delivery report unless the project already defines a verification location; do not add unrelated test evidence to the import root merely to satisfy this process.

Use [interaction-and-design.md](interaction-and-design.md) for the design rules, [runtime-capabilities.md](runtime-capabilities.md) for exact API support, and [debugging-and-release.md](debugging-and-release.md) for release flow. The selected-version official documentation and runnable samples remain authoritative.

## Authority and version boundary

The default stable source remains AIUI [`v0.17.0`](https://github.com/yodaos-project/AIUI/tree/88e70bb0382525c1a93ef077c2401dcc31a273ce). The current official `aiui-dev` [UX checklist](https://github.com/yodaos-project/AIUI/blob/63bb5f5efa2f0c11a2defca35bc00777150f43d2/skills/aiui-dev/references/checklist.md#L47-L57), [API/capability checks](https://github.com/yodaos-project/AIUI/blob/63bb5f5efa2f0c11a2defca35bc00777150f43d2/skills/aiui-dev/references/checklist.md#L59-L83), [executable validation](https://github.com/yodaos-project/AIUI/blob/63bb5f5efa2f0c11a2defca35bc00777150f43d2/skills/aiui-dev/references/checklist.md#L84-L100), and [evidence report rules](https://github.com/yodaos-project/AIUI/blob/63bb5f5efa2f0c11a2defca35bc00777150f43d2/skills/aiui-dev/references/checklist.md#L102-L110) support this mandatory test protocol.

That current checklist belongs to commit `63bb5f5efa2f0c11a2defca35bc00777150f43d2`, whose changelog identifies [v0.18.0](https://github.com/yodaos-project/AIUI/blob/63bb5f5efa2f0c11a2defca35bc00777150f43d2/documentation/7-changelog/latest.md#L1-L7). Reuse its general testing discipline, not its feature availability, for a 0.17 target. Confirm each component/API/event against the selected version; keep Widgets, Agent Workers, and other newer features gated.

## Result contract

- `PASS` means the required evidence layer was executed and its result was captured with a command, log, screenshot, recording, or reproducible artifact.
- `FAIL` means executed evidence contradicts the acceptance criterion; record the defect and retest after correction.
- `BLOCKED` means the applicable check cannot yet be executed or proved. `Not tested`, `unverified`, and missing evidence are `BLOCKED`, never pass.
- `N/A` requires a concrete scope reason, such as a surface or capability that the shipped project does not support. Lack of time, credentials, or hardware is `BLOCKED`.

For a release critical path, any applicable `FAIL` or `BLOCKED` means the work must not be described as complete or release-ready. A narrower statement such as “local deterministic checks pass; device UX is blocked” is valid.

## Evidence ladder

| Layer | Can establish | Cannot establish |
| --- | --- | --- |
| SOURCE | Target-version support from an exact official page and runnable sample | Project behavior or host availability |
| STATIC | Manifest, routes, declarations, bindings, source invariants, and import-root structure | Runtime semantics or usable UX |
| LOGIC | Deterministic state, boundaries, failures, fallback, and cleanup in executed code | Host event delivery, permissions, or optics |
| AIX | Advertised pack/list behavior and basic browser Ink rendering/events | Studio compatibility or physical hardware behavior |
| STUDIO | Authenticated import and host-like Web simulation on the selected runtime | Physical optics, sensors, keys, thermals, or endurance |
| DEVICE | Behavior on the named glasses/runtime in real visual and input conditions | Platform review approval or future compatibility |

An AIX/browser preview must not be used as proof of physical focus, keys, voice, gesture, permission, optics, or performance. Likewise, source or static evidence cannot replace execution.

## Required UX matrix

Copy these rows into the project audit and split a row when surfaces, states, or inputs need different results. Fill every cell; do not collapse applicable rows into prose.

| ID | Surface/state | Risk | Test | Evidence layer | Result | Evidence |
| --- | --- | --- | --- | --- | --- | --- |
| UX-TARGET | Every supported `_current`, `_blank`, and transition | Wrong density, host behavior, or business-state drift | Exercise each declared surface and target change with the same input | LOGIC, STUDIO, DEVICE as applicable | Record one allowed result | Attach target-specific output |
| UX-STATE | Every loading, empty, ready, active, success, error, denied, and recovery state used by the product | Hidden, misleading, or dead-end states | Reach each state and every legal and illegal transition | LOGIC plus rendered evidence | Record one allowed result | Attach state trace and render |
| UX-TEXT | Empty, minimum, maximum, long Chinese/English, mixed Unicode, and malformed input | Clipping, unreadable wrapping, unsafe interpolation, or hidden actions | Exercise boundary values, overflow, scrolling, and fixed-action visibility | LOGIC, AIX, STUDIO, DEVICE | Record one allowed result | Attach cases and captures |
| UX-FOCUS | Host and every actionable element | Invisible focus, focus trap, or unfocused activation | Exercise host focus/blur, element focus/blur, order, activation, and return | STATIC, STUDIO, DEVICE | Record one allowed result | Attach focus trace or video |
| UX-INPUT | Every claimed tap, Enter, Back, directional, touchpad, voice, and gesture path | Double action, stolen host default, unsupported event, or no fallback | Exercise owned and ignored inputs, default prevention, and a non-sensor fallback | LOGIC, STUDIO, DEVICE | Record one allowed result | Attach event/action trace |
| UX-RECOVERY | Offline, timeout, denied, unavailable, invalid, and retry states that apply | Silent failure or endless retry | Force each failure, verify useful feedback, bounded retry, back/finish, and recovery | LOGIC, STUDIO, DEVICE | Record one allowed result | Attach failure/recovery trace |
| UX-LIFECYCLE | First open, hide/show, unload/reopen, and repeated attach/open where applicable | Stale state, duplicate work, leaked timers/listeners, or wrong resume | Exercise lifecycle ordering, state reconciliation, and cleanup | LOGIC, STUDIO, DEVICE | Record one allowed result | Attach lifecycle trace |
| UX-VISUAL | Every meaningful state and focus level | Meaning conveyed only by green luminance, weak hierarchy, excess fill, or clutter | Check labels/shapes plus luminance, typography, spacing, line weight, fill, and information density | STATIC, AIX, DEVICE | Record one allowed result | Attach annotated captures |
| UX-ENVIRONMENT | Runtime viewport and bright, dark, and cluttered real scenes | Desktop-readable UI fails in the optical field | Inspect the actual viewport, comfortable region, backgrounds, posture, and motion | AIX for framing, DEVICE for optics | Record one allowed result | Attach viewport and glasses evidence |
| UX-MOTION | Transitions, animation, repeated navigation, and continuous use | Distraction, unsupported motion, dropped frames, heat, or instability | Exercise reduced/absent motion fallback, overlap, cold start, and endurance as applicable | LOGIC, STUDIO, DEVICE | Record one allowed result | Attach timing/performance evidence |

The official stable green design defines the [480 × 352 canvas and monochrome semantic boundary](https://github.com/yodaos-project/AIUI/blob/88e70bb0382525c1a93ef077c2401dcc31a273ce/design/monochrome/design-system-green.md#L1-L23), [layout and structural rules](https://github.com/yodaos-project/AIUI/blob/88e70bb0382525c1a93ef077c2401dcc31a273ce/design/monochrome/design-system-green.md#L407-L455), and a [visual acceptance checklist](https://github.com/yodaos-project/AIUI/blob/88e70bb0382525c1a93ef077c2401dcc31a273ce/design/monochrome/design-system-green.md#L751-L766). The optical-region distinction and focus model are detailed in [interaction-and-design.md](interaction-and-design.md). The official stable flow separates [Web simulation from real-device debugging](https://github.com/yodaos-project/AIUI/blob/88e70bb0382525c1a93ef077c2401dcc31a273ce/documentation/0-guide/quickstart/quickstart.md#L76-L90); use physical results as the final UX authority.

## Required capability matrix

Create one row for every used non-trivial component, API, host event, device capability, or version-gated feature. This includes routing, network/streams, storage, timers, camera/media/recording, speech, sensors/Bluetooth, Canvas, Page world awareness, and targeted Widgets or Agent Workers. Remove a row only when the shipped code and product claim remove the capability.

| Capability | Version/device/surface | API/component/event | Declaration/permission | Official source/sample | Positive path | Negative/fallback path | Lifecycle/cleanup | Evidence layer | Result | Evidence |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| One row per used capability | Name exact target | Name exact symbol and event | Record exact manifest entry or none required | Link version-matched official docs and runnable sample | State expected success case | Test applicable denial, revocation, unavailable, timeout, malformed response, and fallback | Test start, hide/show, unload, cancellation, and release as applicable | Name every required layer | Record one allowed result | Attach source and executed evidence |

For each row, first confirm the capability in version-matched official documentation and a runnable official sample or implementation when available. If the signature, permission, event delivery, or host support is unresolved, keep the row `BLOCKED`; do not infer it from browsers, WeChat, types, or a newer AIUI release.

Test the positive path and every relevant negative path: permission denial and later revocation, capability unavailable, offline/timeout, malformed or partial responses, repeated callbacks, cancellation, and fallback. Verify hide/show reconciliation and unload cleanup for timers, listeners, streams, media, sensors, network work, Workers, and other retained resources.

## Execution order

1. Record the source revision, import root, target AIUI version, glasses/host, supported surfaces, business states, inputs, and claimed capabilities.
2. Create both matrices before sign-off. Mark unexecuted applicable cells `BLOCKED` rather than leaving them blank.
3. Run strict project validation and deterministic tests against the exact delivered source. Execute the real Page/Widget/Worker logic where practical; a copied model test is weaker evidence.
4. Probe the installed AIX help, then run only advertised pack/list/preview checks. Inspect every supported surface and state with boundary text.
5. Run authenticated Studio import/simulation and then physical-glasses checks for the cells that require those layers.
6. Return both completed matrices, exact commands/artifacts, unresolved gates, and a scoped release decision. Retest corrected failures; never convert a missing environment into `PASS`.
