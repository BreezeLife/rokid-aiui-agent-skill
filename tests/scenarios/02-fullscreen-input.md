# Scenario 02: Full-screen Multimodal Input

## Prompt

已有一个 ROKID AIUI 全屏任务列表页。请加上这些交互：遮罩打开时 Backspace 只关闭遮罩；ArrowUp/ArrowDown 移动列表焦点；Enter 执行当前项；说出唤醒词后更新状态；点头确认当前项、摇头取消。为了更快响应，我坚持所有按键都在 onKeyDown 里调用 preventDefault。今天必须上线，不要问问题，直接实现并说明怎样验证。

## Observable invariants

Score one point for each invariant met. Do not award partial credit.

1. Identify the page as a full-screen (`_blank`) Page, not a Widget or conversation-only card.
2. Explicitly reject the blanket `onKeyDown.preventDefault()` requirement: host defaults are defined on `keyup`, so interception belongs in `onKeyUp` only for actions the page replaces.
3. Handle `Backspace` conditionally: when the overlay is visible, prevent the `keyup` default and close only the overlay; otherwise allow host back behavior.
4. Provide one coherent, non-duplicating strategy for ArrowUp/ArrowDown/Enter: custom state changes occur once, and the matching `keyup` default is prevented only when the app replaces it.
5. Keep list focus index bounded, update visible focus/state feedback, and define safe behavior for an empty list.
6. Implement `onVoiceWakeup(event)` using `event.keyword` without assuming every host uses the same wake word.
7. Call Page-only `enableWorldAwareness()` before relying on head gestures, feature-detect it, and handle unavailability.
8. Implement `onHeadGesture(event)` using `event.gesture` for nod/shake and avoid low-level sensor reconstruction when the page-level event suffices.
9. Avoid treating device-specific `GlobalHook`, browser keyboard behavior, or emulator behavior as universal runtime facts.
10. Require layered verification: deterministic state tests, AIX/static checks, supported preview, and physical-device tests covering key down/up, overlay back, focus visibility, voice, nod/shake, cancellation, and unload cleanup.

## Critical failures

- Claims `preventDefault()` in `onKeyDown` suppresses the host's return/scroll/activation defaults.
- Uses head-gesture callbacks without enabling world awareness.
- Claims gesture or hardware-input success based only on a desktop preview.
