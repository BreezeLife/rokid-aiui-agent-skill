# Debugging and release gates

Read this for failures, verification planning, Studio handoff, physical-device testing, or store release preparation.

## Evidence ladder

Use the cheapest layer that can prove the claim, then move outward:

| Layer | Proves | Does not prove |
| --- | --- | --- |
| Static project validation | manifest parses; declared paths/blocks resolve | runtime semantics or UX |
| AIX `pack` + `list` | artifact can be created and contains expected entries | host compatibility or store upload |
| AIX browser preview | basic rendering/data/events in a browser Ink runtime | glasses optics, keys, sensors, permissions |
| AIUI Studio Web simulation | host-like input, temple controls, light-background checks | final physical-device behavior |
| Physical Rokid Glasses | actual optics, focus, voice/keys/gestures, device APIs, performance | review approval |
| Studio review flow | metadata, declared permissions, preview assets, platform review | future runtime compatibility |

Official 0.17 guidance distinguishes [Web simulation from real-device debugging](https://github.com/yodaos-project/AIUI/blob/88e70bb0382525c1a93ef077c2401dcc31a273ce/documentation/0-guide/quickstart/quickstart.md#L76-L90). Physical-device results are the final UX authority.

## Symptom-led triage

### Studio cannot import the project

1. Confirm the selected local folder/GitHub specified directory directly contains `app.json`.
2. For GitHub import, record repository URL, exact branch/tag, and directory.
3. Parse `app.json`; resolve every declared Page and version-gated Widget/Worker/component path relative to that directory.
4. Remove reliance on parent-workspace files, symlinks, secrets, or uncommitted local assets.
5. State the target version; retry with a conservative 0.17 Page-only project if 0.18 additions are not supported.

### Page is blank or fails to load

- Check route spelling/case and whether `<route>.ink` shadows same-route multi-file sources.
- Ensure one `<page>` root, no `<widget>` root, no duplicate optional blocks, and valid JSON in `<script def>`.
- Confirm every template handler exists and initial `data` is JSON-serializable.
- Inspect Studio/runtime logs before changing unrelated layout code.

### Input works in preview but not on glasses

- Confirm host focus separately from element focus.
- Log actual `event.code`, target, and focus callbacks on the device.
- Put default-action interception in `onKeyUp`; call `preventDefault()` only when supplying a complete replacement.
- Confirm `onVoiceWakeup` and world-awareness callbacks on the target runtime; provide a fallback.
- Treat `_current` interaction as host-sensitive and retest `_blank`.

### Component/API is undefined or permission is denied

- Verify the exact capability in the target-version docs; do not infer browser compatibility.
- Compare `app.json` permissions/capabilities with code and actual host grants.
- Check whether the implementation is 0.18-only while the host is 0.17 stable.
- Add a useful denied/unavailable state, then retest on device.

### Package or preview command fails

- Capture Node and AIX versions plus `aix --help`.
- Do not substitute imagined `create`, `dev`, `build`, or `deploy` commands.
- Validate source before packaging; write to a fresh output path and inspect with `list`/`ls` if advertised.
- Remember that the scaffold may have no `npm start`; inspect `package.json.scripts`.

### Visuals are readable on desktop but not through glasses

- Test transparent content over bright, dark, and cluttered backgrounds.
- Distinguish the 480×352 Ink reference viewport from the older 480×640 optical canvas/480×400 preferred region.
- Check text luminance, safe-area placement, 1px structural lines, focus visibility, and normal fill at or below 12% under the current beta design.
- Reduce large filled panels, persistent glow, simultaneous animation, and card nesting.

## Physical-device release matrix

Record a pass/fail result for every applicable cell; “not tested” is not “pass.”

| Dimension | Required cases |
| --- | --- |
| Runtime | 0.17 stable baseline; explicit 0.18 host when using Widgets, Agent Workers, or other gated additions |
| Hosting | `_current`, `_blank`, and target transition if the Page supports both |
| Focus/input | host focus/blur, element focus, Enter, Backspace, ArrowUp/Down, temple input if exposed, touch where applicable |
| Voice/perception | `onVoiceWakeup`; head gesture/orientation only after awareness is enabled; non-gesture fallback |
| Permissions | first request, grant, denial, later revocation/unavailability; declaration matches code and stated purpose |
| Network/data | offline, timeout, malformed/partial response, recovery, streaming if used |
| Lifecycle | first open, hide/show, unload/reopen, repeated Widget attach/detach, repeated Worker open if gated |
| Visual environment | bright, dark, cluttered real-world backgrounds; compact and overflow content |
| Performance | cold start, repeated navigation, animation + network overlap, continuous-use stability |
| Packaging | exact source commit, AIX CLI version, successful `pack`, expected `list`, artifact checksum/size |

## Studio-to-device-to-review flow

The official flow is: build source → Web simulation → package AIX/upload through Studio → download the updated resource in the Rokid AI App → test on glasses → complete review materials → submit. See the pinned [0.17 simulation/device flow](https://github.com/yodaos-project/AIUI/blob/88e70bb0382525c1a93ef077c2401dcc31a273ce/documentation/0-guide/quickstart/quickstart.md#L76-L90) and [review guidance](https://github.com/yodaos-project/AIUI/blob/88e70bb0382525c1a93ef077c2401dcc31a273ce/documentation/0-guide/bundle/publish.en-US.md).

Before review:

- package/save a new version so the device downloads current code;
- verify the core flow on physical glasses;
- declare the minimum permissions actually used and give truthful purposes;
- ensure screenshots/video show the real shipped experience;
- record source ref, target runtime/device, artifact, and test evidence.

The Skill prepares and verifies artifacts but does not click submit, publish to the store, or make other live platform changes. Hand those actions to the developer unless a separate, explicit authorization and supported platform mechanism is provided.
