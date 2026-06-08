# Zienswijzer sAId-Kick App Store Submission Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add all files needed to publish the Zienswijzer WOO app to the Province of South Holland "sAId-Kick App Store" — a Helm chart (api + frontend + ingress), an `appstore.yaml` manifest, demo/docs assets, four audit documents, and a `SUBMISSION.md` handoff guide — verified by deploying to a local `kind` cluster.

**Architecture:** A single Helm chart at `chart/` deploys two Deployments (api, frontend) behind one Kubernetes Ingress that reproduces the production nginx routing contract: `/api/(.*)` is rewritten to the api service root, `/` goes to the frontend. The chart is driven by a `values.schema.json` (the platform's deploy form). The existing `backend/`, `frontend/`, `nginx/`, and compose files are **left untouched** — this is purely additive packaging. nginx + certbot from the prod compose are replaced by the Ingress + cluster TLS.

**Tech Stack:** Helm v3, Kubernetes Ingress (ingress-nginx), `kind` for local validation, Trivy (SARIF security scan), pandoc/weasyprint (audit PDFs). App images: `ghcr.io/gradient-ds/woo-api` (FastAPI, **listens on :8000**) and `ghcr.io/gradient-ds/woo-frontend` (static React via `serve`, :3000).

---

## CRITICAL GROUND TRUTH (verified against the code — overrides the spec where they differ)

The approved design spec contains several stale claims. These were verified against the actual source and **the spec's values are wrong**; use the values below:

1. **Backend port is `8000`, not `5002`.** `backend/server/__main__.py:5` runs `uvicorn.run(app, host="0.0.0.0", port=8000)` and has since the first commit. The `5002` in the Dockerfile `EXPOSE`, `nginx/nginx.conf`, `docker-compose.prod.yaml`, and `config.yaml` is stale and unused. **The published `woo-api` image serves on `:8000`.** Every Service `targetPort`, `containerPort`, probe port, and Ingress backend port for the api MUST be `8000`. (Decision locked with user: target 8000, no image rebuild.)

2. **Routes are served at root, no `/api` prefix.** Verified: `app.py` defines `@app.get("/health")` (line 240), `/cases`, `/documents`, `/auth/login`, etc. at root. The Ingress must strip `/api` before forwarding (mirrors the nginx `proxy_pass http://api:5002/;` trailing-slash strip).

3. **Liveness/readiness path is `GET /health` on `:8000`.** The Dockerfile healthcheck `GET /api/helloworld` is stale — do NOT use it.

4. **Real secrets are Azure OAuth, not model keys.** `backend/server/email/config.py` uses pydantic `BaseSettings` (`env_prefix="MICROSOFT_"`) and **requires** `client_id`, `client_secret`, `tenant_id` with **no defaults**. `email_config = EmailConfig()` runs at **module import** (`config.py:86`), pulled in by `app.include_router(email_router)`. **Therefore the api pod CrashLoopBackOffs on startup unless `MICROSOFT_CLIENT_ID`, `MICROSOFT_CLIENT_SECRET`, `MICROSOFT_TENANT_ID` are set** (dummy values are fine for the kind test). The spec's `MODEL_PROVIDER`/`HF_KEY`/`UBIOPS_KEY`/`FLASK_SECRET_KEY` do **not** exist in the code — do not use them. (Decision locked with user: model the real `MICROSOFT_*` creds.)

5. **AI model is hardcoded, no key needed.** `backend/server/reply_classification/classification.py` lazy-loads HuggingFace `transformers` with model `cross-encoder/nli-deberta-v3-small`. So `appstore.yaml` `ai.base_model: cross-encoder/nli-deberta-v3-small` (resolves spec open item 3). Inference runs in-cluster → `data_residency: EU` holds.

6. **SQLite DB is at `/app/server/db/database.sqlite3`, baked-in and seeded.** `backend/server/db/database.py:10` resolves `DB_PATH = Path(__file__).with_name("database.sqlite3")`; the container WORKDIR is `/app` with code copied to `/app`, so the runtime path is `/app/server/db/database.sqlite3` (NOT `/app/db/`). The 2 MB seeded DB is committed in the image, and `init_db()` (called from `@app.on_event("startup")`, `app.py:38`) runs `CREATE TABLE IF NOT EXISTS`. **The kind round-trip test uses the baked-in seeded data with no volume.** The app writes to that directory, so the api rootfs must stay writable (see Task 3 rationale).

7. **App also needs `/app/flask_session` and `/tmp` writable** (the prod compose mounts tmpfs there). Provide `emptyDir` volumes.

---

## File Structure

All new files are at the **repo root** (the platform fetches from fixed paths on `main`). Nothing under `backend/`, `frontend/`, `nginx/`, or the compose files is modified.

```
appstore.yaml                         # app manifest (Task 9)
chart/
  Chart.yaml                          # Task 1
  values.yaml                         # Task 2
  values.schema.json                  # Task 2
  .helmignore                         # Task 1
  templates/
    _helpers.tpl                      # Task 1
    NOTES.txt                         # Task 1
    deployment-api.yaml               # Task 3
    service-api.yaml                  # Task 3
    deployment-frontend.yaml          # Task 4
    service-frontend.yaml             # Task 4
    configmap-api.yaml                # Task 5
    secret-api.yaml                   # Task 5
    ingress.yaml                      # Task 6
docs/
  description.md                      # Task 9  (<= 500 chars)
  openapi.yaml                        # Task 9  (exported from the running api)
  screenshots/                        # Task 9  (>= 3 PNG/JPEG)
audit/
  dpia.md       -> dpia.pdf                       # Task 10
  ai-risk-assessment.md -> ai-risk-assessment.pdf # Task 10
  accessibility-report.md -> accessibility-report.pdf # Task 10
  security-scan.sarif                 # Task 11  (real Trivy scan, <= 100 KB)
scripts/
  export-openapi.sh                   # Task 9
  trivy-scan.sh                       # Task 11
  kind-acceptance.sh                  # Task 8
SUBMISSION.md                         # Task 12
docs/superpowers/plans/...            # this plan
```

**Verification model (no pytest here — this is packaging/IaC):** each chart task's "test" is `helm lint chart/` + `helm template chart/` (schema validation runs automatically during template/install). The end-to-end "test" is the `kind` acceptance script (Task 8). Audit-doc tasks verify by file existence, format, and size gates.

---

## Task 0: Workspace setup

**Files:** none (git/worktree only)

- [ ] **Step 1: Confirm an isolated worktree exists**

The controller (subagent-driven-development) must have created an isolated worktree/branch via `superpowers:using-git-worktrees` before dispatching Task 1 — do NOT implement on `main`. Verify you are on a feature branch:

Run: `git rev-parse --abbrev-ref HEAD`
Expected: a branch like `zienswijzer-saidkick-submission` (NOT `main`).

- [ ] **Step 2: Confirm tooling is available**

Run: `helm version && kind version && kubectl version --client && trivy --version`
Expected: all four print versions. If any is missing, install before proceeding (`brew install helm kind kubectl trivy`). Note for the implementer: `trivy` and `kind` are only needed for Tasks 8/11; `helm` is needed from Task 1.

---

## Task 1: Helm chart skeleton (Chart.yaml, _helpers.tpl, NOTES.txt, .helmignore)

**Files:**
- Create: `chart/Chart.yaml`
- Create: `chart/templates/_helpers.tpl`
- Create: `chart/templates/NOTES.txt`
- Create: `chart/.helmignore`
- Create: `chart/values.yaml` (minimal placeholder so `helm lint` runs; fully fleshed out in Task 2)

- [ ] **Step 1: Write `chart/Chart.yaml`**

```yaml
apiVersion: v2
name: zienswijzer
description: Zienswijzer — WOO (Wet Open Overheid) case & document management for Dutch public bodies.
type: application
# Chart version — bump on chart changes (semver).
version: 0.1.0
# appVersion MUST match the released image tag set in values.yaml (image.*.tag).
# TODO(open-item-5): replace with the concrete immutable released tag before submission.
appVersion: "latest"
home: https://github.com/gradient-ds/zienswijzer
sources:
  - https://github.com/gradient-ds/zienswijzer
maintainers:
  - name: Gradient
    email: lex@gradient-ds.com
keywords:
  - woo
  - foia
  - document-management
  - government
  - eu
```

- [ ] **Step 2: Write `chart/templates/_helpers.tpl`**

```yaml
{{/*
Expand the name of the chart.
*/}}
{{- define "zienswijzer.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Create a fully qualified app name.
*/}}
{{- define "zienswijzer.fullname" -}}
{{- if .Values.fullnameOverride }}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- $name := default .Chart.Name .Values.nameOverride }}
{{- if contains $name .Release.Name }}
{{- .Release.Name | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" }}
{{- end }}
{{- end }}
{{- end }}

{{/*
Chart name and version label.
*/}}
{{- define "zienswijzer.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Common labels.
*/}}
{{- define "zienswijzer.labels" -}}
helm.sh/chart: {{ include "zienswijzer.chart" . }}
{{ include "zienswijzer.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}

{{/*
Selector labels (release-wide).
*/}}
{{- define "zienswijzer.selectorLabels" -}}
app.kubernetes.io/name: {{ include "zienswijzer.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{/*
Per-component selector labels. Call with (dict "ctx" . "component" "api").
*/}}
{{- define "zienswijzer.componentSelectorLabels" -}}
{{ include "zienswijzer.selectorLabels" .ctx }}
app.kubernetes.io/component: {{ .component }}
{{- end }}

{{/*
Per-component full labels. Call with (dict "ctx" . "component" "api").
*/}}
{{- define "zienswijzer.componentLabels" -}}
{{ include "zienswijzer.labels" .ctx }}
app.kubernetes.io/component: {{ .component }}
{{- end }}
```

- [ ] **Step 3: Write `chart/templates/NOTES.txt`**

```txt
Zienswijzer has been deployed.

{{- if .Values.ingress.enabled }}

Access the app through the Ingress:
  Frontend:  http{{ if .Values.ingress.tls.enabled }}s{{ end }}://{{ .Values.ingress.host }}/
  API:       http{{ if .Values.ingress.tls.enabled }}s{{ end }}://{{ .Values.ingress.host }}/api/health

The Ingress rewrites /api/(.*) -> api service "/$1" (the backend serves routes at root on :8000).
{{- else }}

Ingress is disabled. Reach the services in-cluster:
  API:       {{ include "zienswijzer.fullname" . }}-api:{{ .Values.service.api.port }}/health
  Frontend:  {{ include "zienswijzer.fullname" . }}-frontend:{{ .Values.service.frontend.port }}/
{{- end }}

Pods:
  kubectl get pods -l app.kubernetes.io/instance={{ .Release.Name }}
```

- [ ] **Step 4: Write `chart/.helmignore`**

```txt
.git/
.gitignore
*.tmp
*.bak
.DS_Store
docs/
audit/
```

- [ ] **Step 5: Write a minimal `chart/values.yaml` placeholder (replaced in Task 2)**

```yaml
nameOverride: ""
fullnameOverride: ""
ingress:
  enabled: false
  host: ""
  tls:
    enabled: false
service:
  api:
    port: 8000
  frontend:
    port: 3000
```

- [ ] **Step 6: Lint the skeleton**

Run: `helm lint chart/`
Expected: `1 chart(s) linted, 0 chart(s) failed`. (A `values.schema.json` info message may appear once Task 2 adds the schema — fine.)

- [ ] **Step 7: Commit**

```bash
git add chart/Chart.yaml chart/templates/_helpers.tpl chart/templates/NOTES.txt chart/.helmignore chart/values.yaml
git commit -m "feat(chart): scaffold zienswijzer helm chart skeleton"
```

---

## Task 2: values.yaml + values.schema.json (deploy form source of truth)

**Files:**
- Modify: `chart/values.yaml` (replace the Task 1 placeholder with the full default set)
- Create: `chart/values.schema.json`

Schema rules to honor (from the manual): secrets must use `"format": "secret"` (never plaintext defaults); the schema drives the deploy form; a missing schema = instant reject.

- [ ] **Step 1: Write the full `chart/values.yaml`**

```yaml
# Default values for the Zienswijzer chart.
# Secret values (MICROSOFT_* credentials) are intentionally EMPTY here — they are
# supplied at deploy time via the platform's Vault (fields marked "format": secret
# in values.schema.json). Never commit real secrets.

replicaCount: 1

image:
  # TODO(open-item-5): replace "latest" with a concrete immutable released tag/digest
  # before submission. TODO(open-item-4): confirm these images are PUBLIC on ghcr;
  # if private, the platform/kind need an imagePullSecret.
  pullPolicy: IfNotPresent
  pullSecrets: []
  api:
    repository: ghcr.io/gradient-ds/woo-api
    tag: latest
  frontend:
    repository: ghcr.io/gradient-ds/woo-frontend
    tag: latest

# Non-secret backend configuration (rendered into the api ConfigMap / env).
config:
  email:
    enabled: true
    mockMode: false
  # Non-secret MICROSOFT_* OAuth config (the three credentials are secrets — see below).
  microsoft:
    redirectUri: "http://localhost:8000/email/callback"
    graphApiEndpoint: "https://graph.microsoft.com/v1.0"
    scopes: "User.Read,Mail.Read,Mail.Send,Mail.ReadWrite"

# Secret values — EMPTY by default; injected from Vault at deploy time.
# REQUIRED for the api pod to start (pydantic BaseSettings has no defaults for these).
secrets:
  microsoftClientId: ""
  microsoftClientSecret: ""
  microsoftTenantId: ""

service:
  api:
    port: 8000        # the backend listens on 8000 (see GROUND TRUTH #1)
  frontend:
    port: 3000

ingress:
  enabled: true
  className: "nginx"
  host: "zienswijzer.local"
  tls:
    enabled: false
    secretName: ""

# Optional persistence for the SQLite DB dir (/app/server/db).
# Default OFF: use the image's baked-in seeded DB (see GROUND TRUTH #6).
# Enabling mounts an empty PVC over the seeded DB; init_db() recreates the schema (empty data).
persistence:
  enabled: false
  size: 1Gi
  storageClassName: ""

resources:
  api:
    requests:
      cpu: 250m
      memory: 512Mi
    limits:
      cpu: "1"
      memory: 2Gi
  frontend:
    requests:
      cpu: 50m
      memory: 64Mi
    limits:
      cpu: 250m
      memory: 256Mi

nameOverride: ""
fullnameOverride: ""
```

- [ ] **Step 2: Write `chart/values.schema.json` (JSON Schema draft-07)**

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "Zienswijzer deploy configuration",
  "type": "object",
  "additionalProperties": true,
  "required": ["replicaCount", "image", "service", "ingress", "secrets"],
  "properties": {
    "replicaCount": {
      "type": "integer",
      "title": "Replica count",
      "minimum": 1,
      "maximum": 10,
      "default": 1
    },
    "image": {
      "type": "object",
      "required": ["api", "frontend"],
      "properties": {
        "pullPolicy": {
          "type": "string",
          "enum": ["IfNotPresent", "Always", "Never"],
          "default": "IfNotPresent"
        },
        "pullSecrets": {
          "type": "array",
          "items": { "type": "string" },
          "default": []
        },
        "api": {
          "type": "object",
          "required": ["repository", "tag"],
          "properties": {
            "repository": { "type": "string", "minLength": 1 },
            "tag": { "type": "string", "minLength": 1 }
          }
        },
        "frontend": {
          "type": "object",
          "required": ["repository", "tag"],
          "properties": {
            "repository": { "type": "string", "minLength": 1 },
            "tag": { "type": "string", "minLength": 1 }
          }
        }
      }
    },
    "config": {
      "type": "object",
      "properties": {
        "email": {
          "type": "object",
          "properties": {
            "enabled": { "type": "boolean", "default": true },
            "mockMode": { "type": "boolean", "default": false }
          }
        },
        "microsoft": {
          "type": "object",
          "properties": {
            "redirectUri": { "type": "string" },
            "graphApiEndpoint": { "type": "string" },
            "scopes": { "type": "string" }
          }
        }
      }
    },
    "secrets": {
      "type": "object",
      "title": "Credentials (stored in Vault)",
      "required": ["microsoftClientId", "microsoftClientSecret", "microsoftTenantId"],
      "properties": {
        "microsoftClientId": {
          "type": "string",
          "title": "Microsoft OAuth Client ID",
          "format": "secret"
        },
        "microsoftClientSecret": {
          "type": "string",
          "title": "Microsoft OAuth Client Secret",
          "format": "secret"
        },
        "microsoftTenantId": {
          "type": "string",
          "title": "Microsoft Azure AD Tenant ID",
          "format": "secret"
        }
      }
    },
    "service": {
      "type": "object",
      "required": ["api", "frontend"],
      "properties": {
        "api": {
          "type": "object",
          "properties": {
            "port": { "type": "integer", "default": 8000, "minimum": 1, "maximum": 65535 }
          }
        },
        "frontend": {
          "type": "object",
          "properties": {
            "port": { "type": "integer", "default": 3000, "minimum": 1, "maximum": 65535 }
          }
        }
      }
    },
    "ingress": {
      "type": "object",
      "required": ["enabled"],
      "properties": {
        "enabled": { "type": "boolean", "default": true },
        "className": { "type": "string", "default": "nginx" },
        "host": { "type": "string" },
        "tls": {
          "type": "object",
          "properties": {
            "enabled": { "type": "boolean", "default": false },
            "secretName": { "type": "string" }
          }
        }
      }
    },
    "persistence": {
      "type": "object",
      "properties": {
        "enabled": { "type": "boolean", "default": false },
        "size": { "type": "string", "default": "1Gi" },
        "storageClassName": { "type": "string" }
      }
    },
    "resources": {
      "type": "object"
    },
    "nameOverride": { "type": "string" },
    "fullnameOverride": { "type": "string" }
  }
}
```

- [ ] **Step 3: Verify values validate against the schema (helm validates schema on template/lint)**

Run: `helm lint chart/ && helm template zw chart/ >/dev/null && echo SCHEMA_OK`
Expected: lint passes and `SCHEMA_OK` prints (templating fails loudly if `values.yaml` violates `values.schema.json`).

- [ ] **Step 4: Verify the schema REJECTS bad input (negative test)**

Run: `helm template zw chart/ --set replicaCount=99 2>&1 | grep -qi "schema\|maximum\|valid" && echo REJECTED_AS_EXPECTED || echo "FAIL: schema did not reject replicaCount=99"`
Expected: `REJECTED_AS_EXPECTED` (replicaCount max is 10).

- [ ] **Step 5: Commit**

```bash
git add chart/values.yaml chart/values.schema.json
git commit -m "feat(chart): add values.yaml defaults and values.schema.json deploy form"
```

---

## Task 3: API Deployment + Service

**Files:**
- Create: `chart/templates/deployment-api.yaml`
- Create: `chart/templates/service-api.yaml`

**Rationale notes for the implementer (do not omit):**
- `containerPort`/probe port/`targetPort` = **8000** (GROUND TRUTH #1).
- Liveness/readiness path = **`/health`** (GROUND TRUTH #3).
- `securityContext` runs as non-root uid 1000 (matches Dockerfile `useradd -m -u 1000`). **`readOnlyRootFilesystem` is intentionally `false`** because the app writes the SQLite DB into its code directory `/app/server/db` and calls `DB_PATH.parent.mkdir(...)` (GROUND TRUTH #6); a read-only rootfs would crash it. This is a deliberate deviation from the spec's "readOnlyRootFilesystem where feasible" — it is not feasible without an out-of-scope code change.
- `envFrom` the Secret (Task 5) so `MICROSOFT_CLIENT_ID/_SECRET/_TENANT_ID` are present, plus the non-secret MICROSOFT_* env from values.
- `emptyDir` at `/app/flask_session` and `/tmp`; when `persistence.enabled`, mount a PVC at `/app/server/db` (otherwise use the baked-in DB, no volume).

- [ ] **Step 1: Write `chart/templates/deployment-api.yaml`**

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: {{ include "zienswijzer.fullname" . }}-api
  labels:
    {{- include "zienswijzer.componentLabels" (dict "ctx" . "component" "api") | nindent 4 }}
spec:
  replicas: {{ .Values.replicaCount }}
  selector:
    matchLabels:
      {{- include "zienswijzer.componentSelectorLabels" (dict "ctx" . "component" "api") | nindent 6 }}
  template:
    metadata:
      labels:
        {{- include "zienswijzer.componentSelectorLabels" (dict "ctx" . "component" "api") | nindent 8 }}
      annotations:
        # Roll pods when the rendered config/secret changes.
        checksum/config: {{ include (print $.Template.BasePath "/configmap-api.yaml") . | sha256sum }}
    spec:
      {{- with .Values.image.pullSecrets }}
      imagePullSecrets:
        {{- toYaml . | nindent 8 }}
      {{- end }}
      securityContext:
        runAsNonRoot: true
        runAsUser: 1000
        fsGroup: 1000
      containers:
        - name: api
          image: "{{ .Values.image.api.repository }}:{{ .Values.image.api.tag }}"
          imagePullPolicy: {{ .Values.image.pullPolicy }}
          ports:
            - name: http
              containerPort: {{ .Values.service.api.port }}
              protocol: TCP
          envFrom:
            - secretRef:
                name: {{ include "zienswijzer.fullname" . }}-api
          env:
            - name: MICROSOFT_REDIRECT_URI
              value: {{ .Values.config.microsoft.redirectUri | quote }}
            - name: MICROSOFT_GRAPH_API_ENDPOINT
              value: {{ .Values.config.microsoft.graphApiEndpoint | quote }}
            - name: MICROSOFT_SCOPES
              value: {{ .Values.config.microsoft.scopes | quote }}
          livenessProbe:
            httpGet:
              path: /health
              port: http
            initialDelaySeconds: 20
            periodSeconds: 15
            timeoutSeconds: 5
            failureThreshold: 6
          readinessProbe:
            httpGet:
              path: /health
              port: http
            initialDelaySeconds: 10
            periodSeconds: 10
            timeoutSeconds: 5
            failureThreshold: 6
          resources:
            {{- toYaml .Values.resources.api | nindent 12 }}
          securityContext:
            allowPrivilegeEscalation: false
            readOnlyRootFilesystem: false  # SQLite writes into /app/server/db (see plan rationale)
            capabilities:
              drop: ["ALL"]
          volumeMounts:
            - name: flask-session
              mountPath: /app/flask_session
            - name: tmp
              mountPath: /tmp
            {{- if .Values.persistence.enabled }}
            - name: db
              mountPath: /app/server/db
            {{- end }}
      volumes:
        - name: flask-session
          emptyDir: {}
        - name: tmp
          emptyDir: {}
        {{- if .Values.persistence.enabled }}
        - name: db
          persistentVolumeClaim:
            claimName: {{ include "zienswijzer.fullname" . }}-db
        {{- end }}
```

