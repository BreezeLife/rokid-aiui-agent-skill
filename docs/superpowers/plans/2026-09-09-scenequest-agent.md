# SceneQuest Agent Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Deliver a Japanese SceneQuest MVP as a complete stable-AIUI-0.17 Studio-importable Page project with exactly 12 source-traceable Osaka pilgrimage spots, bounded confidence behavior, tolerant photo guidance, and recorded UX/capability evidence.

**Architecture:** The Agent consumes host-provided image, location, and question context, reasons only over curated facts embedded in `AGENTS.md`, and invokes one Page with a bounded JSON result. The Page does not capture camera or GPS directly; it validates the result again, renders compact `_current` and expanded `_blank` views, and supports focused selection of up to three nearby spots.

**Tech Stack:** AIUI 0.17 `.ink`, Open Agent Format, JavaScript, Python `unittest`, Node.js 24 behavior harness, repository validator, `@yodaos-pkg/aix-cli@0.8.2`.

---

## File map

- Create `examples/scenequest-agent/AGENTS.md`: identity, Japanese prompts, triggers, confidence policy, Page contract, and 12 compact runtime records.
- Create `examples/scenequest-agent/SOURCES.md`: evidence registry for the same 12 spot IDs.
- Create `examples/scenequest-agent/app.js`: dependency-free entry.
- Create `examples/scenequest-agent/app.json`: one Page route.
- Create `examples/scenequest-agent/pages/index/index.ink`: schema, normalization, result UI, nearby selection, and target-aware styling.
- Create `tests/test_scenequest_agent_contract.py`: catalog, Agent, schema, behavior, UX, and delivery contracts.
- Modify `.github/workflows/ci.yml`, `README.md`, and `PROJECT.md`: integrate validation, AIX, preview, and handoff documentation.
- Modify `MEMORY.md`, `TASKS.md`, `WORKLOG.md`: preserve decisions, status, evidence, and manual gates.

### Task 1: Build a source-gated 12-spot catalog

**Files:**
- Create: `tests/test_scenequest_agent_contract.py`
- Create: `examples/scenequest-agent/SOURCES.md`

- [ ] **Step 1: Write the failing source contract**

```python
from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
EXAMPLE = ROOT / "examples" / "scenequest-agent"
INK = EXAMPLE / "pages" / "index" / "index.ink"
VALIDATOR = ROOT / "skills" / "rokid-aiui-agent" / "scripts" / "validate_aiui_project.py"
SOURCE_SPOT = re.compile(r"^## Spot: ([a-z0-9-]+)$", re.MULTILINE)

def read_example(relative: str) -> str:
    path = EXAMPLE / relative
    if not path.is_file():
        raise AssertionError(f"missing SceneQuest file: {relative}")
    return path.read_text(encoding="utf-8")

class SceneQuestAgentContractTests(unittest.TestCase):
    def test_source_registry_has_twelve_complete_spots(self) -> None:
        sources = read_example("SOURCES.md")
        ids = SOURCE_SPOT.findall(sources)
        self.assertEqual(len(ids), 12)
        self.assertEqual(len(set(ids)), 12)
        sections = re.split(r"(?=^## Spot: )", sources, flags=re.MULTILINE)[1:]
        for section in sections:
            for label in (
                "- Place:", "- Coordinates:", "- Work:", "- Media:",
                "- Episode/chapter/scene:", "- Visual anchors:",
                "- Photo position:", "- Safety:", "- Sources:",
                "- Source class:", "- Verified:", "- Uncertainty:",
            ):
                self.assertIn(label, section)
            self.assertRegex(section, r"https://")
            self.assertRegex(section, r"- Verified: 2026-\d{2}-\d{2}")
            self.assertNotRegex(section, r"\b(?:TBD|TODO|unknown)\b")
```

- [ ] **Step 2: Verify RED**

Run `python3 -m unittest tests.test_scenequest_agent_contract -v`.

Expected: failure reports `missing SceneQuest file: SOURCES.md`.

- [ ] **Step 3: Research and accept exactly 12 Osaka records**

