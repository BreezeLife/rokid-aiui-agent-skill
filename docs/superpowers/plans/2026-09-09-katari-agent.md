# KATARI Agent Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Deliver KATARI as a Japanese-first, source-traceable Osaka Local Story Agent in a complete AIUI 0.17 Studio-importable Page project, with exactly 20 short Japanese/English stories and recorded UX and capability test evidence.

**Architecture:** The host supplies available image, place, GPS, voice, and locale context to the Agent. The Agent reasons only over a curated 20-record runtime catalog, applies explicit location/visual evidence gates, speaks one authored 15–30 second story, and invokes one bounded result Page. The Page normalizes its input and renders the approved A · Quiet Marker design in compact `_current` and expanded `_blank` densities without directly using camera, location, network, or background APIs.

**Tech Stack:** AIUI 0.17 `.ink`, Open Agent Format, JavaScript, Python `unittest`, Node.js 24 Page harness, repository validator, `@yodaos-pkg/aix-cli@0.8.2`, browser-based 480×352 UX inspection.

---

## File map

- Create `examples/katari-agent/AGENTS.md`: identity, triggers, language and evidence policy, Page contract, and 20 compact runtime records.
- Create `examples/katari-agent/SOURCES.md`: source registry for the same 20 spot IDs.
- Create `examples/katari-agent/app.js`: minimal application entry.
- Create `examples/katari-agent/app.json`: one stable-0.17 Page route and no direct device permissions.
- Create `examples/katari-agent/pages/index/index.ink`: schema, normalization, five states, target-aware Quiet Marker UI, and styles.
- Create `tests/test_katari_agent_contract.py`: catalog, Agent, Page behavior, visual, evaluation, and delivery contracts.
- Create `tests/evaluations/katari-capability.md`: 15-case capability evidence matrix.
- Create `tests/evaluations/katari-ux.md`: AIX preview and 480×352 UX evidence.
- Modify `.github/workflows/ci.yml`, `README.md`, and `PROJECT.md`: integrate validation, packaging, preview, and delivery documentation.
- Modify `MEMORY.md`, `TASKS.md`, and `WORKLOG.md`: preserve decisions, results, and external gates.

## Fixed catalog candidates

Research these candidates in order and accept exactly 20 only after the Task 1 source gate passes:

1. `dotonbori` — 道頓堀
2. `ebisu-bridge` — 戎橋
3. `glico-running-man` — 道頓堀グリコサイン
4. `hozenji-yokocho` — 法善寺横丁
5. `mizukake-fudo` — 水掛不動尊
6. `osaka-castle` — 大阪城
7. `tsutenkaku` — 通天閣
8. `shinsekai` — 新世界
9. `kuromon-market` — 黒門市場
10. `shinsaibashi-suji` — 心斎橋筋
11. `doguyasuji` — 千日前道具屋筋商店街
12. `namba-yasaka-shrine` — 難波八阪神社
13. `shitennoji` — 四天王寺
14. `sumiyoshi-taisha` — 住吉大社
15. `tenjinbashi-suji` — 天神橋筋商店街
16. `osaka-tenmangu` — 大阪天満宮
17. `osaka-central-public-hall` — 大阪市中央公会堂
18. `tekijuku` — 適塾
19. `tower-of-the-sun` — 太陽の塔
20. `osaka-station` — 大阪駅

If a candidate fails the central-story source gate, replace it with the first passing candidate from this reserve order: `nakanoshima-library`, `nipponbashi-den-den-town`, then `abeno-harukas`. Record the rejected candidate and reason in `SOURCES.md`; a rejected record does not count toward the 20 runtime IDs and contributes no story text to `AGENTS.md`.

### Task 1: Build the source-gated 20-spot registry

**Files:**
- Create: `tests/test_katari_agent_contract.py`
- Create: `examples/katari-agent/SOURCES.md`

- [ ] **Step 1: Write the failing source contract**

Create the shared paths and first test:

```python
from __future__ import annotations

import json
import re
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
EXAMPLE = ROOT / "examples" / "katari-agent"
INK = EXAMPLE / "pages" / "index" / "index.ink"
VALIDATOR = ROOT / "skills" / "rokid-aiui-agent" / "scripts" / "validate_aiui_project.py"
SOURCE_SPOT = re.compile(r"^## Spot: ([a-z0-9-]+)$", re.MULTILINE)
AGENT_SPOT = re.compile(r"^### Story Spot: ([a-z0-9-]+)$", re.MULTILINE)

def read_example(relative: str) -> str:
    path = EXAMPLE / relative
    if not path.is_file():
        raise AssertionError(f"missing KATARI file: {relative}")
    return path.read_text(encoding="utf-8")

def extract_block(source: str, pattern: str, label: str) -> str:
    match = re.search(pattern, source, flags=re.DOTALL)
    if match is None:
        raise AssertionError(f"missing {label} block")
    return match.group(1).strip()

class KatariAgentContractTests(unittest.TestCase):
    def test_source_registry_has_twenty_complete_story_spots(self) -> None:
        sources = read_example("SOURCES.md")
        ids = SOURCE_SPOT.findall(sources)
        self.assertEqual(len(ids), 20)
        self.assertEqual(len(set(ids)), 20)
        sections = re.split(r"(?=^## Spot: )", sources, flags=re.MULTILINE)[1:]
        for section in sections:
            for label in (
                "- Place JA:", "- Place EN:", "- Category:",
                "- Locality:", "- Coordinates:", "- Candidate radius:",
                "- Visual anchors:", "- Facts:", "- Story claim:",
                "- Knowledge kind:", "- Sources:", "- Source classes:",
                "- Verified:", "- Uncertainty:",
            ):
                self.assertIn(label, section)
            self.assertRegex(section, r"https://")
            self.assertRegex(section, r"- Verified: 2026-\d{2}-\d{2}")
            self.assertRegex(section, r"- Knowledge kind: (?:fact|legend|tradition)$")
            facts = re.findall(r"^  \d+\. .+$", section, re.MULTILINE)
            self.assertGreaterEqual(len(facts), 3)
            self.assertLessEqual(len(facts), 5)
            self.assertNotRegex(section, r"\b(?:TBD|TODO)\b")
```

- [ ] **Step 2: Run the focused test and verify RED**

Run `python3 -m unittest tests.test_katari_agent_contract -v`.

Expected: failure reports `missing KATARI file: SOURCES.md`.

- [ ] **Step 3: Research and gate every candidate**

Verify identity and location through an official place, municipal, heritage, transport, shrine/temple, museum, or tourism source. Verify the central story with a primary institutional source where possible and a reputable secondary source when a nickname or social custom is not documented by the institution. Reject claims that depend only on SEO pages, social posts, anonymous blogs, or circular citation. Mark legend/tradition explicitly. Do not copy source prose or images.

- [ ] **Step 4: Author exactly 20 source sections**

Create `SOURCES.md` and use this exact parseable shape for each record:

```markdown
## Spot: ebisu-bridge

- Place JA: 戎橋
- Place EN: Ebisu Bridge
- Category: bridge
- Locality: Dotonbori, Chuo Ward, Osaka
- Coordinates: 34.6687, 135.5013
- Candidate radius: 80 m
- Visual anchors: bridge balustrade; Dotonbori canal; adjacent large signs
- Facts:
  1. Osaka City says the bridge was likely built around the same time as the Dotonbori canal.
  2. The bridge served people heading toward Imamiya Ebisu and the theatres south of the bridge.
  3. It was also called Ayatsuri Bridge because a puppet theatre stood on its south side.
- Story claim: Before it became a sign-viewing landmark, the bridge carried worshippers and theatre-goers through Osaka's entertainment district.
- Knowledge kind: fact
- Sources:
  - https://www.city.osaka.lg.jp/kensetsu/page/0000021695.html
- Source classes: Osaka City bridge history
- Verified: 2026-09-09
- Uncertainty: Osaka City says the bridge-name origin is not certain, so the story does not assert one origin as fact.
```

Use this record as the formatting model and verify its coordinates during implementation together with the other records. Use researched facts and direct URLs for all 20 spots, numeric coordinates, and an integer radius from 25 through 300 metres. The introduction documents source precedence, copyright boundaries, verification date meaning, and rejected candidates.

- [ ] **Step 5: Verify GREEN and commit**

Run `python3 -m unittest tests.test_katari_agent_contract -v`; expect one test and `OK`.

