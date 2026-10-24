# Independent community-adaptation ownership probe

This is a pure JavaScript ownership model with fake dependencies, authored only from
the installed rokid-aiui-agent Skill and its routed references. It is not a product,
an AIUI adapter, an official sample, or an AIUI release audit. No real services,
network access, camera, speech player, Studio, browser preview, or glasses are used.

## Replay

Use Node.js with the built-in test runner:

```sh
node --test --test-reporter=tap controller.test.mjs
```

The evaluation used Node.js `24.19.0`. Run the command from this directory.

`controller.mjs` models acquisition, encoded-photo validation, abortable request,
speech task acquisition/generation, player acquisition/playback, and ownership
cleanup. `controller.test.mjs` uses manually resolved/rejected promises and manual
deadline callbacks, with no wall-clock sleeps. `run.tap` records the actual run.
`provenance.json` identifies the Skill inputs and their SHA-256 hashes.

## Boundaries

- Dependency names are invented injection seams, not AIUI API signatures.
- Passing tests prove only assertions about this independent model, not generated
  application source, API support, physical input delivery, or release readiness.
- The synthetic activation ID must be supplied by an adapter derived from observed
  host events; it is not claimed to be a native AIUI event field. The model's ID
  registry is session-scoped and unbounded; a production adapter needs an observed,
  bounded activation lifecycle and cannot merely reuse a global debounce delay.
- The observed-capture-overlay reason is an engineering policy that cannot be
  enabled without target-host traces. Ordinary hide cancels in this model; a
  recognized capture overlay holds upload until show. Show never repeats capture.
- A 1024-byte limit and 120-character summary limit are tiny test fixtures, not
  recommended production limits. PNG bytes are synthetic and are never decoded.
  Byte/MIME preservation tests do not prove image validity or recognition quality.
- Fake abort/stop/destroy counters do not prove that an AIUI runtime or server
  honors cancellation, stops processing, or deletes uploaded data.
- No sample mode, real authentication, health endpoint, streaming, content quality,
  real encoding, permission revocation, optics, performance, or actual host-event
  arbitration is implemented or verified here.
- The installed Skill keeps all AIUI 0.19 capability audit rows BLOCKED pending a
  version-specific policy and matching evidence. This probe does not override it.

This archived probe is evaluation evidence, not a shipped Skill asset or an AIUI
implementation template. Its retained job/trace registries are also unbounded.
The repository unit suite is separate; replay this probe with the command above.
