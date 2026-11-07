# Silent context in five pictures

`../silent-context-in-five.pdf` is the short deck for the submission's pitch deck field: five pages of 1920 by
1080 in the page's own look, written at the event on 7.11.2026 (the owner: a version from which the thing
opens with about five pictures). The ten-slide deck beside it stays as a supporting document.

| File | What |
|---|---|
| `five.html` | The five pages: the chat and "It lives in one chat"; the four steps; the agent's answer and the agent acting under the policy; the doubt cases and the drafted question; what was measured and the limits. Light since 7.11. evening, in the page's own tokens (decision 24). |
| `shoot.js` | The crops of the running page in `shots/`, read from the page's own elements at device scale 2; a crop ends at a named element's bottom edge (`until`), so no row is cut in half. |
| `render.js` | Writes the PDF from `five.html` with headless Chrome, and a PNG per page when given a folder. |
| `shots/` | The crops the pages use. |

From an empty folder beside a checkout, with the page running:

```bash
npm install puppeteer-core
```

```bash
node <repo>/docs/slides/five/shoot.js http://127.0.0.1:8000/
```

```bash
node <repo>/docs/slides/five/render.js <repo>/docs/slides/five/five.html <repo>/docs/slides/silent-context-in-five.pdf
```

Tooling for the submission, not part of the product. The scripts expect Google Chrome at its usual place on a Mac.