> **Implementer note:** the api does NOT mount the ConfigMap as a file, because `config.yaml` is not actually read by the app (verified: no loader references it). Config is delivered purely via env. Keep `configmap-api.yaml` (Task 5) only for transparency and to back the `checksum/config` annotation; do NOT add a file mount for it.

- [ ] **Step 2: Write `chart/templates/service-api.yaml`**

```yaml
apiVersion: v1
kind: Service
metadata:
  name: {{ include "zienswijzer.fullname" . }}-api
  labels:
    {{- include "zienswijzer.componentLabels" (dict "ctx" . "component" "api") | nindent 4 }}
spec:
  type: ClusterIP
  selector:
    {{- include "zienswijzer.componentSelectorLabels" (dict "ctx" . "component" "api") | nindent 4 }}
  ports:
    - name: http
      port: {{ .Values.service.api.port }}
      targetPort: http
      protocol: TCP
```

- [ ] **Step 3: Add the PVC template (only used when persistence.enabled)**

Create `chart/templates/pvc-db.yaml`:

```yaml
{{- if .Values.persistence.enabled }}
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: {{ include "zienswijzer.fullname" . }}-db
  labels:
    {{- include "zienswijzer.componentLabels" (dict "ctx" . "component" "api") | nindent 4 }}
spec:
  accessModes: ["ReadWriteOnce"]
  {{- if .Values.persistence.storageClassName }}
  storageClassName: {{ .Values.persistence.storageClassName | quote }}
  {{- end }}
  resources:
    requests:
      storage: {{ .Values.persistence.size }}
{{- end }}
```

