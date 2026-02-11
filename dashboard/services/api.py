"""Dashboard HTTP client for the Wealthtender API.

Provides typed helpers for every API endpoint and a robust warm-up routine
that retries with exponential back-off so Render cold-starts don't leave the
dashboard with empty data.
"""

from typing import Optional, Dict, Any
import logging
import os
import threading
import time

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

log = logging.getLogger(__name__)

API_BASE = os.getenv("API_BASE", "http://localhost:8000")
API_KEY = os.getenv("API_KEY", "")

# ---------------------------------------------------------------------------
# Low-level helpers
# ---------------------------------------------------------------------------

_session = requests.Session()
_retry = Retry(total=2, backoff_factor=0.5, status_forcelist=[429, 502, 503, 504])
_session.mount("http://", HTTPAdapter(max_retries=_retry, pool_maxsize=20))
_session.mount("https://", HTTPAdapter(max_retries=_retry, pool_maxsize=20))

# Attach API key header to every request when configured.
if API_KEY:
    _session.headers["X-API-Key"] = API_KEY


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
_warm_lock = threading.Lock()
_warm_started = False


def is_api_ready() -> bool:
    """Check whether warm_api has successfully contacted the API."""
    return _api_ready


def warm_api(
    max_attempts: int = 12,
    initial_delay: float = 5.0,
    max_delay: float = 30.0,
    boot_wait: float = 15.0,
) -> None:
    """Hit the API health endpoint with exponential back-off.

    Render free-tier services spin down after inactivity.  When the dashboard
    container starts, the API container may still be cold.  This routine keeps
    retrying so the API is warm by the time the user's first callback fires.

    Parameters
    ----------
    boot_wait : float
        Seconds to sleep before the first attempt, giving the API container
        time to boot so we don't burn retries (and trigger 429s) while
        Render's reverse proxy is still starting the process.
    """
    global _api_ready, _warm_started

    # Thread-safe: only the first thread to acquire the lock runs warm-up.
    with _warm_lock:
        if _warm_started:
            return
        _warm_started = True

    url = f"{API_BASE}/api/health"

    # --- Initial grace period ---
    # On Render the API container typically needs 10-20s to boot.
    # Waiting here avoids the first ~5 retries that always get 429'd.
    if boot_wait > 0:
        log.info("Waiting %.0fs for API container to boot before first health check...", boot_wait)
        time.sleep(boot_wait)

    delay = initial_delay

    for attempt in range(1, max_attempts + 1):
        try:
            resp = _session.get(url, timeout=15)
            if resp.status_code == 200:
                log.info("API is ready (attempt %d/%d)", attempt, max_attempts)
                _api_ready = True
                return
            if resp.status_code == 429:
                # Rate-limited during cold start -- back off more aggressively
                log.info(
                    "API rate-limited 429 (attempt %d/%d, backing off %.0fs)",
                    attempt, max_attempts, delay,
                )
            else:
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
        delay = min(delay * 2, max_delay)

    log.error("API failed to respond after %d warm-up attempts", max_attempts)
