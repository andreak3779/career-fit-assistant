# 0006 — Three separate project domains instead of one flat structure

**Status:** Accepted

## Context

`project-1-application-engine`, `project-2-profile-learning-hub`, and
`project-3-presence-identity` each have their own `skills/`, reference
data, and `CLAUDE.md`, and now share one CLI dispatcher, one MCP server,
and one `shared/` core. Once containerization made "run everything from
one image" the deployment model, it was worth asking directly whether the
three-way split still earned its keep or was left over from before the CLI
unified them.

## Decision

Keep them separate. The split isn't a packaging artifact — it encodes a
real privacy boundary the code itself enforces:
`project-2-profile-learning-hub/skills/profile_hub_bundle_generator/scripts/build_bundles.py`
calls `assert_presence_safe()` specifically when generating
`project-3-presence-identity`'s `presence-bundle.json` (public-facing
content), but not when generating `project-1-application-engine`'s
full-detail bundle. Flattening the three directories into one would turn
that boundary from something the build step checks into something a
human has to remember.

## Consequences

- The PII/public-safety boundary between "full CV detail" and
  "presence-scanned, safe for a LinkedIn/GitHub update" stays a build-time
  check, not a convention that quietly erodes as files move around.
- Each project can still function as its own Claude Code working context
  (its own `CLAUDE.md`) for someone working inside just that subdirectory.
- The cost is real, paid once: `pyproject.toml` needs an explicit
  `package-dir` remap (the on-disk directories use dashes,
  `project-1-application-engine`; the import contract needs underscores,
  `project_1_application_engine`) since `setuptools`' package auto-discovery
  can't bridge that gap on its own.
- Containerizing didn't change this calculus either way — the bind-mount
  design in ADR [0005](0005-container-data-via-bind-mount.md) mounts the
  whole repo as one unit, so the internal project boundaries are invisible
  to the container regardless of whether they're flat or split.
