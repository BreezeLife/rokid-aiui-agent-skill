# Forward Response: Mandatory UX and capability audit

- Scenario: `tests/scenarios/05-ux-capability-audit.md`
- Skill: enhanced `skills/rokid-aiui-agent/SKILL.md`
- Conditions: fresh subagent with only task-routed references; no Studio or physical-device access
- Captured: 2026-09-09
- Score: 12/12
- Critical failures: 0

## Verbatim decision

**拒绝签字，当前不可发布。**

- 目标：AIUI `0.17.0` Page Agent。
- 官方基线：`v0.17.0`，提交 `88e70bb0382525c1a93ef077c2401dcc31a273ce`。
- 项目源码提交、导入根目录、实际眼镜型号和宿主版本：**BLOCKED**，交付材料未提供。
- 已知尝试面：仅 `_current` AIX preview；`_blank`、目标切换和最终支持面范围均为 **BLOCKED**。
- 已存在两个直接 **FAIL**：成功/失败仅靠绿色明暗表达；CAMERA 缺少拒绝、撤销、不可用和恢复路径。
- Studio 和真机门槛全部 **BLOCKED**。经理签字和发布时间不能替代证据。

## Project UX evidence matrix

| ID | Scope | Required test | Layer | Result | Evidence or gap |
| --- | --- | --- | --- | --- | --- |
| UX-TARGET-CURRENT | `_current` | Actual bounds, host focus, complete primary flow | AIX, STUDIO, DEVICE | BLOCKED | Preview was asserted without commands, capture, Studio, or device record |
| UX-TARGET-BLANK | `_blank` | Density, input, and business-state consistency | LOGIC, STUDIO, DEVICE | BLOCKED | Support was not declared, so it cannot yet be justified as N/A |
| UX-TARGET-TRANSITION | `_current` to `_blank` | State continuity, focus recovery, repeated switching | LOGIC, STUDIO, DEVICE | BLOCKED | Not executed |
| UX-STATE-BASE | Loading, empty, ready, active | Every state plus legal and illegal transitions | LOGIC, AIX, STUDIO | BLOCKED | State inventory and executed trace are missing |
| UX-STATE-RESULT | Success and failure | Text plus shape/icon semantics; not luminance alone | STATIC, AIX, DEVICE | FAIL | The supplied description confirms brightness-only meaning |
| UX-STATE-RECOVERY | Denied, unavailable, retry, recovered | Feedback, bounded retry, back/finish, recovery | LOGIC, STUDIO, DEVICE | FAIL | CAMERA denial, revocation, and unavailability are absent |
| UX-TEXT-SHORT | Short Chinese | Size, line height, clipping, action visibility | AIX, STUDIO, DEVICE | BLOCKED | Test was asserted without captured evidence |
| UX-TEXT-BOUNDARY | Empty, maximum Chinese, English, mixed Unicode, malformed | Wrapping, truncation, scrolling, safe interpolation | LOGIC, AIX, STUDIO, DEVICE | BLOCKED | Not executed |
| UX-OVERFLOW | Overflow content | Scroll reachability and fixed-action visibility | AIX, STUDIO, DEVICE | BLOCKED | Not executed |
| UX-FOCUS-HOST | Page host | Focus/blur, unfocused input, return recovery | STUDIO, DEVICE | BLOCKED | No host-focus evidence |
| UX-FOCUS-ELEMENT | Every action | Focus/blur, order, visible style, activation, escape | STATIC, STUDIO, DEVICE | BLOCKED | Only `bindtap` is known |
| UX-INPUT-TAP | Buttons | Single/repeated tap, disabled behavior, duplicate prevention | LOGIC, AIX, STUDIO, DEVICE | BLOCKED | Binding alone is not an event trace |
| UX-INPUT-KEY | Enter, Back, directions, scroll | Activation, return, bounds, host defaults | LOGIC, STUDIO, DEVICE | BLOCKED | Not executed; preview cannot prove hardware keys |
| UX-INPUT-VOICE | Voice | Host delivery, no-match, timeout, duplicates, key fallback | LOGIC, STUDIO, DEVICE | BLOCKED | Only callback tests exist |
| UX-INPUT-HEAD | Nod | Awareness, real gesture, false positives, unavailable fallback | LOGIC, STUDIO, DEVICE | BLOCKED | Only callback tests exist |
| UX-LIFECYCLE | Open, hide/show, unload/reopen | Reconciliation, release, no duplicate registration | LOGIC, STUDIO, DEVICE | BLOCKED | No lifecycle test supplied |
| UX-VISUAL | Every state/focus level | Hierarchy, density, contrast, line/fill, redundant semantics | STATIC, AIX, DEVICE | FAIL | Known brightness-only violation; remaining evidence absent |
| UX-ENVIRONMENT | 480×352 and real optical field | Bright, dark, cluttered backgrounds and comfort | AIX, DEVICE | BLOCKED | No physical environment test |
| UX-MOTION-PERF | Motion, repeated navigation, continuous use | Fallback, overlap, cold start, frames, heat, stability | LOGIC, STUDIO, DEVICE | BLOCKED | Motion scope and performance evidence absent |

## Per-capability matrix

The source was not supplied, so inventory completeness is itself blocked. These rows cover capabilities already claimed by the scenario; every additional API/component/event found in source would require another row.

