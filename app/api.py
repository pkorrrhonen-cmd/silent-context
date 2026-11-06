"""HTTP interface of the demo. Each build phase adds its own endpoints."""

from typing import Literal

from fastapi import FastAPI
from pydantic import BaseModel

from app import claims, db, export

app = FastAPI(title="Silent context capture for network operations")


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


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/graph")
def get_graph() -> dict:
    with db.session() as conn:
        return export.graph(conn)


@app.post("/claims_for")
def post_claims_for(query: ClaimsQuery) -> dict:
    observed = query.observed.model_dump() if query.observed else None
    return claims.claims_for(query.entity, query.symptom, query.at, observed)


@app.get("/access_for")
def get_access_for(place: str, at: str | None = None) -> dict:
    return claims.access_for(place, at)
