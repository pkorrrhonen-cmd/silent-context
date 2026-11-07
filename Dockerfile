# Silent context as one image: the FastAPI app, the page and the data it is rebuilt from.
# No model and no key: the store is built from data/ on first use and on every move of the demo clock.
# Built for linux/amd64, which is what Cloudflare Containers runs; docs/hosting.md has the commands.

FROM python:3.12-slim

COPY --from=ghcr.io/astral-sh/uv:0.9 /uv /bin/uv

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    PYTHONUNBUFFERED=1

WORKDIR /srv

# Dependencies first, so a change to the code does not reinstall them.
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

COPY app ./app
COPY web ./web
COPY data ./data

# The store is derived and lives only inside the container; the agent's log goes with it.
RUN useradd --system --home /srv --no-create-home silent \
    && mkdir -p /srv/store \
    && chown -R silent:silent /srv/store
USER silent

ENV PATH="/srv/.venv/bin:$PATH" \
    STORE_PATH=/srv/store/claims.db

EXPOSE 8000
CMD ["uvicorn", "app.api:app", "--host", "0.0.0.0", "--port", "8000"]
