#!/usr/bin/env bash
# install.sh — copy agent-loop into a target repo (Option B, no plugin install).
# Usage: ./install.sh /path/to/your/repo
set -euo pipefail

TARGET="${1:-}"
if [ -z "$TARGET" ] || [ ! -d "$TARGET" ]; then
  echo "usage: ./install.sh /path/to/your/repo" >&2
  exit 1
fi

HERE="$(cd "$(dirname "$0")" && pwd)"
SRC="$HERE/plugins/agent-loop"

mkdir -p "$TARGET/.claude/skills" "$TARGET/.loop"
cp -R "$SRC/skills/spawn-loop" "$TARGET/.claude/skills/spawn-loop"
cp -R "$SRC/skills/loop-tick"  "$TARGET/.claude/skills/loop-tick"
cp "$SRC/loop/loop.py"        "$TARGET/.loop/loop.py"
cp "$SRC/loop/profiles.json"  "$TARGET/.loop/profiles.json"

echo "installed agent-loop into $TARGET"
echo "  .claude/skills/{spawn-loop,loop-tick}"
echo "  .loop/{loop.py,profiles.json}"
echo "next: open Claude Code in $TARGET and run  /spawn-loop \"<your goal>\""