```bash
git add tests/test_katari_agent_contract.py examples/katari-agent/SOURCES.md
git commit -m "test: define KATARI source catalog"
```

### Task 2: Add the importable Agent shell and runtime catalog

**Files:**
- Modify: `tests/test_katari_agent_contract.py`
- Create: `examples/katari-agent/AGENTS.md`
- Create: `examples/katari-agent/app.js`
- Create: `examples/katari-agent/app.json`
- Create: `examples/katari-agent/pages/index/index.ink`

- [ ] **Step 1: Add failing import-root and Agent tests**

Require exactly the five project files, one `pages/index/index` route, and no `widgets`, `agentWorkers`, or `permissions`. Require Agent identity, Japanese default/English selection, all five states, one retry, 15–30 seconds, one-story output, fact/legend distinction, Page targets, and explicit exclusions for routing, recommendations, news, proactive prompts, and direct Page camera/GPS. Require exactly 20 unique `### Story Spot: <id>` headings matching `SOURCES.md`.

```python
    def test_runtime_catalog_matches_source_registry(self) -> None:
        source_ids = SOURCE_SPOT.findall(read_example("SOURCES.md"))
        agent_ids = AGENT_SPOT.findall(read_example("AGENTS.md"))
        self.assertEqual(len(agent_ids), 20)
        self.assertEqual(len(set(agent_ids)), 20)
        self.assertEqual(set(agent_ids), set(source_ids))
```

- [ ] **Step 2: Verify RED**

Run `python3 -m unittest tests.test_katari_agent_contract -v`.

Expected: missing `AGENTS.md`, manifest, app entry, and Page failures.

- [ ] **Step 3: Create the minimal application shell**

`app.js`:

```javascript
App({
  globalData: { productName: 'KATARI', targetVersion: '0.17.0' }
});
```

`app.json`:

```json
{
  "pages": ["pages/index/index"],
  "window": { "navigationBarTitleText": "KATARI" }
}
```

Add a temporary valid `.ink` Page with one JSON definition, one setup export, one Page root, and black/green style. This keeps the directory Studio-selectable while Tasks 3–4 replace the stub behavior and markup.

- [ ] **Step 4: Author `AGENTS.md` and 20 runtime records**

Use the standard sections `System Prompts`, `Capabilities`, `Configuration`, and `Dependencies`. State that the host supplies available image/GPS/place/voice/locale context. Encode these outcomes exactly:

```text
matched    = agreeing location plus multiple distinctive visual anchors, or
             exact signage plus multiple anchors when GPS is absent
uncertain  = partial evidence or one conflict; ask for one specific view once
no_story   = place identity is supported but no authored claim remains reliable
no_match   = retry failed, no catalog record fits, or identity would be a guess
invalid    = all useful image, place, location, and question context is absent
```

For each runtime spot, include coordinates/radius, anchors, three-to-five accepted facts, one Japanese story of 60–120 characters, one English story of 35–70 words, paired memory hooks, `fact|legend|tradition`, direct source IDs, and 15–30 second integer durations. The two versions express the same central claim. Prohibit invented dialogue, motives, causality, scene detail, extra years, people, events, and live retrieval.

- [ ] **Step 5: Verify GREEN, validate, and commit**

```bash
python3 -m unittest tests.test_katari_agent_contract -v
python3 skills/rokid-aiui-agent/scripts/validate_aiui_project.py examples/katari-agent --target-version 0.17.0 --strict
git add tests/test_katari_agent_contract.py examples/katari-agent
git commit -m "feat: add KATARI agent catalog"
```

Expected: focused tests and strict validation pass.

### Task 3: Implement the bounded five-state Page behavior

**Files:**
- Modify: `tests/test_katari_agent_contract.py`
- Modify: `examples/katari-agent/pages/index/index.ink`

- [ ] **Step 1: Add failing schema and Node behavior tests**

Require the `schema.data` object to declare:

```text
status: enum matched|uncertain|no_story|no_match|invalid
spotId: string, maxLength 48
placeNameJa: string, maxLength 48
placeNameEn: string, maxLength 64
localityLabel: string, maxLength 48
storyDurationSeconds: integer, minimum 15, maximum 30
memoryHook: string, maxLength 140
confidenceLabel: string, maxLength 64
evidenceNote: string, maxLength 160
knowledgeKind: enum fact|legend|tradition
recoveryHint: string, maxLength 160
```

