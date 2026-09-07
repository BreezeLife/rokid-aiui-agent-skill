# Work Log

## 2026-09-07

- Confirmed the workspace was empty and not yet a Git repository; the expected continuity files did not exist.
- Confirmed GitHub CLI authentication for `BreezeLife` and verified that `BreezeLife/rokid-aiui-agent-skill` did not already exist.
- Initialized a local Git repository with `main` as the initial branch.
- Cloned source repositories into a temporary research directory without modifying upstream sources.
- Verified that `jsar-project/AIUI` and `jsar-project/aix` redirect to the `yodaos-project` organization.
- Found that the old AIX documentation hostname is stale and began validating commands against repository source and published packages.
- Downloaded the official nine-page ROKID AIUI courseware PDF, extracted its text, rendered it, and visually reviewed the relevant pages.
- Selected a compact router plus on-demand references and deterministic validation as the implementation direction.
- Found material conflicts inside the official AIUI repository: the current quickstart permits conversation-embedded interaction, v0.18 documents animation support, and the beta green design has moved to sparse 1px/open-field styling, while the bundled `aiui-dev` Skill retains older restrictions and visual tokens.
- Updated the design source precedence so current changelog/documentation, implementation, and runnable samples outrank stale bundled summaries.
- Completed the official design and third-party workflow audit. Recorded the unresolved distinction between the `480x352` Ink preview viewport and the official `480x640` optical canvas with a `480x400` preferred region.
- Ran three fresh pre-Skill scenarios. The baseline scored 7/30 with four critical failures: it removed a currently supported conversation interaction, invented AIX commands, and lacked a safe end-to-end release gate.
- Added a fourth Studio-delivery baseline. The complete RED suite scored 8/40 with six critical failures, including snippets-only delivery, invented project files/APIs, and a fake ZIP-to-AIX workflow.
- Implemented a compact `rokid-aiui-agent` Skill derived from the official `aiui-dev` routing model, with seven focused, commit-pinned references and an explicit stable `0.17.0` default.
- Packaged the Skill at `skills/rokid-aiui-agent/` so its directory matches frontmatter `name` and both GitHub CLI and generic Skills CLI can discover it.
- Added a complete Page-only AIUI source project under `assets/studio-importable-minimal/`; its project root is suitable for Studio local selection or GitHub specified-directory import.
- Built a dependency-free project validator with stable diagnostics for manifests, routes, `.ink`, WXML, Widgets, Agent Workers, application entries, version gates, and unsafe paths.
- Added adversarial regressions for empty or malformed WXML, crossed/unbalanced Ink tags, invalid `app.ink`, missing Widget family, near-match AIX listings, escaped/symlinked Markdown paths, and stale/unpinned source syntax.
- Checked the markup stack against all 12 official v0.17 sample WXML files and five representative official Ink Page/Widget sources without false positives.
- Verified the final suite at 49/49 unit tests, OpenAI Skill validation, GitHub Skill dry-run discovery, strict project validation, reference validation, Python compilation, Bash syntax, YAML parsing, and whitespace checks.
- Ran published `@yodaos-pkg/aix-cli@0.8.2` against both the fixture and packaged Studio example. Both produced non-empty archives whose exact listings contain generated manifest, `app.json`, and the declared Page.
- Generated a static AIX browser preview for the packaged example and visually confirmed `Preview ready` plus the expected “AIUI project ready” content. This remains browser evidence, not Studio or glasses evidence.
- Installed the Skill to isolated temporary directories with GitHub CLI, discovered it with the generic Skills CLI, and successfully ran the installed copy's bundled AIX smoke flow.
- Ran four fresh forward scenarios with the Skill. Results improved from 8/40 to 40/40 with no critical failures; the Studio scenario was rerun after adding an explicit prohibition on fabricated verification claims.
- Completed independent Studio-contract and adversarial code/CI reviews. Fixed the discovered selector, validator, reference, AIX listing, and pinned-CI execution issues; final reviewers reported no remaining implementation P0/P1.
- Created the public `BreezeLife/rokid-aiui-agent-skill` repository, pushed `main`, and verified its public visibility, default branch, homepage, topics, and published Skill/example paths through the GitHub API.
- Confirmed GitHub Actions run `34138056856` succeeded at commit `bb33dbe4e907aa1fe617690431d60e635c485886`, including both the validation job and the published-AIX packaging job.
- Reinstalled the published repository through both documented paths. `gh skill install` resolved the public `main` branch and copied the complete package; `npx skills add` resolved the same commit, copied all 16 Skill files without a diff, and the installed validator accepted its bundled Studio example in strict `0.17.0` mode.
- Re-ran `gh skill publish . --dry-run` after publication; discovery passed. The authenticated AIUI Studio import and physical-glasses checks remain explicitly separate manual gates.
- Began the first product-shaped project generated with the published Skill. Compared a next-action card, translation card, and field checklist, then selected the offline stable-0.17 `Next Step Agent` to exercise Agent-to-Page input, local interaction state, and `_current`/`_blank` density without unverified capabilities.
- During version-matched source review, found that the Skill's Page definition example omitted the official `schema.data` envelope. Scoped a regression-first correction before generating the new Agent.