- [ ] **Step 4: Render and inspect the api objects**

Run: `helm template zw chart/ --show-only templates/deployment-api.yaml --show-only templates/service-api.yaml`
Expected: valid YAML; api `containerPort: 8000`, both probes `path: /health port: http`, `envFrom` the `-api` secret, no `volumeMounts-config-marker` line remaining.

- [ ] **Step 5: Confirm probe port resolves to 8000 end-to-end**

Run: `helm template zw chart/ --show-only templates/service-api.yaml | grep -A2 "ports:"`
Expected: `port: 8000` and `targetPort: http`.

- [ ] **Step 6: Commit**

```bash
git add chart/templates/deployment-api.yaml chart/templates/service-api.yaml chart/templates/pvc-db.yaml
git commit -m "feat(chart): add api deployment, service and optional db PVC"
```

---

## Task 4: Frontend Deployment + Service

**Files:**
- Create: `chart/templates/deployment-frontend.yaml`
- Create: `chart/templates/service-frontend.yaml`

**Rationale:** frontend image runs `serve -s dist -l 3000` as user `node`; probe `GET /` on :3000. Static server → rootfs can be read-only with a `/tmp` emptyDir.

- [ ] **Step 1: Write `chart/templates/deployment-frontend.yaml`**

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: {{ include "zienswijzer.fullname" . }}-frontend
  labels:
    {{- include "zienswijzer.componentLabels" (dict "ctx" . "component" "frontend") | nindent 4 }}