Extract the real setup block into a temporary `.mjs`, import it with Node, and mount a Page object whose `setData` merges patches. Exercise valid Japanese and English matches, every recovery state, missing/array roots, unknown status, invalid duration 14/31/fraction/string, wrong field types, and Unicode values one code point below/at/above every maximum. Assert malformed inputs become `invalid` and no raw value leaks into the patch.

- [ ] **Step 2: Verify RED**

Run `python3 -m unittest tests.test_katari_agent_contract -v`.

Expected: schema fields and normalizer cases fail against the stub.

- [ ] **Step 3: Implement pure bounded normalization**

Use `Array.from(value).length` for Unicode length and reject non-string values. A valid `matched` input requires non-empty `spotId`, both place names, an integer duration from 15 through 30, and a valid knowledge kind. Derive `knowledgeLabel` as `FACT`, `LEGEND`, or `TRADITION` and `showStoryMeta: true`.

All invalid inputs use this safe core patch:

```javascript
{
  status: 'invalid',
  spotId: '',
  placeNameJa: '場所を見せてください',
  placeNameEn: 'LOOK AT A LANDMARK',
  localityLabel: '',
  storyDurationSeconds: 0,
  memoryHook: '',
  confidenceLabel: 'KATARI',
  evidenceNote: '',
  knowledgeKind: 'fact',
  knowledgeLabel: '',
  recoveryHint: '建物や看板が見える向きでもう一度聞いてください。',
  showStoryMeta: false,
  showExpandedDetail: false
}
```

Give `uncertain`, `no_story`, and `no_match` distinct Japanese and English fallback titles and hints. `onLoad(query)` calls the normalizer once and applies one complete patch. Do not add camera, location, network, storage, speech, timer, world-awareness, key, or background APIs.

- [ ] **Step 4: Replace the definition with the bounded schema**

Add all ten fields under the official `schema.data` envelope and use the exact enums and limits from Step 1. Keep recovery fields optional globally because the runtime normalizer performs state-aware validation.

- [ ] **Step 5: Verify GREEN, validate, and commit**

```bash
python3 -m unittest tests.test_katari_agent_contract -v
python3 skills/rokid-aiui-agent/scripts/validate_aiui_project.py examples/katari-agent --target-version 0.17.0 --strict
git add tests/test_katari_agent_contract.py examples/katari-agent/pages/index/index.ink
git commit -m "feat: add KATARI result states"
```

Expected: focused behavior tests and strict validation pass.

### Task 4: Implement and contract-test A · Quiet Marker

**Files:**
- Modify: `tests/test_katari_agent_contract.py`
- Modify: `examples/katari-agent/pages/index/index.ink`

- [ ] **Step 1: Add failing markup/style tests**

Require the Page to contain `KATARI / LOCAL MEMORY`, both place names, locality, `LOCAL STORY · {{storyDurationSeconds}} SEC`, memory hook, confidence/evidence, knowledge label, and recovery hint. Require `_current` and `_blank` media rules, black floor, `#72ff9e`, one 1 px divider, 6 px group radius, no buttons/tap handlers/key interception, and no `@keyframes`.

```python
    def test_quiet_marker_has_target_aware_low_mass_ui(self) -> None:
        ink = read_example("pages/index/index.ink")
        page = extract_block(ink, r"<page\b[^>]*>(.*?)</page>", "page")
        style = extract_block(ink, r"<style>\s*(.*?)\s*</style>", "style")
        self.assertIn("KATARI / LOCAL MEMORY", page)
        self.assertIn("LOCAL STORY · {{storyDurationSeconds}} SEC", page)
        self.assertIn("@media (target: _current)", style)
        self.assertIn("@media (target: _blank)", style)
        self.assertIn(".expanded-only { display: none; }", style)
        self.assertIn("background-color: #000000", style)
        self.assertIn("color: #72ff9e", style)
        self.assertIn("border-top: 1px solid", style)
        self.assertIn("border-radius: 6px", style)
        self.assertNotIn("<button", page)
        self.assertNotIn("bindtap=", page)
        self.assertNotIn("onKeyUp", ink)
        self.assertNotIn("@keyframes", style)
```

