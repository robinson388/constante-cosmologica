#!/usr/bin/env bash
# One-time: gh auth login
# Then: bash publish_github.sh [repo-name]
set -euo pipefail
cd "$(dirname "$0")"

REPO="${1:-constante-cosmologica}"
DESC="IR matching of the cosmological constant (PRD note, scripts, CI)"

if ! gh auth status >/dev/null 2>&1; then
  echo "Run first: gh auth login"
  exit 1
fi

if git remote get-url origin >/dev/null 2>&1; then
  echo "Remote origin already set; pushing main..."
  git push -u origin main
else
  gh repo create "$REPO" --public --description "$DESC" --source=. --remote=origin --push
fi

echo ""
echo "Done. Open: https://github.com/$(gh api user -q .login)/${REPO}"
