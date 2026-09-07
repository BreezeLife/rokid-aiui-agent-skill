# Scenario 04: AIUI Studio Import Delivery

## Prompt

请从零实现一个 ROKID AIUI 喝水提醒智能体。我只需要你在回答里贴核心代码和生成一个 `.aix` 包，不需要整理完整工程；版本没有指定。最终要让我同事从本地目录或 GitHub 导入 AIUI Studio。不要问问题，直接交付并说明导入方式。

## Observable invariants

Score one point for each invariant met. Do not award partial credit.

1. Reject snippets-only delivery and make the primary output a complete editable AIUI project directory.
2. State the exact local project root, and for GitHub delivery state repository URL, revision, and the root or explicit import subdirectory.
3. Put `app.json` at that import root with a non-empty `pages` array.
4. Include `AGENTS.md` and an application entry suitable for the selected runtime.
5. Resolve every declared Page route to a complete `.ink` page or multi-file WXML page, and include every referenced source/asset.
6. Because no version is discoverable, disclose the assumption and use the official `0.17.0` stable compatibility baseline.
7. Do not add `0.18.0`-only Widgets, Agent Workers, manifest fields, or APIs without target evidence.
8. Run strict structural validation against the exact import directory and report the command/result.
9. Probe the selected AIX CLI, then use only advertised `pack` and `list`/`ls`; keep the `.aix` as an additional artifact rather than the source deliverable.
10. Explain the Studio flow accurately: choose the local folder, or provide GitHub URL plus branch/tag and specified directory; keep platform upload and physical-device verification as later evidence gates.

## Critical failures

- Returns only snippets or an `.aix` archive while claiming the project is ready for Studio source import.
- Places `app.json` above or below the stated import root without naming the correct subdirectory.
- Silently uses `0.18.0`-only project features for the unspecified target.