- [ ] **Step 2: Verify RED**

Run `python3 -m unittest tests.test_katari_agent_contract -v`.

Expected: missing Quiet Marker hierarchy and target-density failures.

- [ ] **Step 3: Implement the approved hierarchy**

Use one Page surface: eyebrow; Japanese name; English name/locality; matched-only duration row with status dot; recovery-only label/hint; `_blank`-only memory hook, knowledge label, and evidence note. Use structural `ink:if` branches so a recovery state never exposes matched metadata. Keep the place name as the only dominant element.

- [ ] **Step 4: Implement low-mass 480×352 styling**

Use a black floor, `#72ff9e` primary text, lower-opacity green secondary text, one 1 px divider, 6 px group radius, no large filled panel, and no ambient motion. Keep the safe region approximately 36 px from horizontal and 30 px from vertical edges. Hide `.expanded-only` in `_current`; show it as a vertical group in `_blank` without moving the identity out of the safe region.

- [ ] **Step 5: Verify GREEN, validate, and commit**

```bash
python3 -m unittest tests.test_katari_agent_contract -v
python3 skills/rokid-aiui-agent/scripts/validate_aiui_project.py examples/katari-agent --target-version 0.17.0 --strict
git add tests/test_katari_agent_contract.py examples/katari-agent/pages/index/index.ink
git commit -m "feat: add KATARI Quiet Marker UI"
```

Expected: focused UX contracts and strict validation pass.

### Task 5: Complete the Agent capability evaluation

**Files:**
- Modify: `tests/test_katari_agent_contract.py`
- Create: `tests/evaluations/katari-capability.md`

- [ ] **Step 1: Add a failing evidence-record test**

Require exactly 15 unique `## Case:` sections. Every case contains `Input evidence`, `Expected state`, `Expected behavior`, `Observed`, `Result`, and `Evidence class`. Require all five states, both story languages, fact/legend distinction, GPS-only, vision-only, location/visual conflict, look-alike anchors, retry exhaustion, concise output, and an out-of-scope route request.

```python
    def test_capability_evaluation_records_fifteen_cases(self) -> None:
        report = (ROOT / "tests" / "evaluations" / "katari-capability.md").read_text(encoding="utf-8")
        cases = re.split(r"(?=^## Case: )", report, flags=re.MULTILINE)[1:]
        self.assertEqual(len(cases), 15)
        for case in cases:
            for label in (
                "- Input evidence:", "- Expected state:",
                "- Expected behavior:", "- Observed:",
                "- Result:", "- Evidence class:",
            ):
                self.assertIn(label, case)
            self.assertRegex(case, r"- Result: (?:PASS|FAIL)$")
        for state in ("matched", "uncertain", "no_story", "no_match", "invalid"):
            self.assertIn(f"- Expected state: {state}", report)
```

- [ ] **Step 2: Verify RED**

Run `python3 -m unittest tests.test_katari_agent_contract -v`.

Expected: missing `katari-capability.md`.

- [ ] **Step 3: Write the 15 cases before scoring**

Use these exact intents:

1. Japanese match from GPS plus two distinctive anchors.
2. English match from GPS plus two distinctive anchors.
3. GPS only near a dense candidate cluster returns `uncertain`.
4. Vision only with exact sign plus multiple anchors can match and discloses missing location.
5. Location/visual conflict returns `uncertain` and one specific request.
6. A second unresolved view returns `no_match` without a third request.
7. Look-alike architecture does not force a famous-place result.
8. Supported identity with withdrawn/insufficient story returns `no_story` without a substitute.
9. A place outside the 20 records returns `no_match`.
10. Missing all useful input returns `invalid`.
11. A Japanese legend uses non-factual wording.
12. An English tradition uses non-factual wording.
13. A request for a long answer still returns one bounded story.
14. A route request is declined or redirected without navigation data.
15. User-suggested false history does not override catalog evidence.

For each, write concrete evidence, expected Page fields, and story ID/language expectations.

- [ ] **Step 4: Execute and record the prompt-contract evaluation**

Apply the final `AGENTS.md` rules and selected catalog record to every case. Record selected state, story ID or absence, language, character/word count, duration, recovery hint, and policy violations. Mark `PASS` only when state and content match and no unsupported fact appears. Set `Evidence class` to `local prompt-contract evaluation` and state that this is not an authenticated Studio host, production-model, camera/GPS, or device test.