For each candidate, verify place identity/coordinates through an official
venue, municipality, tourism board, station, or shrine source plus an
independent map source. Verify the work relationship through the publisher,
studio, game publisher, licensed campaign/exhibition, municipal collaboration,
or reputable reporting. Third-party pilgrimage indexes can identify leads but
cannot establish a fact alone.

Reject candidates with an untraceable relationship. Use `未特定` when the work
relationship is supported but the episode/chapter is not. Check every photo
position for public access, traffic, private-property, crowd, and station-flow
risk. Do not bundle anime screenshots or quote source prose.

- [ ] **Step 4: Write all accepted records in one exact format**

Each section heading is `## Spot:` followed by its actual stable lowercase
Osaka ID. Under it, write the labels asserted by the test with the verified
canonical Japanese name/full address, numeric coordinates and integer radius,
canonical work title, one of the three media values, verified unit or
`未特定`, at least two anchors, public photo position/direction/tolerance,
specific safety constraint, direct HTTPS URLs and their source classes, the
actual 2026 verification date, and one precisely bounded uncertainty statement.

The introduction states that no anime frames are bundled and access conditions
may change. All 12 records contain actual verified values rather than template
or example tokens.

- [ ] **Step 5: Verify GREEN and commit**

Run `python3 -m unittest tests.test_scenequest_agent_contract -v`; expect `OK`.

```bash
git add tests/test_scenequest_agent_contract.py examples/scenequest-agent/SOURCES.md
git commit -m "test: define SceneQuest source catalog"
```

### Task 2: Add the importable Agent shell

**Files:**
- Modify: `tests/test_scenequest_agent_contract.py`
- Create: `examples/scenequest-agent/AGENTS.md`
- Create: `examples/scenequest-agent/app.js`
- Create: `examples/scenequest-agent/app.json`
- Create: `examples/scenequest-agent/pages/index/index.ink`

- [ ] **Step 1: Add failing import and Agent assertions**

```python
def test_import_root_and_agent_policy(self) -> None:
    expected = {
        "AGENTS.md", "SOURCES.md", "app.js", "app.json",
        "pages/index/index.ink",
    }
    actual = {
        path.relative_to(EXAMPLE).as_posix()
        for path in EXAMPLE.rglob("*") if path.is_file()
    }
    self.assertEqual(actual, expected)
    manifest = json.loads(read_example("app.json"))
    self.assertEqual(manifest["pages"], ["pages/index/index"])
    self.assertNotIn("widgets", manifest)
    self.assertNotIn("agentWorkers", manifest)
    agents = read_example("AGENTS.md")
    runtime_ids = re.findall(
        r"^### Catalog Spot: ([a-z0-9-]+)$", agents, re.MULTILINE
    )
    self.assertEqual(runtime_ids, SOURCE_SPOT.findall(read_example("SOURCES.md")))
    for fragment in (
        "# Agent: SceneQuest", "セイチ｜SEICHI", "日本語",
        "matched", "uncertain", "no_match", "invalid", "最大1回",
        "_current", "_blank", "アニメ画像を同梱しない",
        "バックグラウンド位置監視を行わない", "全国対応を主張しない",
        "ここはどのアニメに出てくる？", "聖地巡礼",
        "近くのアニメスポット",
    ):
        self.assertIn(fragment, agents)
```

- [ ] **Step 2: Verify RED**

Run `python3 -m unittest tests.test_scenequest_agent_contract -v`.

Expected: import/Agent assertions fail on missing files.

- [ ] **Step 3: Create the stable Page-only manifest and entry**

`app.json`:

```json
{
  "pages": ["pages/index/index"],
  "window": { "navigationBarTitleText": "セイチ" }
}
```

`app.js`:

```js
export default {};
```

- [ ] **Step 4: Write the runtime Agent rules and catalog**

Use the standard `Meta Information`, `System Prompts`, `Capabilities`,
`Configuration`, and `Dependencies` sections. The prompt must enforce this
sequence:

```text
Location narrows candidates but never proves a match. Compare at least two
distinctive visual anchors unless supplied evidence is equivalently decisive.
A requested work/character filters candidates but cannot force a match.
Conflicting or partial evidence becomes uncertain and asks for one concrete
additional view at most once. A failed retry or persistent contradiction becomes
no_match. Never invent a spot, unit, distance, or source; never interpret a
catalog miss as proof that no work has ever used the location. Exact movement
distance requires catalog or host measurement evidence. Respond in concise
Japanese and invoke a fresh Page for each new result.
```

