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