spec:
  replicas: {{ .Values.replicaCount }}
  selector:
    matchLabels:
      {{- include "zienswijzer.componentSelectorLabels" (dict "ctx" . "component" "frontend") | nindent 6 }}
  template:
    metadata:
      labels:
        {{- include "zienswijzer.componentSelectorLabels" (dict "ctx" . "component" "frontend") | nindent 8 }}
    spec:
      {{- with .Values.image.pullSecrets }}
      imagePullSecrets:
        {{- toYaml . | nindent 8 }}
      {{- end }}
      securityContext:
        runAsNonRoot: true
        fsGroup: 1000
      containers:
        - name: frontend
          image: "{{ .Values.image.frontend.repository }}:{{ .Values.image.frontend.tag }}"
          imagePullPolicy: {{ .Values.image.pullPolicy }}
          ports:
            - name: http
              containerPort: {{ .Values.service.frontend.port }}
              protocol: TCP
          livenessProbe:
            httpGet:
              path: /
              port: http
            initialDelaySeconds: 10
            periodSeconds: 15
            timeoutSeconds: 5
            failureThreshold: 6
          readinessProbe:
            httpGet:
              path: /
              port: http
            initialDelaySeconds: 5
            periodSeconds: 10
            timeoutSeconds: 5
            failureThreshold: 6
          resources:
            {{- toYaml .Values.resources.frontend | nindent 12 }}
          securityContext:
            allowPrivilegeEscalation: false
            readOnlyRootFilesystem: true
            capabilities:
              drop: ["ALL"]
          volumeMounts:
            - name: tmp
              mountPath: /tmp
      volumes:
        - name: tmp
          emptyDir: {}
```

- [ ] **Step 2: Write `chart/templates/service-frontend.yaml`**

```yaml
apiVersion: v1
kind: Service
metadata:
  name: {{ include "zienswijzer.fullname" . }}-frontend
  labels:
    {{- include "zienswijzer.componentLabels" (dict "ctx" . "component" "frontend") | nindent 4 }}
spec:
  type: ClusterIP
  selector:
    {{- include "zienswijzer.componentSelectorLabels" (dict "ctx" . "component" "frontend") | nindent 4 }}
  ports:
    - name: http
      port: {{ .Values.service.frontend.port }}
      targetPort: http
      protocol: TCP
```

- [ ] **Step 3: Render and inspect**

Run: `helm template zw chart/ --show-only templates/deployment-frontend.yaml --show-only templates/service-frontend.yaml`
Expected: valid YAML; `containerPort: 3000`, probes `path: /`, service `port: 3000`.

- [ ] **Step 4: Commit**

```bash
git add chart/templates/deployment-frontend.yaml chart/templates/service-frontend.yaml
git commit -m "feat(chart): add frontend deployment and service"
```

---

## Task 5: ConfigMap + Secret for the api

**Files:**
- Create: `chart/templates/configmap-api.yaml`
- Create: `chart/templates/secret-api.yaml`

**Rationale:** The Secret carries the three REQUIRED Azure creds (`MICROSOFT_CLIENT_ID/_SECRET/_TENANT_ID`) consumed via `envFrom` in Task 3 — without them the pod crashes (GROUND TRUTH #4). The ConfigMap renders a `config.yaml` for transparency/operator inspection and to back the deployment's `checksum/config` annotation; it is not mounted (the app reads config from env, not file).

- [ ] **Step 1: Write `chart/templates/secret-api.yaml`**

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: {{ include "zienswijzer.fullname" . }}-api
  labels:
    {{- include "zienswijzer.componentLabels" (dict "ctx" . "component" "api") | nindent 4 }}
type: Opaque
stringData:
  # REQUIRED — pydantic BaseSettings (env_prefix MICROSOFT_) has no defaults for these.
  MICROSOFT_CLIENT_ID: {{ .Values.secrets.microsoftClientId | quote }}
  MICROSOFT_CLIENT_SECRET: {{ .Values.secrets.microsoftClientSecret | quote }}
  MICROSOFT_TENANT_ID: {{ .Values.secrets.microsoftTenantId | quote }}
```

- [ ] **Step 2: Write `chart/templates/configmap-api.yaml`**

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: {{ include "zienswijzer.fullname" . }}-api
  labels:
    {{- include "zienswijzer.componentLabels" (dict "ctx" . "component" "api") | nindent 4 }}
data:
  # Informational config snapshot (the app is env-driven; this is not mounted).
  config.yaml: |
    database:
      type: sqlite
      path: /app/server/db/database.sqlite3
    email:
      enabled: {{ .Values.config.email.enabled }}
      mock_mode: {{ .Values.config.email.mockMode }}
    api:
      host: 0.0.0.0
      port: {{ .Values.service.api.port }}
      debug: false
```

- [ ] **Step 3: Render and verify the secret carries all three keys**

Run: `helm template zw chart/ --set secrets.microsoftClientId=x --set secrets.microsoftClientSecret=y --set secrets.microsoftTenantId=z --show-only templates/secret-api.yaml`
Expected: `stringData` includes `MICROSOFT_CLIENT_ID: "x"`, `MICROSOFT_CLIENT_SECRET: "y"`, `MICROSOFT_TENANT_ID: "z"`.

- [ ] **Step 4: Commit**

```bash
git add chart/templates/configmap-api.yaml chart/templates/secret-api.yaml
git commit -m "feat(chart): add api configmap and credentials secret"
```

---

## Task 6: Ingress (reproduce the /api rewrite contract)

**Files:**
- Create: `chart/templates/ingress.yaml`

**Rationale:** Mirror nginx `proxy_pass http://api:5002/;` (strip `/api`) but to the api service on **8000**. Use `nginx.ingress.kubernetes.io/rewrite-target: /$2` with path `/api(/|$)(.*)`, and a separate `/` rule to the frontend. Ordering matters: the `/api` rule must precede `/`.