- [ ] **Step 5: Verify GREEN and commit capability evidence**

```bash
python3 -m unittest tests.test_katari_agent_contract -v
git add tests/test_katari_agent_contract.py tests/evaluations/katari-capability.md
git commit -m "test: evaluate KATARI capabilities"
```

Expected: all 15 report cases and prior KATARI tests pass.

### Task 6: Integrate repository delivery and CI gates

**Files:**
- Modify: `tests/test_katari_agent_contract.py`
- Modify: `.github/workflows/ci.yml`
- Modify: `README.md`
- Modify: `PROJECT.md`

- [ ] **Step 1: Add failing documentation and CI tests**

Require README references for `KATARI Local Story Agent`, `examples/katari-agent`, 20 spots, 15–30 seconds, UX/capability evidence, and `Directory: examples/katari-agent`. Require the project architecture to list the example. Parse CI YAML and require KATARI in the strict-validator and stable pack/list steps plus a `Generate the KATARI static preview` step that probes `"$AIX_BIN" --help`, invokes preview for the exact directory, and checks non-empty output.

- [ ] **Step 2: Verify RED**

Run `python3 -m unittest tests.test_katari_agent_contract -v`.

Expected: missing documentation, validation, pack, and preview references.

- [ ] **Step 3: Update CI using existing locked tools**

Append KATARI to the existing strict validation block and stable smoke block. Add a preview step parallel to the Next Step and Focus Timer steps. Use the lockfile-installed `AIX_BIN`, probe `preview` in `--help`, write to `$RUNNER_TEMP`, require a non-empty file, and grep the exact `pages/index/index.ink` path. Do not add or update dependencies.

- [ ] **Step 4: Document delivery and evidence boundaries**

Add a README section covering Osaka-only scope, one authored Japanese/English 15–30 second story, host-provided context, five states, Quiet Marker, Studio coordinates (`BreezeLife/rokid-aiui-agent-skill`, ref `main`, directory `examples/katari-agent`), local test commands, and links to both evaluation records. State the Studio, host, speech, optics, and physical-device manual gates. Register `examples/katari-agent/` in `PROJECT.md` as Page-only AIUI 0.17.

- [ ] **Step 5: Verify GREEN and commit integration**

```bash
python3 -m unittest tests.test_katari_agent_contract -v
git add tests/test_katari_agent_contract.py .github/workflows/ci.yml README.md PROJECT.md
git commit -m "docs: integrate KATARI delivery flow"
```

Expected: focused delivery tests pass and parsed CI retains all existing jobs.

### Task 7: Execute and record the UX test matrix

**Files:**
- Modify: `tests/test_katari_agent_contract.py`
- Create: `tests/evaluations/katari-ux.md`

- [ ] **Step 1: Add a failing UX evidence test**

Require the report to contain `480 × 352`, `A · Quiet Marker`, `AIX preview`, all five state names, `_current`, `_blank`, Japanese and English long-label cases, bright/dark/cluttered simulated backgrounds, clipping, hierarchy, status differentiation, information load, `browser evidence only`, and `physical Rokid Glasses`. Reject `TBD` and `TODO`.

```python
    def test_ux_evaluation_records_states_and_limits(self) -> None:
        report = (ROOT / "tests" / "evaluations" / "katari-ux.md").read_text(encoding="utf-8")
        for fragment in (
            "480 × 352", "A · Quiet Marker", "AIX preview",
            "matched", "uncertain", "no_story", "no_match", "invalid",
            "_current", "_blank", "Japanese long label",
            "English long label", "bright background", "dark background",
            "cluttered background", "clipping", "hierarchy",
            "status differentiation", "information load",
            "browser evidence only", "physical Rokid Glasses",
        ):
            self.assertIn(fragment, report)
        self.assertNotRegex(report, r"\b(?:TBD|TODO)\b")
```

- [ ] **Step 2: Verify RED**

Run `python3 -m unittest tests.test_katari_agent_contract -v`.

Expected: missing `katari-ux.md`.

- [ ] **Step 3: Probe AIX and generate the actual project preview**

