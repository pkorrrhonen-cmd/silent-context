// Screenshots of the demo page's ten scenes at 1600 by 900 CSS pixels, device scale 2.
const puppeteer = require("puppeteer-core");
const path = require("path");
(async () => {
  const url = process.argv[2] || "http://127.0.0.1:8001/";
  const browser = await puppeteer.launch({
    executablePath: "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    headless: true,
    args: ["--hide-scrollbars", "--force-device-scale-factor=2"],
  });
  const page = await browser.newPage();
  await page.setViewport({ width: 1600, height: 900, deviceScaleFactor: 2 });
  const errors = [];
  page.on("console", (m) => { if (m.type() === "error") errors.push(m.text()); });
  page.on("pageerror", (e) => errors.push(String(e)));
  await page.goto(url, { waitUntil: "networkidle0" });
  await page.waitForFunction("() => typeof goTo === 'function' && typeof busy !== 'undefined'");
  await new Promise((r) => setTimeout(r, 800));
  for (let n = 0; n < 10; n++) {
    await page.evaluate(`goTo(${n})`);
    await page.waitForFunction("() => !busy");
    await new Promise((r) => setTimeout(r, 900));
    const file = path.join(__dirname, "shots", `scene-${n + 1}.png`);
    await page.screenshot({ path: file });
    console.log("wrote", file);
  }
  console.log("console errors:", errors.length ? errors : "none");
  await browser.close();
})().catch((e) => { console.error(e); process.exit(1); });