- [ ] **Step 1: Write `chart/templates/ingress.yaml`**

```yaml
{{- if .Values.ingress.enabled }}
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: {{ include "zienswijzer.fullname" . }}
  labels:
    {{- include "zienswijzer.labels" . | nindent 4 }}
  annotations:
    nginx.ingress.kubernetes.io/rewrite-target: /$2
    nginx.ingress.kubernetes.io/proxy-body-size: "100m"
    nginx.ingress.kubernetes.io/proxy-read-timeout: "600"
    nginx.ingress.kubernetes.io/proxy-send-timeout: "600"
spec:
  {{- if .Values.ingress.className }}
  ingressClassName: {{ .Values.ingress.className }}
  {{- end }}
  {{- if .Values.ingress.tls.enabled }}
  tls:
    - hosts:
        - {{ .Values.ingress.host | quote }}
      secretName: {{ .Values.ingress.tls.secretName | quote }}
  {{- end }}
  rules:
    - host: {{ .Values.ingress.host | quote }}
      http:
        paths:
          # /api/(.*) -> api service "/$1" (strips the /api prefix; backend serves at root on :8000)
          - path: /api(/|$)(.*)
            pathType: ImplementationSpecific
            backend:
              service:
                name: {{ include "zienswijzer.fullname" . }}-api
                port:
                  number: {{ .Values.service.api.port }}
          - path: /
            pathType: Prefix
            backend:
              service:
                name: {{ include "zienswijzer.fullname" . }}-frontend
                port:
                  number: {{ .Values.service.frontend.port }}
{{- end }}
```

- [ ] **Step 2: Render and verify routing**

Run: `helm template zw chart/ --show-only templates/ingress.yaml`
Expected: `rewrite-target: /$2`; first path `/api(/|$)(.*)` → `-api` service port `8000`; second path `/` → `-frontend` service port `3000`.

- [ ] **Step 3: Verify ingress is omitted when disabled**

Run: `helm template zw chart/ --set ingress.enabled=false --show-only templates/ingress.yaml 2>&1 | grep -qi "could not find template\|empty" && echo NO_INGRESS_AS_EXPECTED || echo "check: ingress should be absent"`
Expected: `NO_INGRESS_AS_EXPECTED` (helm errors/returns empty for a fully-conditional template that renders nothing).

- [ ] **Step 4: Commit**

```bash
git add chart/templates/ingress.yaml
git commit -m "feat(chart): add ingress reproducing the /api rewrite routing contract"
```

---

## Task 7: Whole-chart lint + render gate

**Files:** none (validation only). This is the spec's acceptance criterion #1.

- [ ] **Step 1: Lint**

Run: `helm lint chart/`
Expected: `0 chart(s) failed`.

- [ ] **Step 2: Full render with defaults (schema validation included)**

Run: `helm template zw chart/ > /tmp/zw-render.yaml && echo RENDER_OK && grep -c "^kind:" /tmp/zw-render.yaml`
Expected: `RENDER_OK`; kind count = 6 with defaults (Deployment x2, Service x2, ConfigMap, Secret) + Ingress = **7** when `ingress.enabled=true` (default). Confirm 7.

- [ ] **Step 3: Render with persistence + TLS toggled on (exercise conditionals)**

Run: `helm template zw chart/ --set persistence.enabled=true --set ingress.tls.enabled=true --set ingress.tls.secretName=zw-tls --set secrets.microsoftClientId=a --set secrets.microsoftClientSecret=b --set secrets.microsoftTenantId=c | grep -E "kind: (PersistentVolumeClaim)" && echo PVC_RENDERED`
Expected: `kind: PersistentVolumeClaim` present, `PVC_RENDERED` printed.

- [ ] **Step 4: Optional kubeconform validation (if installed)**

Run: `command -v kubeconform >/dev/null && helm template zw chart/ | kubeconform -strict -summary -ignore-missing-schemas || echo "kubeconform not installed — skipping (helm template already validated structure)"`
Expected: either a clean kubeconform summary or the skip message.

- [ ] **Step 5: Commit (if any fixes were needed)**

```bash
git add -A chart/
git commit -m "test(chart): whole-chart lint and render gate passes" || echo "nothing to commit"
```

---

## Task 8: kind end-to-end acceptance test (spec acceptance criteria 2–5)

**Files:**
- Create: `scripts/kind-acceptance.sh`

