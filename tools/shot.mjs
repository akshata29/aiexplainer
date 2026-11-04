#!/usr/bin/env node
/** Dev tool: screenshot a URL in headless Edge.  node tools/shot.mjs --url http://localhost:5173/ --out shot.png [--w 1400 --h 900 --wait 1500 --full] */
import { chromium } from "playwright-core";

const a = { url: "", out: "shot.png", w: 1400, h: 900, wait: 1500, full: false, sel: "" };
for (let i = 2; i < process.argv.length; i++) {
  const k = process.argv[i];
  if (k === "--url") a.url = process.argv[++i];
  else if (k === "--out") a.out = process.argv[++i];
  else if (k === "--w") a.w = +process.argv[++i];
  else if (k === "--h") a.h = +process.argv[++i];
  else if (k === "--wait") a.wait = +process.argv[++i];
  else if (k === "--full") a.full = true;
  else if (k === "--sel") a.sel = process.argv[++i];
}
const browser = await chromium.launch({ channel: "msedge", headless: true });
const page = await browser.newPage({ viewport: { width: a.w, height: a.h } });
page.on("pageerror", (e) => console.error("[page error]", e.message));
page.on("console", (m) => { if (m.type() === "error") console.error("[console error]", m.text().slice(0, 300)); });
await page.goto(a.url, { waitUntil: "networkidle" });
if (a.sel) await page.waitForSelector(a.sel, { timeout: 30000 });
await page.waitForTimeout(a.wait);
await page.screenshot({ path: a.out, fullPage: a.full });
await browser.close();
console.log("saved", a.out);
