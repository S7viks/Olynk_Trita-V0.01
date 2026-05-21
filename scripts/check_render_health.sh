#!/usr/bin/env bash
# VA-10 — curl Render (or local) API /health
set -euo pipefail
REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
if [[ -f "$REPO_ROOT/.env" ]]; then
  set -a
  # shellcheck disable=SC1091
  source <(grep -v '^\s*#' "$REPO_ROOT/.env" | grep -v '^\s*$' | sed 's/\r$//')
  set +a
fi
if [[ -z "${RENDER_HEALTH_URL:-}" ]]; then
  echo "Set RENDER_HEALTH_URL in .env" >&2
  exit 2
fi
BASE="${RENDER_HEALTH_URL%/}"
URI="${BASE}/health"
echo "GET ${URI}"
curl -sfS --max-time 30 "${URI}"
echo
