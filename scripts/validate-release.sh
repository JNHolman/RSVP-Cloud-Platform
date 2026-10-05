#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
STRICT_RELEASE="${STRICT_RELEASE:-0}"
SKIPPED=0

mapfile -t stacks <<STACKS
$ROOT/infrastructure/bootstrap-state
$ROOT/infrastructure/project-1-cloud-platform
$ROOT/infrastructure/project-2-ecs-cicd/bootstrap-delivery
$ROOT/infrastructure/project-2-ecs-cicd/terraform
$ROOT/infrastructure/project-3-cloud-governance/organization
$ROOT/infrastructure/project-3-cloud-governance/security-admin
$ROOT/infrastructure/project-3-cloud-governance/log-archive
$ROOT/infrastructure/project-3-cloud-governance/audit-trail
$ROOT/infrastructure/project-3-cloud-governance/identity-center
$ROOT/infrastructure/project-3-cloud-governance/workload
$ROOT/infrastructure/project-3-cloud-governance/finops-ai
STACKS

cleanup_generated() {
  find "$ROOT" -type d \
    \( -name '__pycache__' -o -name '.pytest_cache' -o -name '.ruff_cache' \) \
    -prune -exec rm -rf {} + 2>/dev/null || true
  find "$ROOT" -type f -name '*.pyc' -delete 2>/dev/null || true
}

cleanup_generated
trap cleanup_generated EXIT

for arg in "$@"; do
  case "$arg" in
    --strict)
      STRICT_RELEASE=1
      ;;
    *)
      echo "Unknown argument: $arg" >&2
      echo "Usage: $0 [--strict]" >&2
      exit 64
      ;;
  esac
done

python - <<'PY' "$ROOT"
import ast
import pathlib
import sys

root = pathlib.Path(sys.argv[1])
paths = [
    root / "infrastructure/project-1-cloud-platform",
    root / "infrastructure/project-2-ecs-cicd/app",
    root / "infrastructure/project-3-cloud-governance/security-admin",
    root / "infrastructure/project-3-cloud-governance/finops-ai",
    root / "infrastructure/project-3-cloud-governance/workload",
    root / "tests",
]
for base in paths:
    for path in base.rglob("*.py"):
        ast.parse(path.read_text(), filename=str(path))
PY

python - <<'PY' "$ROOT"
import pathlib, sys, yaml
root = pathlib.Path(sys.argv[1]) / ".github" / "workflows"
for path in root.glob("*.yml"):
    yaml.safe_load(path.read_text())
PY

# Runtime AI regression tests are dependency-isolated and must run even on a
# workstation that does not have the Flask application dependencies installed.
if python -c 'import pytest' >/dev/null 2>&1; then
  (cd "$ROOT" && PYTHONDONTWRITEBYTECODE=1 python -m pytest -q -p no:cacheprovider tests)
else
  echo "SKIP: pytest unavailable; runtime AI regression tests not executed." >&2
  SKIPPED=1
fi

while IFS= read -r -d '' script; do
  bash -n "$script"
done < <(find "$ROOT/ops" -type f -name '*.sh' -print0)

if grep -RIEq 'assign_public_ip\s*=\s*true|associate_public_ip_address\s*=\s*true' "$ROOT/infrastructure" --include='*.tf'; then
  echo "Public workload IP regression found" >&2
  exit 1
fi

if grep -RIEq 'allow_origins\s*=\s*\["\*"\]|Access-Control-Allow-Origin.*\*' "$ROOT/infrastructure" --include='*.tf' --include='*.py'; then
  echo "Wildcard CORS regression found" >&2
  exit 1
fi

if grep -RIEq 'OPENAI_API_KEY\s*=\s*var\.|variable "openai_api_key"' "$ROOT/infrastructure" --include='*.tf'; then
  echo "Plaintext OpenAI Terraform secret regression found" >&2
  exit 1
fi