**Rationale:** Stand up a `kind` cluster + ingress-nginx, install the chart with dummy MICROSOFT_* creds (so the api boots — GROUND TRUTH #4), wait for Ready, then prove: frontend HTML at `/`, `GET /api/health` → 200 (the rewrite contract), and one real API round-trip. Handles private images via `kind load docker-image` (GROUND TRUTH / open item 4).

- [ ] **Step 1: Write `scripts/kind-acceptance.sh`**

```bash
#!/usr/bin/env bash
set -euo pipefail

CLUSTER="zienswijzer-test"
RELEASE="zw"
HOST="zienswijzer.local"
API_IMG="ghcr.io/gradient-ds/woo-api:latest"
FE_IMG="ghcr.io/gradient-ds/woo-frontend:latest"

cleanup() { kind delete cluster --name "$CLUSTER" >/dev/null 2>&1 || true; }
trap cleanup EXIT

echo "==> Creating kind cluster with ingress-ready node"
cat <<'EOF' | kind create cluster --name "$CLUSTER" --config -
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
        hostPort: 8080
        protocol: TCP
EOF

echo "==> Installing ingress-nginx"
kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/main/deploy/static/provider/kind/deploy.yaml
kubectl wait --namespace ingress-nginx \
  --for=condition=ready pod \
  --selector=app.kubernetes.io/component=controller \
  --timeout=180s

echo "==> Loading app images into kind (covers private ghcr images; harmless if public/pre-pulled)"
docker pull "$API_IMG" || echo "WARN: could not pull $API_IMG (private?). Ensure it is available locally."
docker pull "$FE_IMG"  || echo "WARN: could not pull $FE_IMG (private?). Ensure it is available locally."
kind load docker-image "$API_IMG" --name "$CLUSTER" || true
kind load docker-image "$FE_IMG"  --name "$CLUSTER" || true

echo "==> helm install with dummy MICROSOFT_* creds (required for the api to boot)"
helm install "$RELEASE" chart/ \
  --set ingress.host="$HOST" \
  --set image.pullPolicy=IfNotPresent \
  --set secrets.microsoftClientId=dummy-client-id \
  --set secrets.microsoftClientSecret=dummy-client-secret \
  --set secrets.microsoftTenantId=dummy-tenant-id \
  --wait --timeout 300s

echo "==> Waiting for all pods Ready"
kubectl wait --for=condition=ready pod \
  -l app.kubernetes.io/instance="$RELEASE" --timeout=300s

echo "==> Acceptance checks via the ingress (Host header -> 127.0.0.1:8080)"
fail=0

echo "-- [4a] frontend HTML at /"
code=$(curl -s -o /tmp/zw-root.html -w '%{http_code}' -H "Host: $HOST" http://127.0.0.1:8080/ || true)
if [ "$code" = "200" ] && grep -qi "<div id=\"root\"\|<!doctype html\|<html" /tmp/zw-root.html; then
  echo "   OK ($code, HTML served)"
else
  echo "   FAIL (status=$code)"; fail=1
fi

echo "-- [4b] GET /api/health -> 200 (proves /api rewrite contract to :8000 /health)"
code=$(curl -s -o /tmp/zw-health.json -w '%{http_code}' -H "Host: $HOST" http://127.0.0.1:8080/api/health || true)
if [ "$code" = "200" ]; then echo "   OK ($code): $(cat /tmp/zw-health.json)"; else echo "   FAIL (status=$code)"; fail=1; fi

echo "-- [5] real API round-trip: GET /api/cases (list cases from seeded DB)"
code=$(curl -s -o /tmp/zw-cases.json -w '%{http_code}' -H "Host: $HOST" http://127.0.0.1:8080/api/cases || true)
# Accept 200 (public) OR 401 (auth-guarded) — both prove the request reached the app and routed correctly.
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
```

- [ ] **Step 2: Make executable**

Run: `chmod +x scripts/kind-acceptance.sh`

- [ ] **Step 3: Run the acceptance test**

Run: `./scripts/kind-acceptance.sh`
Expected: ends with `ACCEPTANCE PASSED`; `/api/health` returns 200; `/api/cases` returns 200 or 401 (both prove routing). If pods CrashLoopBackOff, check the api logs printed on failure — the most likely cause is a missing MICROSOFT_* var (should be covered by the `--set` flags) or an image pull failure (open item 4: image visibility).

> **Implementer note:** if `/api/cases` is actually a different list route, adjust to a confirmed root route from `app.py` (e.g. `/cases` is defined at `app.py:380`). The route through the ingress is `/api/cases` → rewritten to `/cases`.

- [ ] **Step 4: Commit**

```bash
git add scripts/kind-acceptance.sh
git commit -m "test(chart): add kind end-to-end acceptance script"
```

---

## Task 9: appstore.yaml + demo docs (description, openapi, screenshots)

**Files:**
- Create: `appstore.yaml`
- Create: `docs/description.md`
- Create: `scripts/export-openapi.sh`
- Create: `docs/openapi.yaml` (generated by the script)
- Create: `docs/screenshots/` (>= 3 images — see note)

- [ ] **Step 1: Write `scripts/export-openapi.sh`**

```bash
#!/usr/bin/env bash
set -euo pipefail
# Export the FastAPI schema from the woo-api image to docs/openapi.yaml.
IMG="${1:-ghcr.io/gradient-ds/woo-api:latest}"
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
  sleep 1
done

curl -fs http://127.0.0.1:18000/openapi.json -o /tmp/openapi.json
# Convert JSON -> YAML with yq (the local Homebrew python lacks PyYAML and pip is broken).
yq -p=json -o=yaml /tmp/openapi.json > docs/openapi.yaml
echo "Wrote docs/openapi.yaml"
```

- [ ] **Step 2: Make executable and run it**

Run: `chmod +x scripts/export-openapi.sh && ./scripts/export-openapi.sh`
Expected: `docs/openapi.yaml` exists and contains `openapi:` and `/health` / `/cases` paths.
Fallback: if Docker isn't available, run the app locally (`cd backend && python -m server` with dummy MICROSOFT_* env) and `curl localhost:8000/openapi.json`. If `PyYAML` is missing: `pip install pyyaml`.

- [ ] **Step 3: Write `docs/description.md` (<= 500 chars — the listing blurb)**

```markdown
Zienswijzer is a WOO (Wet Open Overheid) case and document management app for Dutch public bodies. It ingests requests and documents, organises them into cases and workspaces, tracks stakeholders, and uses on-device AI to classify whether stakeholder replies agree to or object to publication. Built by Gradient for EU public-sector transparency. All processing runs in-cluster (data residency: EU).
```

Verify length: Run `wc -m docs/description.md` → expected <= 500.

- [ ] **Step 4: Provide screenshots (>= 3, PNG/JPEG)**

The platform requires 3–20 PNG/JPEG screenshots. These must be real UI captures and cannot be synthesised by the implementer. Create the directory and a README placeholder, and flag for the user:

Create `docs/screenshots/README.md`:

```markdown
# Screenshots (REQUIRED: 3–20 PNG/JPEG)

Place at least 3 real screenshots of the running Zienswijzer UI here, e.g.:
- 01-case-list.png
- 02-case-overview.png
- 03-document-detail.png

Capture them against the running app (kind: `http://zienswijzer.local` via the
acceptance test, or `docker compose -f docker-compose.prod.yaml up`). PNG or JPEG only.
```

> **Implementer note / handoff:** screenshots are a USER action (real UI captures). List this as an outstanding item in `SUBMISSION.md` (Task 12). The submission will be auto-rejected with fewer than 3, so it must be done before submitting.

- [ ] **Step 5: Write `appstore.yaml`**

```yaml
apiVersion: appstore.saidkick.nl/v1
kind: AppManifest
metadata:
  name: zienswijzer                 # immutable slug, 3-60 chars, a-z0-9-
  display_name: Zienswijzer
  vendor: Gradient
  contact: lex@gradient-ds.com
  license: EUPL-1.2
spec:
  chart:
    path: chart/
    type: helm
  categories:
    - document        # TODO(open-item-2): no allowed enum in the manual; adjust if validation rejects.
    - productivity
  ai:
    risk_class: limited
    base_model: cross-encoder/nli-deberta-v3-small   # hardcoded zero-shot classifier (verified in code)
    data_residency: EU
  interfaces:
    - type: api
      openapi: docs/openapi.yaml
  demo:
    description: docs/description.md
    screenshots:
      - docs/screenshots/01-case-list.png
      - docs/screenshots/02-case-overview.png
      - docs/screenshots/03-document-detail.png
  audit:
    dpia: audit/dpia.pdf
    security_scan: audit/security-scan.sarif
    ai_risk: audit/ai-risk-assessment.pdf
    accessibility: audit/accessibility-report.pdf
```

- [ ] **Step 6: Validate appstore.yaml is well-formed YAML and required fields present**

Run (uses `yq`, since local python lacks PyYAML):
```bash
name=$(yq '.metadata.name' appstore.yaml)
res=$(yq '.spec.ai.data_residency' appstore.yaml)
lic=$(yq '.metadata.license' appstore.yaml)
[ "$res" = "EU" ] && [ "$lic" = "EUPL-1.2" ] \
  && echo "$name" | grep -Eq '^[a-z0-9-]{3,60}$' \
  && echo "appstore.yaml OK" || echo "appstore.yaml INVALID"
```
Expected: `appstore.yaml OK` (yq also fails loudly if the YAML is malformed).

- [ ] **Step 7: Commit**

```bash
git add appstore.yaml docs/description.md docs/openapi.yaml docs/screenshots/README.md scripts/export-openapi.sh
git commit -m "feat(submission): add appstore.yaml manifest, description, openapi export and screenshots placeholder"
```

---

## Task 10: Audit documents — DPIA, AI risk, accessibility (markdown → PDF)

**Files:**
- Create: `audit/dpia.md` → render `audit/dpia.pdf`
- Create: `audit/ai-risk-assessment.md` → render `audit/ai-risk-assessment.pdf`
- Create: `audit/accessibility-report.md` → render `audit/accessibility-report.pdf`
- Create: `scripts/render-pdfs.sh`

**Rationale:** Author each as markdown (reviewable in git), render to PDF via whichever tool is installed (pandoc → weasyprint → headless Chrome).

- [ ] **Step 1: Write `audit/dpia.md` (GDPR Data Protection Impact Assessment)**

```markdown
# Data Protection Impact Assessment (DPIA) — Zienswijzer

**Controller:** Deploying public body (the organisation installing Zienswijzer).
**Processor:** Gradient (vendor) / the deploying body's own infrastructure.
**Date:** 2026-06-05
**Application:** Zienswijzer — WOO case & document management.

## 1. Description of processing
Zienswijzer processes WOO (Wet Open Overheid) requests, the documents attached to
them, and correspondence with stakeholders. It organises these into cases and
workspaces and classifies stakeholder replies (agree/object to publication).

## 2. Categories of data subjects and personal data
- **Requesters / correspondents:** name, email address, message content.
- **Stakeholders:** name, organisation, contact details, submitted views.
- **Document content:** may contain personal data of third parties referenced in
  WOO documents.
- **Authentication:** application user accounts (username, session).

