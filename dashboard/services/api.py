"""Dashboard HTTP client for the Wealthtender API.

Provides typed helpers for every API endpoint and a robust warm-up routine
that retries with exponential back-off so Render cold-starts don't leave the
dashboard with empty data.
"""

from typing import Optional, Dict, Any
import logging
import os
import time

import requests

log = logging.getLogger(__name__)

API_BASE = os.getenv("API_BASE", "http://localhost:8000")

# ---------------------------------------------------------------------------
# Low-level helpers
# ---------------------------------------------------------------------------

_session = requests.Session()


def _get(path: str, params: Optional[Dict] = None, timeout: int = 30) -> Any:
    """GET an API endpoint and return parsed JSON, or None on failure."""
    url = f"{API_BASE}{path}"
    try:
        resp = _session.get(url, params=params, timeout=timeout)
        if resp.status_code == 200:
            return resp.json()
        log.warning("API %s returned %s: %s", url, resp.status_code, resp.text[:200])
    except requests.ConnectionError:
        log.warning("API unreachable: %s (is the API service running?)", url)
    except requests.Timeout:
        log.warning("API timeout after %ss: %s", timeout, url)
    except Exception:
        log.exception("Unexpected error calling %s", url)
    return None


# ---------------------------------------------------------------------------
# Public API helpers
# ---------------------------------------------------------------------------

def get_firms() -> list:
    return _get("/api/firms") or []


def get_firm_summary(firm_id: str) -> dict:
    return _get(f"/api/firm/{firm_id}/summary") or {}


def get_firm_dimensions(firm_id: str) -> list:
    return _get(f"/api/firm/{firm_id}/dimensions") or []


def get_stopwords() -> list:
    return _get("/api/stopwords") or []


def get_eda_charts(params: dict) -> dict:
    return _get("/api/eda/charts", params=params) or {}


def get_review_detail(review_id: str) -> dict:
    return _get(f"/api/reviews/{review_id}") or {}


# ---------------------------------------------------------------------------
# API warm-up with retry (critical for Render cold-start)
# ---------------------------------------------------------------------------

_api_ready = False


def is_api_ready() -> bool:
    """Check whether warm_api has successfully contacted the API."""
    return _api_ready


def warm_api(
    max_attempts: int = 10,
    initial_delay: float = 2.0,
    max_delay: float = 30.0,
) -> None:
    """Hit the API health endpoint with exponential back-off.

    Render free-tier services spin down after inactivity.  When the dashboard
    container starts, the API container may still be cold.  This routine keeps
    retrying so the API is warm by the time the user's first callback fires.
    """
    global _api_ready
    url = f"{API_BASE}/api/health"
    delay = initial_delay

    for attempt in range(1, max_attempts + 1):
        try:
            resp = _session.get(url, timeout=15)
            if resp.status_code == 200:
                log.info("API is ready (attempt %d/%d)", attempt, max_attempts)
                _api_ready = True
                return
            log.warning(
                "API health returned %s (attempt %d/%d)",
                resp.status_code, attempt, max_attempts,
            )
        except requests.ConnectionError:
            log.info(
                "API not yet reachable (attempt %d/%d, retrying in %.0fs)",
                attempt, max_attempts, delay,
            )
        except requests.Timeout:
            log.info(
                "API health timed out (attempt %d/%d, retrying in %.0fs)",
                attempt, max_attempts, delay,
            )
        except Exception:
            log.exception("Unexpected error during warm-up (attempt %d/%d)", attempt, max_attempts)

        time.sleep(delay)
        delay = min(delay * 1.5, max_delay)

    log.error("API failed to respond after %d warm-up attempts", max_attempts)
