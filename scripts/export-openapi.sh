#!/usr/bin/env bash
set -euo pipefail
# Export the FastAPI schema from the zienswijzer-api image to docs/openapi.yaml.
IMG="${1:-ghcr.io/gradient-ds/zienswijzer-api:latest}"
NAME="zw-openapi-export"

cleanup() { docker rm -f "$NAME" >/dev/null 2>&1 || true; }
trap cleanup EXIT

docker run -d --rm --name "$NAME" \
  -e MICROSOFT_CLIENT_ID=dummy \
  -e MICROSOFT_CLIENT_SECRET=dummy \
  -e MICROSOFT_TENANT_ID=dummy \
  -p 18000:8000 "$IMG"

echo "Waiting for the api to come up..."
for i in $(seq 1 30); do
  if curl -fs http://127.0.0.1:18000/health >/dev/null 2>&1; then break; fi
  if [ "$i" -eq 30 ]; then
    echo "ERROR: api did not become healthy within 30s" >&2
    docker logs "$NAME" 2>&1 | tail -20 >&2 || true
    exit 1
  fi
  sleep 1
done

curl -fs http://127.0.0.1:18000/openapi.json -o /tmp/openapi.json
# Convert JSON -> YAML with yq (the local Homebrew python lacks PyYAML and pip is broken).
yq -p=json -o=yaml /tmp/openapi.json > docs/openapi.yaml
echo "Wrote docs/openapi.yaml"
