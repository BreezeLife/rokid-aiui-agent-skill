# SceneQuest ROKID AIUI Agent Design

**Date:** 2026-09-09  
**Status:** Implemented and locally verified
**Target:** AIUI 0.17 stable compatibility  
**Product name:** SceneQuest / セイチ｜SEICHI

## 1. Product definition

SceneQuest identifies whether the real place in front of the user is related to
an anime, manga, or game scene. It connects the real location to a verified
work and scene, briefly explains the story relationship, guides the user toward
a comparable photo composition, and recommends one to three nearby recorded
spots.

The product loop is:

> Reality → Anime Scene → Story → Next Spot

The first release is a demonstrable, curated MVP rather than a general Japan
anime-location search engine. The initial catalog contains exactly 12 verified
Osaka spots and is structured so later catalogs can cover other
Japanese cities.

## 2. Confirmed product decisions

- The host supplies available camera imagery, GPS/current-location context,
  the user's spoken question, and an optional work or character constraint to
  the Agent.
- The Agent performs candidate selection, visual reasoning, confidence
  assessment, and response orchestration.
- A single AIUI Page displays the structured result. It does not directly
  capture imagery or location in this MVP.
- The default user-facing language is Japanese. Official work titles and place
  names retain their canonical spelling.
- Invocation is user initiated. The MVP does not implement background
  geofencing or automatic pop-ups.
- Photo guidance combines curated reference positions with tolerant visual
  adjustment. It may give coarse directional guidance when visual evidence is
  sufficient and otherwise falls back to the curated position.
- Copyrighted anime screenshots are not packaged. The catalog stores verified
  metadata, scene descriptions, visual composition features, and source
  records.
- The project is Page-only and defaults to AIUI 0.17. It does not introduce
  0.18-only Widgets or Agent Workers.

## 3. Scope

### 3.1 In scope

- Recognize recorded buildings, streets, bridges, stations, shrines, stores,
  and other stable real-world landmarks from host-provided context.
- Combine GPS and visual features to rank only catalog candidates.
- Match a work and a verified episode, chapter, or scene descriptor.
- Explain the location, work, story connection, and pilgrimage value briefly.
- Give a curated photo position and, when supported by the current image, a
  tolerant left/right/forward/backward or viewing-direction adjustment.
- Recommend one to three nearby recorded spots when valid location data is
  available.
- Handle matched, uncertain, no-match, and invalid-input states without
  inventing facts or leaving the Page blank.
- Support a compact conversation-hosted `_current` view and a richer `_blank`
  view from the same Page and the same business state.

### 3.2 Out of scope

- General anime knowledge, anime news, or character chat.
- Nationwide open-ended image search or claims of comprehensive coverage.
- Background location monitoring, geofencing, or unsolicited notifications.
- Complex city-scale AR navigation, pixel-perfect live overlay, or metric
  movement estimates without reliable scale evidence.
- Automatically generated or weakly sourced pilgrimage locations.
- Bundled anime frames or other copyrighted production images.
- Claims that browser preview proves Studio import, permissions, host context,
  camera/GPS behavior, optics, or physical-glasses UX.

## 4. Architecture

SceneQuest uses Agent orchestration and one result Page.

1. The host provides any available image, location, voice question, and user
   constraint to the Agent.
2. The Agent normalizes the request and filters catalog candidates by location
   when location is present.
3. The Agent compares observable visual anchors and applies any work/character
   constraint as a filter, never as evidence of a match.
4. The Agent chooses one of four result states and prepares a strict Page input
   object.
5. The Page validates the object again, derives safe presentation state, and
   renders target-aware density.
6. The Agent supplies the longer Japanese explanation through the conversation
   voice response. The Page stays concise and does not duplicate an
   encyclopedia answer.

The Page is presentation and lightweight interaction, not the source of match
truth. Raw imagery is not passed into the Page input. Business truth does not
change when the host changes between `_current` and `_blank`; only visible
density changes.

## 5. Components and repository structure

The implementation adds a complete Studio-importable source project:

```text
examples/scenequest-agent/
├── AGENTS.md
├── SOURCES.md
├── app.js
├── app.json
└── pages/
    └── index/
        └── index.ink
```

- `AGENTS.md` defines the SceneQuest identity, Japanese response policy,
  triggers, matching discipline, confidence rules, anti-hallucination rules,
  Page invocation contract, and the compact runtime facts required for the
  curated catalog.
