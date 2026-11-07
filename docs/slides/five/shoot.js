// Crops of the demo page for the five-picture deck, at 1600 by 900 CSS pixels, device scale 2, into shots/.
// Each crop is read from the page's own elements, so a layout change moves the crop with it.
// From an empty folder beside a checkout, with the page running:  npm install puppeteer-core  then
//   node <repo>/docs/slides/five/shoot.js http://127.0.0.1:8000/
// Written at the event; tooling for the submission, not part of the product.
const puppeteer = require("puppeteer-core");
const path = require("path");
const CROPS = [
  // scene index, name, selector, and the part of the element kept: top and height in CSS px (0 = all), or
  // until, a selector whose bottom edge ends the crop, so a crop never cuts a row in half (7.11. evening).
  // The page's scenes: 0 gap, 1 capture, 2 bind, 3 use, 4 learn, 5 act, 6 ageing, 7 not for all, 8 disagree,
  // 9 barrier, 10 any source, 11 ask, 12 limits.
  { scene: 3, name: "use-answer", sel: "#answer", top: 0, until: "#answer dl" },
  { scene: 4, name: "learn-answer", sel: "#answer", top: 0, until: "#answer dl" },
  { scene: 5, name: "act-answer", sel: "#answer", top: 0, until: "#answer dl" },
  { scene: 6, name: "ageing-head", sel: "#answer", top: 0, until: "#answer .next" },
  { scene: 7, name: "notforall-card", sel: "#answer .sides > :nth-child(2)", top: 0, until: "#answer .sides > :nth-child(2) .note" },
  { scene: 8, name: "disagree-head", sel: "#answer", top: 0, until: "#answer .next" },
  { scene: 10, name: "sources-list", sel: "#sources", top: 0, height: 0 },
  { scene: 10, name: "koski-answer", sel: "#answer", top: 0, until: "#answer .next" },
  { scene: 11, name: "ask-draft", sel: "#answer .draft", top: 0, height: 0 },
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
    const r = await page.evaluate((sel, until) => {
      const el = document.querySelector(sel);
      if (!el) return null;
      // A panel scrolls, so the crop's end is brought into view first; otherwise the panel's edge cuts it.
      (document.querySelector(until || sel) || el).scrollIntoView({ block: "end" });
      el.scrollIntoView({ block: "nearest" });
      const b = el.getBoundingClientRect();
      const end = until ? document.querySelector(until)?.getBoundingClientRect().bottom : null;
      return { x: b.x, y: b.y, width: b.width, height: b.height, end };
    }, c.sel, c.until || null);
    if (!r) { console.log("missing", c.name, c.sel); continue; }
    if (c.until && r.end == null) { console.log("missing", c.name, c.until); continue; }
    const height = c.until ? r.end - r.y + 8 : (c.height ? Math.min(c.height, r.height - c.top) : r.height - c.top);
    const clip = { x: Math.round(r.x), y: Math.round(r.y + c.top), width: Math.round(r.width), height: Math.round(height) };
    const file = path.join(__dirname, "shots", `${c.name}.png`);
    await page.screenshot({ path: file, clip });
    console.log("wrote", c.name, clip.width, "x", clip.height);
  }
  await browser.close();
})().catch((e) => { console.error(e); process.exit(1); });
