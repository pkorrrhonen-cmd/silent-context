# Hosting the demo

A hosted copy of the page, for a jury member who wants to try it rather than watch the video. It is the
same FastAPI app as `uv run uvicorn app.api:app`, in a Docker image, run on Cloudflare Containers behind a
small Worker. No model is called and no key exists there: the store is rebuilt from `data/` at every move
of the demo clock, as it is everywhere. The address is in the README's Demo section.

This is a demo copy, not a deployment of a product. Nothing here is Elisa's, and nothing in this file or
in the configuration names an account: wrangler takes the account from the login on the machine.

## What is where

| Path | What |
|---|---|
| [`Dockerfile`](../Dockerfile) | The image: Python 3.12 slim, the dependencies from `uv.lock`, `app/`, `web/` and `data/`, uvicorn on port 8000, a non-root user. |
| [`.dockerignore`](../.dockerignore) | The build context is the whole checkout; this keeps everything but what the app reads out of the image. |
| [`hosting/wrangler.jsonc`](../hosting/wrangler.jsonc) | The Worker, the container (type `basic`, one instance), the Durable Object binding and the cron that keeps the instance awake. |
| [`hosting/worker.js`](../hosting/worker.js) | The Worker: every request goes to one named container instance; the cron sends it a health request. |
| [`hosting/package.json`](../hosting/package.json) | `@cloudflare/containers` and a pinned `wrangler`. |

## Prerequisites

- Docker running (`docker info`). The image is built for `linux/amd64`, which Cloudflare runs; wrangler
  passes the platform itself, so an Apple Silicon Mac builds it under emulation.
- Node 20 or newer, for wrangler.
- A Cloudflare account on the Workers Paid plan: Containers are not on the free plan.
- Once per machine, a login that opens the browser:

```bash
cd hosting && npx wrangler login
```

## Deploy, and deploy again

One command builds the image, pushes it to the account's registry, uploads the Worker and rolls the
container out. Run it again after any change to `app/`, `web/` or `data/`; it is the whole publication.

```bash
cd hosting && npm ci && npx wrangler deploy
```

The first deploy provisions the container, and Cloudflare says to wait several minutes before requests to
it succeed. A later deploy replaces the one instance: whoever is on the page at that moment loses the
clock position and reloads.

A check without leaving the terminal:

```bash
curl -s https://<the address>/health
```

The answer is `{"status":"ok"}`. Then the page itself in a private window, the arrow keys through the
thirteen scenes, and one of the ready questions at the bottom.

## What the visitor gets

- **One instance.** Every visitor reaches the same container, named `demo`. The demo clock is the store's
  state, so two visitors moving through the scenes at the same moment move each other's clock; a visit is
  two minutes, so the chance is small, and the README says it. The agent's log is shared for the same
  reason and may reset.
- **Sleep and wake.** The instance sleeps after two hours without a request. The first request after that
  is a cold start: the image is already on Cloudflare's machines, and uvicorn imports FastAPI and the
  OpenAI client before it listens; the Worker waits up to 90 seconds for the port, the package's default
  being 20. The disk is new on each start, so the store is rebuilt and the log is empty.
- **Awake for the jury.** The cron in `wrangler.jsonc` sends a health request every five minutes on Sundays
  from 06:00 to 11:55 UTC, which is 08:00 to 13:55 Finnish time in November, around the jury's 10:00 to
  13:00. A request resets the sleep timer, so the instance stays warm through the window. The window is
  one line to change; Cloudflare's cron runs on UTC and counts Sunday as 1 or `sun`.
- **Logs.** `cd hosting && npx wrangler tail` streams the Worker's log; the container's own output is in
  the Cloudflare dashboard under the Worker's container.

## A local check of the image

The same image runs on the Mac without Cloudflare, on a port the other servers do not use:

```bash
docker build --platform linux/amd64 -t silent-context:local .
```

```bash
docker run --rm -p 127.0.0.1:8010:8000 silent-context:local
```

Then `http://127.0.0.1:8010`.

## Cost

Cloudflare's Containers pricing page, read 7.11.2026: the Workers Paid plan includes 375 vCPU-minutes,
25 GiB-hours of memory and 200 GB-hours of disk a month; beyond that, CPU is billed on use at 0.000020
USD per vCPU-second, memory and disk on what the instance type provisions at 0.0000025 USD per GiB-second
and 0.00000007 USD per GB-second. The `basic` type is a quarter vCPU, 1 GiB and 4 GB: an hour awake costs
at most about 0.03 USD once the included amounts are used, and nothing while asleep. The Worker's own
requests are within the plan.

## After the event

The Worker, its container and the Durable Object go in one command; the image stays in the registry until
it is deleted.

```bash
cd hosting && npx wrangler delete
```

```bash
cd hosting && npx wrangler containers images list
```

```bash
cd hosting && npx wrangler containers images delete <image:tag>
```

## Measured, 7.11.2026

- The image: 94 MB, built for `linux/amd64` on the Mac in 14 s the first time and from cached layers after
  that. Under emulation with a quarter CPU it answered `/health` 13 s after start and moved the clock in 0.4
  to 0.6 s.
- The deploy: 57 s the first time (image push, Worker upload, the container application created), 28 s the
  second time, the new instance serving about two minutes after the command returned.
- On Cloudflare, the `basic` type: a cold start of 10 s to the first `/health` answer; warm requests 0.15 s;
  a clock move 0.2 to 0.5 s; the page, its script, its stylesheet and the Jost font all served by the
  container, nothing loaded from outside; the thirteen scenes on the arrow keys and a ready question
  answered in the browser.
