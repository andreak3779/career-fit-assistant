# 0003 — Fit gate enforced in code at the MCP boundary

**Status:** Accepted

## Context

The `create-a-cover-letter-and-tailored-resume-for-job-description` skill
already states the rule "only generate if the fit rating is Strong or
Good" — but that's prompt-level guidance Claude follows when it's the one
deciding to invoke the skill. An MCP client (Claude Desktop, or any other
MCP-capable app) calling `generate_resume` or `generate_cover_letter`
directly skips the skill, and the rule, entirely. The rule needed to be
true regardless of who or what is calling the tool.

## Decision

`mcp_server/server.py`'s `_require_good_fit()` re-runs the same
`parse_jd`/`rate_fit` computation the underlying scripts already do
internally, as a precondition inside `generate_resume`,
`generate_cover_letter`, and `generate_application_documents`. Below a
Good rating it raises a `ToolError` with the rating and rationale instead
of dispatching to the CLI — no document gets written, no MCP client can
work around it by calling the tool a different way.

## Consequences

- The rule is enforced identically whether Claude is following the skill's
  guidance or an MCP client is calling the tool cold — there's exactly one
  place this can be bypassed from (editing `mcp_server/server.py` itself),
  not two independent surfaces to keep in sync.
- The rating gets computed twice per gated call (once by
  `_require_good_fit()`, once more inside the generator script it then
  dispatches to) — accepted as cheap and deterministic (ADR
  [0001](0001-deterministic-fit-engine.md)) rather than worth threading a
  precomputed `FitResult` through the CLI's argv boundary.
- Test fixtures need at least one JD that genuinely rates Strong against
  the real profile bundle (`tests/fixtures/strong-fit-jd.md`) — none of the
  repo's original JD fixtures did, which was a real gap this decision
  surfaced and required fixing before the gated tests could be written.
- `generate_cold_call` and `generate_job_site_letter` are deliberately
  **not** gated this way — they're governed by different skills that don't
  carry this rule, and gating them would be inventing a constraint nobody
  asked for.
