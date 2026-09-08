# Focus Timer Agent Design

## Product contract

Build a Japanese-language focus timer for Rokid Glasses under `examples/focus-timer-agent/`. The import root targets stable AIUI 0.17.0 and contains one Page, with no Widget or Agent Worker. Conversation input is `durationSeconds`, an integer from 1 through 3600, plus optional `label`, a string of at most 48 Unicode code points.

The Agent prompt extracts those fields without inventing background execution, alarms, notifications, or persistence. Missing or malformed duration and malformed or oversized labels produce `error`; valid input produces `idle` with the complete configured duration.

## Architecture

The project follows `examples/next-step-agent/`: `AGENTS.md`, `app.json`, `app.js`, and one `pages/index/index.ink`. The Page owns a five-state machine: `idle`, `running`, `paused`, `finished`, and `error`.

`running` stores an absolute `deadlineMs`. Every display refresh computes `remainingMs = max(0, deadlineMs - Date.now())`; `setInterval` only requests refreshes. Pausing captures the current real remaining milliseconds. Continuing creates a new deadline from that value. Restarting immediately begins a full new interval, while resetting preserves the input configuration and returns to full-duration `idle`.

Legal state actions are:

| State | Primary action | Additional `_blank` actions |
| --- | --- | --- |
| `idle` | Start | Reset |
| `running` | Pause | Restart, Reset |
| `paused` | Continue | Restart, Reset |
| `finished` | Restart | Reset |
| `error` | Reset | None |

Invalid or repeated actions are no-ops. Resetting an invalid input keeps the Page in `error`, because no valid timer configuration exists.

## Lifecycle

`onHide` clears the refresh interval without changing timer truth. `onShow` recalculates from `deadlineMs` and restarts refresh only if still running. `onUnload` always clears the interval. A completion detected during refresh or after showing the Page transitions once to `finished` and leaves no active interval.

## Surfaces and visual design

The same business state supports both host targets. `_current` shows the task label (or a Japanese default), remaining time, and only the primary action. `_blank` adds the explicit state, elapsed progress, configured duration, and all actions valid for the current state.

The Page uses a black background and one green luminance family, 1px structural lines, 4px button radii, a 6px outer group radius, no ambient animation, and text labels in addition to luminance. Every button binds `bindtap`, `bindfocus`, and `bindblur`; focus is tracked per action so hidden or unrelated controls cannot inherit focus styling.

## Test and evidence contract

Python `unittest` contract tests inspect the import tree, schema, Page-only manifest, Japanese text, target-specific layouts, and bindings. A Node harness executes the real `<script setup>` with fake `Date.now`, `setInterval`, and `clearInterval`, advancing time synchronously to cover boundaries, legal and invalid transitions, duplicate clicks, pause/continue, completion, hide/show recalculation, and unload cleanup without waiting.

Release evidence consists of the full repository unit suite, strict validator with `--target-version 0.17.0`, the installed locked AIX CLI help output, static preview generation, pack, and list of the exact archive. Authenticated AIUI Studio import and physical Rokid Glasses verification remain manual gates.

## Import coordinates

```text
Repository: https://github.com/BreezeLife/rokid-aiui-agent-skill
Ref: main
Directory: examples/focus-timer-agent
```
