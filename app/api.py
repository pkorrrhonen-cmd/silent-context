"""HTTP interface of the demo. Each build phase adds its own endpoints."""

from fastapi import FastAPI

from app import db, export

app = FastAPI(title="Silent context capture for network operations")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/graph")
def get_graph() -> dict:
    with db.session() as conn:
        return export.graph(conn)
