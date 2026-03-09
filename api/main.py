import os
from typing import Optional, List, Literal

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from api.services.artifacts import ArtifactStore, STOPWORDS_SORTED

app = FastAPI(title="Wealthtender Dashboard API", version="0.1.0")

# Allow the dashboard (on a different Render subdomain) to call the API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten to your dashboard URL in production
    allow_methods=["GET"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# API key auth
# ---------------------------------------------------------------------------
# Set API_KEY on both the API and dashboard services. When set, every request
# (except /api/health) must include an X-API-Key header with the matching
# value. When not set (local dev), all requests are allowed.

_API_KEY = os.environ.get("API_KEY", "")


@app.middleware("http")
async def verify_api_key(request: Request, call_next):
    # Health endpoint is always open (needed for Render health checks)
    if request.url.path == "/api/health":
        return await call_next(request)
    # If no key is configured, skip auth (local dev convenience)
    if not _API_KEY:
        return await call_next(request)
    # Check the header
    provided = request.headers.get("X-API-Key", "")
    if provided != _API_KEY:
        return JSONResponse(
            status_code=401,
            content={"detail": "Invalid or missing API key"},
        )
    return await call_next(request)


store = ArtifactStore()


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------

@app.get("/api/health")
@app.head("/api/health")
def health():
    return {"status": "ok"}


# ---------------------------------------------------------------------------
# Metadata
# ---------------------------------------------------------------------------

@app.get("/api/metadata/latest")
def metadata_latest():
    return store.metadata


# ---------------------------------------------------------------------------
# Firm endpoints
# ---------------------------------------------------------------------------

@app.get("/api/firms")
def firms():
    return store.list_firms()


@app.get("/api/firm/{firm_id}/summary")
def firm_summary(firm_id: str):
    summary = store.firm_summary(firm_id)
    if summary is None:
        raise HTTPException(status_code=404, detail="firm not found")
    return summary


@app.get("/api/firm/{firm_id}/dimensions")
def firm_dimensions(firm_id: str):
    dimensions = store.firm_dimensions(firm_id)
    if dimensions is None:
        raise HTTPException(status_code=404, detail="firm not found")
    return dimensions


@app.get("/api/firm/{firm_id}/advisors")
def firm_advisors(firm_id: str):
    advisors = store.firm_advisors(firm_id)
    if advisors is None:
        raise HTTPException(status_code=404, detail="firm not found")
    return advisors


@app.get("/api/firm/{firm_id}/advisor/{advisor_id}")
def advisor_detail(firm_id: str, advisor_id: str):
    detail = store.advisor_detail(firm_id, advisor_id)
    if detail is None:
        raise HTTPException(status_code=404, detail="advisor not found")
    return detail


@app.get("/api/firm/{firm_id}/benchmarks")
def firm_benchmarks(firm_id: str):
    benchmarks = store.firm_benchmarks(firm_id)
    if benchmarks is None:
        raise HTTPException(status_code=404, detail="firm not found")
    return benchmarks


@app.get("/api/firm/{firm_id}/personas")
def firm_personas(firm_id: str):
    personas = store.firm_personas(firm_id)
    if personas is None:
        raise HTTPException(status_code=404, detail="firm not found")
    return personas


# ---------------------------------------------------------------------------
# EDA
# ---------------------------------------------------------------------------

@app.get("/api/stopwords")
def stopwords():
    """Return the default NLTK-equivalent stopword list for the frontend UI."""
    return STOPWORDS_SORTED


@app.get("/api/eda/charts")
def eda_charts(
    scope: Literal["global", "firm"] = "global",
    firm_id: Optional[str] = None,
    advisor_id: Optional[str] = None,
    date_start: Optional[str] = None,
    date_end: Optional[str] = None,
    rating: Optional[float] = Query(None, ge=0.0, le=5.0),
    min_tokens: Optional[int] = Query(None, ge=0),
    max_tokens: Optional[int] = Query(None, ge=0),
    min_reviews_per_advisor: Optional[int] = Query(None, ge=0),
    max_reviews_per_advisor: Optional[int] = Query(None, ge=0),
    lexical_n: Optional[int] = Query(1, ge=1, le=5),
    lexical_top_n: Optional[int] = Query(20, ge=1, le=500),
    exclude_stopwords: Optional[bool] = False,
    custom_stopwords: Optional[List[str]] = Query(None),
    preset: Optional[str] = None,
    time_freq: Optional[str] = Query("month", regex="^(month|quarter|year)$"),
):
    if scope == "firm" and not firm_id and not advisor_id:
        raise HTTPException(
            status_code=400,
            detail="firm_id or advisor_id is required when scope is 'firm'",
        )

    payload = store.eda_payload(
        scope=scope,
        firm_id=firm_id,
        advisor_id=advisor_id,
        date_start=date_start,
        date_end=date_end,
        rating=rating,
        min_tokens=min_tokens,
        max_tokens=max_tokens,
        min_reviews_per_advisor=min_reviews_per_advisor,
        max_reviews_per_advisor=max_reviews_per_advisor,
        lexical_n=lexical_n,
        lexical_top_n=lexical_top_n,
        exclude_stopwords=exclude_stopwords,
        custom_stopwords=custom_stopwords,
        preset=preset,
        time_freq=time_freq,
    )
    if not payload:
        raise HTTPException(status_code=404, detail="EDA data not available")
    return payload


# ---------------------------------------------------------------------------
# Reviews
# ---------------------------------------------------------------------------

@app.get("/api/reviews/{review_id}")
def review_detail(review_id: str):
    detail = store.review_detail(review_id)
    if detail is None:
        raise HTTPException(status_code=404, detail="review not found")
    return detail


# ---------------------------------------------------------------------------
# Advisor DNA
# ---------------------------------------------------------------------------

@app.get("/api/advisor-dna/macro")
def advisor_dna_macro():
    data = store.dna_macro_sample()
    if not data:
        raise HTTPException(status_code=404, detail="Advisor DNA data not available")
    return data


@app.get("/api/advisor-dna/macro-totals")
def advisor_dna_macro_totals():
    data = store.dna_macro_totals()
    if not data:
        raise HTTPException(status_code=404, detail="Advisor DNA data not available")
    return data


@app.get("/api/advisor-dna/entities")
def advisor_dna_entities():
    return store.dna_entity_list()


@app.get("/api/advisor-dna/entity-reviews")
def advisor_dna_entity_reviews(entity_id: str = Query(...)):
    reviews = store.dna_entity_reviews(entity_id)
    if reviews is None:
        raise HTTPException(status_code=404, detail="entity not found")
    return reviews


@app.get("/api/advisor-dna/advisor-scores")
def advisor_dna_advisor_scores(
    entity_id: str = Query(...),
    method: Literal["mean", "penalized", "weighted"] = "mean",
):
    scores = store.dna_advisor_scores(entity_id, method)
    if scores is None:
        raise HTTPException(status_code=404, detail="entity or method not found")
    return scores


@app.get("/api/advisor-dna/percentile-scores")
def advisor_dna_percentile_scores(
    entity_id: str = Query(...),
    method: Literal["mean", "penalized", "weighted"] = "mean",
    min_peer_reviews: int = Query(0, ge=0),
):
    scores = store.dna_percentile_scores(entity_id, method, min_peer_reviews)
    if scores is None:
        raise HTTPException(status_code=404, detail="entity or method not found")
    return scores


@app.get("/api/advisor-dna/population-medians")
def advisor_dna_population_medians(
    method: Literal["mean", "penalized", "weighted"] = "mean",
    entity_type: str = "firm",
):
    return store.dna_population_medians(method, entity_type)


@app.get("/api/advisor-dna/method-breakpoints")
def advisor_dna_method_breakpoints(
    method: Literal["mean", "penalized", "weighted"] = "mean",
    entity_type: str = "firm",
):
    return store.dna_method_breakpoints(method, entity_type)


@app.get("/api/advisor-dna/review/{review_idx}")
def advisor_dna_review_detail(review_idx: int):
    detail = store.dna_review_detail(review_idx)
    if detail is None:
        raise HTTPException(status_code=404, detail="review not found")
    return detail
