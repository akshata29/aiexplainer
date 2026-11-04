#!/usr/bin/env node
/** Dev tool: measure text widths in the real browser. stdin: JSON [{text,size,family}] -> stdout: JSON [width,...] */
import { chromium } from "playwright-core";
import http from "node:http";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const distDir = path.join(root, "tools", "export-dist");
const MIME = { ".html": "text/html", ".js": "text/javascript", ".css": "text/css", ".woff2": "font/woff2" };
const srv = http.createServer((req, res) => {
  const u = decodeURIComponent((req.url || "/").split("?")[0]);
  const p = path.join(distDir, u === "/" ? "index.html" : u);
  if (!p.startsWith(distDir) || !fs.existsSync(p) || fs.statSync(p).isDirectory()) { res.writeHead(404); res.end(); return; }
  res.writeHead(200, { "content-type": MIME[path.extname(p)] || "application/octet-stream" });
  fs.createReadStream(p).pipe(res);
});
await new Promise((r) => srv.listen(0, "127.0.0.1", r));
const items = JSON.parse(fs.readFileSync(0, "utf8"));
const browser = await chromium.launch({ channel: "msedge", headless: true });
const page = await browser.newPage();
await page.goto(`http://127.0.0.1:${srv.address().port}/index.html`);
await page.waitForFunction(() => window.ready === true);
// make Excalidraw register its fonts by exporting a tiny scene that uses each family
const fams = [...new Set(items.map((i) => i.family))];
const famId = { Virgil: 1, Cascadia: 3, Excalifont: 5, Nunito: 6, "Comic Shanns": 8 };
const scene = { elements: fams.map((f, i) => ({ id: "t" + i, type: "text", x: 0, y: i * 40, width: 200, height: 25, angle: 0, strokeColor: "#000", backgroundColor: "transparent", fillStyle: "solid", strokeWidth: 1, strokeStyle: "solid", roughness: 0, opacity: 100, groupIds: [], frameId: null, index: "a" + i, roundness: null, seed: 1, version: 1, versionNonce: 1, isDeleted: false, boundElements: null, updated: 1, link: null, locked: false, text: "Hello world abc", fontSize: 20, fontFamily: famId[f] ?? 5, textAlign: "left", verticalAlign: "top", containerId: null, originalText: "Hello world abc", autoResize: true, lineHeight: 1.25 })), files: {} };
await page.evaluate((s) => window.renderScene(s, { scale: 1 }), scene);
const widths = await page.evaluate((it) => window.measureText(it), items);
process.stdout.write(JSON.stringify(widths));
await browser.close();
srv.close();
