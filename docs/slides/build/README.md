# Building the slides

The deck `../silent-context.pptx` is written by these scripts, so a change to the words is a change to `deck.js`
and a rebuild. They are tooling for the submission, not part of the product, and they need Node and the demo
page running. Written at the event, 7.11.2026.

| File | What |
|---|---|
| `shoot.js` | The ten scenes of the page at 1600 by 900, device scale 2, into `shots/`, with headless Chrome. |
| `crops.js` | The claim and graph panels and the agent's answer, cropped from the same page, into `shots/`. |
| `deck.js` | The ten slides from `../../slides.md`, in the page's own colours, Calibri and Consolas; writes the theme colours into the file itself. |

From an empty folder beside a checkout, with the page running at `http://127.0.0.1:8000`:

```bash
npm install pptxgenjs puppeteer-core
```

```bash
node shoot.js http://127.0.0.1:8000/
```

```bash
node crops.js http://127.0.0.1:8000/
```

```bash
node deck.js ../silent-context.pptx
```

`shoot.js` and `crops.js` expect Google Chrome at its usual place on a Mac; `deck.js` reads `shots/` next to
itself. The PDF beside the deck was exported with LibreOffice (`soffice --headless --convert-to pdf`), with Office's
Calibri and Consolas available to it, or from PowerPoint by hand.