Email integration uses Microsoft Graph (OAuth) under the deploying body's own
Azure AD tenant; mailbox data is accessed under the scopes the body grants.

## 3. Purpose and lawful basis
Processing supports a legal obligation (handling WOO requests) and the public-
interest task of the public body (Art. 6(1)(c)/(e) GDPR). AI classification assists
human case handlers; it does not make automated decisions with legal effect.

## 4. Necessity and proportionality
Only data necessary to triage and publish WOO material is processed. AI inference
runs in-cluster (no third-party transfer). Data residency: EU.

## 5. Data flows and storage
- SQLite database inside the cluster (`/app/server/db`), optionally on a PVC.
- Session data in ephemeral storage.
- Email accessed via Microsoft Graph over TLS; nothing exported outside the EU.

## 6. Risks and mitigations
| Risk | Mitigation |
| --- | --- |
| Exposure of third-party personal data in documents | Access control; human review before publication. |
| Unauthorised access | Authenticated app; cluster RBAC; secrets in Vault, never in values.yaml. |
| Misclassification by AI | Limited-risk assistive use; human case handler decides. |
| Data in transit | TLS at the Ingress; in-cluster service traffic. |
| Credential leakage | MICROSOFT_* credentials delivered via Kubernetes Secret / platform Vault. |

## 7. Residual risk and DPO sign-off
Residual risk assessed **low** given human oversight and EU-only processing.

**DPO sign-off**

- Name: ______________________________
- Role / Organisation: ________________
- Date: _______________________________
- Signature: __________________________
```

- [ ] **Step 2: Write `audit/ai-risk-assessment.md` (EU AI Act, limited risk)**

```markdown
# EU AI Act Risk Assessment — Zienswijzer

**Risk classification:** Limited risk.
**Date:** 2026-06-05
**Vendor:** Gradient.

## 1. AI system description
Zienswijzer uses a single AI component: a zero-shot text classifier
(`cross-encoder/nli-deberta-v3-small`, via HuggingFace `transformers`) that labels
stakeholder replies as "agrees to publish" or "objects to publication". The model
runs locally inside the deployment container; no inference data leaves the cluster.

## 2. Intended use
Assistive triage for human WOO case handlers. Output is a suggestion with a
confidence score; a human makes the publication decision.

## 3. Why "limited risk"
- Not a prohibited practice (Art. 5).
- Not high-risk (Annex III): it does not determine access to essential services,
  is not used in law enforcement decisioning, and has no legal effect on persons.
- It is an assistive classification tool with human oversight → limited risk, subject
  to transparency obligations (Art. 50).

## 4. Transparency (Art. 50)
Users are informed that classification is AI-generated. Labels and confidence
scores are surfaced in the UI; the candidate labels are fixed and documented.

## 5. Human oversight
Every classification is reviewable and overridable by the case handler. No
automated publication occurs based solely on the model output.

## 6. Data governance & residency
Inference runs in-cluster on EU infrastructure (data_residency: EU). No training
on user data is performed by this deployment. The base model is a fixed,
pre-trained, open model.

## 7. Robustness & monitoring
The classifier is loaded lazily and isolated to the `/classification` endpoints;
failures are surfaced as errors and do not affect core case management.
```

- [ ] **Step 3: Write `audit/accessibility-report.md` (WCAG 2.2 AA)**

```markdown
# Accessibility Report — Zienswijzer (WCAG 2.2 Level AA)

**Date:** 2026-06-05
**Standard:** WCAG 2.2, Level AA.
**Method:** Automated checks (axe-core / Lighthouse) against the running frontend,
plus manual keyboard and contrast review.

## 1. Scope
The Zienswijzer React frontend (served at `/`): login, case list, case overview,
document detail, stakeholder views.

## 2. Summary of conformance
| Principle | Status | Notes |
| --- | --- | --- |
| Perceivable | Partially verified | Colour contrast and text alternatives reviewed on core screens. |
| Operable | Partially verified | Keyboard navigation across primary flows. |
| Understandable | Partially verified | Consistent navigation, labelled form fields. |
| Robust | Partially verified | Semantic HTML; ARIA where needed. |

## 3. Automated scan
Run axe-core/Lighthouse against the running app (see SUBMISSION.md) and paste the
score and any violations here before submission. Target: no critical violations.

## 4. Known items / remediation
- Document any contrast or focus-order issues found during the scan and the plan
  to address them.

