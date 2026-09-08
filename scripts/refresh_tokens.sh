#!/usr/bin/env bash
# Daily refresh of the Claude Code token meter. The transcripts it counts are
# machine-local, so the fetch cannot run in Actions. A systemd user timer runs
# this instead: mithils3-tokens.timer.
set -uo pipefail
export PATH="/usr/local/bin:/usr/bin:/bin:$HOME/.local/bin"
export GIT_SSH_COMMAND="ssh -o BatchMode=yes"
cd "$(dirname "$0")/.." || exit 1

[ "$(git symbolic-ref --short HEAD)" = main ] || { echo "not on main, skipping"; exit 0; }
git diff --quiet && git diff --cached --quiet || { echo "working tree dirty, skipping"; exit 0; }

git pull --rebase --quiet origin main || { echo "pull failed"; exit 1; }
python3 scripts/fetch_claude_tokens.py || exit 1
python3 scripts/build_svgs.py >/dev/null || exit 1

git add data/claude-tokens.json assets
git diff --cached --quiet && { echo "no change"; exit 0; }
git commit -q -m "chore: refresh the token meter" || exit 1
git push --quiet origin main || { echo "push failed, commit is local"; exit 1; }
echo "pushed $(git rev-parse --short HEAD)"
