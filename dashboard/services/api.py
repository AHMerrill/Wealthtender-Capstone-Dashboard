from typing import Optional, Dict

import requests

API_BASE = "http://localhost:8000"


def _get(path: str, params: Optional[Dict] = None):
    try:
        resp = requests.get(f"{API_BASE}{path}", params=params, timeout=2)
        if resp.status_code == 200:
            return resp.json()
    except Exception:
        return None
    return None


def get_firms():
    data = _get("/api/firms")
    return data if data else []


def get_firm_summary(firm_id: str):
    data = _get(f"/api/firm/{firm_id}/summary")
    return data if data else {}


def get_firm_dimensions(firm_id: str):
    data = _get(f"/api/firm/{firm_id}/dimensions")
    return data if data else []


def get_macro_insights(params: dict):
    data = _get("/api/macro-insights/charts", params=params)
    return data if data else {}


def get_review_detail(review_id: str):
    data = _get(f"/api/reviews/{review_id}")
    return data if data else {}
