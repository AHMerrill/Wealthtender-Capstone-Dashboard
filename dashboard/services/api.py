import requests
from dashboard.data.mock_data import MOCK_FIRMS, MOCK_FIRM_SUMMARY

API_BASE = "http://localhost:8000"


def _get(path: str):
    try:
        resp = requests.get(f"{API_BASE}{path}", timeout=2)
        if resp.status_code == 200:
            return resp.json()
    except Exception:
        return None
    return None


def get_firms():
    data = _get("/api/firms")
    return data if data else MOCK_FIRMS


def get_firm_summary(firm_id: str):
    data = _get(f"/api/firm/{firm_id}/summary")
    return data if data else MOCK_FIRM_SUMMARY
