# Wealthtender Capstone Dashboard

This repo contains two modular apps:
- `api/` (FastAPI) serves normalized dashboard data.
- `dashboard/` (Plotly Dash) renders views for firms and advisors.

Launch Dashboard (local demo):

[![Launch Dashboard](https://img.shields.io/badge/launch-dashboard-blue)](http://localhost:8050)

## Quickstart (local)

### macOS / Linux (one command)

```bash
git clone https://github.com/AHMerrill/Wealthtender-Capstone-Dashboard.git && cd Wealthtender-Capstone-Dashboard && ./run.sh
```

### Windows PowerShell (one command)

```powershell
git clone https://github.com/AHMerrill/Wealthtender-Capstone-Dashboard.git; cd Wealthtender-Capstone-Dashboard; .\run.ps1
```

Then open:

```
http://localhost:8050
```

If you already cloned the repo, just run:

```bash
./run.sh
```

Do not run `git clone` from inside an existing clone (it creates nested folders).

Note: the first run installs dependencies and can take a minute. Subsequent runs are fast.

## Notes on Python Version

This repo supports Python 3.9–3.13. The launcher prefers 3.12 or 3.11 if available,
but will use your default `python3` if not.

## Structure

- `api/` FastAPI service that reads artifacts and exposes firm/advisor endpoints.
- `dashboard/` Dash app (multi-page) that calls the API.
- `artifacts/` Example artifacts (dev only).
- `data_contract/` Data contract and schema expectations.
- `config/` Dashboard and scoring configuration.

## Notes

- Auth is stubbed. The dashboard currently uses a firm selector to simulate firm scoping.
- Artifacts are loaded via the API. The dashboard does not read files directly.

## Deployment + Auth Handoff

This repo is designed for a standard production setup:

1. Deploy the API and Dash app on a server or container.
2. Put authentication in front of the app (reverse proxy or API-layer auth).
3. Expose a URL like `dashboard.clientsite.com`, or embed via iframe.

Common auth options:
- Username/password via reverse proxy (e.g., Nginx + basic auth or OAuth/SSO).
- Firm-scoped JWTs enforced by the API.
- SSO integration handled at the hosting layer.

The dashboard already assumes firm scoping. In production, the selected firm should
come from the authenticated user context rather than a dropdown.
