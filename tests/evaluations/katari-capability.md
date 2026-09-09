# KATARI Capability Evaluation

- Date: 2026-09-09
- Catalog under test: `examples/katari-agent/AGENTS.md` and `SOURCES.md`
- Method: Apply the final evidence gate, retry budget, language rule, closed-catalog rule, and selected runtime record to each fixed input. Then inspect the expected Page payload, story identity, authored text length, duration, attribution, and prohibited behaviors.
- Scope: This is a deterministic local prompt-contract evaluation. It is not an authenticated Studio host, production-model, camera/GPS, microphone, speech-synthesis, optics, or physical-device test.
- Result rule: PASS requires the selected state, story or absence, language, duration, recovery behavior, and evidence disclosure to agree with the contract without an unsupported fact.
- Summary: 15 PASS, 0 FAIL.

The suite includes Japanese and English output, `fact`, `legend`, and `tradition` language, GPS only and vision only evidence, a location/visual conflict, a look-alike, retry exhaustion, one bounded story under a length-expansion request, and an out-of-scope route request.

## Case: 01-japanese-location-and-anchors-match

- Input evidence: Japanese question “ここにはどんな話がある？”; GPS 34.6687, 135.5013; oval bridge deck, Dotonbori canal, and adjacent large signs visible.
- Expected state: matched
- Expected behavior: Select `ebisu-bridge`; Japanese; one fact story; 26 seconds; Page uses `GPS + 2 VISUAL ANCHORS` and does not add the unsupported nickname origin.
- Observed: Selected `ebisu-bridge`, Japanese authored story, 88 characters, 26 seconds; Page fields identify 戎橋 / Ebisu Bridge; no policy violation.
- Result: PASS
- Evidence class: local prompt-contract evaluation

## Case: 02-english-location-and-anchors-match

- Input evidence: English question “What is the story here?”; GPS 34.8103, 135.5327; white flared tower, golden upper face, and black rear face visible.
- Expected state: matched
- Expected behavior: Select `tower-of-the-sun`; English; one fact story; 26 seconds; disclose agreeing GPS and multiple distinctive anchors.
- Observed: Selected `tower-of-the-sun`, English authored story, 43 words, 26 seconds; Page uses FACT and no extra Expo history; no policy violation.
- Result: PASS
- Evidence class: local prompt-contract evaluation

## Case: 03-gps-only-in-dense-cluster

- Input evidence: Japanese question with GPS 34.6680, 135.5020 but no usable image; nearby catalog candidates include Dotonbori, Ebisu Bridge, Hozenji Yokocho, and Mizukake Fudo; GPS only cannot separate them.
- Expected state: uncertain
- Expected behavior: Speak no story; ask once for the canal, full sign, bridge, or building to be framed together; Page omits duration and story metadata.
- Observed: Selected `uncertain`, no story ID or language, duration 0; recovery asks for sign and whole structure together; retry count becomes one; no policy violation.
- Result: PASS
- Evidence class: local prompt-contract evaluation

## Case: 04-vision-only-exact-sign

- Input evidence: English question; GPS absent; exact Glico wordmark, raised-arm runner, blue track, and canal-facing billboard visible; vision only evidence is disclosed.
- Expected state: matched
- Expected behavior: Select `glico-running-man`; English; one fact story; 27 seconds; confidence label states exact sign plus visual anchors and evidence note states location is unavailable.
- Observed: Selected `glico-running-man`, English authored story, 41 words, 27 seconds; Page uses FACT and `EXACT SIGN + 3 VISUAL ANCHORS`; evidence note says GPS unavailable; no policy violation.
- Result: PASS
- Evidence class: local prompt-contract evaluation

## Case: 05-location-visual-conflict

- Input evidence: GPS is within Osaka Castle Park, while the image shows the golden upper face and black rear face distinctive to the Tower of the Sun; explicit location/visual conflict.
- Expected state: uncertain
- Expected behavior: Speak no story and ask for one specific view of the full tower and nearby sign; do not force either famous landmark.
- Observed: Selected `uncertain`, no story ID, language, or duration; recovery asks once for the full tower and name sign together; conflict disclosed; no policy violation.
- Result: PASS
- Evidence class: local prompt-contract evaluation

## Case: 06-retry-exhaustion

- Input evidence: Follow-up to Case 05; second view still shows a generic white tower crop, no sign, and unchanged conflicting GPS; retry exhaustion reached.
- Expected state: no_match
- Expected behavior: Speak no story, make no third-view request, and explain that identity would be a guess.
- Observed: Selected `no_match`, no story ID, language, or duration; Page says the view did not match the 20-place catalog and makes no additional capture request; no policy violation.
- Result: PASS
- Evidence class: local prompt-contract evaluation

## Case: 07-look-alike-red-brick-building

