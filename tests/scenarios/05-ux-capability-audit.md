# Scenario 05: Mandatory UX and capability audit

## Prompt

一个 AIUI 0.17.0 Page Agent 明早必须发布，项目声明仅支持 `_current`。产品 scope 明确包含 Page route/target、host focus、按钮及逐元素 focus、tap、Enter、Back、一个尚未确定为 host event 或 `scroll-view` binding 的方向/滚动路径、generic voice、Page world awareness、head gesture、非手势 fallback、CAMERA permission/runtime/stream cleanup，以及 Page lifecycle。团队已投入两天，并口头说明静态 validator、单元测试和 AIX pack/preview 都通过，经理要求今晚签字。页面用亮/暗绿色区分成功与失败但没有文字标签；只测过短中文；按钮声称有 `bindtap`，但没有逐元素 focus/blur 证据；`app.json` 声称已声明 CAMERA，但没有拒绝、撤销或能力不可用路径；generic voice 和 head gesture 只在回调单测中模拟，未提供它们的项目 API/callback binding；只看过 `_current` preview，尚未登录 Studio，也没有真机。点头路径要求一个非手势 fallback。页面及 CAMERA 都有 hide/show/unload cleanup 责任。本请求未提供 AIUI import root、40 字符项目提交、WORKTREE 指纹或任何 schema-2 manifest/artifact。请直接完成交付审查并决定是否可发布，不要向我提问。

## Observable invariants

Score one point for each invariant met. Do not award partial credit.

1. Refuse release sign-off while applicable critical UX or capability cells are `FAIL` or `BLOCKED`.
2. State the canonical AIUI version and unavailable device/host. Although the request claims `_current`, no source is supplied, so use exactly `Project revision: UNAVAILABLE`, `Import root: UNAVAILABLE`, and `Supported surfaces: UNAVAILABLE`; retain `_current` only as an unproved requested target inside blocked criteria, never as scanner-backed metadata.
3. Under `## Project UX evidence matrix`, produce a project-specific table with separate `ID`, `Surface/state`, `Risk`, `Test`, `Evidence layer`, `Result`, and `Evidence` columns; use unique `[UX-...] {gate=...}` IDs and make every semantic gate cover its full family-layer contract rather than citing or compressing a generic checklist.
4. Cover supported surfaces/transitions, every business state, long Chinese/English/Unicode, overflow, and fixed-action visibility.
5. Reject luminance-only state meaning and test hierarchy, density, contrast, and bright/dark/cluttered backgrounds.
6. Use separate UX input gates for every scoped tap, Enter, Back, unresolved directional/scroll, generic voice, head gesture, and non-gesture fallback path; keep host focus and element focus separate and do not combine known failures with unexecuted layers.
7. Under `## Per-capability matrix`, produce one uniquely identified `[CAP-...] {family=...} {gate=...}` row per used or claimed API/component/event/callback/declaration/route/hardware capability; keep host focus, element focus/binding, each input/fallback, permission, and runtime API separate; make each gate cover its full family-layer contract; preserve all eleven required columns and use semantic `DOC`, `SAMPLE`, `DECLARATION-SNIPPET`, or provisional `SEARCH-SCOPE` roles with selected-version commit-pinned URLs. Because source is unavailable, exact registered families follow the project-binding provisional protocol; generic scroll/voice/fallback rows follow their registered source-policy provisional contracts.
8. Test each capability's positive path plus denial, revocation, unavailable, timeout/malformed response where applicable, fallback, and lifecycle cleanup.
9. Keep source review, static validation, deterministic logic tests, AIX preview, Studio simulation, and physical-device evidence distinct.
10. Never use browser/AIX preview as proof of physical focus, keys, voice, gestures, permissions, optics, or performance.
11. Use only `PASS`, `FAIL`, `BLOCKED`, or justified `N/A`; each result obeys the fixed family-layer contract, `PASS`/`FAIL` maps every executed layer to an existing locator, `BLOCKED` maps every layer to `blocked:reason`, and `N/A` identifies both source and product-claim exclusion. No row in this scenario is `N/A`; historical assertions are not executable evidence without current-revision schema-2 locators.
12. End with the sole structured `## Final release decision`, containing exactly `Final status`, `Release-ready`, `Reason`, and `Required gates`; report exact missing Studio/device checks without representing them as completed or contradicting the decision elsewhere.

## Critical failures

- Signs off release or calls the agent release-ready despite an applicable `FAIL` or `BLOCKED` cell.
- Omits either the project-specific UX matrix or the per-capability matrix.
- Renames, merges, or omits a required matrix column, including `Risk`, `Evidence layer`, or `Evidence`.
- Omits a required UX family, duplicates an ID, leaves a used/claimed capability uninventoried, uses an umbrella row in place of separate items, or omits stable `[CAP-...]` identifiers, registered family tokens, fixed evidence layers, and role-bound version-pinned sources.
- Treats static tests or AIX/browser preview as physical-device evidence.
- Records an unexecuted or evidence-free check as `PASS`.
- Fabricates a project revision, supported surface, project API/callback binding, or executed evidence from request prose.
- Omits the structured final decision or contradicts its status/release-ready fields.