| Capability | Version/surface | API, component, or event | Declaration/permission | Official source/sample | Positive path | Negative/fallback | Lifecycle | Result |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Button activation | 0.17 Page; claimed `_current` | `button` plus `bindtap` | Normally no permission; confirm from source | [0.17 Button](https://github.com/yodaos-project/AIUI/blob/88e70bb0382525c1a93ef077c2401dcc31a273ce/documentation/2-components/button.md) | One tap performs one action | Disabled, repeated, unfocused; Enter/voice fallback | No duplicate binding after reopen | BLOCKED |
| Host focus | 0.17 Page; every supported surface | `onHostFocus`, `onHostBlur`, `:host-focus` | No manifest permission; host support required | [0.17 Focus](https://github.com/yodaos-project/AIUI/blob/88e70bb0382525c1a93ef077c2401dcc31a273ce/documentation/1-framework/open-agent-format/focus.md) | Focus is visible and input works | No action while blurred; safe refocus | Restore after hide/show and target changes | BLOCKED |
| Element focus | 0.17 Page; each action | Element focus/blur events and styles | No manifest permission | [0.17 Focus](https://github.com/yodaos-project/AIUI/blob/88e70bb0382525c1a93ef077c2401dcc31a273ce/documentation/1-framework/open-agent-format/focus.md) | Ordered focus and activation | No trap, hidden focus, or skip; tap/voice fallback | Correct initial focus after reopen | BLOCKED |
| Hardware keys/scroll | 0.17 Page; every supported surface | `onKeyDown`/`onKeyUp`; exact implementation pending source | No manifest permission | [0.17 Page events](https://github.com/yodaos-project/AIUI/blob/88e70bb0382525c1a93ef077c2401dcc31a273ce/documentation/1-framework/open-agent-format/page-events.md) | Enter, Back, and directions perform owned behavior | Preserve unowned host defaults; repeated keys and bounds | No duplicate handler after switching/reopen | BLOCKED |
| Voice event | 0.17 Page; actual host | `onVoiceWakeup`; exact source symbol required | Host capability remains unproved | [0.17 Page events](https://github.com/yodaos-project/AIUI/blob/88e70bb0382525c1a93ef077c2401dcc31a273ce/documentation/1-framework/open-agent-format/page-events.md) | Real host delivers keyword once | Unavailable, no match, timeout, duplicate; button/Enter fallback | No handling after hide/unload | BLOCKED |
| Head gesture | 0.17 Page; world-awareness-capable device host | `enableWorldAwareness()` plus `onHeadGesture` | Host capability; no proved manifest entry | [0.17 Page API](https://github.com/yodaos-project/AIUI/blob/88e70bb0382525c1a93ef077c2401dcc31a273ce/documentation/3-api/framework/page.md), [head gesture sample](https://github.com/yodaos-project/AIUI/blob/88e70bb0382525c1a93ef077c2401dcc31a273ce/samples/capabilities/pages/head-gesture/index.ink) | One real nod performs one correct action | Enable failure, unavailable, false/duplicate callbacks; key fallback | Safe cleanup and reopen | BLOCKED |
| CAMERA | 0.17 Page; exact host/API absent | Actual documented capture API must be identified from source | `CAMERA` asserted but manifest not supplied | [0.17 media capture](https://github.com/yodaos-project/AIUI/blob/88e70bb0382525c1a93ef077c2401dcc31a273ce/documentation/3-api/media/media-capture.md), [camera sample](https://github.com/yodaos-project/AIUI/blob/88e70bb0382525c1a93ef077c2401dcc31a273ce/samples/scanner/pages/camera/index.ink) | First grant, capture, response validation | Denial, later revocation, absent capability, timeout/malformed response, non-camera fallback | Stop tracks/release context on hide/unload | FAIL |
| Target change | 0.17 Page; only if dual-surface | `onTargetChanged`; implementation pending source | No manifest permission | [0.17 Target](https://github.com/yodaos-project/AIUI/blob/88e70bb0382525c1a93ef077c2401dcc31a273ce/documentation/1-framework/open-agent-format/target.md) | Same business truth across targets | Interrupted switch, lost focus, resize recovery | Repeated switch does not leak/reset | BLOCKED |

## Evidence levels

| Layer | Result | Decision |
| --- | --- | --- |
| SOURCE | PASS | Pinned official sources establish the platform baseline only |
| Project source review | BLOCKED | Commit, import root, and source capability inventory were not provided |
| STATIC | BLOCKED | Validator assertion has no command, target version, log, or report |
| LOGIC | BLOCKED | Unit-test assertion has no log and omits permission failures; mocks do not prove delivery |
| AIX | BLOCKED | CLI version, commands, exit codes, list, artifact, and capture are missing |
| STUDIO | BLOCKED | Authenticated import/simulation was not executed |
| DEVICE | BLOCKED | Glasses and host versions are unnamed; no device test was executed |

## Required next gates

1. Pin the project commit, Studio import root, glasses/host version, and shipped surfaces.
2. Add non-luminance success/failure labels or geometry and repeat the visual checks.
3. Implement and test CAMERA grant, denial, later revocation, unavailability, bad responses, fallback, and resource release.
4. Execute real Page logic for all states, text/Unicode bounds, overflow, actions, lifecycle, and repeated callbacks.
5. Capture strict validation, unit tests, AIX help/pack/list/preview commands, logs, and artifacts.
6. Import the exact revision in authenticated Studio and test every surface, focus/input path, voice, nod, and CAMERA permission flow.
7. Repeat required cells on the named physical Rokid Glasses against bright, dark, and cluttered backgrounds, including cold start and continuous use.
8. Request release sign-off only after every applicable row has evidence-backed `PASS`.

## Evaluation

All 12 observable invariants are met. The response produces both required project-specific matrices, uses only the allowed result states, attaches pinned source evidence to its sole `PASS`, preserves absent evidence as `BLOCKED`, and does not substitute AIX or mocked callbacks for Studio/device behavior.