Use the repository's verified Node 24 runtime and lockfile-installed AIX:

```bash
AIX_BIN="$PWD/node_modules/.bin/aix"
"$AIX_BIN" --help
preview_dir="$(mktemp -d "${TMPDIR:-/tmp}/katari-preview.XXXXXX")"
preview_html="$preview_dir/katari-agent.html"
"$AIX_BIN" preview examples/katari-agent --html-out "$preview_html"
test -s "$preview_html"
grep -Fq 'pages/index/index.ink' "$preview_html"
wc -c "$preview_html"
```

Do not run a command absent from `--help`. Serve the generated HTML locally and open it in a browser. Record whether it reaches `Preview ready`, lists the exact Page, which state renders without host input, viewport, and console output.

- [ ] **Step 4: Inspect the five-state 480×352 gallery**

Create a temporary browser-only gallery outside `examples/katari-agent/` using the production Page's final copy, hierarchy, colors, spacing, and maximum-length fixtures. Show matched, uncertain, no-story, no-match, and invalid in `_current` and `_blank`; include maximum Japanese and English names. Place every state over bright, dark, and cluttered simulated scenes.

For every scenario, record pass/fail and an observation for:

```text
clipping
hierarchy
status differentiation
information load
```

If a scenario fails, add a focused failing contract or behavior test, make the smallest Page correction, rerun focused tests and strict validation, and repeat the visual inspection. Do not mark revised but uninspected UI as passing.

- [ ] **Step 5: Write final UX evidence**

Create `katari-ux.md` with environment, timestamp, exact AIX command, preview byte count, browser/viewport, state matrix, observations, changes made, and final results. Label the AIX page as runtime preview evidence and the state gallery as supporting visual evidence. State that both are browser evidence only and do not prove authenticated Studio import, host camera/GPS, speech pacing, optics, or physical Rokid Glasses.

- [ ] **Step 6: Verify GREEN and commit UX evidence**

```bash
python3 -m unittest tests.test_katari_agent_contract -v
git add tests/test_katari_agent_contract.py tests/evaluations/katari-ux.md
git commit -m "test: record KATARI UX evidence"
```

Expected: the UX evidence contract and prior tests pass.

### Task 8: Run the complete local release gate

**Files:**
- Modify: `MEMORY.md`
- Modify: `TASKS.md`
- Modify: `WORKLOG.md`
- Modify if final evidence changed: `tests/evaluations/katari-ux.md`

- [ ] **Step 1: Run the full unit suite**

Run `python3 -m unittest discover -s tests -p "test_*.py" -v`.

Expected: zero failures and errors. Record the exact test count from fresh output.

- [ ] **Step 2: Run all strict project validators**

Run the exact `Validate importable AIUI projects strictly` block from the updated CI workflow locally, including KATARI. Expected: every validator exits 0; do not infer other projects pass from KATARI alone.

- [ ] **Step 3: Run references, syntax, YAML, and whitespace gates**

```bash
python3 skills/rokid-aiui-agent/scripts/verify_references.py .
python3 -m py_compile tests/test_katari_agent_contract.py
python3 - <<'PY'
from pathlib import Path
import yaml
for path in (
    Path('.github/workflows/ci.yml'),
    Path('skills/rokid-aiui-agent/agents/openai.yaml'),
):
    yaml.safe_load(path.read_text(encoding='utf-8'))
    print(f'parsed {path}')
PY
git diff --check
```

Expected: references pass, Python and YAML exit 0, and whitespace output is empty.

- [ ] **Step 4: Probe and run AIX pack/list**

With Node `24.19.0` and the lockfile-installed `@yodaos-pkg/aix-cli@0.8.2`, run:

```bash
AIX_BIN="$PWD/node_modules/.bin/aix"
"$AIX_BIN" --help
AIX_BIN="$AIX_BIN" bash skills/rokid-aiui-agent/scripts/smoke_aix.sh examples/katari-agent
```

Expected only when advertised and successful: a non-empty archive whose exact listing includes generated `META-INF/aix/manifest.json`, `app.json`, `AGENTS.md`, `SOURCES.md`, and `pages/index/index.ink`. Record archive byte count and SHA-256. Packaging is not upload or publication.

- [ ] **Step 5: Repeat final preview and browser inspection**