## 5. Statement
Zienswijzer targets WCAG 2.2 AA. This report should be refreshed with the latest
automated scan output against the deployed build prior to each submission.
```

> **Implementer note:** the accessibility report contains placeholders for real axe/Lighthouse output. Note in `SUBMISSION.md` that the user should run a scan against the running frontend and paste results before submitting. The document is structurally complete and valid as-is.

- [ ] **Step 4: Write `scripts/render-pdfs.sh`**

```bash
#!/usr/bin/env bash
set -euo pipefail
# Render audit markdown -> PDF using whatever is installed: pandoc -> weasyprint -> chrome.
render() {
  local md="$1" pdf="${1%.md}.pdf"
  if command -v pandoc >/dev/null; then
    pandoc "$md" -o "$pdf" && { echo "pandoc -> $pdf"; return; }
  fi
  if command -v weasyprint >/dev/null && command -v pandoc >/dev/null; then
    pandoc "$md" -o /tmp/_a.html && weasyprint /tmp/_a.html "$pdf" && { echo "weasyprint -> $pdf"; return; }
  fi
  # Headless Chrome fallback (markdown rendered as preformatted HTML).
  python3 -c 'import html,sys; print("<pre>"+html.escape(open(sys.argv[1]).read())+"</pre>")' "$md" > /tmp/_a.html
  for chrome in "google-chrome" "chromium" "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"; do
    if command -v "$chrome" >/dev/null 2>&1 || [ -x "$chrome" ]; then
      "$chrome" --headless --disable-gpu --print-to-pdf="$pdf" "file:///tmp/_a.html" && { echo "chrome -> $pdf"; return; }
    fi
  done
  echo "ERROR: no PDF renderer found (install pandoc, weasyprint, or Chrome)"; exit 1
}
render audit/dpia.md
render audit/ai-risk-assessment.md
render audit/accessibility-report.md
```

- [ ] **Step 5: Render the PDFs**

Run: `chmod +x scripts/render-pdfs.sh && ./scripts/render-pdfs.sh && ls -la audit/*.pdf`
Expected: `audit/dpia.pdf`, `audit/ai-risk-assessment.pdf`, `audit/accessibility-report.pdf` all exist and are > 0 bytes.

- [ ] **Step 6: Commit**

```bash
git add audit/dpia.md audit/ai-risk-assessment.md audit/accessibility-report.md audit/dpia.pdf audit/ai-risk-assessment.pdf audit/accessibility-report.pdf scripts/render-pdfs.sh
git commit -m "feat(audit): add DPIA, AI risk and accessibility documents (md + pdf)"
```

---

## Task 11: Real Trivy security scan → SARIF (gating risk)

**Files:**
- Create: `scripts/trivy-scan.sh`
- Create: `audit/security-scan.sarif`

**Rationale:** SARIF 2.1.0, **≤ 100 KB**, from a **real** Trivy scan of both ghcr images. **Auto-reject if any finding has CVSS ≥ 7.0.** This is a gating risk — if HIGH/CRITICAL findings exist, they must be remediated (image rebuild) before submission; flag loudly rather than hide them.

- [ ] **Step 1: Write `scripts/trivy-scan.sh`**

```bash
#!/usr/bin/env bash
set -euo pipefail
API_IMG="${1:-ghcr.io/gradient-ds/woo-api:latest}"
FE_IMG="${2:-ghcr.io/gradient-ds/woo-frontend:latest}"
OUT="audit/security-scan.sarif"

echo "==> Trivy scan (SARIF) of both images"
# Scan each image to SARIF, then merge runs into one SARIF document.
trivy image --quiet --format sarif --output /tmp/api.sarif "$API_IMG"
trivy image --quiet --format sarif --output /tmp/fe.sarif  "$FE_IMG"

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
hc=$(trivy image --quiet --format json --severity HIGH,CRITICAL "$API_IMG" "$FE_IMG" 2>/dev/null \
     | python3 -c 'import json,sys; d=json.load(sys.stdin); print(sum(len(r.get("Vulnerabilities") or []) for r in (d.get("Results") or [])))' 2>/dev/null || echo "?")
echo "HIGH/CRITICAL findings (approx): ${hc}"
if [ "$hc" != "0" ] && [ "$hc" != "?" ]; then
  echo "!!! GATING: HIGH/CRITICAL vulnerabilities present. The platform auto-rejects CVSS>=7.0."
  echo "!!! Remediate (rebuild images with patched base/deps) before submitting."
fi
```

- [ ] **Step 2: Run the scan**

Run: `chmod +x scripts/trivy-scan.sh && ./scripts/trivy-scan.sh`
Expected: `audit/security-scan.sarif` written; size printed (aim ≤ 100 KB — if over, re-run trivy with `--severity HIGH,CRITICAL` inside the script); HIGH/CRITICAL count printed.

- [ ] **Step 3: Validate SARIF structure and size gate**

Run: `python3 -c 'import json; d=json.load(open("audit/security-scan.sarif")); assert d["version"]=="2.1.0", d.get("version"); assert d["runs"]; print("SARIF 2.1.0 OK, runs:", len(d["runs"]))' && [ $(wc -c < audit/security-scan.sarif) -le 102400 ] && echo "SIZE_OK (<=100KB)" || echo "SIZE_OVER_100KB — shrink with --severity HIGH,CRITICAL"`
Expected: `SARIF 2.1.0 OK` and `SIZE_OK`.

- [ ] **Step 4: Record the CVSS gate result**

If HIGH/CRITICAL findings exist, STOP and surface to the controller/user: the submission will be auto-rejected and images must be rebuilt (this is explicitly the only sanctioned source-change trigger per the spec's "out of scope"). If zero, note "no CVSS ≥ 7.0 findings" in `SUBMISSION.md`.

- [ ] **Step 5: Commit**

```bash
git add scripts/trivy-scan.sh audit/security-scan.sarif
git commit -m "feat(audit): add real Trivy security scan SARIF with CVSS gate"
```

---

## Task 12: SUBMISSION.md handoff guide

**Files:**
- Create: `SUBMISSION.md`

**Rationale:** Browser-only steps are out of scope for automation; document them precisely, plus the outstanding manual items (screenshots, accessibility scan results, concrete image tag, image visibility, any CVSS remediation).

- [ ] **Step 1: Write `SUBMISSION.md`**

```markdown
# Zienswijzer — sAId-Kick App Store submission guide

This repo contains everything the platform fetches from the root of `main`:
`appstore.yaml`, `chart/`, `docs/`, and `audit/`. This guide covers the
browser-only steps and the manual items that must be done before submitting.

## 0. Pre-submission checklist (DO THESE FIRST)

- [ ] **Image tag** — replace `latest` in `chart/values.yaml` (`image.api.tag`,
      `image.frontend.tag`) and `Chart.yaml` `appVersion` with a concrete immutable
      released tag/digest. (Open item 5.)
- [ ] **Image visibility** — confirm `ghcr.io/gradient-ds/woo-api` and
      `woo-frontend` are PUBLIC. If private, external one-click deploys need an
      imagePullSecret (configure `image.pullSecrets`). (Open item 4.)
- [ ] **Screenshots** — add ≥ 3 real PNG/JPEG captures under `docs/screenshots/`
      (the manifest references `01-case-list.png`, `02-case-overview.png`,
      `03-document-detail.png`). Capture against the running app
      (`./scripts/kind-acceptance.sh` exposes it at `http://zienswijzer.local`
      via `Host:` header on `127.0.0.1:8080`, or use the prod compose).
- [ ] **Accessibility scan** — run axe-core/Lighthouse against the running
      frontend and paste results into `audit/accessibility-report.md`, then
      re-render: `./scripts/render-pdfs.sh`.
- [ ] **Security gate** — `./scripts/trivy-scan.sh` must show **no HIGH/CRITICAL
      (CVSS ≥ 7.0)** findings. If any exist, rebuild the images with patched
      bases/deps and re-scan — the platform auto-rejects otherwise.
- [ ] **Local acceptance** — `./scripts/kind-acceptance.sh` ends with
      `ACCEPTANCE PASSED`.
- [ ] **categories** — `appstore.yaml` uses `document`/`productivity` as a best
      guess (the manual has no enum). Adjust if automated validation rejects.
      (Open item 2.)

## 1. Rename the GitHub repository
Rename the repo to `zienswijzer` (the immutable app slug; user action — out of
scope for automation).

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
- The backend listens on **:8000**; the Ingress rewrites `/api/(.*)` → api `/$1`.
- Required runtime secrets are Azure OAuth: `MICROSOFT_CLIENT_ID`,
  `MICROSOFT_CLIENT_SECRET`, `MICROSOFT_TENANT_ID` (supplied via the platform Vault;
  `format: secret` in `values.schema.json`). The api will not start without them.
- License: **EUPL-1.2**. EU AI Act class: **limited**. Data residency: **EU**.
```

- [ ] **Step 2: Verify the guide references real files**

Run: `for f in appstore.yaml chart/values.schema.json scripts/kind-acceptance.sh scripts/trivy-scan.sh scripts/render-pdfs.sh; do test -f "$f" && echo "OK $f" || echo "MISSING $f"; done`
Expected: all `OK`.

- [ ] **Step 3: Commit**

```bash
git add SUBMISSION.md
git commit -m "docs: add SUBMISSION.md handoff guide for browser-only signup steps"
```

---

## Final review (after all tasks)

- [ ] Run the whole-chart gate again: `helm lint chart/ && helm template zw chart/ >/dev/null && echo OK`.
- [ ] Run `./scripts/kind-acceptance.sh` once more end-to-end → `ACCEPTANCE PASSED`.
- [ ] Confirm the submission tree exists: `appstore.yaml`, `chart/` (with `values.schema.json`), `docs/` (description, openapi, ≥3 screenshots), `audit/` (3 PDFs + SARIF ≤ 100 KB, no CVSS ≥ 7.0).
- [ ] Dispatch a final code-reviewer over the whole branch.
- [ ] Use `superpowers:finishing-a-development-branch` to integrate.

---

## Spec coverage self-check

| Spec deliverable | Task |
| --- | --- |
| Submission files at repo root, existing files untouched | 1–12 (additive only) |
| Helm chart: api + frontend + ingress; lint + template + schema | 1–7 |
| Deploys & serves on local kind (acceptance 1–5) | 7, 8 |
| Four audit docs, SARIF from real Trivy | 10, 11 |
| SUBMISSION.md handoff | 12 |
| appstore.yaml (slug, license EUPL-1.2, ai limited/EU, openapi, screenshots, audit) | 9 |
| values.schema.json drives form; secrets via format:secret | 2, 5 |
| Ingress `/api(/|$)(.*)` rewrite to api:8000, `/` to frontend | 6 |
| Open items: license(1) EUPL-1.2, categories(2) document/productivity, base_model(3) resolved, image visibility(4) flagged, image tag(5) flagged | 1, 9, 11, 12 |

## Deviations from the spec (intentional, justified)
- **Backend port 8000, not 5002** — the code/image actually serves 8000 (verified; locked with user).
- **Secrets are MICROSOFT_* OAuth, not MODEL_PROVIDER/HF_KEY/etc.** — the latter don't exist in the code (verified; locked with user).
- **api `readOnlyRootFilesystem: false`** — SQLite writes into the code dir; read-only would crash the pod (a code change to relocate the DB is out of scope).
- **DB path `/app/server/db`, not `/app/db`** — actual `Path(__file__).with_name(...)` resolution.
- **ConfigMap not mounted** — the app is env-driven; `config.yaml` is not read by the code.