if grep -RIEq '156\.78|Sample data - Cost Explorer' "$ROOT/infrastructure/project-3-cloud-governance/finops-ai"; then
  echo "Synthetic cost fallback regression found" >&2
  exit 1
fi

if grep -RIEq 'amzn2-ami|Amazon Linux 2' "$ROOT/infrastructure" --include='*.tf' --include='*.md'; then
  echo "Amazon Linux 2 regression found" >&2
  exit 1
fi

if command -v terraform >/dev/null 2>&1; then
  terraform fmt -check -recursive "$ROOT/infrastructure"
  for stack in "${stacks[@]}"; do
    (cd "$stack" && terraform init -backend=false -input=false >/dev/null && terraform validate)
  done
else
  echo "SKIP: terraform executable not installed; fmt/init/validate not executed." >&2
  SKIPPED=1
fi

if python -c 'import flask, pytest' >/dev/null 2>&1; then
  (cd "$ROOT" && PYTHONDONTWRITEBYTECODE=1 python -m pytest -q -p no:cacheprovider infrastructure/project-2-ecs-cicd/app/tests)
else
  echo "SKIP: Flask/pytest dependencies unavailable; app tests not executed." >&2
  SKIPPED=1
fi

# Mirror CI's blocking quality/security gates. A strict local certification must
# not claim success merely because Terraform and unit tests happened to run.
if command -v ruff >/dev/null 2>&1; then
  (cd "$ROOT" && ruff check \
    infrastructure/project-1-cloud-platform/ai_log_summarizer.py \
    infrastructure/project-2-ecs-cicd/app \
    infrastructure/project-3-cloud-governance/security-admin/ai_incident_analyzer.py \
    infrastructure/project-3-cloud-governance/finops-ai/cost_analyzer.py \
    infrastructure/project-3-cloud-governance/workload/dashboard_api.py \
    tests)
else
  echo "SKIP: Ruff unavailable; Python lint gate not executed." >&2
  SKIPPED=1
fi

if command -v pip-audit >/dev/null 2>&1; then
  (cd "$ROOT" && pip-audit -r infrastructure/project-2-ecs-cicd/app/requirements.txt)
else
  echo "SKIP: pip-audit unavailable; dependency vulnerability audit not executed." >&2
  SKIPPED=1
fi

if command -v checkov >/dev/null 2>&1; then
  (cd "$ROOT" && checkov -d infrastructure --framework terraform --config-file .checkov.yml --quiet)
else
  echo "SKIP: Checkov unavailable; IaC security gate not executed." >&2
  SKIPPED=1
fi

if command -v tflint >/dev/null 2>&1; then
  for stack in "${stacks[@]}"; do
    if [[ -n "$stack" ]]; then
      (cd "$stack" && tflint --init >/dev/null && tflint --recursive)
    fi
  done
else
  echo "SKIP: TFLint unavailable; Terraform lint gate not executed." >&2
  SKIPPED=1
fi

if command -v docker >/dev/null 2>&1 && command -v trivy >/dev/null 2>&1; then
  IMAGE_TAG="rsvp-project2-release-validation:local"
  docker build -t "$IMAGE_TAG" "$ROOT/infrastructure/project-2-ecs-cicd/app"
  trivy image --exit-code 1 --ignore-unfixed --severity HIGH,CRITICAL "$IMAGE_TAG"
else
  echo "SKIP: Docker and/or Trivy unavailable; container vulnerability gate not executed." >&2
  SKIPPED=1
fi

if [[ "$STRICT_RELEASE" == "1" && "$SKIPPED" != "0" ]]; then
  echo "Release certification failed because mandatory checks were skipped." >&2
  exit 2
fi

if [[ "$SKIPPED" == "0" ]]; then
  echo "Release checks passed with no mandatory checks skipped."
else
  echo "Available checks passed; release certification is incomplete because mandatory checks were skipped."
fi