## 2026-09-08

- Added a regression for the official Page `schema.data` envelope and corrected the routed Ink authoring reference.
- Defined the Next Step Agent contract before implementation, then applied review-driven fixes covering all five states, 12 invalid transitions, at least 11 boundary and Unicode input cases, per-action element focus, and the official `scroll-view` component.
- Ran the full unit suite with 56/56 passing tests, and accepted `examples/next-step-agent/` with the strict AIUI `0.17.0` validator.
- Pinned both verification jobs to Node.js `24.19.0` and locked `@yodaos-pkg/aix-cli@0.8.2` through `package-lock.json`; local installation used `npm ci`.
- The lockfile-resolved AIX pack/list run produced a `10939`-byte archive containing exactly `AGENTS.md`, `META-INF/aix/manifest.json`, `VERSION`, `app.js`, `app.json`, and `pages/index/index.ink`.
- The lockfile-resolved AIX preview produced `28338` bytes and contained the exact Page path `pages/index/index.ink`.
- Browser inspection showed `Preview ready`, source `next-step-agent`, four files, and a legible green-on-black `_current` empty state at `480x352`, with no overlap or clipping. The console had no errors and one upstream `@yodaos-pkg/ink@0.17.1` deprecated `initialization-parameters` warning.
- This is browser evidence only; it does not prove authenticated AIUI Studio import or physical-device behavior.
- Re-ran the final local gate from the feature branch: all 56 unit tests passed; all four stable/preview fixture and example strict validators exited cleanly; reference and OpenAI Skill validation passed; Bash syntax, both YAML files, and tracked whitespace passed.
- Reinstalled the lockfile with Node.js `24.19.0` and ran all three AIX pack/list gates successfully. The first local attempt exposed an unhealthy Homebrew Node selected by `/usr/bin/env`; explicitly placing the verified Node runtime first on `PATH` fixed the environment, and the complete gate was rerun rather than treating the first attempt as evidence.
- Regenerated the exact Next Step preview at 28,338 bytes, confirmed `pages/index/index.ink`, and completed `gh skill publish . --dry-run`. The dry run passed with only the repository's existing advisory that tag-protection rules are not configured.
- Final delivery review found that reference validation re-scanned Markdown inside installed dependencies. Added a RED/GREEN regression and pruned `.git`, `.worktrees`, and `node_modules` during traversal so the documented local workflow is repeatable after `npm ci` and in repository worktrees.
- Re-ran the complete suite after the review fix: all 57 unit tests passed, including the real Page state-machine harness and the installed-dependency reference regression.
- Recovered the exact verified feature snapshot into a clean clone after iCloud offloaded part of the local Git metadata; recovered files were checked against the original commit blobs before publication.
- Fast-forwarded public `main` to `eb8204799b0cb13aae180e00a30283eb5367b35a` and verified the remote `examples/next-step-agent/app.json` through the GitHub API.
- GitHub Actions run `34158236017` completed successfully: both `Validate skill and examples` and `Package importable projects with published AIX` passed, including the locked preview gate.
