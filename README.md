# Wealthtender Capstone Dashboard

This repo contains two modular apps:
- `api/` (FastAPI) serves normalized dashboard data.
- `dashboard/` (Plotly Dash) renders views for firms and advisors.

Launch Dashboard (local demo):

[![Launch Dashboard](https://img.shields.io/badge/launch-dashboard-blue)](http://localhost:8050)

## Quickstart (local)

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Terminal 1
uvicorn api.main:app --reload --port 8000

# Terminal 2
python dashboard/app.py
```

Then open:

```
http://localhost:8050
```

## Structure

- `api/` FastAPI service that reads artifacts and exposes firm/advisor endpoints.
- `dashboard/` Dash app (multi-page) that calls the API.
- `artifacts/` Example artifacts (dev only).
- `data_contract/` Data contract and schema expectations.
- `config/` Dashboard and scoring configuration.

## Notes

- Auth is stubbed. The dashboard currently uses a firm selector to simulate firm scoping.
- Artifacts are loaded via the API. The dashboard does not read files directly.
