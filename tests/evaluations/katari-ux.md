# KATARI UX Evaluation

## Decision

Local deterministic, AIX, and browser-supported UX checks pass after one long-label correction. Authenticated Studio behavior and physical Rokid Glasses optics remain BLOCKED; therefore this report does not call KATARI device-ready or release-ready.

- Design: A · Quiet Marker
- Import root: `examples/katari-agent`
- Target: AIUI `0.17.0`, Page-only
- Supported surfaces: `_current`, `_blank`
- Business states: `matched`, `uncertain`, `no_story`, `no_match`, `invalid`
- Evaluation date: 2026-09-09, Asia/Shanghai
- Browser canvas: 480 × 352 CSS pixels for each gallery scenario

## AIX preview evidence

Environment: macOS local worktree, bundled Node `24.19.0`, lockfile dependency `@yodaos-pkg/aix-cli@0.8.2`, in-app Chromium browser.

Executed commands:

```bash
AIX_BIN="$PWD/node_modules/.bin/aix"
"$AIX_BIN" --help
preview_html="/private/var/folders/15/skjy53_93qj231nvd_6dcczc0000gn/T/katari-preview.vnjWD3/katari-agent.html"
"$AIX_BIN" preview examples/katari-agent --html-out "$preview_html"
test -s "$preview_html"
grep -Fq 'pages/index/index.ink' "$preview_html"
wc -c "$preview_html"
shasum -a 256 "$preview_html"
```

Observed final artifact:

- AIX help advertised `pack`, `list`, `optimize`, and `preview`.
- Preview size: 99,798 bytes.
- Preview SHA-256: `a00ea20faaca289dd44d5f17d7d8c5d72989c05f15a3edc410619a9f97cd75e8`.
- Browser status reached `Preview ready.` and listed source `katari-agent`, five files, and the exact `pages/index/index.ink` route.
- With no host query, the real Page rendered the safe `invalid` state at the runtime's 960 × 704 backing buffer / 2 scale factor, corresponding to the 480 × 352 design canvas.
- Console: zero errors. One dependency warning reported deprecated runtime initialization parameters; it originated from `@yodaos-pkg/ink@0.17.1`, not project code, and did not prevent initialization.

This AIX preview is runtime preview evidence for bundle opening and the default Page render. It does not inject all host payloads, so the state matrix below is separate supporting visual evidence.

## Five-state visual gallery

The temporary gallery was created outside the import root at `.superpowers/katari-ux-gallery.html`. It reproduces the production hierarchy, copy, spacing, `#72ff9e` palette, one-pixel divider, six-pixel detail radius, `_current` density, and `_blank` expansion. The background layer is a simulation of optical context, not a claim that browser compositing reproduces the display.

The gallery rendered 30 scenarios: five states × two targets × bright background, dark background, and cluttered background. Matched scenarios used a 48-code-point Japanese long label and a 64-code-point English long label. A browser measurement compared `scrollHeight/clientHeight` and `scrollWidth/clientWidth` for the viewport, both names, locality, memory hook, evidence, and recovery hint. The final run reported 30 scenarios and zero overflows above the one-pixel font-rounding tolerance.

| State | Target | Bright | Dark | Cluttered | clipping | hierarchy | status differentiation | information load | Observation |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `matched` | `_current` | PASS | PASS | PASS | PASS | PASS | PASS | PASS | 48-code-point Japanese and 64-code-point English names fit using compact density; only identity, locality, evidence cue, and duration remain. |
| `matched` | `_blank` | PASS | PASS | PASS | PASS | PASS | PASS | PASS | Memory hook, FACT label, and evidence note appear below the unchanged identity hierarchy. |
| `uncertain` | `_current` | PASS | PASS | PASS | PASS | PASS | PASS | PASS | “ONE MORE VIEW” and one concrete capture instruction distinguish retry from failure. |
| `uncertain` | `_blank` | PASS | PASS | PASS | PASS | PASS | PASS | PASS | No story duration or knowledge metadata leaks into recovery state. |
| `no_story` | `_current` | PASS | PASS | PASS | PASS | PASS | PASS | PASS | Confirmed identity remains dominant while “STORY UNAVAILABLE” explains the refusal to improvise. |
| `no_story` | `_blank` | PASS | PASS | PASS | PASS | PASS | PASS | PASS | Expansion does not fabricate detail when the authored claim is unavailable. |
| `no_match` | `_current` | PASS | PASS | PASS | PASS | PASS | PASS | PASS | Distinct Japanese and English titles state that no catalog match was made. |
| `no_match` | `_blank` | PASS | PASS | PASS | PASS | PASS | PASS | PASS | Closed-catalog explanation remains short and readable. |
| `invalid` | `_current` | PASS | PASS | PASS | PASS | PASS | PASS | PASS | Default AIX render asks for a landmark without exposing malformed input. |
| `invalid` | `_blank` | PASS | PASS | PASS | PASS | PASS | PASS | PASS | Expansion adds no irrelevant metadata or controls. |

Visual observations:

