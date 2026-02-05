from fastapi import FastAPI, HTTPException
from api.services.artifacts import ArtifactStore

app = FastAPI(title="Wealthtender Dashboard API", version="0.1.0")
store = ArtifactStore()

@app.get("/api/health")
def health():
    return {"status": "ok"}

@app.get("/api/metadata/latest")
def metadata_latest():
    return store.metadata

@app.get("/api/firms")
def firms():
    return store.list_firms()

@app.get("/api/firm/{firm_id}/summary")
def firm_summary(firm_id: str):
    summary = store.firm_summary(firm_id)
    if not summary:
        raise HTTPException(status_code=404, detail="firm not found")
    return summary

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
