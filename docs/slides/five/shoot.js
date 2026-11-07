// Crops of the demo page for the five-picture deck, at 1600 by 900 CSS pixels, device scale 2, into shots/.
// Each crop is read from the page's own elements, so a layout change moves the crop with it.
// From an empty folder beside a checkout, with the page running:  npm install puppeteer-core  then
//   node <repo>/docs/slides/five/shoot.js http://127.0.0.1:8000/
// Written at the event; tooling for the submission, not part of the product.
const puppeteer = require("puppeteer-core");
const path = require("path");
const CROPS = [
  // scene index, name, selector, and the part of the element kept (top, height in CSS px; 0 = all)
  { scene: 3, name: "use-answer", sel: "#answer", top: 0, height: 150 },
  { scene: 4, name: "learn-answer", sel: "#answer", top: 0, height: 180 },
  { scene: 5, name: "ageing-head", sel: "#answer", top: 0, height: 96 },
  { scene: 6, name: "notforall-card", sel: "#answer .sides > :nth-child(2)", top: 0, height: 84 },
  { scene: 7, name: "disagree-head", sel: "#answer", top: 0, height: 96 },
  { scene: 2, name: "bind-claim", sel: "#claim-list > :first-child", top: 0, height: 0 },
];
(async () => {
  const url = process.argv[2] || "http://127.0.0.1:8000/";
  const browser = await puppeteer.launch({
    executablePath: "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    headless: true, args: ["--hide-scrollbars", "--force-device-scale-factor=2"],
  });
  const page = await browser.newPage();
  await page.setViewport({ width: 1600, height: 900, deviceScaleFactor: 2 });
  await page.goto(url, { waitUntil: "networkidle0" });
  await page.waitForFunction("() => typeof goTo === 'function' && typeof busy !== 'undefined'");
  await new Promise((r) => setTimeout(r, 800));
  let current = -1;
  for (const c of CROPS) {
    if (c.scene !== current) {
      await page.evaluate(`goTo(${c.scene})`);
      await page.waitForFunction("() => !busy");
      await new Promise((r) => setTimeout(r, 1000));
      current = c.scene;
    }
    const r = await page.evaluate((sel) => {
      const el = document.querySelector(sel);
      if (!el) return null;
      const b = el.getBoundingClientRect();
      return { x: b.x, y: b.y, width: b.width, height: b.height };
    }, c.sel);
    if (!r) { console.log("missing", c.name, c.sel); continue; }
    const clip = { x: Math.round(r.x), y: Math.round(r.y + c.top), width: Math.round(r.width),
                   height: Math.round(c.height ? Math.min(c.height, r.height - c.top) : r.height - c.top) };
    const file = path.join(__dirname, "shots", `${c.name}.png`);
    await page.screenshot({ path: file, clip });
    console.log("wrote", c.name, clip.width, "x", clip.height);
  }
  await browser.close();
})().catch((e) => { console.error(e); process.exit(1); });