Copy only verified runtime facts from each source record into a matching
`### Catalog Spot:` heading followed by the same actual spot ID. Include location/radius, work/unit, anchors,
one-line story, photo position/tolerance/safety, and nearby IDs. State all
non-goals explicitly and do not claim that the Page captures camera/GPS.

- [ ] **Step 5: Add a valid placeholder Page and verify GREEN**

```html
<script def>
{
  "navigationBarTitleText": "セイチ",
  "description": "聖地照合結果を短く表示します。",
  "schema": { "data": { "type": "object", "properties": {} } }
}
</script>
<script setup>export default { data: {} };</script>
<page><text>セイチ</text></page>
<style>page { color: #40ff5e; background-color: #000000; }</style>
```

Run:

```bash
python3 -m unittest tests.test_scenequest_agent_contract -v
python3 skills/rokid-aiui-agent/scripts/validate_aiui_project.py examples/scenequest-agent --target-version 0.17.0 --strict
```

Expected: both pass. Commit:

```bash
git add examples/scenequest-agent tests/test_scenequest_agent_contract.py
git commit -m "feat: add SceneQuest agent shell"
```

### Task 3: Implement bounded Page capability behavior

**Files:**
- Modify: `tests/test_scenequest_agent_contract.py`
- Modify: `examples/scenequest-agent/pages/index/index.ink`

- [ ] **Step 1: Add failing schema and real-Page behavior tests**

Parse `<script def>` and assert exact bounds: `workTitle` 64,
`episodeScene` 72, `storyLine` 100, `photoGuidance` 80,
`confidenceLabel` 16, and `nearbySpots.maxItems` 3. Each nearby object requires
`spotId`, `name`, `distanceLabel`, and `directionHint` with bounds 40/48/16/48.

Extract `<script setup>` into a temporary `page.mjs`, import it with Node, mount
a Page using a fake `setData`, and emit snapshots for:

```js
const inputs = {
  matched: validMatched(),
  uncertain: { status: 'uncertain', photoGuidance: '駅名が入るよう左を向く', confidenceLabel: '要確認', nearbySpots: [] },
  noMatch: { status: 'no_match', nearbySpots: [] },
  explicitInvalid: { status: 'invalid', workTitle: '表示してはいけない入力' },
  nullRoot: null,
  arrayRoot: [],
  unknownStatus: { status: 'certain' },
  longTitle: { ...validMatched(), workTitle: 'あ'.repeat(65) },
  emojiLimit: { ...validMatched(), workTitle: '😀'.repeat(64) },
  fourNearby: { status: 'no_match', nearbySpots: Array(4).fill(validNearby()) },
  malformedNearby: { status: 'no_match', nearbySpots: [{ name: '欠落' }] },
};
```

Assert valid states remain, whitespace is trimmed, emoji limit is valid, and
all malformed cases become the Japanese `invalid` fallback without exposing
caller-provided invalid text.

- [ ] **Step 2: Verify RED**

Run `python3 -m unittest tests.test_scenequest_agent_contract -v`.

Expected: schema and normalization assertions fail against the placeholder.

- [ ] **Step 3: Implement exact schema and normalizer**

Use one `schema.data` object with the exact limits above. Implement these core
helpers inside `<script setup>`:

```js
const LIMITS = {
  workTitle: 64, episodeScene: 72, storyLine: 100,
  photoGuidance: 80, confidenceLabel: 16, spotId: 40,
  nearbyName: 48, distanceLabel: 16, directionHint: 48
};
const STATUSES = ['matched', 'uncertain', 'no_match', 'invalid'];

function unicodeLength(value) { return Array.from(value).length; }
function boundedString(value, limit) {
  if (typeof value !== 'string' || unicodeLength(value) > limit) return null;
  return value.trim();
}
function invalidResult() {
  return {
    state: 'invalid', workTitle: '場所を確認できません', episodeScene: '',
    storyLine: '作品名または場所を変えて、もう一度聞いてください。',
    photoGuidance: '会話に戻って再確認してください。',
    confidenceLabel: '入力不足', nearbySpots: [],
    selectedNearbyIndex: -1, focusedNearbyIndex: -1,
    selectedNearbyName: '', selectedNearbyHint: ''
  };
}
```

