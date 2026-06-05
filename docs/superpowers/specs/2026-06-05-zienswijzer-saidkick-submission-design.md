# Design: sAId-Kick App Store submission for Zienswijzer (WOO)

**Date:** 2026-06-05
**Status:** Approved — ready for implementation planning
**Author:** Lex Lubbers (lex@gradient-ds.com) with Claude

## Context

The Province of South Holland operates a Kubernetes-based "sAId-Kick App Store"
(by Clappform) where external developers publish apps. Other organisations then
deploy those apps onto their own clusters in one click (Argo CD reconciles the
submitted Helm chart). We want to publish **Zienswijzer**, our WOO (Wet Open
Overheid) application, to this platform.

The platform's onboarding rules come from the manual `Saidkick upload app EN.pdf`
and the reference implementation `github.com/ClappFormOrg/nginx-ai-demo`.

### The app today

Zienswijzer is a full-stack WOO case/document-management app:

- **api** — `ghcr.io/gradient-ds/woo-api`, FastAPI on **:5002**, SQLite
  (`/app/db/database.sqlite3`), Flask session dir (`/app/flask_session`), reads
  `/app/config.yaml`, uses AI model providers via env (`MODEL_PROVIDER`,
  `HF_KEY`, `UBIOPS_KEY`, plus email creds). Runs as non-root uid 1000.
  **Routes are served at root** (`/health`, `/cases`, `/documents`,
  `/auth/login`, …) — there is **no `/api` prefix on the backend**.
- **frontend** — `ghcr.io/gradient-ds/woo-frontend`, static React served by
  `serve` on **:3000**. Built with `VITE_APP_FLASK_BACKEND_URL=/api`.
- **nginx** — reverse proxy: `/` → frontend:3000, `/api/` →
  `http://api:5002/` (trailing slash **strips** the `/api` prefix).
- **certbot** — Let's Encrypt TLS renewal.

**Routing contract (critical):** frontend calls `/api/*`; nginx strips `/api`
and forwards to the backend root. On Kubernetes the **Ingress must reproduce
this**: `/api/(.*)` → api service `/$1`, and `/` → frontend service. The
backend liveness path is **`GET /health` on :5002** (the Dockerfile's
`/api/helloworld` healthcheck is stale and must not be reused).

## Platform requirements (from the manual)

**Repo layout** (fetched from fixed paths at the **root of `main`**):

```
appstore.yaml              # app manifest (required)
chart/                     # Helm chart
  Chart.yaml
  values.yaml
  values.schema.json       # drives the deploy form (required)
  templates/
docs/screenshots/          # >= 3 screenshots, PNG/JPEG
audit/
  dpia.pdf
  security-scan.sarif
  ai-risk-assessment.pdf
  accessibility-report.pdf
```

**Hard limits / auto-reject rules:**

| Rule | Value |
| --- | --- |
| Screenshots | 3 min, 20 max (PNG/JPEG) |
| SARIF size | ≤ 100 KB |
| Security threshold | **no finding with CVSS ≥ 7.0** (auto-reject) |
| `ai.data_residency` | must be exactly `"EU"` |
| App name (slug) | 3–60 chars, `a-z 0-9 -`, **immutable after first publish** |
| Image registry | ghcr.io or Docker Hub (ghcr recommended) |
| Missing `values.schema.json` | rejected immediately |
| Secrets in plain `values.yaml` | use `format: secret` in the schema instead |
| License | one of EUPL-1.2, Apache-2.0, MIT, BSD-3-Clause, GPL-3.0-only, LGPL-3.0-only, MPL-2.0 |

**Submission flow (steps 5–7, browser-only — handed off to the user):**
install the `saidkick-appstore-testing` GitHub App → dashboard *App toevoegen* →
enter GitHub App Installation ID + repo owner/name → *App registreren*
(automated validation < 60 s) → *Indienen voor beoordeling* →
cross-organisational audit (2–5 business days, an auditor from a **different**
org) → live.

