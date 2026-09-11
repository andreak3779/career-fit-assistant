# Architecture Decision Records

Short records of the decisions that shape `career-fit-assistant`, in the order they
were made. Each follows the same shape: Context (the problem, as it was
actually encountered), Decision, Consequences (including the ones we
accepted rather than solved).

| # | Decision | Status |
| --- | --- | --- |
| [0001](0001-deterministic-fit-engine.md) | Deterministic fit-rating engine instead of an LLM call | Accepted |
| [0002](0002-mcp-thin-adapter-over-cli.md) | MCP server is a thin adapter over the CLI, not independent logic | Accepted |
| [0003](0003-fit-gate-enforced-at-mcp-boundary.md) | Fit gate enforced in code at the MCP boundary | Accepted |
| [0004](0004-stdio-only-transport.md) | stdio transport only — no network-facing MCP server | Accepted (revisit if a LAN setup is built) |
| [0005](0005-container-data-via-bind-mount.md) | Container built from code only; personal data reaches it via bind mount | Accepted |
| [0006](0006-separate-project-domains.md) | Three separate project domains instead of one flat structure | Accepted |
| [0007](0007-lazy-submodule-imports-in-shared.md) | Lazy per-submodule imports in `shared/` instead of eager package-level imports | Accepted |
