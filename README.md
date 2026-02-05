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

## Notes on Python Version

This repo supports Python 3.11–3.13. The launcher will use 3.12 or 3.11 if available,
but 3.13 should work out of the box with the current dependency pins.

## Structure

- `api/` FastAPI service that reads artifacts and exposes firm/advisor endpoints.
- `dashboard/` Dash app (multi-page) that calls the API.
- `artifacts/` Example artifacts (dev only).
- `data_contract/` Data contract and schema expectations.
- `config/` Dashboard and scoring configuration.

## Notes

- Auth is stubbed. The dashboard currently uses a firm selector to simulate firm scoping.
- Artifacts are loaded via the API. The dashboard does not read files directly.
