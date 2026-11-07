// The Worker that fronts Silent context on Cloudflare: one container, the app as it is in the image.
//
// Every request goes to one named instance. The demo clock and the agent's log live in that instance's
// store, so two visitors at the same moment share them; the README's Demo section says so. The disk is
// ephemeral: when the instance sleeps, the log resets and the store is rebuilt from data/ on the next
// request, which is how the app works everywhere.

import { Container, getContainer } from "@cloudflare/containers";

const INSTANCE = "demo";
const PORT = 8000;

export class SilentContext extends Container {
  defaultPort = PORT;
  // Two hours of quiet before the instance sleeps; a request or a ping resets the timer.
  sleepAfter = "2h";
  // Reached through the container's port while waiting for it to listen; any HTTP answer counts.
  pingEndpoint = "silent-context/health";

  async fetch(request) {
    if (!this.ctx.container.running) {
      // A cold start imports FastAPI and the OpenAI client before uvicorn listens. The package's
      // default of 20 seconds is usually enough; this gives the first visitor more room than that.
      await this.startAndWaitForPorts({
        ports: [PORT],
        cancellationOptions: { portReadyTimeoutMS: 90_000, abort: request.signal },
      });
    }
    return super.fetch(request);
  }
}

export default {
  async fetch(request, env) {
    return getContainer(env.SILENT_CONTEXT, INSTANCE).fetch(request);
  },

  // The cron in wrangler.jsonc fires this while the jury reads. A health request counts as activity,
  // so the instance stays awake and nobody meets a cold start.
  async scheduled(_controller, env, ctx) {
    ctx.waitUntil(
      getContainer(env.SILENT_CONTEXT, INSTANCE).fetch(new Request("https://silent-context/health")),
    );
  },
};
