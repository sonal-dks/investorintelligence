#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
OUT_DIR="${ROOT_DIR}/frontend-deploy"
SOURCE_FRONTEND="${ROOT_DIR}/phase-04-dashboard/frontend"

echo "[phase-12] Assembling frontend into ${OUT_DIR}"
rm -rf "${OUT_DIR}"
mkdir -p "${OUT_DIR}"

python3 - <<'PY' "${SOURCE_FRONTEND}" "${OUT_DIR}"
import shutil
import sys
from pathlib import Path

src = Path(sys.argv[1])
dst = Path(sys.argv[2])

for item in src.iterdir():
    if item.name in {"node_modules", "dist", ".env", ".env.local", ".env.production"}:
        continue
    target = dst / item.name
    if item.is_dir():
        shutil.copytree(
            item,
            target,
            ignore=shutil.ignore_patterns("node_modules", "dist", ".env*", "*.tsbuildinfo"),
        )
    else:
        shutil.copy2(item, target)
PY

cp "${ROOT_DIR}/phase-12-assembly-deploy/templates/vercel.json" "${OUT_DIR}/vercel.json"

echo "[phase-12] Frontend assembly complete."
