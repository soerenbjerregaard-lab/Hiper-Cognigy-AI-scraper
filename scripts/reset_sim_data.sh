#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

TS="$(date +%Y%m%d-%H%M%S)"
mkdir -p "exports/archive/$TS"

found=0
for f in exports/*.csv exports/runmeta-*.json; do
  [ -e "$f" ] || continue
  mv "$f" "exports/archive/$TS/"
  found=1
done

: > conversations.db
rm -f simlab.db

if [ "$found" -eq 1 ]; then
  echo "Archived prior exports to exports/archive/$TS"
else
  echo "No exports found to archive"
fi

echo "Reset complete: conversations.db truncated, simlab.db removed"
