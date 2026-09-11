# 0001 — Deterministic fit-rating engine instead of an LLM call

**Status:** Accepted

## Context

Every generation path in this system needs to answer one question first:
does Sarah's actual profile fit a given job description well enough to be
worth drafting for? That question could be answered by asking an LLM to
read the JD and the profile and render a judgment, or by computing it.

## Decision

`shared/fit_engine.py`'s `rate_fit()` is plain, deterministic Python: it
expands a skill-alias registry, splits compound phrases in the JD, and
classifies each required/nice-to-have skill against the profile's evidence
level (production use, project use, course-level, absent), then rolls that
up into one of four fixed ratings — Strong / Good / Stretch / Pass — with a
rationale string built from the same classification, not a separate
explanation pass.

## Consequences

- Fully reproducible and unit-testable — the same JD against the same
  profile always produces the same rating, byte for byte. Most of the 348
  tests in this repo exist because this is testable in the first place.
- Zero runtime API cost, latency, or network dependency for the single
  most-run operation in the system (`fit_check`, and the gate every
  document-generation tool runs first).
- The rating is only as good as the alias registry and evidence rules
  behind it — a skill phrased in a way the registry doesn't recognize reads
  as a gap even if the underlying experience covers it. This is accepted
  maintenance burden, not a defect: the registry gets extended as real JDs
  surface gaps in it, the same way the two real parser bugs found and fixed
  earlier in this project's history were.
- An LLM-based rating would flex better to novel phrasing but couldn't give
  the hard guarantee ADR
  [0003](0003-fit-gate-enforced-at-mcp-boundary.md) depends on: that the
  same inputs always produce the same gate decision, checkable in a test
  without mocking a model call.
