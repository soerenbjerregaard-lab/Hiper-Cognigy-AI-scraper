#!/bin/bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT/evidence-dashboard"

# Install dependencies automatically if Evidence CLI is missing.
if [ ! -x "node_modules/.bin/evidence" ]; then
  echo "Installing Evidence dashboard dependencies..."
  npm install
fi

npm run data:build
npm run sources
npm run dev:simlab
