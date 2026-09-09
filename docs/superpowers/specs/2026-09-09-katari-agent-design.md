# KATARI ROKID AIUI Agent Design

**Date:** 2026-09-09

**Status:** Approved concept; awaiting written-spec review

**Target:** AIUI 0.17 stable compatibility

**Product name:** KATARI / カタリ

**Slogan:** Every place has a story. Just look.

## 1. Product definition

KATARI is a lightweight local-story Agent for Rokid Glasses. It identifies a
place, building, street, bridge, shrine, temple, shop, object, or landmark in
front of the user, grounds that recognition with available location context,
and tells one short, source-traceable local story worth remembering.

The product loop is:

> See a place → Understand the context → Hear one local story

KATARI is not a local encyclopedia. The first release is a user-invoked Osaka
MVP with exactly 20 curated Story Spots. It prefers silence or an explicit
recovery response over an attractive but unsupported story.

## 2. Confirmed product decisions

- The first catalog contains exactly 20 source-traceable Osaka Story Spots.
- Each spot contains three to five verified facts and one primary short story
  in Japanese and English. The record format may later support two additional
  stories without changing the Page contract.
- A story targets 15–30 seconds: 60–120 Japanese characters or 35–70 English
  words. It contains at most one year or era reference and one named person or
  event.
- The host supplies any available camera image, GPS/current-place context,
  spoken question, locale, time, weather, and route context to the Agent.
- The Agent performs candidate selection, visual/location grounding,
  confidence gating, story selection, and spoken response orchestration.
- A single AIUI Page displays a concise structured result. It does not capture
  camera or GPS data or perform open-web retrieval in the MVP.
- Japanese is the default story language. English is used when the user asks
  in English or explicitly requests English. Canonical Japanese place names
  remain visible in both modes.
- Invocation is user initiated. The MVP does not implement background
  geofencing, gaze-duration triggers, or unsolicited prompts.
- The selected visual direction is **A · Quiet Marker**: the place is the only
  visual focal point and speech carries the story.
- The project is Page-only and targets AIUI 0.17. It does not use 0.18-only
  Widgets or Agent Workers.

## 3. Scope

### 3.1 In scope

- Recognize cataloged buildings, streets, bridges, shrines, temples, stores,
  sculptures, signs, districts, and landmarks from host-provided context.
- Combine GPS or human-readable location with observable visual anchors.
- Answer questions such as “What story does this place have?”, “What was this
  place before?”, “Why is it famous?”, and “What do locals call it?”.
- Select one authored story that is directly related to the current view and
  favors contrast, local character, and a memorable ending.
- Distinguish verified fact from a sourced legend or local tradition.
- Render matched, uncertain, no-story, no-match, and invalid-input states.
- Support compact conversation-hosted `_current` and expanded `_blank` views
  without changing the underlying recognition result.
- Provide Japanese and English authored story versions rather than translating
  a newly generated story at runtime.

### 3.2 Out of scope

- A complete city guide, nationwide coverage, or open-ended Wikipedia Q&A.
- Route planning, restaurant recommendations, events, or real-time news.
- Background location monitoring, automatic pop-ups, or gaze tracking.
- Live web research during the user interaction.
- Long historical narration, fact lists spoken aloud, or multiple stories in
  one response.
- Unsupported urban legends, reconstructed dialogue, motives, scenes, or
  invented narrative connective tissue.
- Claims that browser preview proves Studio import, camera/GPS delivery,
  speech behavior, optical readability, or physical-glasses UX.

## 4. Architecture and data flow

KATARI uses Agent orchestration and one result Page.

1. The host provides any available image, coordinates/place context, spoken
   question, locale, and optional environment context.
2. The Agent normalizes the request and filters the 20-record catalog by
   location when valid location is present.
3. The Agent compares visible landmarks, geometry, signs, materials, and other
   stable anchors. A place name supplied by the user narrows candidates but
   does not prove a match.
4. An explainable evidence gate selects one of five states. The Agent does not
   expose a fabricated numeric precision score.
5. For a match, the Agent chooses the single authored story most directly
   related to the current view and speaks the selected Japanese or English
   version without embellishment.
6. The Agent invokes the Page with a bounded, JSON-serializable presentation
   object. Raw imagery and coordinates are not passed into the Page.
7. The Page validates the object again, derives safe fallback content, and
   renders target-aware information density.

The Page is presentation, not the source of place or story truth. Business
truth remains identical if the host moves the same Page between `_current` and
`_blank`; only visible detail changes.

## 5. Components and repository structure

The implementation adds a complete Studio-importable source project:

```text
examples/katari-agent/
├── AGENTS.md
├── SOURCES.md
├── app.js
├── app.json
└── pages/
    └── index/
        └── index.ink
```

- `AGENTS.md` defines identity, triggers, Japanese/English language policy,
  evidence gates, anti-hallucination rules, spoken-story constraints, Page
  invocation contract, and the compact facts and stories needed at runtime.
