#!/usr/bin/env bash
set -euo pipefail

CLUSTER="zienswijzer-test"
RELEASE="zw"
HOST="zienswijzer.local"
API_IMG="ghcr.io/gradient-ds/zienswijzer-api:latest"
FE_IMG="ghcr.io/gradient-ds/zienswijzer-frontend:latest"
# Host port the kind node's :80 is mapped to. Override if 8081 is taken on your
# machine: `HOST_PORT=9090 ./scripts/kind-acceptance.sh`. (Port 80 is privileged,
# so we map to an unprivileged host port and curl it with the Host header below.)
HOST_PORT="${HOST_PORT:-8081}"

cleanup() { kind delete cluster --name "$CLUSTER" >/dev/null 2>&1 || true; }
trap cleanup EXIT

echo "==> Creating kind cluster with ingress-ready node (host port ${HOST_PORT})"
cat <<EOF | kind create cluster --name "$CLUSTER" --config -
kind: Cluster
apiVersion: kind.x-k8s.io/v1alpha4
nodes:
  - role: control-plane
    kubeadmConfigPatches:
      - |
        kind: InitConfiguration
        nodeRegistration:
          kubeletExtraArgs:
            node-labels: "ingress-ready=true"
    extraPortMappings:
      - containerPort: 80
        hostPort: ${HOST_PORT}
        protocol: TCP
EOF

echo "==> Installing ingress-nginx"
kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/main/deploy/static/provider/kind/deploy.yaml
echo "    waiting for ingress-nginx pods to be scheduled..."
until kubectl get pods -n ingress-nginx -l app.kubernetes.io/component=controller 2>/dev/null | grep -q controller; do sleep 2; done
kubectl wait --namespace ingress-nginx \
  --for=condition=ready pod \
  --selector=app.kubernetes.io/component=controller \
  --timeout=180s

echo "==> Verifying app images are pullable (public registry)"
docker pull "$API_IMG" || echo "WARN: could not pull $API_IMG — kind will try at deploy time"
docker pull "$FE_IMG"  || echo "WARN: could not pull $FE_IMG — kind will try at deploy time"
# NOTE: kind load docker-image does not support multi-arch OCI index manifests.
# Images are public on ghcr.io so we use pullPolicy=Always and let the cluster pull directly.

echo "==> helm install with dummy MICROSOFT_* creds (required for the api to boot)"
helm install "$RELEASE" chart/ \
  --set ingress.host="$HOST" \
  --set image.pullPolicy=Always \
  --set secrets.microsoftClientId=dummy-client-id \
  --set secrets.microsoftClientSecret=dummy-client-secret \
  --set secrets.microsoftTenantId=dummy-tenant-id \
  --wait --timeout 600s

echo "==> Waiting for all pods Ready"
kubectl wait --for=condition=ready pod \
  -l app.kubernetes.io/instance="$RELEASE" --timeout=600s

echo "==> Letting ingress endpoint sync (5s)"
sleep 5

echo "==> Acceptance checks via the ingress (Host header -> 127.0.0.1:${HOST_PORT})"
fail=0

echo "-- [4a] frontend HTML at /"
code=$(curl -s -o /tmp/zw-root.html -w '%{http_code}' -H "Host: $HOST" http://127.0.0.1:${HOST_PORT}/ || true)
if [ "$code" = "200" ] && grep -qi "<div id=\"root\"\|<!doctype html\|<html" /tmp/zw-root.html; then
  echo "   OK ($code, HTML served)"
else
  echo "   FAIL (status=$code)"; fail=1
fi

echo "-- [4b] GET /api/health -> 200 (proves /api rewrite contract)"
code=$(curl -s -o /tmp/zw-health.json -w '%{http_code}' -H "Host: $HOST" http://127.0.0.1:${HOST_PORT}/api/health || true)
if [ "$code" = "200" ]; then echo "   OK ($code): $(cat /tmp/zw-health.json)"; else echo "   FAIL (status=$code)"; fail=1; fi

echo "-- [5] real API round-trip: GET /api/cases"
code=$(curl -s -o /tmp/zw-cases.json -w '%{http_code}' -H "Host: $HOST" http://127.0.0.1:${HOST_PORT}/api/cases || true)
if [ "$code" = "200" ] || [ "$code" = "401" ]; then
  echo "   OK ($code): reached api through ingress. Body: $(head -c 200 /tmp/zw-cases.json)"
else
  echo "   FAIL (status=$code)"; fail=1
fi

echo "==> Pod status:"
kubectl get pods -l app.kubernetes.io/instance="$RELEASE"

if [ "$fail" = "0" ]; then
  echo "==> ACCEPTANCE PASSED"
else
  echo "==> ACCEPTANCE FAILED — dumping api logs"
  kubectl logs -l app.kubernetes.io/component=api --tail=80 || true
  exit 1
fi
