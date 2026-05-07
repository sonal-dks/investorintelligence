#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
OUT_DIR="${ROOT_DIR}/backend-deploy"
TMP_REQ="${OUT_DIR}/requirements._all.txt"

echo "[phase-12] Assembling backend into ${OUT_DIR}"
rm -rf "${OUT_DIR}"
mkdir -p "${OUT_DIR}/app" "${OUT_DIR}/phases"

PHASE_BACKENDS=(
  "phase-03-auth/backend"
  "phase-04-dashboard/backend"
  "phase-05-smart-search/backend"
  "phase-06-voice-agent/backend"
  "phase-07-intent-approvals/backend"
  "phase-08-calendar-booking/backend"
  "phase-09-weekly-pulse/backend"
  "phase-10-explorer-resources/backend"
  "phase-11-evaluation-suite/backend"
)

# Phase-02 uses backend/app.py rather than backend/main.py
mkdir -p "${OUT_DIR}/phases/phase-02-rag-pipeline"
cp -R "${ROOT_DIR}/phase-02-rag-pipeline/backend" "${OUT_DIR}/phases/phase-02-rag-pipeline/"

for phase_backend in "${PHASE_BACKENDS[@]}"; do
  phase_name="$(echo "${phase_backend}" | cut -d'/' -f1)"
  mkdir -p "${OUT_DIR}/phases/${phase_name}"
  cp -R "${ROOT_DIR}/${phase_backend}" "${OUT_DIR}/phases/${phase_name}/"
done

cp "${ROOT_DIR}/phase-12-assembly-deploy/templates/backend_main.py" "${OUT_DIR}/app/main.py"
cp "${ROOT_DIR}/phase-12-assembly-deploy/templates/render.yaml" "${OUT_DIR}/render.yaml"

echo "# Auto-generated consolidated requirements" > "${TMP_REQ}"
for req in "${ROOT_DIR}"/phase-*/requirements.txt; do
  [ -f "${req}" ] || continue
  echo "" >> "${TMP_REQ}"
  echo "# from $(basename "$(dirname "${req}")")" >> "${TMP_REQ}"
  cat "${req}" >> "${TMP_REQ}"
done

python3 - <<'PY' "${TMP_REQ}" "${OUT_DIR}/requirements.txt"
import sys
from pathlib import Path

src = Path(sys.argv[1]).read_text(encoding="utf-8").splitlines()
out = []
seen = set()
for line in src:
    raw = line.strip()
    if not raw:
        if out and out[-1] != "":
            out.append("")
        continue
    if raw.startswith("#"):
        continue
    key = raw.lower()
    if key in seen:
        continue
    seen.add(key)
    out.append(raw)
Path(sys.argv[2]).write_text("\n".join(out).strip() + "\n", encoding="utf-8")
PY

rm -f "${TMP_REQ}"
echo "[phase-12] Backend assembly complete."
