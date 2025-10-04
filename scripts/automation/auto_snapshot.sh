#!/usr/bin/env bash
set -euo pipefail
TS="${1:-$(date +%Y%m%d_%H%M%S)}"
NAME="project_snapshot_${TS}.zip"
OUTDIR="snapshots"
mkdir -p "$OUTDIR"
# Exclude common build/venv/cache dirs; tweak as needed:
zip -r "${OUTDIR}/${NAME}" . -x "*/.git/*" "*/__pycache__/*" "*/dist/*" "*/build/*" "*/.ruff_cache/*" "*/.pytest_cache/*"
echo "Created ${OUTDIR}/${NAME}"