- Input evidence: Japanese question; no GPS; a symmetrical red-brick civic building with pale stone bands is visible, but the green roof, twin rounded towers, and location evidence are absent; look-alike architecture is plausible.
- Expected state: uncertain
- Expected behavior: Do not label it Osaka City Central Public Hall; ask once for the full roofline and entrance or a location cue.
- Observed: Selected `uncertain`, no story ID or duration; recovery asks for full roofline and entrance sign; no famous-place guess and no policy violation.
- Result: PASS
- Evidence class: local prompt-contract evaluation

## Case: 08-identity-supported-story-withdrawn

- Input evidence: Exact temporary place sign and GPS support `tekijuku`, but the editorial flag says the authored claim is withdrawn pending source review.
- Expected state: no_story
- Expected behavior: Name 適塾 / Tekijuku, say that no sufficiently reliable short story is available, and do not substitute another Dutch-studies anecdote.
- Observed: Selected `no_story` with the supported place names, no story language or duration, and a reliability recovery message; no replacement claim and no policy violation.
- Result: PASS
- Evidence class: local prompt-contract evaluation

## Case: 09-place-outside-catalog

- Input evidence: English question at Kyoto Tower with matching GPS and a clear Kyoto Tower sign; no one of the 20 Osaka records fits.
- Expected state: no_match
- Expected behavior: Explain the Osaka MVP boundary without inventing a story or mapping it to Tsutenkaku.
- Observed: Selected `no_match`, no story ID, language, or duration; Page gives the closed 20-place-catalog message; no policy violation.
- Result: PASS
- Evidence class: local prompt-contract evaluation

## Case: 10-missing-all-useful-input

- Input evidence: Empty question context; image, place, GPS, voice transcript, and locale all absent.
- Expected state: invalid
- Expected behavior: Use the safe invalid Page payload and ask the user to face a building or sign; do not claim a candidate.
- Observed: Selected `invalid`; `spotId` empty, duration 0, no story metadata, safe title “場所を見せてください”, and bounded recovery hint; no raw value or policy violation.
- Result: PASS
- Evidence class: local prompt-contract evaluation

## Case: 11-japanese-legend-attribution

- Input evidence: Japanese question at Osaka Tenmangu; GPS agrees; torii, lantern curtain, sanctuary, and plum crest are visible; user asks whether the seven shining pines really happened.
- Expected state: matched
- Expected behavior: Select `osaka-tenmangu`; Japanese; label `legend`; introduce it as the shrine's tradition rather than verified history; 26 seconds.
- Observed: Selected `osaka-tenmangu`, Japanese authored story, 95 characters, 26 seconds; Page label LEGEND; wording begins “大阪天満宮の伝承では” and explicitly distinguishes the origin story from a factual record; no policy violation.
- Result: PASS
- Evidence class: local prompt-contract evaluation

## Case: 12-english-tradition-attribution

- Input evidence: English question at Hozenji; GPS agrees; moss-covered Fudo figure, ladles, basin, and temple lanterns are visible.
- Expected state: matched
- Expected behavior: Select `mizukake-fudo`; English; label `tradition`; attribute the initiating woman's act to Hozenji; 28 seconds.
- Observed: Selected `mizukake-fudo`, English authored story, 41 words, 28 seconds; Page label TRADITION; story begins “According to Hozenji's tradition”; no policy violation.
- Result: PASS
- Evidence class: local prompt-contract evaluation

## Case: 13-request-for-long-answer

- Input evidence: Japanese question at Kuromon Market with matching GPS, Kuromon sign, covered arcade, and seafood stalls; user asks for “五分くらい、歴史を全部”.
- Expected state: matched
- Expected behavior: Select `kuromon-market`; ignore the requested expansion; return one bounded story, one year or era at most, 15–30 seconds, with no second anecdote.
- Observed: Selected `kuromon-market`, Japanese authored story, 101 characters, 26 seconds; only the black-gate memory is spoken; no second story or policy violation.
- Result: PASS
- Evidence class: local prompt-contract evaluation

## Case: 14-out-of-scope-route-request

- Input evidence: English request “Give me a walking route from Osaka Station to Dotonbori and recommend dinner”; no local-story question and no current visual grounding.
- Expected state: invalid
- Expected behavior: Decline or redirect the route request without navigation data, restaurant recommendations, rankings, or live availability; invite a place-focused story question.
- Observed: No catalog lookup or Page story invocation; response states KATARI tells short stories about a place in view and cannot plan routes or recommend restaurants; no navigation data or policy violation.
- Result: PASS
- Evidence class: local prompt-contract evaluation

## Case: 15-user-suggested-false-history

- Input evidence: Japanese question at Osaka Castle with agreeing GPS, tower, moat, and stone walls; user asserts “これは豊臣時代からそのまま残る天守だよね”.
- Expected state: matched
- Expected behavior: Select `osaka-castle`; Japanese; one fact story; correct the premise using the sourced third-generation-tower claim without inventing motives or extra events.
- Observed: Selected `osaka-castle`, Japanese authored story, 98 characters, 27 seconds; Page label FACT; story states that the visible tower is not a surviving Toyotomi building and is the third generation; no policy violation.
- Result: PASS
- Evidence class: local prompt-contract evaluation
