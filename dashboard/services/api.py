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
# Only auto-retry on actual server errors. Do NOT retry on 429 -- that makes
# rate-limiting worse by hammering the API with extra requests during cold start.
_retry = Retry(total=2, backoff_factor=0.5, status_forcelist=[502, 503, 504])
_session.mount("http://", HTTPAdapter(max_retries=_retry, pool_maxsize=20))
_session.mount("https://", HTTPAdapter(max_retries=_retry, pool_maxsize=20))

# Attach API key header to every request when configured.
if API_KEY:
    _session.headers["X-API-Key"] = API_KEY


def _get(path: str, params: Optional[Dict] = None, timeout: int = 30) -> Any:
    """GET an API endpoint and return parsed JSON, or None on failure."""
    global _api_ready
    url = f"{API_BASE}{path}"
    try:
        resp = _session.get(url, params=params, timeout=timeout)
        if resp.status_code == 200:
            # Mark the API as ready so the status banner clears, even if
            # the warm-up thread hasn't finished its own health check yet.
            if not _api_ready:
                _api_ready = True
            return resp.json()
        if resp.status_code == 429:
            # Rate-limited (common during Render cold start) — return None
            # quietly so the dashboard shows empty data and the interval
            # callback retries on its own schedule.
            log.info("API rate-limited (429): %s — will retry on next callback", path)
        else:
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


def get_stopwords() -> list:
    return _get("/api/stopwords") or []


def get_eda_charts(params: dict) -> dict:
    return _get("/api/eda/charts", params=params) or {}


def get_review_detail(review_id: str) -> dict:
    return _get(f"/api/reviews/{review_id}") or {}


def get_dna_macro_totals(min_peer_reviews: int = 0) -> dict:
    params = {}
    if min_peer_reviews > 0:
        params["min_peer_reviews"] = min_peer_reviews
    return _get("/api/advisor-dna/macro-totals", params=params or None) or {}


def get_dna_entities() -> dict:
    return _get("/api/advisor-dna/entities") or {"firms": [], "advisors": []}


def get_dna_entity_reviews(entity_id: str) -> list:
    return _get("/api/advisor-dna/entity-reviews", params={"entity_id": entity_id}) or []


def get_dna_advisor_scores(entity_id: str, method: str = "mean") -> dict:
    return _get("/api/advisor-dna/advisor-scores",
                params={"entity_id": entity_id, "method": method}) or {}


def get_dna_percentile_scores(entity_id: str, method: str = "mean",
                              min_peer_reviews: int = 0) -> dict:
    params = {"entity_id": entity_id, "method": method}
    if min_peer_reviews > 0:
        params["min_peer_reviews"] = min_peer_reviews
    return _get("/api/advisor-dna/percentile-scores", params=params) or {}


def get_dna_method_breakpoints(method: str = "mean", entity_type: str = "firm") -> dict:
    return _get("/api/advisor-dna/method-breakpoints",
                params={"method": method, "entity_type": entity_type}) or {}


def get_dna_review_detail(review_idx: int) -> dict:
    return _get(f"/api/advisor-dna/review/{review_idx}") or {}


# ---------------------------------------------------------------------------
# Benchmarks / Leaderboard / Comparisons
# ---------------------------------------------------------------------------

def get_benchmark_pool_stats(min_peer_reviews: int = 20) -> dict:
    return _get("/api/benchmarks/pool-stats",
                params={"min_peer_reviews": min_peer_reviews}) or {}


def get_benchmark_distributions(method: str = "mean", entity_type: str = "all",
                                 min_peer_reviews: int = 0) -> dict:
    params = {"method": method, "entity_type": entity_type}
    if min_peer_reviews > 0:
        params["min_peer_reviews"] = min_peer_reviews
    return _get("/api/benchmarks/distributions", params=params) or {}


def get_leaderboard(method: str = "mean", entity_type: str = "all",
                    min_peer_reviews: int = 0, top_n: int = 10) -> dict:
    params = {"method": method, "entity_type": entity_type,
              "min_peer_reviews": min_peer_reviews, "top_n": top_n}
    return _get("/api/leaderboard", params=params) or {}


def get_partner_groups() -> list:
    return _get("/api/comparisons/partner-groups") or []


def get_partner_group_members(group_code: str, method: str = "mean") -> dict:
    return _get(f"/api/comparisons/partner-group/{group_code}",
                params={"method": method}) or {}


def get_entity_comparison(entity_ids: list, method: str = "mean") -> list:
    return _get("/api/comparisons/entities",
                params={"entity_ids": entity_ids, "method": method}) or []


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
    max_attempts: int = 15,
    initial_delay: float = 8.0,
    max_delay: float = 45.0,
    boot_wait: float = 30.0,
) -> None:
    """Hit the API health endpoint with exponential back-off.

    Render free-tier services spin down after inactivity.  When the dashboard
    container starts, the API container may still be cold.  This routine keeps
    retrying so the API is warm by the time the user's first callback fires.

    IMPORTANT: This uses a plain requests.get() — NOT the shared _session —
    because _session has urllib3 Retry configured with 429 in the
    status_forcelist.  That causes retries-inside-retries during cold start,
    which hammers the API and makes the 429 storm worse.  We control the
    retry timing ourselves here with the backoff loop.

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

    # Use a plain session with NO automatic retries for warm-up.
    # This prevents urllib3 from retrying 429s internally and compounding
    # the rate-limit problem during Render cold starts.
    warm_session = requests.Session()
    if API_KEY:
        warm_session.headers["X-API-Key"] = API_KEY

    # --- Initial grace period ---
    # On Render the API container typically needs 20-40s to boot.
    # Waiting here avoids the first several retries that always get 429'd.
    if boot_wait > 0:
        log.info("Waiting %.0fs for API container to boot before first health check...", boot_wait)
        time.sleep(boot_wait)

    delay = initial_delay

    for attempt in range(1, max_attempts + 1):
        try:
            resp = warm_session.get(url, timeout=20)
            if resp.status_code == 200:
                log.info("API is ready (attempt %d/%d)", attempt, max_attempts)
                _api_ready = True
                return
            if resp.status_code == 429:
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
