# Next Step Agent Design

## Context

The repository now needs a product-shaped AIUI project created with the published `rokid-aiui-agent` Skill. The example must prove the Skill can produce more than a structural fixture while remaining safe to import, preview, and package without credentials or device permissions.

The user previously authorized autonomous continuation without clarification stops. This design therefore selects the smallest useful personal Agent that exercises the stable AIUI workflow and keeps Studio and physical-device checks as explicit external gates.

## Approaches considered

### 1. Next Step Agent (selected)

Turn one user goal into one concrete action and let the user move it through ready, active, and done states. This creates a complete Agent-to-Page data flow and a meaningful local interaction without network, storage, timers, sensors, or version-gated features.

### 2. Pocket translation card

Show source text, a translation, and a useful phrase. This fits an eyewear context, but it would require a confirmed model or network capability and a product-specific failure strategy. Those dependencies would weaken a stable offline reference project.

### 3. Field checklist

Guide a user through several inspection items. This has strong hands-free potential, but a reliable first version would need more complex list focus, hardware-key behavior, persistence decisions, and physical-device evidence.

## Product contract

The product name is **Next Step Agent / 下一步**. When a user states a goal, the Agent reduces it to one action that can begin immediately. The Page displays the original goal, the next action, and its current state.

Example:

- User goal: “我今天要把发布说明写完。”
- Agent goal value: “完成今天的发布说明”
- Agent next-step value: “先列出这次发布最重要的三个变化”

The Agent must keep the action specific, startable now, and small enough to complete in one sitting. It must not promise reminders, persistence, background execution, or completion outside the current Page.

## Importable architecture

`examples/next-step-agent/` is the AIUI Studio import root:

```text
examples/next-step-agent/
├── AGENTS.md
├── app.json
├── app.js
└── pages/
    └── index/
        └── index.ink
```

The project targets stable AIUI `0.17.0`, declares only `pages/index/index`, and uses one Page `.ink` file. It has no Widgets, Agent Workers, network calls, storage, timers, permissions, or external assets.

For GitHub import, the coordinates are:

```text
Repository: https://github.com/BreezeLife/rokid-aiui-agent-skill
Ref: main
AIUI project directory: examples/next-step-agent
```

## Agent and Page input contract

`AGENTS.md` contains the documented metadata, system-prompt, capabilities, configuration, and dependency sections. It tells the Agent to produce exactly two Page inputs:

- `goal`: a non-empty string of at most 120 characters that preserves the user's intended outcome;
- `nextStep`: a non-empty string of at most 48 characters containing one concrete action.

The Page `<script def>` declares a description and the stable conversation-tool envelope `schema.data`. The `type`, `properties`, and `required` members live inside `schema.data`, not directly inside `schema`. Both fields are strings with `minLength: 1`, their `maxLength` values match the limits above, and both are required. These limits apply to the raw input strings and count Unicode code points, matching JSON Schema string-length semantics rather than JavaScript UTF-16 code units. The Page still handles missing, malformed, or oversized inputs because preview, manual navigation, or host failures can bypass an ideal model response.

## State model

The Page has five explicit states:

| State | Meaning | Primary action |
| --- | --- | --- |
| `empty` | `goal` or `nextStep` is missing or blank | None; ask the user to return to the conversation |
| `error` | A supplied field has the wrong type or the input is not an object | None; ask the user to generate the action again |
| `ready` | A valid action is ready to start | `startTask()` |
| `active` | The user has started the action | `completeTask()` |
| `done` | The user marked the action complete | `restartTask()` |

The only valid transitions are:

```text
ready -> active -> done -> ready
```

`onLoad(query)` normalizes the input once in this order:

1. A missing or null input produces `empty`.
2. Any other non-object input produces `error`.
3. Any provided `goal` or `nextStep` value with a non-string type produces `error`.
4. Before trimming, a raw `goal` longer than 120 Unicode code points or raw `nextStep` longer than 48 Unicode code points produces `error`.
5. The strings are trimmed after the raw-length check.
6. A missing field or a string that becomes empty after `trim()` produces `empty`.
7. Two non-empty trimmed strings whose raw inputs were within the limits produce `ready`.

The Page stores and displays trimmed valid strings. Raw oversized input is rejected rather than trimmed or truncated into a valid saved value; the complete generic `error` view uses empty stored fields. Every transition updates the displayed status through `this.setData()` and preserves valid `goal` and `nextStep` values.

## Surface and interaction design

The same Page supports conversation-embedded (`_current`) and full-screen (`_blank`) hosting. Target affects density, not the task state:

- `_current` shows the state, the next action, and the single primary action. It hides the original goal and supporting explanation.
- `_blank` adds the original goal, supporting explanation, and completion guidance while retaining the same state and primary action.
- CSS `@media (target: _current)` and `@media (target: _blank)` control those differences. Page logic does not branch on either target or `onTargetChanged`, so a host transition cannot reset progress.

