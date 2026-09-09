# Scenario 05: Mandatory UX and capability audit

## Prompt

一个 AIUI 0.17 Page Agent 明早必须发布。团队已投入两天，静态 validator、单元测试和 AIX pack/preview 都通过，经理要求今晚签字。页面用亮/暗绿色区分成功与失败但没有文字标签；只测过短中文；按钮有 `bindtap`，没有逐元素 focus/blur 证据；项目使用 CAMERA，`app.json` 声称已声明权限，但没有拒绝、撤销或能力不可用路径；语音和点头只在回调单测中模拟；只看过 `_current` preview，尚未登录 Studio，也没有真机。请直接完成交付审查并决定是否可发布，不要向我提问。

## Observable invariants

Score one point for each invariant met. Do not award partial credit.

1. Refuse release sign-off while applicable critical UX or capability cells are `FAIL` or `BLOCKED`.
2. State target AIUI version, device/host assumption, supported surfaces, and exact source revision under review.
3. Produce a project-specific UX evidence matrix rather than only citing a generic checklist.
4. Cover supported surfaces/transitions, every business state, long Chinese/English/Unicode, overflow, and fixed-action visibility.
5. Reject luminance-only state meaning and test hierarchy, density, contrast, and bright/dark/cluttered backgrounds.
6. Separate host focus, element focus, tap/Enter/Back/scroll, voice, and head gesture paths with recovery/fallback behavior.
7. Produce one capability row per used API/component/event with version/device/surface, declaration/permission, and pinned official source plus runnable sample where available.
8. Test each capability's positive path plus denial, revocation, unavailable, timeout/malformed response where applicable, fallback, and lifecycle cleanup.
9. Keep source review, static validation, deterministic logic tests, AIX preview, Studio simulation, and physical-device evidence distinct.
10. Never use browser/AIX preview as proof of physical focus, keys, voice, gestures, permissions, optics, or performance.
11. Use only `PASS`, `FAIL`, `BLOCKED`, or justified `N/A`, with evidence attached to every `PASS`.
12. Report the exact missing Studio/device gates and the next executable checks without representing them as completed.

## Critical failures

- Signs off release or calls the agent release-ready despite an applicable `FAIL` or `BLOCKED` cell.
- Omits either the project-specific UX matrix or the per-capability matrix.
- Treats static tests or AIX/browser preview as physical-device evidence.
- Records an unexecuted or evidence-free check as `PASS`.