## Decisions (locked with the user)

| Decision | Choice |
| --- | --- |
| Submission location | **This repo's root** (repo will be renamed `zienswijzer`) |
| nginx / TLS on k8s | **Kubernetes Ingress** (drop nginx + certbot from the chart) |
| EU AI Act risk class | **limited** |
| License | **EUPL-1.2** (default; matches the EU-gov reference app) |
| Local test cluster | **kind** + ingress-nginx |

## End state / deliverables

1. Submission files added at repo root (`appstore.yaml`, `chart/`, `docs/`,
   `audit/`); existing `backend/`, `frontend/`, `nginx/`, compose files untouched.
2. A Helm chart deploying **api + frontend + ingress** that passes
   `helm lint` and `helm template`, and validates against its own
   `values.schema.json`.
3. The chart **deploys and serves on a local `kind` cluster** (acceptance below).
4. Four audit documents present and valid (SARIF from a **real Trivy scan**).
5. A `SUBMISSION.md` handoff guide for the browser-only signup steps.

## Component design

### Helm chart (`chart/`)

Mirror the example chart's idioms (`_helpers.tpl` naming, labels) but model two
workloads plus an ingress.

- **Chart.yaml** — `name: zienswijzer`, `apiVersion: v2`, semver `version`,
  `appVersion` matching the released image tag, EU-gov maintainers.
- **templates/deployment-api.yaml** — image `image.api.{repository,tag}`;
  ConfigMap mount at `/app/config.yaml`; envFrom the Secret; emptyDir (or PVC
  when `persistence.enabled`) at `/app/db` and emptyDir at `/app/flask_session`;
  `securityContext` non-root uid 1000, `readOnlyRootFilesystem` where feasible;
  liveness/readiness `GET /health` :5002; resource requests/limits.
- **templates/deployment-frontend.yaml** — image
  `image.frontend.{repository,tag}`; probes `GET /` :3000; resources.
- **templates/service-api.yaml** — ClusterIP :5002.
- **templates/service-frontend.yaml** — ClusterIP :3000.
- **templates/ingress.yaml** — when `ingress.enabled`:
  - path `/api(/|$)(.*)` → api:5002 with
    `nginx.ingress.kubernetes.io/rewrite-target: /$2` (strips `/api`, matching
    current nginx),
  - path `/` → frontend:3000,
  - configurable `host`, `className`, optional TLS block.
- **templates/configmap-api.yaml** — renders `config.yaml` (DB path, email,
  api host/port) from values.
- **templates/secret-api.yaml** — templated Secret for model/email creds; real
  values supplied at deploy time via the platform's Vault (schema `format:
  secret` fields). Never commit real secrets.
- **templates/_helpers.tpl**, **NOTES.txt** — standard.

### `chart/values.yaml` + `chart/values.schema.json`

`values.yaml` holds safe defaults; `values.schema.json` (JSON Schema draft-07)
is the source of truth for the deploy form. Fields:

- `replicaCount` (integer, default 1, 1–10)
- `image.api.{repository,tag}`, `image.frontend.{repository,tag}` — defaults
  pinned to `ghcr.io/gradient-ds/woo-{api,frontend}` and a **concrete released
  tag, not `latest`** (immutable digest preferred).
- `ingress.{enabled,host,className}`, `ingress.tls.enabled`
- `persistence.{enabled,size}`
- `resources` (requests/limits)
- **Secret fields (`"format": "secret"` → routed to Vault):**
  `modelProvider`, `hfKey`, `ubiopsKey`, `flaskSecretKey`, and email
  credentials. These never appear in plaintext, logs, or the deploy UI.

### `appstore.yaml`

```yaml
apiVersion: appstore.saidkick.nl/v1
kind: AppManifest
metadata:
  name: zienswijzer            # immutable slug, 3-60, a-z0-9-
  display_name: Zienswijzer
  vendor: Gradient
  contact: lex@gradient-ds.com
  license: EUPL-1.2