`normalizeNearby()` rejects non-arrays, more than three entries, missing keys,
wrong types, overlong fields, empty `spotId`/`name`/`directionHint`, and permits
an empty `distanceLabel`. `normalizeInput()` rejects non-object roots and
unknown states. `matched` requires all four display strings; `uncertain`
requires guidance; `no_match` permits empty descriptive strings; explicit
`invalid` always uses `invalidResult()`.

Export JSON-serializable initial data and call `this.setData(normalizeInput(query))`
once in `onLoad(query)`.

- [ ] **Step 4: Verify GREEN and commit**

```bash
python3 -m unittest tests.test_scenequest_agent_contract -v
python3 skills/rokid-aiui-agent/scripts/validate_aiui_project.py examples/scenequest-agent --target-version 0.17.0 --strict
git add tests/test_scenequest_agent_contract.py examples/scenequest-agent/pages/index/index.ink
git commit -m "feat: validate SceneQuest result state"
```

Expected: tests and validator pass before commit.

### Task 4: Implement and test the target-aware UX

**Files:**
- Modify: `tests/test_scenequest_agent_contract.py`
- Modify: `examples/scenequest-agent/pages/index/index.ink`

- [ ] **Step 1: Add failing UX and interaction assertions**

Assert one `scroll-view`, one nearby loop, and all nearby buttons bind
`selectNearby`, `focusNearby`, and `blurNearby`. Assert `_current` hides
`.expanded-only`, `_blank` displays it, the persistent photo guidance sits
outside the scrolling list, normal borders are 1px, focused borders are 2px,
controls include 4px radius, and the outer group includes 6px radius.

Extend the Node harness:

```js
page.focusNearby({ currentTarget: { dataset: { index: '1' } } });
const focused = page.data.focusedNearbyIndex;
page.selectNearby({ currentTarget: { dataset: { index: '1' } } });
const selected = [page.data.selectedNearbyIndex, page.data.selectedNearbyName, page.data.selectedNearbyHint];
page.blurNearby();
const blurred = page.data.focusedNearbyIndex;
page.selectNearby({ currentTarget: { dataset: { index: '99' } } });
const afterInvalidTap = page.data.selectedNearbyIndex;
```

Expect focus `1`, selection from the second normalized record, blur `-1`, and
no change after the invalid tap.

- [ ] **Step 2: Verify RED**

Run `python3 -m unittest tests.test_scenequest_agent_contract -v`.

Expected: missing markup, media-query, and handler assertions fail.

- [ ] **Step 3: Implement Japanese four-state markup**

Use one Page with top label `SEICHI`, categorical confidence, work title,
episode/scene, one story line, and a persistent `PHOTO GUIDE`. Add state labels
`一致`, `要確認`, `登録なし`, and `入力不足`. Put only the nearby list and selected
hint in an `_blank`-only scrollable region. Do not add a route/navigation claim,
camera/GPS API, network, storage, timer, key interception, or ambient animation.

- [ ] **Step 4: Implement guarded nearby focus and selection**

```js
function eventIndex(event) {
  const value = event && event.currentTarget && event.currentTarget.dataset
    ? event.currentTarget.dataset.index : undefined;
  const index = Number(value);
  return Number.isInteger(index) ? index : -1;
}

focusNearby(event) {
  const index = eventIndex(event);
  if (index < 0 || index >= this.data.nearbySpots.length) return;
  this.setData({ focusedNearbyIndex: index });
},
blurNearby() { this.setData({ focusedNearbyIndex: -1 }); },
selectNearby(event) {
  const index = eventIndex(event);
  if (index < 0 || index >= this.data.nearbySpots.length) return;
  const spot = this.data.nearbySpots[index];
  this.setData({
    selectedNearbyIndex: index,
    selectedNearbyName: spot.name,
    selectedNearbyHint: spot.directionHint
  });
}
```

Merge these into the existing default export.

- [ ] **Step 5: Apply the stable-compatible visual grammar**

