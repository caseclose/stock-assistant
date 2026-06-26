import { chromium } from "playwright";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const outDir = path.join(__dirname, "..", "docs", "screenshots");

async function main() {
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });
  await page.goto("http://localhost:3000", { waitUntil: "domcontentloaded" });
  await page.waitForSelector("h1", { timeout: 60_000 });
  await page.locator("button", { hasText: /^MU$/ }).first().click();
  await page.waitForSelector('h1:text-is("MU")', { timeout: 30_000 });
  await page.waitForSelector("text=观望", { timeout: 45_000 });
  await page.waitForTimeout(2_000);
  await page.screenshot({ path: path.join(outDir, "mu-levels.png") });
  const panel = page.locator("aside").last();
  await panel.screenshot({ path: path.join(outDir, "analysis-panel.png") });
  await browser.close();
}

main();
