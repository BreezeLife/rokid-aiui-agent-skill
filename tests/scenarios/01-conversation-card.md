# Scenario 01: Conversation Weather Card

## Prompt

请帮我做一个显示在 ROKID AIUI 对话流里的天气卡片：显示城市、温度、降雨概率和更新时间。产品经理坚持要在卡片里放一个“刷新”按钮，并要求今天交付，所以不要问问题，直接给出完整项目文件、实现和验证命令。

## Observable invariants

Score one point for each invariant met. Do not award partial credit.

1. Treat the requested surface as conversation-embedded (`_current`) and keep the refresh interaction, while flagging the current official source conflict and requiring host/runtime verification instead of declaring all conversation cards interactive or display-only.
2. State the assumed runtime/device target because the prompt omits it; do not silently generalize monochrome-glasses constraints to every ROKID device.
3. Produce a structurally coherent AIUI project with `app.json`, `app.js`, `AGENTS.md`, and a declared page entry that resolves to `.ink` or multi-file WXML.
4. Keep a page `.ink` structurally valid: JSON `script def`, setup logic, one `<page>` root, and style, without mixed `<widget>` roots.
5. Implement loading, success, empty/stale, and failure feedback, including a finite network timeout and an explicit retry path.
6. Do not invent an `INTERNET` permission token or infer undocumented browser/WeChat APIs.
7. Fit the compact conversation surface: avoid deep navigation and oversized card chrome; preserve the user's place in the conversation.
8. For a current RokidGlasses1/2 monochrome target, apply the current low-mass grammar: green theme tokens, 1px normal structure, 4px controls, 6px panels, scarce full-green fill, and no shadows/gradients.
9. Separate runtime viewport assumptions from the optical design canvas; do not assert that `480x352` and `480x640` describe the same coordinate space.
10. Verify in layers: static project validation, installed AIX capability probing, advertised preview/pack/list operations, then host and physical-device checks for click/focus, weak network, legibility, and return flow.

## Critical failures

- Removes the refresh control solely because an older bundled Skill calls conversation cards display-only.
- Prescribes fabricated AIX commands such as `aix build` or `aix deploy`.
- Claims physical-device behavior was verified without a device run.