- clipping: First inspection found the maximum Japanese label clipped in all six matched scenarios. A failing normalizer/UI contract was added, `nameDensity` now selects a 20 px / 24 px compact Japanese treatment and 12 px / 16 px English treatment, and the full 30-scenario matrix was reinspected with zero measured overflow.
- hierarchy: The Japanese place name remains the only dominant element; English/locality form one secondary group; story or recovery metadata sits at the lower edge.
- status differentiation: Each recovery state uses a different title and explicit label; `matched` alone shows the filled status dot and `LOCAL STORY · N SEC`.
- information load: `_current` hides the memory/evidence group; `_blank` adds only one memory hook, knowledge kind, and evidence note. No button, cursor, animation, route, or secondary story appears.
- Bright and dark scenes retained readable separation in the browser simulation. The cluttered scene remained legible under the simulated dark optical floor, but this is not physical contrast evidence.

## Required UX matrix

| ID | Surface/state | Risk | Test | Evidence layer | Result | Evidence |
| --- | --- | --- | --- | --- | --- | --- |
| UX-TARGET-LOCAL | `_current`, `_blank` | Wrong density or business-state drift | Contract-test both media regions; render both targets with identical state data | LOGIC + browser | PASS | Unit contract plus 30-scenario gallery; `_current` hides and `_blank` reveals only `.expanded-only`. |
| UX-TARGET-HOST | Target transition in authenticated host and glasses | Host transition differs from browser media simulation | Open the same result in both targets on Studio and glasses | STUDIO + DEVICE | BLOCKED | No authenticated Studio session or target glasses were available. |
| UX-STATE | All five states | Hidden, misleading, or mixed story/recovery state | Execute normalizer for valid, missing, malformed, conflict, and catalog-boundary inputs; render every state | LOGIC + AIX + browser | PASS | Node-mounted real setup block, AIX default invalid render, and gallery captures. |
| UX-TEXT-LOCAL | Empty, maximum, Japanese long label, English long label, mixed Unicode, malformed types | Clipping, unsafe interpolation, or raw-value leak | Test below/at/above every schema limit; measure rendered content in both targets | LOGIC + browser | PASS | Unicode boundary suite plus 48/64-code-point zero-overflow gallery result after correction. |
| UX-TEXT-DEVICE | Maximum labels in optics | Browser-readable wrapping fails in optical field | Read long Japanese/English cases on physical display while standing and walking safely | DEVICE | BLOCKED | physical Rokid Glasses were unavailable. |
| UX-FOCUS | Display-only Page | Invisible focus or focus trap | Inspect markup for actionable elements and focus/key handlers | STATIC | N/A | Product has no buttons, tap handlers, focus order, key interception, or Page-owned activation. |
| UX-INPUT-PAGE | Page input payload | Malformed object or out-of-range value leaks or misstates story | Mount the real setup block and submit null, arrays, wrong types, invalid durations, enum errors, and Unicode limits | LOGIC | PASS | One complete `setData` patch per case; malformed values collapse to the safe `invalid` state. |
| UX-INPUT-HOST | Voice, image, GPS, place, locale | Host omits, conflicts, or misroutes evidence | Exercise real voice/camera/GPS/locale delivery and fallback | STUDIO + DEVICE | BLOCKED | Host integration and physical sensors were unavailable; browser fixtures do not substitute. |
| UX-RECOVERY | `uncertain`, `no_story`, `no_match`, `invalid` | Endless retry, silent failure, or fabricated story | Force every recovery state and second unresolved view; inspect copy and metadata branches | LOGIC + browser | PASS | 15-case capability report and recovery renders; retry budget is one. |
| UX-LIFECYCLE | First open and repeated Page instances | Stale or retained state | Call `onLoad` for independent mounted instances and inspect source for retained resources | LOGIC + STATIC | PASS | Each mount applies one full patch; no timers, listeners, streams, storage, or background work exist. |
| UX-VISUAL-LOCAL | Every state and target | Weak hierarchy, excess fill, motion, or meaning only by luminance | Inspect 30 renders and source tokens | STATIC + AIX + browser | PASS | Labels accompany status; one green hue, one divider, compact detail group, no animation. |
| UX-ENVIRONMENT-AIX | 480 × 352 runtime framing | Content leaves comfortable region | Open final AIX artifact and inspect default Page | AIX | PASS | `Preview ready.` at the 480 × 352 design canvas; default state stayed within the 36 px × 30 px safe inset. |
| UX-ENVIRONMENT-DEVICE | Bright, dark, cluttered real scenes and posture | Browser scene differs from optical field | Inspect all states in actual scenes on glasses | DEVICE | BLOCKED | Gallery is browser evidence only; optics, posture, and real-world contrast need physical Rokid Glasses. |
| UX-MOTION | All states | Distraction, unsupported animation, heat | Inspect source for animation and retained work | STATIC | N/A | No transitions, keyframes, timers, continuous rendering, or ambient motion are implemented. |

## Evidence boundary

The AIX render and state gallery are browser evidence only. They do not prove authenticated AIUI Studio import, host camera/GPS/locale delivery, speech pacing, Page-to-speech coordination, target transitions in the host, optical comfort, real bright/dark/cluttered scenes, sensors, thermal behavior, or physical Rokid Glasses interaction. Those rows remain BLOCKED until executed on their required evidence layers.
