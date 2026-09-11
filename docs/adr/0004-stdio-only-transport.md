# 0004 — stdio transport only — no network-facing MCP server

**Status:** Accepted (revisit if a LAN setup is built)

## Context

While scoping container support, a separate-Linux-PC-on-the-LAN option was
explored: the MCP SDK supports a `streamable-http` transport that could let
a container on a different machine be reached over the network, with
Claude Desktop pointed at it as a remote connector instead of a local
stdio command. That path was prototyped as far as identifying the concrete
mechanism (`mcp.run(transport="streamable-http", host=..., port=...)`,
`TransportSecuritySettings` for the DNS-rebinding allowlist) before being
weighed against the same-machine alternative.

## Decision

`mcp_server/server.py` keeps the SDK's default transport (`mcp.run()` with
no `transport` argument — stdio). Claude Desktop always spawns the server
as a local child process, whether that's the bare `python3 -m
mcp_server.server` command or `podman run -i --rm ...` (ADR
[0005](0005-container-data-via-bind-mount.md)) — Docker/Podman being local
child processes either way, stdio framing passes through unchanged with no
server code required to know the difference.

## Consequences

- Zero network attack surface: the server never binds a port, so there's
  nothing to authenticate, firewall, or expose by accident. This mattered
  concretely — the streamable-http path as scoped would have had **no
  auth layer**, meaning anything else on the LAN could call every tool,
  including generating documents from real profile data.
- The tool can only ever be used by Claude Desktop running on the same
  machine as the server. The separate-LAN-PC scenario is explicitly
  deferred, not ruled out — the note in `mcp_server/README.md` and this
  ADR exist so that choice doesn't get silently re-litigated later without
  the auth gap being addressed first.
- If a future LAN setup is built, it needs its own decision (and likely its
  own ADR) covering authentication — this decision does not pre-approve
  that path, only leaves it open.