- `SOURCES.md` is the developer-facing evidence registry for the same 20 spot
  IDs. It records direct URLs, source classes, verification date, and bounded
  uncertainty. Runtime behavior must not assume this file is loaded by the
  host, so every fact required to answer is also represented in `AGENTS.md`.
- `app.json` declares the single Page and no unnecessary permissions.
- `app.js` contains only the required application entry and shared metadata.
- `pages/index/index.ink` owns the Page schema, normalization, state
  derivation, target-aware markup, and Quiet Marker styling.

The repository also adds `tests/test_katari_agent_contract.py` and a recorded
KATARI capability/UX evaluation under `tests/evaluations/`. Existing
validation and AIX gates are extended only where KATARI requires coverage.

## 6. Curated Story Spot record

Every accepted spot has:

- stable lowercase `spotId`;
- canonical Japanese name, English name, category, and Osaka locality;
- latitude, longitude, and a deliberately selected candidate radius;
- stable observable visual anchors;
- three to five atomic facts, each traceable to a source;
- exactly one primary story in authored Japanese and English versions;
- one short memory hook in Japanese and English;
- `fact`, `legend`, or `tradition` classification;
- estimated integer duration from 15 through 30 seconds for each language;
- direct source URLs, source classes, verification date, and uncertainty note.

A record is excluded when the place identity or the central story claim cannot
be supported. Official municipal, cultural-property, venue, shrine/temple,
museum, archival, and tourism sources are preferred. Reputable reporting or
scholarship may support local nicknames and social history. A third-party list
may identify a lead but cannot establish a story by itself.

Coordinates narrow the candidate set; they do not prove a match. Current
access rules and opening information are not treated as durable story facts.

## 7. Story contract

Every spoken story follows this structure:

1. identify what the user is looking at;
2. tell one verified local story;
3. end with one memorable reason the place matters.

The story must:

- fit its language-specific length bound and 15–30 second target;
- use no more than one year or era reference;
- use no more than one named person or event;
- connect directly to the place or visible feature;
- mark a legend or tradition with non-factual language;
- omit unsupported causal claims and scene-setting detail;
- avoid enumerating dimensions, dates, rebuilds, and statistics;
- remain semantically aligned across Japanese and English.

The Agent returns the authored text. It may shorten the story when the user
explicitly asks for a faster answer, but it may not add new facts. If no story
passes the evidence gate, it uses `no_story` rather than generating one.

## 8. Evidence and state policy

KATARI uses five states:

- `matched`: location and multiple distinctive visual anchors agree, or an
  equivalently strong exact-sign-plus-visual evidence set identifies one
  catalog record when GPS is unavailable.
- `uncertain`: evidence is partial, candidate records conflict, or location
  and visual signals disagree. The Agent requests one concrete additional
  view or observation at most once.
- `no_story`: the place identity is adequately supported, but KATARI has no
  reliable authored story for that place or the relevant catalog record has
  failed its evidence review.
- `no_match`: the retry remains inconclusive, no catalog record fits, or the
  place cannot be identified without guessing.
- `invalid`: the request cannot be normalized because all useful image,
  location, place-name, and question context is absent or malformed.

Missing GPS does not automatically produce failure. Strong exact signage and
multiple distinctive visual anchors may support a match, while the Agent says
that location was unavailable when relevant. GPS alone never proves a match.

A user claim, desired answer, or prior conversational suggestion is a filter,
not evidence. An uncertain result must not visually resemble a confirmed one.
After one failed retry, the Agent moves to `no_match` instead of continuing to
ask the user for more views.

## 9. Agent-to-Page contract

The Page accepts a bounded object with:

- `status`: `matched`, `uncertain`, `no_story`, `no_match`, or `invalid`;
- `spotId`;
- `placeNameJa`;
- `placeNameEn`;
- `localityLabel`;
- `storyDurationSeconds`;
- `memoryHook`;
- `confidenceLabel`;
- `evidenceNote`;
- `knowledgeKind`: `fact`, `legend`, or `tradition`;
- `recoveryHint`.

The schema and runtime normalizer define explicit string-length bounds.
`storyDurationSeconds` accepts only an integer from 15 through 30 for a matched
result. Unknown statuses, wrong types, overlong values, invalid durations, and
malformed roots become `invalid`. State-specific fields may be empty only when
the normalizer has a documented safe fallback.

The full story is spoken by the Agent and is not duplicated in Page input.
`spotId` supports traceability but is not shown as user-facing copy.

## 10. UX design — A · Quiet Marker

### 10.1 `_current`

The conversation-hosted view shows only:

1. a quiet `KATARI / LOCAL MEMORY` eyebrow;
2. the canonical Japanese place name;
3. the English place name and locality;
4. `LOCAL STORY · N SEC` with a small status dot.

The place name is the only dominant element. There is no story transcript,
menu, source list, map, route, decorative illustration, or persistent
animation. The Page does not intercept host key behavior.

### 10.2 `_blank`

The expanded view preserves the same hierarchy and may add:

- one memory hook;
- a categorical confidence label and concise evidence note;
- a `FACT`, `LEGEND`, or `TRADITION` label.

