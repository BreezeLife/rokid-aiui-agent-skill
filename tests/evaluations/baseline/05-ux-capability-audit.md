# Baseline Response: Mandatory UX and capability audit

- Scenario: `tests/scenarios/05-ux-capability-audit.md`
- Conditions: fresh subagent using the current pre-enhancement Skill; no Studio or physical-device access
- Captured: 2026-09-09
- Score: 8/12
- Critical failures: 1 (no explicit per-capability matrix)

## Observed decision

The baseline correctly allowed only a “local validation passed” statement and blocked release. It separated validator/unit/AIX evidence from Studio and device proof; rejected luminance-only state meaning; identified long-text, element-focus, CAMERA denial/revocation/unavailability, voice, nod, surface, Studio, and physical-glasses gaps.

## Observed output gap

The response offered a flat sign-off list using `PASS`, `PARTIAL PASS`, `FAIL`, `UNVERIFIED`, and `BLOCKER`. It did not produce two mandatory matrices with stable fields. In particular, it had no per-capability row containing the exact API/component/event, version/device/surface, pinned official source/sample, declaration/permission, positive path, negative/fallback path, lifecycle cleanup, required evidence layer, result, and evidence.

The evaluator explicitly concluded:

> 现有 Skill 有分散规则与“physical-device release matrix”，但没有明文强制每个项目产出一个逐项、项目化的“UX × 能力 × surface × evidence layer”矩阵，也没有统一列定义……本次场景下我会主动整理表格，因为审查任务需要；但这是推导行为，不是根 `SKILL.md` 的不可跳过交付物，因此不同执行者可能只引用通用发布矩阵。

This is the RED result for the focused Skill change: the safety decision is mostly correct, but the requested audit artifact and consistent evidence semantics are not reliably enforced.
