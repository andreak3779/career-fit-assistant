#!/usr/bin/env bash
# One-time setup: installs this repo's tracked git hooks into .git/hooks/.
#
# Git hooks live outside version control by default (.git/ isn't tracked),
# so a hook committed under scripts/hooks/ does nothing until this is run.
# Re-run it any time scripts/hooks/pre-commit changes.

set -euo pipefail
cd "$(git rev-parse --show-toplevel)"

cp scripts/hooks/pre-commit .git/hooks/pre-commit
chmod +x .git/hooks/pre-commit

echo "Installed scripts/hooks/pre-commit -> .git/hooks/pre-commit"
