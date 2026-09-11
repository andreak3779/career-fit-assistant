# 0002 — MCP server is a thin adapter over the CLI, not independent logic

**Status:** Accepted

## Context

The system needs to be usable two ways: from a terminal (`python3 -m
cli.career_fit_api ...`) and from Claude Desktop via MCP. The straightforward
path — give `mcp_server/server.py` its own copy of the generation/rating
logic, tuned for the MCP calling convention — would let the two surfaces
drift: a fix applied to one CLI script wouldn't automatically reach the
matching MCP tool, and vice versa.

## Decision

`mcp_server/server.py` holds no generation logic. Every `@mcp.tool()`
function builds the exact argv list the CLI itself would take, calls
`cli.career_fit_api.main(argv)` in-process with stdout/stderr captured, and
returns what the CLI printed (plus, per ADR
[0005](0005-container-data-via-bind-mount.md)'s unrelated sibling change,
the artifact content that printed path pointed at). The CLI dispatcher
(`cli/career_fit_api.py`) is the one place argv gets turned into a script
call.

## Consequences

- The CLI and MCP surfaces are provably identical in behavior — a bug fixed
  in `cli/career_fit_api.py` or a `project-*/scripts/*.py` generator is fixed
  for both callers simultaneously, with no second copy to remember.
- `tests/test_mcp_server.py` can test tool wrappers by calling the
  decorated Python functions directly (the SDK leaves them callable) and
  trust that CLI-level tests already cover the actual generation logic —
  no duplicated test surface either.
- The one deliberate exception is documented in the module docstring and in
  ADR [0003](0003-fit-gate-enforced-at-mcp-boundary.md): the fit gate is a
  judgment check, not generation logic, and it has to live in the MCP layer
  specifically because that's the boundary a direct tool call can't get
  around.
