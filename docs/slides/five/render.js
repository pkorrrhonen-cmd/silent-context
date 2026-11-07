// Renders five.html to the PDF beside the other slides, and one PNG per page for a look.
//   node <repo>/docs/slides/five/render.js <repo>/docs/slides/five/five.html <repo>/docs/slides/silent-context-in-five.pdf [png folder]
const puppeteer = require("puppeteer-core");
const path = require("path");
(async () => {
  const [src, out, pngs] = process.argv.slice(2);
  const browser = await puppeteer.launch({ executablePath: "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome", headless: true, args: ["--hide-scrollbars"] });
  const page = await browser.newPage();
  await page.setViewport({ width: 1920, height: 1080, deviceScaleFactor: 1 });
  await page.goto("file://" + path.resolve(src), { waitUntil: "networkidle0" });
  await page.pdf({ path: out, width: "1920px", height: "1080px", printBackground: true, preferCSSPageSize: true });
  console.log("wrote", out);
  if (pngs) {
    const slides = await page.$$(".slide");
    for (let i = 0; i < slides.length; i++) {
      await slides[i].screenshot({ path: path.join(pngs, `five-${i + 1}.png`) });
    }
    console.log("wrote", slides.length, "pngs to", pngs);
  }
  await browser.close();
})().catch((e) => { console.error(e); process.exit(1); });
