#!/usr/bin/env bash
set -euo pipefail

PROJECT_ID="${PROJECT_ID:?Set PROJECT_ID}"
REGION="${REGION:-asia-south1}"
SERVICE="${SERVICE:-sage-career-backend}"
ENV_FILE="${ENV_FILE:-deploy/cloud-run/backend.env.yaml}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
BACKEND_PATH="${REPO_ROOT}/backend"
ENV_PATH="${REPO_ROOT}/${ENV_FILE}"

if [[ ! -f "${ENV_PATH}" ]]; then
  echo "Missing env file: ${ENV_PATH}" >&2
  echo "Copy deploy/cloud-run/backend.env.yaml.example to deploy/cloud-run/backend.env.yaml and fill production values." >&2
  exit 1
fi

JWT_SECRET="$(awk -F: '/^[[:space:]]*JWT_SECRET[[:space:]]*:/ { sub(/^[[:space:]]+/, "", $2); sub(/[[:space:]]+$/, "", $2); gsub(/^["'\'']|["'\'']$/, "", $2); print $2; exit }' "${ENV_PATH}")"
if [[ -z "${JWT_SECRET}" ]]; then
  echo "Missing JWT_SECRET in ${ENV_PATH}. Add a production secret with at least 32 characters before deploying." >&2
  exit 1
fi

if [[ ${#JWT_SECRET} -lt 32 || "${JWT_SECRET}" == __SET_* || "${JWT_SECRET}" == replace-with* ]]; then
  echo "JWT_SECRET in ${ENV_PATH} must be replaced with a real production secret of at least 32 characters." >&2
  exit 1
fi

gcloud config set project "${PROJECT_ID}"
gcloud run deploy "${SERVICE}" \
  --source "${BACKEND_PATH}" \
  --region "${REGION}" \
  --port 8080 \
  --env-vars-file "${ENV_PATH}" \
  --allow-unauthenticated