- `SOURCES.md` is the developer-facing evidence registry. It records source
  URLs, source class, verification date, and uncertainty for every formal spot.
  The runtime must not depend on undocumented automatic loading of this file.
  Contract tests keep its 12 spot IDs synchronized with the runtime facts in
  `AGENTS.md`.
- `app.json` declares the single Page and minimal global configuration.
- `app.js` contains only required application lifecycle/shared state.
- `pages/index/index.ink` owns the Page schema, input normalization, state
  derivation, target-aware markup, focus behavior, and monochrome styling.

The repository also adds `tests/test_scenequest_agent_contract.py`. Existing
project validation and AIX smoke paths are extended only where SceneQuest needs
coverage; unrelated examples and Skill behavior are not refactored.

## 6. Curated spot record

Every formal spot must have these fields in the authored catalog:

- stable `spotId`;
- canonical Japanese place name and city;
- latitude, longitude, and a deliberately chosen candidate radius;
- observable visual anchors that remain useful without an anime screenshot;
- canonical work title and media type;
- episode, chapter, or a clearly labeled `未特定` value when a precise unit
  cannot be verified;
- one-sentence story connection and pilgrimage significance;
- curated standing position, viewing direction, tolerance, and safety note;
- related nearby spot IDs;
- source URLs, source classes, verification date, and any uncertainty note.

A spot is excluded when the real place, work connection, or claimed episode /
chapter cannot be supported by traceable evidence. Third-party pilgrimage
indexes may identify research leads but are labeled non-authoritative and do
not independently establish a fact.

## 7. Agent input and Page contract

Agent context may contain:

- current camera image;
- current latitude/longitude or a human-readable location;
- the user's spoken question;
- an optional work or character name.

All fields are optional individually because host capability and permissions
may vary. The Agent must not claim a source was present when it was absent.
When none of image, location, place/work constraint, or usable question text is
available, the Agent returns the `invalid` recovery flow.

The Page accepts a bounded JSON-serializable object with:

- `status`: `matched`, `uncertain`, `no_match`, or `invalid`;
- `workTitle`;
- `episodeScene`;
- `storyLine`;
- `photoGuidance`;
- `confidenceLabel`;
- `nearbySpots`: zero to three compact entries.

Each nearby entry contains a `spotId`, Japanese `name`, `distanceLabel`, and
`directionHint`. `distanceLabel` is empty when distance has not been derived
from valid location data. No other entry shape is accepted by the Page.

The implementation sets explicit string-length and array-count limits in the
Page schema and runtime normalizer. State-specific fields may be empty, but the
normalizer supplies safe Japanese fallback copy. Unknown status values and
wrong field types become `invalid` rather than being rendered directly.

## 8. Matching and confidence policy

Location narrows candidates; it does not prove a match. Visual anchors rank the
remaining candidates. A user-specified work or character narrows the search
space and never forces a result.

- `matched`: location and multiple distinctive visual anchors agree, or an
  equivalently strong set of catalog evidence is present.
- `uncertain`: evidence is partial, candidates conflict, or a decisive anchor
  is missing. The Agent asks for one concrete additional observation or image
  adjustment at most once.
- `no_match`: the retry remains inconclusive, location and visual evidence
  conflict, or no catalog entry fits.
- `invalid`: the request cannot be safely normalized into a supported flow.

The Agent does not expose a fake precision score. Japanese confidence labels
are categorical and explain what evidence is missing when uncertain.

Dynamic photo guidance is deliberately tolerant. It may state coarse movement
or camera direction when visible anchors support that advice. It must not emit
an exact number of meters unless the distance comes from a curated, verified
reference or reliable host-provided measurement. Low-quality, occluded, or
ambiguous imagery falls back to the curated position.

## 9. UX design

### 9.1 `_current`

The conversation-hosted first view displays only:

1. work title;
2. episode or scene;
3. one sentence of story context;
4. one photo-direction instruction.

It may include a short categorical confidence label but no dense evidence,
route list, long synopsis, or repeated metadata.

### 9.2 `_blank`

The expanded view retains the same match truth and may add:

- the current composition adjustment;
- one to three nearby spots with distance or walking estimate only when that
  value is supported;
- short explanatory or safety text.

Long content uses the documented scrolling component. The primary photo
direction remains visible and is not displaced by the nearby list.

### 9.3 Error and recovery states

- `uncertain`: says that more evidence is needed, gives one specific viewing or
  capture request, and does not visually resemble a confirmed match.
- `no_match`: explicitly says that no recorded scene was found. It offers the
  nearest recorded spot only when valid location is available.
