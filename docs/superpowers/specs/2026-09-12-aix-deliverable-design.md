# AIX deliverable design

## Goal

Make a verified `.aix` archive a normal additional output of AIUI creation and implementation work while preserving the complete, editable AIUI Studio import root as the primary deliverable.

## Selected approach

The Skill will use a dual-output contract:

1. Always deliver the exact editable source root that contains `app.json`, `AGENTS.md`, the application entry, every declared Page, and all referenced resources.
2. After source validation and tests, probe the selected AIX CLI with `--help`. When `pack` and `list` or `ls` are advertised and execution succeeds, also deliver a non-empty `.aix` archive.
3. Put the archive outside the Studio import root so packaging cannot change the source fingerprint or leak back into a later package. The default recommendation is a sibling path such as `/work/my-agent.aix` for source root `/work/my-agent/`.
4. Inspect the exact handed-off archive with AIX, reject reserved `.git` and `.aiui-evidence` entries, and report its absolute path, byte size, SHA-256, list command, relevant listing, and the source fingerprint captured before and after packaging.
5. If Node/AIX is unavailable or the selected CLI does not advertise both required operations, keep the AIX deliverable `BLOCKED`. If pack/list actually executes but fails, produces an empty package, exposes an invalid listing, or changes the source fingerprint, mark the AIX deliverable `FAIL`. Do not fabricate the archive, weaken the source contract, or claim packaging passed.

The existing `smoke_aix.sh` will gain a persistent mode with an explicit output argument and an explicit repository-root argument. With no output argument it keeps its current temporary smoke-test behavior. Persistent mode snapshots and fingerprints the source in a staging directory next to the requested destination, packages and validates that immutable snapshot, then publishes it through an exclusive no-clobber copy. Filesystem-identity containment rejects case aliases and symlink redirection into the import root; a fixed parent-directory descriptor prevents directory-style target substitution; final listing, inode, size, and digest checks remain bound to the same bytes; and failed cleanup removes only the inode created by the current run. The repository root binds fingerprint exclusions to the intended repository rather than to an inferred parent. This preserves existing CI callers while giving installed-Skill users one deterministic packaging command.

Published AIX `0.8.2` creates a random build ID, so two correct packages of the same source need not have the same SHA-256. The recorded SHA-256 identifies the delivered bytes; the separately recorded unchanged source fingerprint binds the packaging run to the audited source. `.aixignore` may filter development files, but source-root separation and the exact `aix list` result remain the authoritative delivery gate.

## Alternatives rejected

- Committing a prebuilt Focus Timer `.aix` would create a stale binary and would not help a newly generated Agent. Generated archives remain delivery artifacts rather than repository source.
- Placing `.aix` under the Studio import root would change the audited source and can cause recursive package leakage.
- Making the archive replace the source directory conflicts with Studio import and future editing.
- Treating a proposed `aix pack` command as output would provide no execution evidence.

## Documentation contract

The compact `SKILL.md` will state the dual-output rule and route mechanics to `references/aix-workflow.md`. The reference will define ordering, output placement, command capability probing, successful handoff fields, and separate result semantics: unavailable or unsupported tooling is `BLOCKED`, while an attempted packaging, inventory, destination, or fingerprint failure is `FAIL`. The root README and Chinese, English, and Japanese guides will consistently describe `.aix` as an additional deliverable when supported and successfully produced.

The copyable creation prompts will explicitly request the archive. The verification examples will preserve it through the persistent output and repository-root arguments rather than deleting it with a temporary smoke run. Studio instructions will continue to point at the source root, never the `.aix` file.

## Test strategy

Add semantic tests before implementation that require:

- the Skill to distinguish the always-required source root from the conditional verified archive;
- the AIX reference to require an external destination, no overwrite, pack/list inspection, SHA-256, byte size, and honest `BLOCKED`/`FAIL` reporting;
- all three guides to carry the same dual-output semantics and executable output command;
- the packaging script to preserve a verified archive at an explicit path, print its metadata, reject overwrite and in-root destinations, and leave no output after failed inspection;
- the repository not to track generated `.aix` archives.

After RED/GREEN, run the full unit suite, Skill/reference validators, strict AIUI project validators, the real pinned AIX pack/list flows including a persistent delivery artifact in a temporary external directory, preview, and whitespace checks. AIUI Studio and physical-device gates remain independent and `BLOCKED` unless actually executed.

## Scope

This change does not publish an Agent, upload an archive, add another bundled product Agent, or modify AIUI runtime behavior.