Use the repository's black/green palette, 1px normal structure, 2px only for
strong focus, 4px controls, 6px group radius, sparse fill, no nested decorative
cards, and labels plus shape/structure so state is not luminance-only. Keep the
photo guide visible when nearby content scrolls.

- [ ] **Step 6: Verify GREEN and commit**

```bash
python3 -m unittest tests.test_scenequest_agent_contract -v
python3 skills/rokid-aiui-agent/scripts/validate_aiui_project.py examples/scenequest-agent --target-version 0.17.0 --strict
git add tests/test_scenequest_agent_contract.py examples/scenequest-agent/pages/index/index.ink
git commit -m "feat: add SceneQuest result experience"
```

### Task 5: Integrate repository delivery gates

**Files:**
- Modify: `tests/test_scenequest_agent_contract.py`
- Modify: `.github/workflows/ci.yml`
- Modify: `README.md`
- Modify: `PROJECT.md`

- [ ] **Step 1: Add failing repository-integration assertions**

Load CI with PyYAML and assert SceneQuest appears in strict validation,
`smoke_aix.sh`, and a blocking step named `Generate the SceneQuest Agent static
preview`. Assert README contains `SceneQuest / セイチ｜SEICHI`,
`examples/scenequest-agent`, `Directory: examples/scenequest-agent`, the
host-provided camera/GPS boundary, and physical-device limitations.

- [ ] **Step 2: Verify RED**

Run `python3 -m unittest tests.test_scenequest_agent_contract -v`.

Expected: CI/README assertions fail.

- [ ] **Step 3: Add exact CI commands**

Add to strict validation and pack/list respectively:

```bash
python skills/rokid-aiui-agent/scripts/validate_aiui_project.py examples/scenequest-agent --target-version 0.17.0 --strict
bash skills/rokid-aiui-agent/scripts/smoke_aix.sh examples/scenequest-agent
```

Add this blocking preview step:

```yaml
- name: Generate the SceneQuest Agent static preview
  shell: bash
  env:
    AIX_BIN: ${{ github.workspace }}/node_modules/.bin/aix
  run: |
    set -euo pipefail
    preview_html="$RUNNER_TEMP/scenequest-agent-preview.html"
    "$AIX_BIN" --help | grep -Eq '(^|[[:space:]])preview([[:space:]<]|$)'
    "$AIX_BIN" preview examples/scenequest-agent --html-out "$preview_html"
    test -s "$preview_html"
    grep -Fq 'pages/index/index.ink' "$preview_html"
```

- [ ] **Step 4: Document handoff and local commands**

Describe the exact 12-spot Japanese MVP, four states, copyright boundary,
Agent-side host context, and unverified Studio/device gates. Document:

```text
Repository: https://github.com/BreezeLife/rokid-aiui-agent-skill
Ref: main
Directory: examples/scenequest-agent
```

Add SceneQuest validation, smoke, and preview commands to README and add the
example to `PROJECT.md` without changing existing principles.

- [ ] **Step 5: Verify GREEN and commit**

```bash
python3 -m unittest tests.test_scenequest_agent_contract -v
python3 -m unittest discover -s tests -p "test_*.py" -v
git add .github/workflows/ci.yml README.md PROJECT.md tests/test_scenequest_agent_contract.py
git commit -m "test: integrate SceneQuest delivery gates"
```

### Task 6: Run UX and capability verification

**Files:**
- Modify tests/Page only when an executed check exposes a defect.

- [ ] **Step 1: Probe the actual toolchain**

```bash
python3 -m pip install --only-binary=:all: -r requirements-dev.txt
npm ci --ignore-scripts --no-audit --no-fund
AIX_BIN="$PWD/node_modules/.bin/aix"
export AIX_BIN
node --version
"$AIX_BIN" --help
```

Record actual versions and require advertised `preview`, `pack`, and `list`/`ls`.

- [ ] **Step 2: Run automated capability tests**

```bash
python3 -m unittest discover -s tests -p "test_*.py" -v
python3 skills/rokid-aiui-agent/scripts/validate_aiui_project.py examples/scenequest-agent --target-version 0.17.0 --strict
python3 skills/rokid-aiui-agent/scripts/verify_references.py .
git diff --check
```