spec:
  chart: { path: chart/, type: helm }
  categories: [ <TBD - see open item 2> ]
  ai:
    risk_class: limited
    base_model: <TBD - see open item 3>
    data_residency: EU
  interfaces:
    - type: api
      openapi: docs/openapi.yaml
  demo:
    description: docs/description.md
    screenshots:
      - docs/screenshots/<...>.png   # >= 3
  audit:
    dpia: audit/dpia.pdf
    security_scan: audit/security-scan.sarif
    ai_risk: audit/ai-risk-assessment.pdf
    accessibility: audit/accessibility-report.pdf
```

`docs/openapi.yaml` is exported from the running FastAPI app
(`GET /openapi.json` → YAML). `docs/description.md` ≤ 500 chars in the listing.

### Audit documents (`audit/`)

Authored in markdown, rendered to PDF (toolchain chosen from what's installed:
pandoc → weasyprint → headless Chrome fallback):

- **dpia.pdf** — GDPR Data Protection Impact Assessment for processing WOO
  documents and any personal data, with a DPO sign-off block.
- **security-scan.sarif** — **real Trivy scan** of both ghcr images, SARIF
  2.1.0, ≤ 100 KB. If any finding is CVSS ≥ 7.0, the submission is auto-blocked
  → must be remediated (image rebuild) before submitting. This is a gating risk.
- **ai-risk-assessment.pdf** — EU AI Act *limited-risk* assessment: intended
  use, model transparency, human oversight, data residency EU.
- **accessibility-report.pdf** — WCAG 2.2 Level AA report (axe/Lighthouse
  against the running frontend where possible).

### Local kind test — acceptance criteria

1. `helm lint chart/` passes; `helm template` renders with no errors and
   validates against `values.schema.json`.
2. kind cluster up, ingress-nginx installed, `helm install` succeeds.
3. All pods reach **Ready**.
4. Through the ingress: the **frontend HTML loads** at `/`, and
   **`GET /api/health` returns 200** (proving the `/api` rewrite contract).
5. At least one real API round-trip works (e.g. login or list cases) end to end
   frontend → ingress → api.

If `ghcr.io/gradient-ds/woo-*` images are private, load them into kind
(`kind load docker-image`) or configure an imagePullSecret.

### Handoff guide (`SUBMISSION.md`)

Written for the user to execute the browser-only steps: rename repo to
`zienswijzer` → create/login sAId-Kick account (EntraID/Keycloak) → install the
`saidkick-appstore-testing` GitHub App on the repo and copy the Installation ID
→ dashboard *App toevoegen* → Installation ID + owner/name → *App registreren*
→ resolve any validation errors → *Indienen voor beoordeling*.

## Open items (defaults chosen; confirm or override during implementation)

1. **License** — defaulting to **EUPL-1.2**. Override to MIT/Apache-2.0 if preferred.
2. **`categories`** — the manual lists no allowed enum (example used
   `infrastruct`). Use a best-guess (e.g. `document` / `productivity`) and rely
   on the platform's automated validation to confirm; adjust if rejected.
3. **`ai.base_model`** — the actual model id behind `MODEL_PROVIDER` (HF model
   id or UBIOps deployment). Needs a real value before submission.
4. **ghcr image visibility** — confirm `ghcr.io/gradient-ds/woo-{api,frontend}`
   are public; if private, external deploys and the kind test need an
   imagePullSecret.
5. **Image tag** — replace `latest` with a concrete immutable released tag/digest
   before submitting (the platform pins deployments to an immutable git SHA;
   `latest` is poor practice for published charts).

## Out of scope

- Creating the sAId-Kick account, GitHub App install, and dashboard clicks
  (browser-only; documented in `SUBMISSION.md`).
- Renaming the GitHub repository (user action).
- Changing application source code / Dockerfiles (unless a Trivy CVSS ≥ 7.0
  finding forces an image rebuild).
- nginx/certbot in the chart (replaced by Ingress + cluster TLS).
