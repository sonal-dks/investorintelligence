#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
OUT_DIR="${ROOT_DIR}/backend-deploy"
TMP_REQ="${OUT_DIR}/requirements._all.txt"
PACKAGES_DIR="${OUT_DIR}/packages"

echo "[phase-12] Assembling backend into ${OUT_DIR}"
rm -rf "${OUT_DIR}"
mkdir -p "${OUT_DIR}/app" "${PACKAGES_DIR}"

rewrite_backend_imports() {
  local pkg_dir="$1"
  local pkg_name="$2"
  while IFS= read -r -d '' f; do
    perl -pi -e "s/from backend\\./from ${pkg_name}./g" "$f"
    perl -pi -e "s/from backend import/from ${pkg_name} import/g" "$f"
    perl -pi -e "s/import backend\\.config/import ${pkg_name}.config/g" "$f"
  done < <(find "${pkg_dir}" -name '*.py' -print0)
}

copy_isolated() {
  local rel_src="$1"
  local pkg_name="$2"
  local dest="${PACKAGES_DIR}/${pkg_name}"
  rm -rf "${dest}"
  cp -R "${ROOT_DIR}/${rel_src}" "${dest}"
  touch "${dest}/__init__.py"
  rewrite_backend_imports "${dest}" "${pkg_name}"
}

# Unique package names avoid import collisions in one interpreter.
copy_isolated "phase-02-rag-pipeline/backend" "backend_ph02"
copy_isolated "phase-03-auth/backend" "backend_ph03"
copy_isolated "phase-04-dashboard/backend" "backend_ph04"
copy_isolated "phase-05-smart-search/backend" "backend_ph05"
copy_isolated "phase-06-voice-agent/backend" "backend_ph06"
copy_isolated "phase-07-intent-approvals/backend" "backend_ph07"
copy_isolated "phase-08-calendar-booking/backend" "backend_ph08"
copy_isolated "phase-09-weekly-pulse/backend" "backend_ph09"
copy_isolated "phase-10-explorer-resources/backend" "backend_ph10"
copy_isolated "phase-11-evaluation-suite/backend" "backend_ph11"

touch "${OUT_DIR}/app/__init__.py"
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
