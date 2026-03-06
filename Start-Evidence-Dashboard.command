#!/bin/bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT/evidence-dashboard"

npm run data:build
npm run sources
npm run dev:simlab