This gate must cover all four result states, malformed/missing/overlong fields,
Unicode limits, zero/three/four nearby entries, independent focus/blur, invalid
selection, one-retry Agent policy, catalog/source synchronization, and the
absence of direct Page camera/GPS/network/storage/background behavior.

- [ ] **Step 3: Pack, list, and preview the exact import root**

```bash
bash skills/rokid-aiui-agent/scripts/smoke_aix.sh examples/scenequest-agent
scenequest_preview_dir="$(mktemp -d "${TMPDIR:-/tmp}/scenequest-preview.XXXXXX")"
scenequest_preview_html="$scenequest_preview_dir/scenequest-agent.html"
"$AIX_BIN" preview examples/scenequest-agent --html-out "$scenequest_preview_html"
test -s "$scenequest_preview_html"
grep -Fq 'pages/index/index.ink' "$scenequest_preview_html"
```

Record artifact listing/size/checksum and preview size. These prove local
packaging/basic rendering only.

- [ ] **Step 4: Perform the UX matrix**

Inspect `matched`, `uncertain`, `no_match`, `invalid`, long-valid Japanese,
zero nearby, and three nearby in both `_current` and `_blank`. For each, check
clipping, overlap, readable hierarchy, persistent photo guide, scroll behavior,
focus visibility, and truthful recovery text. Repeat representative cases over
dark, bright, and cluttered simulated backgrounds. Record failures explicitly.

- [ ] **Step 5: Preserve the physical capability matrix as manual gates**

Do not convert browser results into passes for authenticated Studio import,
host camera/GPS delivery, first permission grant, denial/revocation, Japanese
voice/Page coordination, host focus, target transitions, optics, occlusion,
viewpoint variation, motion, or continuous-use performance. Record each as
`not tested` until exercised on supported Rokid Glasses.

- [ ] **Step 6: Fix evidence-backed defects through RED/GREEN**

For every defect, add a focused failing assertion first, apply the smallest
Page/Agent change, rerun focused/full tests, and commit only if a defect exists:

```bash
git add tests/test_scenequest_agent_contract.py examples/scenequest-agent
git commit -m "fix: harden SceneQuest UX and capability fallbacks"
```

### Task 7: Record continuity and final evidence

**Files:**
- Modify: `MEMORY.md`
- Modify: `TASKS.md`
- Modify: `WORKLOG.md`
- Modify: `docs/superpowers/specs/2026-09-09-scenequest-agent-design.md`

- [ ] **Step 1: Update durable project state**

Change the design status to `Implemented and locally verified` only after local
gates pass. Record the 12-spot Osaka boundary, Agent-side host context, one
bounded Page, categorical confidence, one retry, no bundled anime frames, and
no background geofencing in `MEMORY.md`. Mark local tasks done and add separate
unchecked Studio, camera/GPS, permission, voice, target, and physical-glasses
gates in `TASKS.md`.

- [ ] **Step 2: Record exact evidence**

In `WORKLOG.md`, record the test count, validator result, resolved Node/AIX
evidence, archive listing/bytes/checksum, preview bytes, UX states/backgrounds
inspected, warnings, and every unexecuted external gate.

- [ ] **Step 3: Run the final gate**

```bash
python3 -m unittest discover -s tests -p "test_*.py" -v
python3 skills/rokid-aiui-agent/scripts/validate_aiui_project.py examples/scenequest-agent --target-version 0.17.0 --strict
python3 skills/rokid-aiui-agent/scripts/verify_references.py .
bash skills/rokid-aiui-agent/scripts/smoke_aix.sh examples/scenequest-agent
git diff --check
git status --short
```

Expected: all verification commands pass; status shows only intended continuity
changes and the untracked brainstorming companion, never unrelated source edits.

- [ ] **Step 4: Commit and hand off**

```bash
git add MEMORY.md TASKS.md WORKLOG.md docs/superpowers/specs/2026-09-09-scenequest-agent-design.md
git commit -m "docs: record SceneQuest delivery evidence"
```

Report the absolute Studio import folder, source commit, exact local results,
AIX evidence, and GitHub coordinates. List Studio and physical-device work as
manual gates until actually executed.
