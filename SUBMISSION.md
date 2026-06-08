# Zienswijzer — sAId-Kick App Store submission guide

This repo contains everything the platform fetches from the root of `main`:
`appstore.yaml`, `chart/`, `docs/`, and `audit/`. This guide covers the
browser-only steps and the manual items that must be done before submitting.

## 0. Pre-submission checklist (DO THESE FIRST)

- [ ] **BLOCKING — security gate.** The Trivy scan found **114 HIGH/CRITICAL
      (CVSS ≥ 7.0)** vulnerabilities (83 in `woo-api`, 31 in `woo-frontend`). The
      platform auto-rejects any CVSS ≥ 7.0 finding, so the submission **cannot pass**
      until both images are rebuilt with patched base images/dependencies and
      re-scanned to **zero** HIGH/CRITICAL (`./scripts/trivy-scan.sh`). The committed
      `audit/security-scan.sarif` is filtered to CRITICAL-only to fit the 100 KB limit.
- [ ] **Image tag** — replace `latest` in `chart/values.yaml` (`image.api.tag`,
      `image.frontend.tag`) and `Chart.yaml` `appVersion` with a concrete immutable
      released tag/digest. (Open item 5.)
- [ ] **Image visibility** — confirmed PUBLIC for both ghcr images; no imagePullSecret
      needed. (Open item 4, resolved.)
- [ ] **Screenshots** — add ≥ 3 real PNG/JPEG captures under `docs/screenshots/`
      (the manifest references `01-case-list.png`, `02-case-overview.png`,
      `03-document-detail.png`). Capture against the running app
      (`./scripts/kind-acceptance.sh` exposes it at `http://zienswijzer.local`
      via the `Host:` header on `127.0.0.1:${HOST_PORT:-8081}`, or use the prod compose).
- [ ] **Accessibility scan** — run axe-core/Lighthouse against the running frontend
      and paste results into `audit/accessibility-report.md`, then re-render:
      `./scripts/render-pdfs.sh`.
- [ ] **Local acceptance** — `./scripts/kind-acceptance.sh` ends with `ACCEPTANCE PASSED`.
- [ ] **categories** — `appstore.yaml` uses `document`/`productivity` as a best guess
      (the manual has no enum). Adjust if automated validation rejects. (Open item 2.)
- [ ] **openapi cleanup (optional)** — `docs/openapi.yaml` includes a dev `/transform`
      route. Consider excluding it from the backend (`include_in_schema=False`) and
      re-running `./scripts/export-openapi.sh` so only product endpoints are published.

## 1. Rename the GitHub repository
Rename the repo to `zienswijzer` (the immutable app slug; user action).

## 2. Create / log in to a sAId-Kick account
Sign in via EntraID/Keycloak on the sAId-Kick dashboard.

## 3. Install the GitHub App
Install the `saidkick-appstore-testing` GitHub App on the `zienswijzer` repo and
copy the **Installation ID**.

## 4. Register the app
Dashboard → **App toevoegen** → enter the GitHub App **Installation ID** and the
repo **owner/name** → **App registreren**. Automated validation runs in < 60 s.

## 5. Resolve validation errors
Fix anything the validator flags (missing `values.schema.json`, screenshot count,
SARIF size > 100 KB, CVSS ≥ 7.0, `ai.data_residency != "EU"`, slug format, license
not in the allowed list, etc.). Re-push to `main` and re-validate.

## 6. Submit for review
**Indienen voor beoordeling** → cross-organisational audit (an auditor from a
**different** org, 2–5 business days) → live.

## Notes on what's in this repo
- The Helm chart deploys **api + frontend + Ingress** (nginx/certbot from the prod
  compose are replaced by the cluster Ingress + TLS).
- The backend listens on **:8000**; the Ingress rewrites `/api/(.*)` → api `/$1`
  (with `use-regex: "true"`).
- Required runtime secrets are Azure OAuth: `MICROSOFT_CLIENT_ID`,
  `MICROSOFT_CLIENT_SECRET`, `MICROSOFT_TENANT_ID` (supplied via the platform Vault;
  `format: secret` in `values.schema.json`). The api will not start without them.
- Persistence is opt-in (`persistence.enabled`); when on, the DB and uploaded
  documents share one PVC (with `helm.sh/resource-policy: keep`).
- License: **EUPL-1.2**. EU AI Act class: **limited**. Data residency: **EU**.