It does not add a second story or encyclopedia detail. The main identification
and duration remain in the comfortable optical field.

### 10.3 Recovery states

- `uncertain`: uses `NEED ONE MORE LOOK`, one specific visual request, and an
  explanation of the missing anchor.
- `no_story`: uses `PLACE CONFIRMED` and says that no sufficiently reliable
  short story is available.
- `no_match`: says that the place could not be identified or is outside the
  current Osaka Story Spot catalog.
- `invalid`: asks the user to face a building, sign, street, or landmark and
  repeat the local-story question.

Recovery states retain the Quiet Marker grammar but do not use the matched
status dot or `LOCAL STORY · N SEC` label.

### 10.4 Visual rules

- Target the 480 × 352 runtime/reference viewport while keeping essential
  content within the comfortable optical region.
- Use a black floor and one monochrome green luminance channel.
- Use 1 px structural lines, 2 px only for strong focus, 4 px control radii,
  and 6 px panel/group radii.
- Keep normal local green fill below 12%; prefer open space and one divider.
- Do not encode state through luminance alone; pair state labels and copy.
- Use no ambient animation. Any host transition remains short and incidental.

## 11. Verification design

### 11.1 Automated catalog and story tests

Tests require exactly 20 unique records and verify:

- complete coordinates, radius, anchors, three-to-five facts, source metadata,
  story classification, and Japanese/English text;
- language-specific story bounds and 15–30 second integer durations;
- no placeholder sources, duplicate records, or catalog/source ID drift;
- fact/legend/tradition wording rules and Japanese/English semantic alignment
  through authored paired identifiers and review metadata;
- one-year/era and one-person/event content budgets;
- no unsupported superlatives, quotation-like reconstructed speech, or story
  text outside the curated records.

### 11.2 Automated Agent and Page contract tests

Tests cover:

- Japanese/English triggers, user-initiated behavior, one-story output, and
  explicit non-goals;
- matching with agreeing evidence, GPS-only input, vision-only input,
  conflicting evidence, look-alike anchors, missing inputs, and one-retry cap;
- all five Page states plus unknown-state degradation;
- absent, malformed, overlong, wrong-type, and Unicode Page fields;
- invalid matched durations and state-specific fallback content;
- `_current` / `_blank` density and absence of unsupported camera, location,
  network, background, Widget, or Worker behavior.

A deterministic Node harness executes the real Page setup code and captures
the rendered data patches. Agent-policy tests validate the authored contract
and catalog invariants; they do not claim to execute a particular hosted LLM.

### 11.3 Recorded capability evaluation

A scenario matrix records expected and observed outcomes for representative
matched, uncertain, no-story, no-match, invalid, bilingual, legend, conflicting
evidence, and concise-story cases. It clearly labels the model/runtime used and
keeps prompt-contract evaluation separate from Studio or device evidence.

### 11.4 Local delivery and UX gates

Run the complete repository unit suite, strict validation against `0.17.0`,
reference checks, syntax checks, and tracked-whitespace checks. Probe the
installed or lockfile-resolved AIX CLI with `aix --help` and use only commands
advertised by that release. When available, run `preview`, `pack`, and `list`
against the exact Studio import folder.

Browser UX review covers matched and all recovery states, representative long
Japanese and English labels, `_current` and `_blank` density, and bright, dark,
and cluttered simulated backgrounds at 480 × 352. The review records clipping,
hierarchy, contrast, status differentiation, and information load. Design
mockups are supporting evidence; the generated AIX preview remains the primary
local runtime visual artifact.

### 11.5 External manual gates

The following remain unverified until executed in their real environments:

- authenticated AIUI Studio import and hosted simulation;
- host delivery of camera, GPS, locale, time, weather, and route context;
- permission grant, denial, revocation, and capability absence;
- Japanese and English speech pacing and Page invocation coordination;
- `_current` / `_blank` host transitions;
- physical-glasses readability against bright, dark, and cluttered scenes;
- real-world visual recognition under viewpoint, occlusion, motion, and night
  conditions;
- final performance and release review on the target Rokid Glasses model.

No local test may be reported as passing one of these external gates.

## 12. Acceptance criteria

The implementation is locally complete when:

1. `examples/katari-agent/` is a self-contained AIUI Studio import root.
2. The catalog contains exactly 20 source-traceable Osaka Story Spots with
   authored Japanese and English stories satisfying the short-story contract.
3. The Agent follows the five-state evidence policy and never invents a story
   to fill missing evidence.
4. The Page renders bounded, safe output for all supported and malformed input
   states.
5. `_current` matches the approved Quiet Marker hierarchy and `_blank` adds
   only the agreed memory/evidence detail.
6. The capability scenario matrix covers recognition, grounding, story
   selection, bilingual output, confidence, and failure recovery without
   overstating hosted-model evidence.
7. Fresh repository, strict-validator, and supported AIX gates pass against the
   exact import directory with recorded outputs.
8. Local browser UX review is recorded, while Studio, host camera/GPS, speech,
   optics, and physical-glasses checks remain explicit manual gates.
