from typing import Optional, List

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from api.services.artifacts import ArtifactStore, STOPWORDS_SORTED

app = FastAPI(title="Wealthtender Dashboard API", version="0.1.0")

# Allow the dashboard (on a different Render subdomain) to call the API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten to your dashboard URL in production
    allow_methods=["GET"],
    allow_headers=["*"],
)

store = ArtifactStore()


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------

@app.get("/api/health")
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
    if not summary:
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
    scope: str = "global",
    firm_id: Optional[str] = None,
    date_start: Optional[str] = None,
    date_end: Optional[str] = None,
    rating: Optional[float] = None,
    min_tokens: Optional[int] = None,
    max_tokens: Optional[int] = None,
    min_reviews_per_advisor: Optional[int] = None,
    max_reviews_per_advisor: Optional[int] = None,
    lexical_n: Optional[int] = 1,
    lexical_top_n: Optional[int] = 20,
    exclude_stopwords: Optional[bool] = False,
    custom_stopwords: Optional[List[str]] = Query(None),
    preset: Optional[str] = None,
):
    payload = store.eda_payload(
        scope=scope,
        firm_id=firm_id,
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
    if not detail:
        raise HTTPException(status_code=404, detail="review not found")
    return detail