- missing location: permits work/place-name exploration without implying that
  distance sorting occurred.
- missing image: gives only the curated position or asks for a view when visual
  confirmation is essential.
- `invalid`: presents a short Japanese retry path and never exposes raw input.

### 9.4 Visual and interaction rules

- Use the low-mass monochrome-green direction: 1 px normal structural lines,
  2 px only for strong focus, 4 px control radius, 6 px panel/group radius, and
  restrained local fill.
- Keep essential content in the comfortable optical field and avoid stacked
  decorative cards.
- Do not encode state through luminance alone; pair labels, structure, and
  copy with focus styling.
- Every actionable nearby entry has its own focus and blur behavior.
- Default host key behavior is not intercepted unless the Page provides a
  complete replacement.
- Motion, if any, is short and event driven. The MVP has no ambient animation.

## 10. Verification design

### 10.1 Automated contract tests

Tests cover:

- required project files, route resolution, and Page-only AIUI 0.17 scope;
- Agent identity, Japanese policy, supported triggers, retry limit, and explicit
  non-goals;
- all four states and unknown-state degradation;
- absent, malformed, overlong, and wrong-type Page fields;
- Unicode code-point limits and a maximum of three nearby spots;
- work/character constraints that do not force a match;
- conflicting location/visual evidence producing uncertainty or no-match;
- no exact movement claim without verified scale evidence;
- no recommendation of the current spot as its own next spot;
- complete source metadata for every formal catalog entry;
- `_current` / `_blank` density and independently focusable actions.

### 10.2 Local delivery gates

Run the complete repository unit suite, strict validation against target
`0.17.0`, reference checks, and syntax/whitespace checks. Probe the installed or
lockfile-resolved AIX CLI with `aix --help`; use only advertised commands. When
available, run `pack`, inspect the exact artifact with `list`, and generate a
browser preview.

Browser visual QA covers matched, uncertain, no-match, invalid, missing-field,
long-Japanese-text, and empty-nearby states in both target densities. It also
checks layout against representative bright, dark, and cluttered backgrounds,
while explicitly recording that this is not physical-optics evidence.

### 10.3 External manual gates

The following remain unverified until executed in their real environments:

- authenticated AIUI Studio import and Web simulation;
- host delivery of camera and GPS context;
- permission grant, denial, revocation, and missing-capability behavior;
- Japanese voice response and Page invocation coordination;
- `_current` / `_blank` focus and target transitions;
- real-glasses readability on bright, dark, and cluttered backgrounds;
- dynamic visual guidance under occlusion, viewpoint variation, and motion;
- final device performance and release review.

No local result may be reported as passing one of these external gates.

## 11. Acceptance criteria

The implementation is locally complete when:

1. `examples/scenequest-agent/` is a self-contained AIUI Studio import root.
2. The Agent follows the four-state confidence policy and responds in Japanese.
3. The Page renders bounded, safe output for every supported or malformed
   input state.
4. `_current` contains only the core answer and `_blank` adds optional nearby
   exploration without changing match truth.
5. The Osaka catalog contains exactly 12 source-traceable spots and
   no bundled anime screenshots.
6. The full local test and validation flow passes.
7. AIX packaging/listing and browser-preview evidence are recorded when the
   probed CLI supports them.
8. Unexecuted Studio and physical-device gates are reported as unverified.

## 12. Authoritative platform references

- [AIUI 0.17 Page overview](https://github.com/yodaos-project/AIUI/blob/88e70bb0382525c1a93ef077c2401dcc31a273ce/documentation/1-framework/open-agent-format/page.en-US.md)
- [AIUI 0.17 Page definition](https://github.com/yodaos-project/AIUI/blob/88e70bb0382525c1a93ef077c2401dcc31a273ce/documentation/1-framework/open-agent-format/page-definition.en-US.md)
- [AIUI 0.17 AGENTS.md specification](https://github.com/yodaos-project/AIUI/blob/88e70bb0382525c1a93ef077c2401dcc31a273ce/documentation/1-framework/open-agent-format/agents.en-US.md)
- [AIUI 0.17 quickstart and verification flow](https://github.com/yodaos-project/AIUI/blob/88e70bb0382525c1a93ef077c2401dcc31a273ce/documentation/0-guide/quickstart/quickstart.md)
- [AIUI 0.17 stable source tree](https://github.com/yodaos-project/AIUI/tree/88e70bb0382525c1a93ef077c2401dcc31a273ce)
