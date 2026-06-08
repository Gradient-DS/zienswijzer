#!/usr/bin/env bash
set -euo pipefail
API_IMG="${1:-ghcr.io/gradient-ds/woo-api:latest}"
FE_IMG="${2:-ghcr.io/gradient-ds/woo-frontend:latest}"
OUT="audit/security-scan.sarif"

echo "==> Trivy scan (SARIF, severity HIGH,CRITICAL) of both images"
echo "    Gate check below covers HIGH+CRITICAL separately."
trivy image --quiet --format sarif --severity HIGH,CRITICAL --output /tmp/api.sarif "$API_IMG"
trivy image --quiet --format sarif --severity HIGH,CRITICAL --output /tmp/fe.sarif  "$FE_IMG"

python3 - "$OUT" /tmp/api.sarif /tmp/fe.sarif <<'PY'
import json, sys
out = sys.argv[1]
docs = [json.load(open(p)) for p in sys.argv[2:]]
merged = docs[0]
for d in docs[1:]:
    merged["runs"].extend(d["runs"])
json.dump(merged, open(out, "w"), separators=(",", ":"))  # compact to help stay <=100KB
print("wrote", out)
PY

echo "==> Size check (<= 100 KB)"
bytes=$(wc -c < "$OUT")
echo "SARIF size: ${bytes} bytes"
if [ "$bytes" -gt 102400 ]; then
  echo "WARN: SARIF > 100 KB. Re-run trivy with --severity HIGH,CRITICAL to shrink:"
  echo "  trivy image --format sarif --severity HIGH,CRITICAL ..."
fi

echo "==> CVSS >= 7.0 gate (HIGH/CRITICAL = auto-reject by the platform)"
api_hc=$(trivy image --quiet --format json --severity HIGH,CRITICAL "$API_IMG" 2>/dev/null \
     | python3 -c 'import json,sys; d=json.load(sys.stdin); print(sum(len(r.get("Vulnerabilities") or []) for r in (d.get("Results") or [])))' 2>/dev/null || echo "?")
fe_hc=$(trivy image --quiet --format json --severity HIGH,CRITICAL "$FE_IMG" 2>/dev/null \
     | python3 -c 'import json,sys; d=json.load(sys.stdin); print(sum(len(r.get("Vulnerabilities") or []) for r in (d.get("Results") or [])))' 2>/dev/null || echo "?")

echo "HIGH/CRITICAL findings — API image:      ${api_hc}"
echo "HIGH/CRITICAL findings — Frontend image: ${fe_hc}"

if [ "$api_hc" = "?" ] || [ "$fe_hc" = "?" ]; then
  echo "WARN: Could not determine HIGH/CRITICAL count for one or both images."
else
  total=$(( api_hc + fe_hc ))
  echo "HIGH/CRITICAL findings (total): ${total}"
  if [ "$total" -gt 0 ]; then
    echo "!!! GATING: HIGH/CRITICAL vulnerabilities present. The platform auto-rejects CVSS>=7.0."
    echo "!!! Remediate (rebuild images with patched base/deps) before submitting."
  else
    echo "GATE PASS: No HIGH/CRITICAL vulnerabilities found."
  fi
fi
