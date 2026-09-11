# 0007 — Lazy per-submodule imports in `shared/` instead of eager package-level imports

**Status:** Accepted

## Context

`shared/__init__.py` re-exports the public surface of every submodule
(`bundle_loader`, `docx_layout`, `fit_engine`, `jd_parser`, `markdown_sources`,
`models`, `pii_guard`) so callers can write `from shared import rate_fit,
load_profile_bundle` instead of reaching into individual files. Doing that
with ordinary `from shared.X import ...` statements at the top of
`__init__.py` means importing `shared` at all — which every CLI command and
MCP tool does, directly or through `cli/career_fit_api.py` — eagerly imports
every submodule too, including their third-party dependencies:
`bundle_loader` needs `jsonschema`, `docx_layout` needs `python-docx`,
`markdown_sources` needs `pyyaml`. A read-only command like `fit-check`,
which never touches a `.docx` file or raw markdown, paid for all three
anyway. Found by reproducing a documented-install failure in scratch venvs
during a dependency audit: `pip install -e ".[schema]"` (correctly scoped
for `fit-check`'s own imports) still failed with `ModuleNotFoundError: No
module named 'yaml'` the moment `shared` was imported at all.

## Decision

Replaced the eager imports in `shared/__init__.py` with PEP 562 module-level
lazy attribute resolution: a `_ATTR_SOURCES` dict maps each re-exported name
to the submodule that defines it, and a module `__getattr__` imports that
submodule — and only that submodule — the first time one of its names is
actually accessed, caching the result in `globals()` so the cost is paid at
most once per process. The real submodules (`shared/bundle_loader.py`,
`shared/docx_layout.py`, etc.) are unchanged; only how `shared/__init__.py`
re-exports their names changed. `__all__` and every existing `from shared
import X` call site are unchanged.

## Consequences

- There is now a real per-command dependency floor, verified empirically
  rather than assumed: `fit-check`/`gap-analysis`/`generate-linkedin`/
  `generate-github` need only `jsonschema` (`bundle_loader`, `fit_engine`,
  `jd_parser`, `models` are pure-stdlib beyond that); `build`/`validate`
  need `jsonschema`+`pyyaml` (they parse raw source markdown via
  `markdown_sources`); the letter-generation commands need
  `jsonschema`+`python-docx`; `interview-prep` needs all three.
- This isn't advertised as a way to hand-pick a minimal install per command
  — the documented setup paths (root `README.md`, `GETTING_STARTED.md`,
  `mcp_server/README.md`) still install the full extras set by default,
  since most real sessions call more than one command. The narrower floor
  exists so a partial install fails at the specific missing dependency
  instead of at whichever submodule happened to be first in `__init__.py`,
  and so future submodules don't silently inherit an ever-growing shared
  dependency footprint.
- Verified with the full `pytest` suite (348 passed, coverage unchanged at
  ~96%) plus `ruff check`, `ruff format --check`, and `mypy shared/ cli/`,
  all clean — the lazy-loading change is invisible to every existing caller.
- A static-analysis cost: `shared/__init__.py`'s exports no longer appear
  as ordinary module-level bindings to tools that don't understand PEP 562
  (mitigated here with a `TYPE_CHECKING`-guarded import block carrying the
  same names, so `mypy` and editor autocomplete still resolve them).
