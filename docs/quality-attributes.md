# Quality attributes

What this system optimizes for, stated plainly rather than left to be
reverse-engineered from code and CI config. See `docs/adr/` for the
decisions behind each of these.

## Determinism & reproducibility

No LLM call happens at runtime anywhere in `shared/`, `cli/`, or
`mcp_server/` — `rate_fit()`, the markdown parsers, and the DOCX/PDF
layout code are plain Python (ADR
[0001](adr/0001-deterministic-fit-engine.md)). The same job description
against the same profile bundle always produces the same fit rating, the
same rationale text, and the same generated document content. This is
what makes the 348-test suite meaningful rather than a suite of
mocked-model assertions.

## Security & data privacy

- **No network exposure.** The MCP server only ever speaks stdio (ADR
  [0004](adr/0004-stdio-only-transport.md)) — no port is bound, so there's
  no authentication surface to build or forget.
- **PII inventory** (three files, confirmed by direct repo audit, not
  assumption):
  - `project-1-application-engine/app-engine-bundle.md` — gitignored,
    regenerated locally, never committed.
  - `project-2-profile-learning-hub/pluralsight_learning_history.json` —
    gitignored, never committed.
  - `project-2-profile-learning-hub/Resume_Snapshot.md` — **tracked in
    git today** (full name, email, phone, city, province). Found during
    the containerization work; the decision was made to leave it tracked
    rather than untrack or rewrite history — recorded here so it isn't
    mistaken for an oversight.
  - A real phone number is also hardcoded as fixture text across five
    tracked test files, needed only in shape, not in being the real
    number — a known, low-severity loose end, not yet cleaned up.
- **Containment.** None of the three PII files ever enter a container
  image layer (ADR [0005](adr/0005-container-data-via-bind-mount.md)),
  confirmed empirically by scanning the built image for all three
  filenames.
- **No at-rest encryption layer** on top of gitignore/`.containerignore`
  today — researched (`age`, 1Password/Bitwarden CLI) and deliberately
  deferred, not overlooked.
- **CI's `pii-guard` job** actively fails a PR if `app-engine-bundle.md`
  is ever staged or tracked — a real, running check, not just a policy
  statement.

## Testing & CI gates

- `pytest tests/ -q` — 348 tests, run against real fixtures
  (`tests/fixtures/*.md`) and the actual bundle-loading/fit-rating code,
  not mocks of it.
- Coverage gate: 80% floor on `shared`/`cli`, enforced in CI
  (`--cov-fail-under=80`; measured coverage sits around 90%).
- `ruff check` — enforced both in CI and via a local pre-commit hook, so
  it's effectively unbypassable on every commit.
- `mypy` — run in CI as its own job, but **not** a merge gate and
  explicitly skipped by the local pre-commit hook (documented there as
  "slower than what belongs on every commit"). Known type gaps are
  tracked via `[[tool.mypy.overrides]]` in `pyproject.toml` rather than
  silenced ad hoc.
- Separate CI jobs validate JSON bundle schema conformance
  (`bundle-schema`), DOCX template syntax (`template-syntax`, Node-based),
  and the PII guard above — each a narrow, fast check rather than one
  monolithic job.

## Operational model

- **Single user, single machine, no SLA.** This is a personal tool, not a
  service — "availability" means "the machine Sarah is using is on,"
  which is also why the same-machine container design (ADR
  [0004](adr/0004-stdio-only-transport.md)) was chosen over a
  separate-always-on host: the latter would trade a real security/uptime
  cost for no corresponding benefit at this scale.
- **No horizontal scaling path, and none needed** — every operation is a
  single local computation over a profile bundle measured in tens of
  kilobytes.
- **Rebuild vs. live-edit boundary is explicit**: the container image
  only needs rebuilding when `pyproject.toml`'s dependencies change; all
  code and data edits reach the running container live through the
  bind mount (ADR [0005](adr/0005-container-data-via-bind-mount.md)).

## Known deferred work

Recorded here rather than left implicit, so revisiting any of these is a
decision, not a rediscovery:

- Network-reachable MCP server (a separate LAN machine) — deferred, not
  ruled out; needs an authentication story first (ADR
  [0004](adr/0004-stdio-only-transport.md)).
- Git history for `Resume_Snapshot.md` — currently tracked; untracking or
  history-rewriting was explicitly deferred as a separate piece of work.
- At-rest encryption for the three PII files — researched, not
  implemented.
- Real phone number hardcoded in five test fixtures — should be swapped
  for an obviously-fake one; low severity, not yet done.