Regenerate preview from the exact final import directory, require non-empty output and the Page path, open it, and inspect the final visible result and console. Update `katari-ux.md` if the artifact or observation changed, then rerun its contract test.

- [ ] **Step 6: Update continuity files**

Record in `MEMORY.md`: stable 0.17 Page-only boundary, 20 source-traceable spots, authored Japanese/English 15–30 second stories, five-state evidence gate, Quiet Marker UI, and local/device evidence separation.

Move KATARI local implementation/testing to Done in `TASKS.md`. Leave authenticated Studio import, real host image/GPS/locale and permission behavior, speech pacing/Page coordination, target transitions, and bright/dark/cluttered physical-glasses readability as unchecked external gates.

Append exact unit count, strict validation, 15 capability results, UX matrix, AIX help/preview/pack/list evidence, artifact size/hash, and remaining gates to `WORKLOG.md`.

- [ ] **Step 7: Verify and commit continuity evidence**

```bash
git diff --check
python3 -m unittest tests.test_katari_agent_contract -v
git add MEMORY.md TASKS.md WORKLOG.md tests/evaluations/katari-ux.md
git commit -m "docs: record KATARI verification"
```

Expected: focused tests pass and only the listed continuity/evidence files enter the commit.

- [ ] **Step 8: Inspect the final branch**

```bash
git status --short
git log --oneline --decorate -12
git diff origin/main...HEAD -- examples/katari-agent tests/test_katari_agent_contract.py tests/evaluations/katari-capability.md tests/evaluations/katari-ux.md .github/workflows/ci.yml README.md PROJECT.md MEMORY.md TASKS.md WORKLOG.md
```

Confirm no `.aix`, generated preview, temporary gallery, credential, downloaded source, or `.superpowers/` file is tracked. Report pre-existing or unrelated changes separately and do not clean them.

### Task 9: Synchronize the verified branch to GitHub

**Files:**
- No source-file changes; this task publishes the already verified Git state.

- [ ] **Step 1: Verify remote and authentication without changing GitHub**

Run `git remote -v`, `gh auth status`, `git status --short`, and `git log -1 --format='%H %s'`. Confirm `origin` is the intended `BreezeLife/rokid-aiui-agent-skill` repository, the branch is `codex/katari-agent`, the KATARI commits are present, and no generated evidence artifact is staged.

- [ ] **Step 2: Re-run the final unit and KATARI strict gates immediately before push**

```bash
python3 -m unittest discover -s tests -p "test_*.py" -v
python3 skills/rokid-aiui-agent/scripts/validate_aiui_project.py examples/katari-agent --target-version 0.17.0 --strict
git diff --check
```

Expected: zero failures/errors, strict validation exit 0, and no whitespace diagnostics.

- [ ] **Step 3: Push the feature branch**

Run `git push -u origin codex/katari-agent`.

Expected: the remote branch resolves to the exact local `HEAD`. Verify with `git ls-remote --heads origin codex/katari-agent` rather than relying only on push text.

- [ ] **Step 4: Observe GitHub Actions for the pushed commit**

Use `gh run list --branch codex/katari-agent --commit "$(git rev-parse HEAD)"` to resolve the run, then `gh run watch <run-id> --exit-status`. Record run ID, commit, conclusion, and both job conclusions. A queued or failing run is not synchronized release evidence.

- [ ] **Step 5: Complete the branch through the required finishing workflow**

Invoke `finishing-a-development-branch`, present its integration options, and follow the user's choice. If the chosen route updates public `main`, verify the remote `main` commit, the KATARI import directory through GitHub, and the `main` CI run before reporting public-main synchronization. Do not claim that a feature-branch push made the README's `Ref: main` coordinates live.

## Completion report requirements

The final handoff includes:

- absolute local Studio import path and target AIUI `0.17.0`;
- exact accepted spot and capability-case counts;
- unit count and strict-validator result;
- AIX version/capabilities, preview result, package size/hash, and exact listing;
- UX findings for all five states and both targets;
- links to capability and UX evidence records;
- pushed GitHub branch, exact remote commit, and GitHub Actions run/conclusion;
- explicit Studio, host context, speech, optics, and physical-device manual gates;
- no claim that local browser or prompt-contract evidence proves those external gates.
