// Crops of the demo page's panels, in CSS pixels at 1600 by 900, device scale 2.
const puppeteer = require("puppeteer-core");
const path = require("path");
const CROPS = [
  { scene: 2, name: "bind-claims-graph", clip: { x: 327, y: 305, width: 1265, height: 292 } },
  { scene: 2, name: "bind-claims", clip: { x: 327, y: 305, width: 701, height: 292 } },
  { scene: 3, name: "use-answer", clip: { x: 428, y: 604, width: 1164, height: 168 } },
  { scene: 3, name: "use-answer-full", clip: { x: 428, y: 604, width: 1164, height: 282 } },
  { scene: 4, name: "learn-answer", clip: { x: 428, y: 604, width: 1164, height: 190 } },
];
(async () => {
  const url = process.argv[2] || "http://127.0.0.1:8001/";
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
      await new Promise((r) => setTimeout(r, 900));
      current = c.scene;
    }
    const file = path.join(__dirname, "shots", `${c.name}.png`);
    await page.screenshot({ path: file, clip: c.clip });
    console.log("wrote", c.name, c.clip.width, "x", c.clip.height);
  }
  await browser.close();
})().catch((e) => { console.error(e); process.exit(1); });
