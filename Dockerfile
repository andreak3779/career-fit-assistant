FROM python:3.11-slim

WORKDIR /app

# Copy dependency metadata first so the pip install layer only invalidates
# when pyproject.toml actually changes, not on every source edit.
COPY pyproject.toml ./
COPY shared ./shared
COPY cli ./cli
COPY mcp_server ./mcp_server
COPY project-1-application-engine ./project-1-application-engine
COPY project-2-profile-learning-hub ./project-2-profile-learning-hub
COPY project-3-presence-identity ./project-3-presence-identity
COPY tests ./tests
COPY README.md ./README.md

# Deliberately no Node.js here: this image only ever runs the MCP server
# (mcp_server/server.py -> cli/career_fit_api.py), and that path generates
# DOCX files purely in Python (shared/docx_layout.py + python-docx, installed
# by the `docx` extra below). Node.js (project-1-application-engine/package.json)
# is only needed for the separate live-chat SKILL.md workflow, which shells
# out to templates/*.js directly — see README.md's setup-dependency diagram.
RUN pip install --no-cache-dir -e ".[mcp,docx,parser,yaml,schema,pdf,dev]"

# shared/bundle_loader.py's _find_repo_root() locates the repo by checking
# for README.md + an outputs/ directory relative to cwd — the directory
# must exist even without a bind mount (e.g. running tests in the bare
# image), and it's gitignored/containerignored so COPY never creates it.
RUN mkdir -p outputs

CMD ["python3", "-m", "mcp_server.server"]
