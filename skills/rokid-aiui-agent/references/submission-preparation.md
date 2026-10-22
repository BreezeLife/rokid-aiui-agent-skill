# Prepare an AIUI Agent submission handoff

Use this when delivering an implemented Agent or preparing its review materials. Produce a filled `submission.md` beside the source directory, with media and verification artifacts outside the Studio import root. Keep a completed draft useful even when publication is blocked. Preparing files does not authorize uploading, saving account changes, or submitting to review.

## Source and requirement boundaries

This guide uses official AIUI 0.19 snapshot `7d62c2d9ac1cdc1389ba06ed0651b395903accff`, checked on 2026-10-23:

- [Review and publishing requirements](https://github.com/yodaos-project/AIUI/blob/7d62c2d9ac1cdc1389ba06ed0651b395903accff/documentation/0-guide/bundle/publish.en-US.md): metadata and preview specifications.
- [Studio import, simulation, device update, and review flow](https://github.com/yodaos-project/AIUI/blob/7d62c2d9ac1cdc1389ba06ed0651b395903accff/documentation/0-guide/quickstart/quickstart.en-US.md): platform handoff sequence.
- [Application configuration and permissions](https://github.com/yodaos-project/AIUI/blob/7d62c2d9ac1cdc1389ba06ed0651b395903accff/documentation/1-framework/open-agent-format/app-json.en-US.md): source declarations and authorization boundaries.

The publishing document specifies a unique functional name of at most 20 characters, a custom relevant icon, category, description of at most 500 characters, and an opening message (300 characters recommended). The platform assigns the Agent ID and increments its own version. Declare used permissions with specific purposes, including personal-data access where applicable. Supply 3–5 preview files with at least one image and one video: JPG/PNG and MP4; video at most 60 seconds. Recommendations: square media, 15–45-second video, at most 50 MB per file. Copy and media must match real functionality; avoid endorsement/ranking claims and test/beta names. Consult the full source for icon and content rules.

These are documented requirements, not an observation of an authenticated Studio form. Record portal/region and inspection date if available. Current category choices, field counters, pixel dimensions, codec rules, and any additional form requirements remain `UNKNOWN` until inspected. Recommendations must not become invented hard limits. The duplicated icon rows in the source describe one icon requirement, not two invented uploads. Runtime `0.19.0`, source revision, and Studio-generated package version are distinct identifiers.

## Assemble from the actual project

1. Inspect `AGENTS.md`, `app.json`, every declared route, entry logic, calls, and the closed claims ledger. Draft capabilities from implemented behavior; link each promise to its code location and exact inventory gate. Keep proposed work separate. Host-routed conversation and optional hardware remain unverified unless captured.
2. Run the [functional/UX workflow](ux-and-capability-testing.md), including the [0.19 scenarios](aiui-0.19.md). Keep the exact audit schemas, source fingerprint, input gates, evidence layers, and signed-evidence requirements. A local callback test cannot certify speech routing or physical input.
3. Package using the advertised [AIX workflow](aix-workflow.md). Record the import root and repository boundary, Git URL/ref/subdirectory when applicable, exact commit or `WORKTREE:SHA-256`, target runtime, AIX version, archive path/bytes/SHA-256, and package listing. Recheck identity after changes. A local archive does not prove that Studio's cloud package contains it.
4. Reconcile three separate permission concerns: application declarations, device authorization, and Studio review selections. Map each actual API/data use to its manifest requirement and truthful purpose. Studio's network/speaker labels do not establish manifest constants named `NETWORK` or `SPEAKER`; consult the API source. Describe third-party endpoints, transmitted data, retention/deletion behavior, and account access only where code or owner evidence supports them. Unverified backend practices stay `UNKNOWN`; an offline Page does not prove the entire host collects no data.
5. Prepare actual listing copy and review instructions now. For unavailable media, produce a shot list and capture steps, not a fake screenshot or fabricated recording. An illustration may explain the flow but cannot prove shipped behavior. Bind every genuine capture to runtime, surface, source revision, timestamp, and evidence layer; record redactions and edits. Preserve original captures where audit evidence requires them.

Use this handoff layout, adapting names to the project:

```text
delivery/
  source/                 # only this directory is selected for Studio import
  agent.aix               # only after successful pack/list and identity checks
  submission.md           # filled preparation report
  verification/           # logs, inventory, audit, capture manifests
  media/                  # actual captures or a clearly named capture-plan.md
```

Keeping delivery material outside `source/` avoids changing the verified import fingerprint merely by writing reports. Do not place credentials, private signing keys, or access tokens in the handoff.

## Fill the handoff

The following is a repository handoff format, not a claimed Studio form schema. Replace descriptive values with project-specific drafts, observed values, or `UNKNOWN` plus the owner/action needed. Use `PASS`, `FAIL`, `BLOCKED`, and justified `N/A` only for verification results; missing evidence stays `BLOCKED`.

```markdown
# Agent submission preparation

## Build identity
- Preparation date / owner:
- Target AIUI runtime / target glasses and firmware:
- Absolute source import root / repository root:
- GitHub repository / branch or tag / exact revision / import subdirectory:
- Source fingerprint / inventory path:
- AIX tool version / artifact path / bytes / SHA-256 / listing log:
- Studio portal and region / form inspection date:
- Studio Agent ID / generated version / cloud-source correspondence:

## Listing draft
- Name:
- Summary (handoff copy; not a documented separate Studio field):
- Feature description:
- Opening message:
- Category candidate / current portal option confirmation:
- Custom icon file / provenance / visual inspection:
- Verified capabilities with source and inventory gate links:
- Limitations and unsupported behavior:

## Usage and reviewer reproduction
| User request | Exact route and target | Parameters/schema/defaults | Expected state and fallback | Evidence/result |
| --- | --- | --- | --- | --- |

Include a first-use example, a parameter change, an invalid request,
and a return/reopen flow. State whether a fresh Page invocation is required.

## Permissions and data-use draft
| Capability/code | Manifest declaration | Device authorization | Studio review selection | Specific purpose/data flow | Denial/recovery evidence |
| --- | --- | --- | --- | --- | --- |

- External services and owner-confirmed retention/deletion behavior:
- Personal-data access and corresponding disclosure:
- Unknown facts requiring owner confirmation:

## Media register and capture plan
| File or planned shot | Actual capture or plan | Surface/state/workflow | Evidence layer | Source/runtime/time | Format/duration/size | Result |
| --- | --- | --- | --- | --- | --- | --- |

List core-state images and a complete interaction recording. Mark missing
captures BLOCKED; give capture steps, owner, and required environment.

## Verification and review notes
- Exact functional/UX and per-capability audit path / validator exit:
- Strict project validation / unit or integration results / preview:
- Studio import, simulation, source/version match, and glasses results:
- Known defects, unsupported claims, and reviewer reproduction steps:
- Evidence staleness check after final source or metadata edits:

## Owner inputs and decision
| Missing input or gate | Owner | Next action | Result |
| --- | --- | --- | --- |

- Materials prepared:
- Release-ready: NO until the audit permits YES
- Platform submission: NOT PERFORMED
```

Use explicit `N/A` with an explanation for irrelevant handoff coordinates, such as a local-only project with no GitHub URL; this is not an audit scope exclusion. Never copy a sample Agent ID, package hash, result, or store version into a new project. A screenshot of AIX preview belongs to the preview layer even if its appearance resembles glasses. Complete supplied media checks by opening the files and inspecting the content and metadata; filenames alone prove neither format nor experience.

## Decide what is ready

Report draft preparation, source delivery, package delivery, and release readiness separately. A written plan is a completed preparation artifact; its unexecuted verification remains `BLOCKED`. Keep 0.19 capability rows `BLOCKED` under the current inventory-only policy, preserve missing Studio/device authority, and include the actual audit exit code. Do not convert a full local test suite or completed metadata into `Release-ready: YES`.

Give the owner the remaining platform steps in order: import the exact source, simulate in Studio, create its cloud AIX version, update the glasses resource package in the companion app, verify the same version on glasses, reconcile review materials with the current form, then perform any separately authorized submission. Record an actual platform response before reporting a saved version, submission, or review result. After rejection or source edits, rebuild and refresh affected captures; preserve the rejection reason and its correction in reviewer notes.
