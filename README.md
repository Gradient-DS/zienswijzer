# Zienswijzer

A WOO (Wet Open Overheid) case and document management app for Dutch public
bodies. It ingests requests and documents, organises them into cases and
workspaces, tracks stakeholders, and uses **on-device AI** to classify whether
stakeholder replies agree to or object to publication. Built by Gradient for
EU public-sector transparency — all processing runs in-cluster
(data residency: **EU**, EU AI Act class: **limited**).

## Features

- **Cases & workspaces** — organise WOO requests, documents, and stakeholders
- **PDF ingestion** — upload, parse, chunk, and view documents in-browser
- **Named-entity recognition** — extract stakeholders from document text
- **Reply classification** — on-device model flags replies as agreeing or objecting to publication
- **Email integration** — fetch and send via Microsoft Graph (Outlook)
- **Microsoft/Azure OAuth** — single-tenant EntraID authentication

## Tech Stack

**Backend** — FastAPI · Python 3.11 · [uv](https://docs.astral.sh/uv/) · SQLite ·
PyMuPDF · spaCy · Transformers / PyTorch (CPU) · MSAL

**Frontend** — React 19 · TypeScript · Vite 7 · TanStack Query · Zustand ·
Tailwind CSS 4 · shadcn/ui · react-pdf

## Quick Start

You need [uv](https://docs.astral.sh/uv/getting-started/installation/) and
Node.js 18+.

### Backend

```bash
cd backend
cp .env.example .env        # fill in MICROSOFT_CLIENT_ID / _SECRET / _TENANT_ID
uv sync                     # installs Python 3.11 + locked deps
uv run uvicorn server.app:app --reload
```

Runs at `http://localhost:8000`. The API will not start without valid Azure
OAuth credentials. Interactive docs at `/docs`; the full contract lives in
[`docs/openapi.yaml`](docs/openapi.yaml).

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Runs at `http://localhost:3000`. Set `VITE_API_BASE_URL` in `frontend/.env` to
point at a non-default backend (defaults to `http://localhost:8000`).

## Configuration

Backend runtime secrets (Azure App Registration → `backend/.env`, see
[`.env.example`](backend/.env.example)):

| Variable | Required | Purpose |
| --- | --- | --- |
| `MICROSOFT_CLIENT_ID` | yes | OAuth client ID |
| `MICROSOFT_CLIENT_SECRET` | yes | OAuth client secret |
| `MICROSOFT_TENANT_ID` | yes | Single-tenant Azure AD tenant |
| `MICROSOFT_REDIRECT_URI` | no | OAuth callback (default `http://localhost:8000/email/callback`) |

## Project Structure

```
backend/server/      FastAPI app, routers (auth, cases, documents, email,
  app.py             classification, verification, pdf)
  db/                SQLite schema, init, dummy seed data
  email/             Microsoft Graph integration
  reply_classification/
  utils/             PDF parsing, chunking, NER processing
frontend/src/        React app (api/, components/, pages/, store/, types/)
chart/               Helm chart (api + frontend + Ingress)
audit/               Accessibility, AI risk, DPIA, Trivy security scan
docs/                openapi.yaml, description, screenshots
scripts/             trivy-scan, kind-acceptance, export-openapi, render-pdfs
```

## Testing

```bash
cd frontend && npm test          # frontend unit tests (Vitest)
cd backend && uv run pytest      # backend tests
```

## Deployment

Container images are published to GHCR
(`ghcr.io/gradient-ds/zienswijzer-api`, `…/zienswijzer-frontend`), both passing
Trivy with **zero HIGH/CRITICAL** CVEs (`./scripts/trivy-scan.sh`).

- **Docker Compose** — [`docker-compose.prod.yaml`](docker-compose.prod.yaml)
  (api + frontend + nginx/certbot TLS)
- **Kubernetes** — Helm [`chart/`](chart) deploys api + frontend + Ingress;
  OAuth secrets come from the platform Vault, persistence is opt-in
- **sAId-Kick App Store** — see [`SUBMISSION.md`](SUBMISSION.md)

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md), [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md),
and [SECURITY.md](SECURITY.md).

## License

Licensed under the **European Union Public Licence v1.2 (EUPL-1.2)** — see
[LICENSE](LICENSE).
