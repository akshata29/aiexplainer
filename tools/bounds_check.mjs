#!/usr/bin/env node
/**
 * Diagnostic: compare Excalidraw's real element bounds with the bounds implied by our own geometry.
 *   node tools/bounds_check.mjs                 # every diagram
 *   node tools/bounds_check.mjs ra-landing-zone # one
 * Prints, per diagram, our bounds vs Excalidraw's and the elements that stick out (curved arrows are the usual cause).
 * Uses the render lock (one browser at a time) but renders nothing, so it is cheap.
 */
import { chromium } from "playwright-core";
import http from "node:http";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const diagramsDir = path.join(root, "diagrams");
const distDir = path.join(root, "tools", "export-dist");
const renderLock = path.join(root, "tools", ".render.lock");
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

const ids = process.argv.slice(2).filter((a) => !a.startsWith("-"));
const files = (ids.length ? ids.map((i) => `${i}.excalidraw`) : fs.readdirSync(diagramsDir).filter((f) => f.endsWith(".excalidraw") && !f.startsWith("_")));

for (let i = 0; ; i++) {
  try { fs.mkdirSync(renderLock); break; } catch {
    try { if (Date.now() - fs.statSync(renderLock).mtimeMs > 180000) fs.rmSync(renderLock, { recursive: true, force: true }); } catch { /* ignore */ }
    await sleep(1500);
  }
}
const release = () => { try { fs.rmSync(renderLock, { recursive: true, force: true }); } catch { /* ignore */ } };
process.on("exit", release);

const MIME = { ".html": "text/html", ".js": "text/javascript", ".css": "text/css", ".woff2": "font/woff2" };
const srv = http.createServer((req, res) => {
  const u = decodeURIComponent((req.url || "/").split("?")[0]);
  const p = path.join(distDir, u === "/" ? "index.html" : u);
  if (!p.startsWith(distDir) || !fs.existsSync(p) || fs.statSync(p).isDirectory()) { res.writeHead(404); res.end(); return; }
  res.writeHead(200, { "content-type": MIME[path.extname(p)] || "application/octet-stream" });
  fs.createReadStream(p).pipe(res);
});
await new Promise((r) => srv.listen(0, "127.0.0.1", r));
const browser = await chromium.launch({ channel: "msedge", headless: true });
try {
  const page = await browser.newPage();
  await page.goto(`http://127.0.0.1:${srv.address().port}/index.html`);
  await page.waitForFunction(() => window.ready === true && typeof window.boundsReport === "function", null, { timeout: 60000 });
  for (const f of files) {
    const scene = JSON.parse(fs.readFileSync(path.join(diagramsDir, f), "utf8"));
    const rep = await page.evaluate((els) => window.boundsReport(els), scene.elements);
    let x0 = Infinity, y0 = Infinity, x1 = -Infinity, y1 = -Infinity;
    for (const e of scene.elements) {
      const pts = e.points?.length ? e.points.map((p) => [e.x + p[0], e.y + p[1]]) : [[e.x, e.y], [e.x + e.width, e.y + e.height]];
      for (const [px, py] of pts) { x0 = Math.min(x0, px); y0 = Math.min(y0, py); x1 = Math.max(x1, px); y1 = Math.max(y1, py); }
    }
    const [cx0, cy0, cx1, cy1] = rep.common;
    const extra = Math.max(x0 - cx0, y0 - cy0, cx1 - x1, cy1 - y1);
    const flag = extra > 40 ? "  <-- EXCALIDRAW BOUNDS LARGER" : "";
    console.log(`${f.replace(".excalidraw", "").padEnd(36)} ours ${Math.round(x1 - x0)}x${Math.round(y1 - y0)}  excalidraw ${cx1 - cx0}x${cy1 - cy0}  (max overhang ${Math.round(extra)}px, ${rep.offenders.length} offenders)${flag}`);
    if (ids.length || extra > 40) for (const o of rep.offenders.slice(0, 6)) console.log(`      ${o.type} ${JSON.stringify(o.own)} -> ${JSON.stringify(o.excal)} ${o.text ?? ""}`);
  }
} finally {
  await browser.close();
  srv.close();
  release();
}
