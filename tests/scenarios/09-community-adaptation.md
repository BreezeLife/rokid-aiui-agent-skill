# Community demo adaptation and asynchronous ownership

## Request

I have a community AIUI demo monorepo: app in `demos/field-note/`, backend next to it, README shows a successful HTML mock and says hide cancels all async work. I want a 0.19 camera → remote analysis → short spoken summary Agent, one tap to start/retry, cancel/back always works. Can I import the entire repository tree URL, trust the mock as preview, reuse the demo request code, and stop capture on hide? Give an actionable adaptation and verification plan; identify source locations in the installed Skill that substantiate your decisions. Include precise lifecycle/race/cancellation acceptance criteria, camera payload/data handling, input arbitration, backend configuration, and Studio import diagnosis if that tree URL fails.

## Evaluation method

Run independently with only the packaged Skill and relevant references, without the intended answer, research notes, or existing evaluation. For a retrieval-only run, disclose that source/runtime/backend/device are unverified. Do not execute third-party code or access demo services.

Assess whether the agent can apply the guidance to this request:

- Resolve the per-application import root and distinguish URL parsing from missing project files, without treating a portal workaround as a universal rule or publishing another branch implicitly.
- Distinguish mock, actual Ink preview, Studio, and device evidence.
- Find the exact official capture environment, encoded payload/MIME, image-capable model, request cancellation, and independently controllable speech contracts.
- Handle late acquisition, retry A/B races including finalizers, explicit hide policy, and cleanup without inventing automatic promise cancellation or generic browser APIs.
- Preserve cancel/back under repeated input and bind a successful result to the actual input rather than samples, health checks, or API presence.
- Keep configuration/secrets, backend ownership, test reproduction, and submission material outside the import root; retain current audit and release boundaries.

If an additional executable probe is used, write it independently outside this repository and exercise the generated controller with controlled asynchronous completions. Such logic tests cannot establish runtime or hardware support. Record the actual scope and outcome, not a universal Skill capability score.
