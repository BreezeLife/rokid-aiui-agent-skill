# Durable Memory

## Decisions

- 2026-09-07: The public repository will be `BreezeLife/rokid-aiui-agent-skill`.
- 2026-09-07: Use a standalone-but-curated design. The Skill works from this repository alone for common work, while linking and pinning authoritative upstream sources for deep or changing API details.
- 2026-09-07: Keep `SKILL.md` compact and route project anatomy, `.ink`, design, runtime capabilities, AIX, and debugging/release details to focused references.
- 2026-09-07: Treat `yodaos-project/AIUI` and `yodaos-project/aix` as the current canonical repositories because the user-provided `jsar-project` URLs redirect there.
- 2026-09-07: Do not document imaginary `aix create`, `aix dev`, `aix build`, or `aix deploy` commands. Probe `aix --help`; map development to supported `preview` behavior and packaging to `pack` only when present.
- 2026-09-07: Official facts and third-party observations must remain visibly separated. Do not copy material from an unlicensed third-party repository.
- 2026-09-07: Repository documentation is bilingual-friendly, while the Skill instructions are concise English for broad coding-agent compatibility; developer-facing README includes Chinese and English usage cues.
- 2026-09-07: The current official quickstart describes conversation-embedded AIUI as interactive; do not preserve the stale bundled Skill claim that conversation-flow cards are display-only.
- 2026-09-07: The current monochrome-green beta design uses low visual mass, 1px normal lines, 4px control radii, 6px panel radii, and at most 12% normal local fill. Do not repeat the stale 2px/12px/card-first summary.
- 2026-09-07: Within the official repository, resolve conflicts in this order: current changelog and implementation-aligned documentation, runtime/source and runnable samples, then bundled `skills/aiui-dev` summaries.

## Source priority

1. Current official AIUI changelog, documentation, design system, implementation, and runnable samples.
2. Current official AIX repository, package registry metadata, and released CLI behavior.
3. Official ROKID course and recommended design guideline.
4. Awesome AIUI as a discovery index.
5. Third-party implementations as non-normative examples only.

## Known upstream state at project start

- AIUI canonical repository commit inspected: `8b19a87b4ba8b486c0dd4dd3fd32290d27891069` (2026-09-07).
- AIX canonical repository commit inspected: `8e5f5b1ba60691291f99d14ea9516995f2af55e4` (2026-09-03).
- Awesome AIUI commit inspected: `98049c58e31e25abcf6c4b9d93e469346a7c88a9` (2026-09-03).
- DeepSeek Harness kit commit inspected: `ddf012da7d3b488b5edf5b77faff71a1663f5342` (2026-08-15); it is a third-party source.
