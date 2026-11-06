"""HTTP interface of the demo. Each build phase adds its own endpoints."""

from fastapi import FastAPI

app = FastAPI(title="Silent context capture for network operations")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
