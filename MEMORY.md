# Durable Memory

## Decisions

- 2026-09-07: The public repository will be `BreezeLife/rokid-aiui-agent-skill`.
- 2026-09-07: Use a standalone-but-curated design. The Skill works from this repository alone for common work, while linking and pinning authoritative upstream sources for deep or changing API details.
- 2026-09-07: Keep `skills/rokid-aiui-agent/SKILL.md` compact and route project anatomy, `.ink`, design, runtime capabilities, AIX, and debugging/release details to focused references.
- 2026-09-07: Treat `yodaos-project/AIUI` and `yodaos-project/aix` as the current canonical repositories because the user-provided `jsar-project` URLs redirect there.
- 2026-09-07: Do not document imaginary `aix create`, `aix dev`, `aix build`, or `aix deploy` commands. Probe `aix --help`; map development to supported `preview` behavior and packaging to `pack` only when present.
- 2026-09-07: Official facts and third-party observations must remain visibly separated. Do not copy material from an unlicensed third-party repository.
- 2026-09-07: Repository documentation is bilingual-friendly, while the Skill instructions are concise English for broad coding-agent compatibility; developer-facing README includes Chinese and English usage cues.
- 2026-09-07: The current official quickstart describes conversation-embedded AIUI as interactive; do not preserve the stale bundled Skill claim that conversation-flow cards are display-only.
- 2026-09-07: The current monochrome-green beta design uses low visual mass, 1px normal lines, 4px control radii, 6px panel radii, and at most 12% normal local fill. Do not repeat the stale 2px/12px/card-first summary.
- 2026-09-07: Within the official repository, resolve conflicts in this order: current changelog and implementation-aligned documentation, runtime/source and runnable samples, then bundled `skills/aiui-dev` summaries.
- 2026-09-07: The default implementation deliverable is editable AIUI source: either a complete local project directory or a GitHub repository root/declared subdirectory that AIUI Studio can import. An `.aix` package alone does not satisfy this contract.
- 2026-09-07: The official documentation selector currently labels AIUI `0.17.0` as stable. Use it as the conservative default when a target cannot be discovered. The inspected repository documents `0.18.0` additions such as Widgets and Agent Workers; do not emit them into a `0.17.0` project without explicit support evidence.
- 2026-09-07: Package the repository Skill at `skills/rokid-aiui-agent/`, because Agent Skills discovery requires a named directory whose basename matches frontmatter `name`. Keep the Studio-importable example inside the package as `assets/studio-importable-minimal/` so it survives installation.
- 2026-09-07: Never report validation, AIX, Studio, platform, or device success from a proposed command alone; success claims require an execution record from the current environment.
- 2026-09-08: The first generated product example is `examples/next-step-agent/`. It uses the official `schema.data` Page input envelope, local Page state, no permissions, and target-specific density without target-specific business state.
- 2026-09-08: Bound `goal` and `nextStep` to 120 and 48 Unicode code points. Keep long Page content inside the official `scroll-view` component, and drive focus feedback from each actionable element's `focus` and `blur` events.
- 2026-09-08: The Japanese `examples/focus-timer-agent/` uses a Page-local absolute deadline for timing. `Date.now()` is the source of remaining time, the interval only refreshes presentation, hide/show suspends and recalculates refresh, and no background execution, alarm, notification, or persistence is promised.
- 2026-09-08: Focus Timer actions use per-button focus state. Running progress is capped at 99%; only `finished` displays 100%, so presentation never claims completion before the absolute deadline.
- 2026-09-09: Focus Timer uses AIUI 0.17 Page World Awareness for head gestures, not eye tracking. A visible Page maps `nod` to its primary state action: idle/start, running/pause, paused/continue, and finished/restart; error is a no-op and button focus/tap remains available.
- 2026-09-09: Voice-driven Focus Timer reconfiguration must happen through a new Page invocation with converted integer `durationSeconds`; AIUI 0.17 `onLoad(query)` runs only once per Page instance, so later conversation must not claim to mutate an already-rendered timer card in place.
- 2026-09-09: Focus Timer defaults an omitted `durationSeconds` to 600 seconds (10 minutes), including empty, null, or undefined Page input. An explicitly supplied invalid duration remains an error rather than silently falling back.
- 2026-09-09: SceneQuest / セイチ｜SEICHI is a curated Osaka MVP with exactly 12 source-traceable spots. Camera imagery, GPS/current-location context, the spoken question, and optional work/character constraints belong to the Agent host; the stable-AIUI-0.17 Page only validates and renders a bounded result and does not capture camera or GPS directly.
- 2026-09-09: SceneQuest uses one Page for `_current` and `_blank`, four categorical result states (`matched`, `uncertain`, `no_match`, `invalid`), and at most one concrete retry for uncertain evidence. It does not bundle anime frames, run background geofencing, or claim nationwide coverage; dynamic visual photo guidance is allowed only when current evidence supports it, otherwise it falls back to the curated position.

## Source priority

1. Official AIUI documentation for the selected runtime, then version-matched implementation and runnable samples.
2. Current official AIX repository, package registry metadata, and released CLI behavior.
3. Newer official AIUI preview changelog, implementation, and samples, used only when target compatibility is established.
4. Official ROKID course and recommended design guideline.
5. Awesome AIUI as a discovery index.
6. Third-party implementations as non-normative examples only.

## Known upstream state at project start

- AIUI stable `v0.17.0` tag verified through the GitHub API: `88e70bb0382525c1a93ef077c2401dcc31a273ce`.
- AIUI canonical repository commit inspected: `8b19a87b4ba8b486c0dd4dd3fd32290d27891069` (2026-09-07).
- AIX canonical repository commit inspected: `8e5f5b1ba60691291f99d14ea9516995f2af55e4` (2026-09-03).
- Awesome AIUI commit inspected: `98049c58e31e25abcf6c4b9d93e469346a7c88a9` (2026-09-03).
- DeepSeek Harness kit commit inspected: `ddf012da7d3b488b5edf5b77faff71a1663f5342` (2026-08-15); it is a third-party source.
