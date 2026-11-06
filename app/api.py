"""HTTP interface of the demo, and the one page that uses it."""

from typing import Literal

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from app import claims, db, export, ingest, llm, view
from app.sources import ROOT

WEB_DIR = ROOT / "web"

app = FastAPI(title="Silent context capture for network operations")
app.mount("/web", StaticFiles(directory=WEB_DIR), name="web")


class Observed(BaseModel):
    link: Literal["up", "down", "unknown"] = "unknown"
    counters: Literal["rising", "zero", "unknown"] = "unknown"
    bounce_done: bool = False
    bounce_failed: bool = False


class ClaimsQuery(BaseModel):
    entity: str
    symptom: str
    at: str | None = None
    observed: Observed | None = None


class Clock(BaseModel):
    as_of: str | None = None
    fresh: bool = False


@app.get("/", include_in_schema=False)
def page() -> FileResponse:
    return FileResponse(WEB_DIR / "index.html")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/graph")
def get_graph() -> dict:
    with db.session() as conn:
        return export.graph(conn)


@app.get("/state")
def get_state() -> dict:
    with db.session() as conn:
        return view.state(conn)


@app.post("/clock")
def post_clock(clock: Clock) -> dict:
    """Moves the demo clock: rebuilds the store as it stood then, from the recorded answers."""
    try:
        path = ingest.run(until=clock.as_of, keep_logs=not clock.fresh)
    except llm.ModelNotConfigured as error:
        raise HTTPException(status_code=409, detail=str(error)) from error
    with db.session(path) as conn:
        return view.state(conn)


@app.get("/source")
def get_source(file: str) -> dict:
    found = view.source(file)
    if found is None:
        raise HTTPException(status_code=404, detail="Not a source in the manifest.")
    return found


@app.post("/claims_for")
def post_claims_for(query: ClaimsQuery) -> dict:
    observed = query.observed.model_dump() if query.observed else None
    return claims.claims_for(query.entity, query.symptom, query.at, observed)


@app.get("/access_for")
def get_access_for(place: str, at: str | None = None) -> dict:
    return claims.access_for(place, at)
