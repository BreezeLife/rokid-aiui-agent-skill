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
