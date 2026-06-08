# Contributing to Zienswijzer

Thanks for your interest in contributing! This document covers everything you
need to get a development environment running and to get your change merged.

By contributing to this project, you agree that your contributions will be
licensed under the [European Union Public Licence v1.2 (EUPL-1.2)](LICENSE), the
same licence that covers the project.

## Code of Conduct

This project and everyone participating in it is governed by our
[Code of Conduct](CODE_OF_CONDUCT.md). By participating, you are expected to
uphold it. Please report unacceptable behaviour to lex@gradient-ds.com.

## Reporting bugs and requesting features

- **Security vulnerabilities:** do **not** open a public issue. Follow our
  [Security Policy](SECURITY.md) instead.
- **Bugs and feature requests:** open a GitHub issue using the provided
  templates. Search existing issues first to avoid duplicates.

## Development setup

The project has two parts: a Python backend (`backend/`) and a React/Vite
frontend (`frontend/`).

### Prerequisites

- [uv](https://docs.astral.sh/uv/) (manages Python and dependencies)
- [Node.js](https://nodejs.org/) 20+ and npm
- Docker (optional, for building/running container images)

### Backend

```bash
cd backend
uv sync                              # creates .venv and installs locked deps
uv run uvicorn server.app:app --reload   # http://localhost:8000
```

Dependencies are declared in `backend/pyproject.toml` and pinned in
`backend/uv.lock`. To add or change a dependency, edit `pyproject.toml` and run
`uv lock`, then commit both files. To bump a single package (e.g. for a security
fix): `uv lock --upgrade-package <name>`.

### Frontend

```bash
cd frontend
npm install
npm run dev                          # http://localhost:3000
```

## Before you open a pull request

Please make sure the relevant checks pass locally:

```bash
# Backend
cd backend
uv run pytest                        # tests
uv run ruff check .                  # lint
uv run black --check .               # formatting

# Frontend
cd frontend
npm run lint
npm run typecheck
npm run test:run
```

## Pull request process

1. Fork the repository and create a topic branch from `main`
   (e.g. `feat/short-description` or `fix/short-description`).
2. Keep changes focused — one logical change per PR.
3. Write clear commit messages. We loosely follow
   [Conventional Commits](https://www.conventionalcommits.org/)
   (`feat:`, `fix:`, `docs:`, `chore:`, etc.).
4. Update documentation and tests alongside code changes.
5. Fill in the pull request template and link any related issues.
6. A maintainer will review your PR. Be responsive to feedback; we may ask for
   changes before merging.

## License

By submitting a contribution, you certify that you have the right to do so and
that your contribution is provided under the EUPL-1.2.
