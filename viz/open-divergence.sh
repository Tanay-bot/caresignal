#!/usr/bin/env bash
# Get the latest Divergence visual and open it in Chrome (macOS).
# Usage: bash open-divergence.sh            (clones into ~/caresignal if needed)
#        CARESIGNAL_DIR=/path bash open-divergence.sh
set -euo pipefail

REPO="https://github.com/Tanay-bot/caresignal.git"
BRANCH="claude/divergence-viz-1s4vmd"
DIR="${CARESIGNAL_DIR:-$HOME/caresignal}"

if [ -d "$DIR/.git" ]; then
  echo "Updating $DIR ..."
  git -C "$DIR" fetch origin "$BRANCH"
  git -C "$DIR" checkout "$BRANCH"
  git -C "$DIR" merge --ff-only "origin/$BRANCH"
else
  echo "Cloning into $DIR ..."
  git clone -b "$BRANCH" "$REPO" "$DIR"
fi

FILE="$DIR/viz/divergence.html"
if ! grep -q "What CareSignal does" "$FILE"; then
  echo "ERROR: $FILE is still the old version." >&2
  exit 1
fi
echo "Latest commit: $(git -C "$DIR" log --oneline -1)"

if open -Ra "Google Chrome" 2>/dev/null; then
  open -a "Google Chrome" "$FILE"
else
  open "$FILE"
fi
echo "Opened. Press Cmd+Ctrl+F for fullscreen, click once, then Shift+3."
