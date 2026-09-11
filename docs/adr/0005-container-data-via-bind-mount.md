# 0005 — Container built from code only; personal data reaches it via bind mount

**Status:** Accepted

## Context

Containerizing with Podman raised a concrete question: three files carry
real personal data (`Resume_Snapshot.md`, `app-engine-bundle.md`,
`pluralsight_learning_history.json` — names, email, phone, career history),
and the running container needs to read them, but nothing should risk
baking that data into an image layer that could later be inspected,
exported, or (even accidentally) pushed somewhere. Research into current
practice for this exact shape of problem (single-user, local-only
container needing sensitive files) consistently pointed at bind mounts
over dedicated secret-management tooling — the latter (HashiCorp Vault,
cloud secret managers) is built for multi-host/production/team deployments
with rotation and audit needs, pure overhead for a tool that never leaves
one machine.

## Decision

`.containerignore` excludes all three PII files (plus `outputs/`) from the
build context entirely — they never enter an image layer, full stop. The
entire repository is then bind-mounted over `/app` at `podman run` time
(`-v <repo>:/app`), so the running container reads Sarah's real, live
host files directly. The image itself contains only a snapshot of the code
plus installed dependencies (`pip install -e .`, editable — imports
redirect back to the mounted `/app` rather than a frozen copy).

## Consequences

- The image is safe to build, inspect, or hand to someone else without
  exposing any personal data — confirmed empirically (`find` over the bare
  image for all three filenames returns nothing).
- Generalizing the same mechanism to *all* data, not just the PII subset,
  answered a second question for free: how do you keep
  `pluralsight_learning_history.json`, `presence-bundle.md`, and
  `roles/*.json` current without rebuilding? You don't — they're live
  through the same mount. The image only needs rebuilding when
  `pyproject.toml`'s dependencies change.
- No at-rest encryption layer sits on top of this today — deliberately.
  `age` and the 1Password/Bitwarden CLIs were researched and documented as
  options, but judged unnecessary given the file already never enters git
  tracking changes or the image; revisit if that changes.
- `Resume_Snapshot.md` — the one PII file of the three that's currently
  *tracked in git* rather than gitignored — was found during this same
  piece of work and deliberately left as-is: a separate decision from the
  container's build-time exclusion, not blocked by or blocking it.