The body is an official AIUI 0.17 [`scroll-view`](https://github.com/yodaos-project/AIUI/blob/88e70bb0382525c1a93ef077c2401dcc31a273ce/documentation/2-components/scroll-view.en-US.md) with vertical scrolling enabled. In `_blank`, this keeps the complete valid goal, next step, and guidance reachable instead of silently clipping text. The action region remains outside that scrolling container and cannot shrink.

Three `button` elements use the documented `bindtap` event and are shown according to Page state. The Page does not intercept `Enter`, arrow keys, or `Backspace`. Exact focus, scrolling, navigation, and activation behavior remains subject to host and physical-device verification.

Each button also uses the documented element `bindfocus` and `bindblur` events. Shared `actionFocused` state adds a 2px strong-focus outline and a green fill no stronger than 12%. A valid task-state transition clears that flag before the next hidden button becomes visible, preventing stale visual focus without taking over key events or promising automatic focus migration.

## Visual direction

The Page uses the current monochrome-green low-mass direction as design guidance without claiming it is a new 0.17 runtime capability:

- transparent or dark-black floor with one green luminance family;
- open hierarchy instead of nested cards;
- 1px structural lines, 4px control radii, and 6px group radii;
- normal green fills no stronger than 12%;
- state communicated with words as well as luminance;
- no ambient or looping animation.

The primary action remains compact and visually distinct. The scrolling content region can shrink while the action region cannot, so long valid copy cannot push the active control outside the Page. Base and `_blank` styles do not cap or hide the goal, next step, or guidance; users can scroll to the complete content. `_current` retains its compact contract by hiding `expanded-only` details and limiting only the primary text to 46px with hidden overflow. Physical optical comfort remains a device-test decision.

## Error handling and boundaries

- `empty` is a normal missing-content state and does not expose a technical error.
- `error` is reserved for malformed types and tells the user to return to the conversation.
- Oversized raw input also produces the complete `error` view before trimming; it is not normalized into a valid saved value.
- The UI never displays stack traces or raw host objects.
- The project requests no permissions and performs no external writes.
- No claim of Studio import, host focus behavior, hardware navigation, optical quality, or physical-device readiness is made without that layer's evidence.

## Skill correction discovered during design

The source audit found that `references/ink-authoring.md` currently shows a Page input schema directly under `schema`, while the pinned AIUI 0.17 quickstart and runnable sample use `schema.data`. The implementation must first add a failing regression test for this envelope, then correct the reference example. The new Agent must use `schema.data`.

## Verification

Automated verification must prove:

1. the exact import root contains all required files and resolves its declared route;
2. the Page definition JSON places `type`, `properties`, and `required` inside `schema.data`, rejects the old direct `schema.properties` shape, and requires length-bounded `goal` and `nextStep` strings;
3. every `bindtap`, `bindfocus`, and `bindblur` handler exists in `<script setup>`;
4. the real Page script produces `empty`, `error`, `ready`, `active`, and `done` as specified when executed in a small Node harness, including exact raw boundaries, padded-over-limit values, and oversized Unicode-code-point inputs;
5. focus/blur handlers update shared state through `setData()`, and valid task transitions clear stale focus;
6. both target media queries exist and Page logic does not make target a business-state input;
7. the official vertical `scroll-view`, complete `_blank` text, and a non-shrinking external action region keep both content and the active control accessible;
8. strict `0.17.0` project validation succeeds;
9. the fixed published AIX CLI packages and lists the exact project;
10. AIX produces a non-empty static preview containing the declared Page source, which proves preview artifact completeness rather than visual correctness;
11. the complete repository test and reference-validation suite remains green.

Local visual inspection may verify the generated browser preview. Authenticated AIUI Studio import and physical Rokid Glasses behavior remain manual gates.

## Non-goals

- Multiple tasks, history, prioritization, or project management
- Timers, reminders, calendars, background work, or persistence
- Network services, accounts, cloud synchronization, or external models
- Recording, camera, sensors, head gestures, or custom hardware-key interception
- AIUI 0.18 Widgets or Agent Workers
- Platform upload, review submission, or store publication

## Acceptance criteria

- `examples/next-step-agent/` is a complete editable AIUI source project and the documented Studio import directory.
- Valid Page input supports the full `ready -> active -> done -> ready` loop.
- Missing, malformed, and oversized input render the specified non-crashing states without truncating oversized content into saved state.
- Element focus is visible, focus state clears across legal task transitions, and the action region remains accessible with maximum-length content.
- `_blank` exposes complete valid goal, next-step, and guidance text through vertical scrolling; only `_current` may visually cap the primary text.
- `_current` and `_blank` share business state and differ only in information density.
- Tests demonstrate a RED failure before implementation and pass after the minimal project is added.
- Strict validation, AIX pack/list, static preview generation, and visual browser inspection have recorded evidence.
- README, CI, project memory, task status, and work log describe the exact project and unverified external gates.
