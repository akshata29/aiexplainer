#!/usr/bin/env node
/**
 * Render .excalidraw files to PNG with the *real* @excalidraw/excalidraw exporter in headless Edge.
 *
 *   node tools/render.mjs --only agent-service                 # overview PNG -> diagrams/previews/work/  (+ tile-grid hint)
 *   node tools/render.mjs --only agent-service --tiles r2c1,r3c2   # also write just those full-resolution tiles
 *   node tools/render.mjs --only agent-service --tiles all     # every tile (slow on tall canvases - avoid)
 *   node tools/render.mjs --all                                # gallery previews (webp) for every diagram -> diagrams/previews/
 *   node tools/render.mjs --file some.excalidraw --out dir
 *   node tools/render.mjs --only toolbox --crop 0,900,1700,950 --width 1800   # one region (scene px, origin = top-left of content)
 *   node tools/render.mjs --shots [--shot name,name]            # README screenshots listed in docs/featured.json -> docs/screenshots/
 *
 * Options: --scale 1  --max-side 1800  --tile 1500x1000  --out <dir>  --width 1800  --fmt webp|png
 *
 * Resource policy: only ONE render runs at a time on the machine. Concurrent callers queue on tools/.render.lock
 * (the holder refreshes a heartbeat; a lock untouched for 3 minutes is treated as stale and reclaimed).
 */
import { chromium } from "playwright-core";
import http from "node:http";
import fs from "node:fs";
import path from "node:path";
import { spawnSync } from "node:child_process";
import { fileURLToPath } from "node:url";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const diagramsDir = path.join(root, "diagrams");
const distDir = path.join(root, "tools", "export-dist");
const renderLock = path.join(root, "tools", ".render.lock");

function parseArgs(argv) {
  const a = { only: [], all: false, scale: 1, maxSide: 1800, tile: "1500x1000", tiles: "", out: null, files: [], thumb: 0, crop: "", width: 1800, fmt: "webp", shots: false, shot: [] };
  for (let i = 0; i < argv.length; i++) {
    const k = argv[i];
    if (k === "--only") a.only.push(...argv[++i].split(","));
    else if (k === "--all") a.all = true;
    else if (k === "--scale") a.scale = parseFloat(argv[++i]);
    else if (k === "--max-side") a.maxSide = parseInt(argv[++i], 10);
    else if (k === "--tile") a.tile = argv[++i];
    else if (k === "--tiles") a.tiles = argv[++i] ?? "";
    else if (k === "--no-tiles") a.tiles = "";
    else if (k === "--out") a.out = argv[++i];
    else if (k === "--file") a.files.push(argv[++i]);
    else if (k === "--thumb") a.thumb = parseInt(argv[++i], 10);
    else if (k === "--crop") a.crop = argv[++i];
    else if (k === "--width") a.width = parseInt(argv[++i], 10);
    else if (k === "--fmt") a.fmt = argv[++i];
    else if (k === "--shots") a.shots = true;
    else if (k === "--shot") a.shot.push(...argv[++i].split(","));
    else { console.error(`unknown arg ${k}`); process.exit(2); }
  }
  return a;
}

const mtime = (p) => (fs.existsSync(p) ? fs.statSync(p).mtimeMs : 0);
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

let lockHeld = false;
let heartbeat = null;
function releaseLock() {
  if (!lockHeld) return;
  lockHeld = false;
  if (heartbeat) clearInterval(heartbeat);
  try { fs.rmSync(renderLock, { recursive: true, force: true }); } catch { /* ignore */ }
}
process.on("exit", releaseLock);
for (const sig of ["SIGINT", "SIGTERM"]) process.on(sig, () => { releaseLock(); process.exit(130); });

async function acquireRenderLock() {
  const t0 = Date.now();
  for (;;) {
    try { fs.mkdirSync(renderLock); lockHeld = true; break; } catch {
      let age = 0;
      try { age = Date.now() - fs.statSync(renderLock).mtimeMs; } catch { continue; }
      if (age > 3 * 60 * 1000) { try { fs.rmSync(renderLock, { recursive: true, force: true }); } catch { /* ignore */ } continue; }
      await sleep(1000 + Math.random() * 1000);
    }
  }
  heartbeat = setInterval(() => { try { const n = new Date(); fs.utimesSync(renderLock, n, n); } catch { /* ignore */ } }, 20000);
  heartbeat.unref();
  const waited = Date.now() - t0;
  if (waited > 2500) console.error(`(queued ${Math.round(waited / 1000)}s behind another render)`);
}

/** Size of the full-resolution export (scene bounds + 32px padding each side), and the tile grid it would be cut into. */
function tileGrid(scene, tw, th) {
  let x0 = Infinity, y0 = Infinity, x1 = -Infinity, y1 = -Infinity;
  for (const e of scene.elements) {
    if (e.isDeleted) continue;
    let ex0 = e.x, ey0 = e.y, ex1 = e.x + e.width, ey1 = e.y + e.height;
    if (e.points) for (const [px, py] of e.points) { ex0 = Math.min(ex0, e.x + px); ey0 = Math.min(ey0, e.y + py); ex1 = Math.max(ex1, e.x + px); ey1 = Math.max(ey1, e.y + py); }
    x0 = Math.min(x0, ex0); y0 = Math.min(y0, ey0); x1 = Math.max(x1, ex1); y1 = Math.max(y1, ey1);
  }
  const W = Math.ceil(x1 - x0 + 64), H = Math.ceil(y1 - y0 + 64);
  const tiled = W > tw * 1.15 || H > th * 1.15;
  return { W, H, cols: tiled ? Math.ceil(W / tw) : 1, rows: tiled ? Math.ceil(H / th) : 1, tiled };
}

async function ensureBundle() {
  const index = path.join(distDir, "index.html");
  const srcs = ["main.ts", "index.html", "vite.config.ts"].map((f) => path.join(root, "tools", "export", f));
  const stale = () => !fs.existsSync(index) || mtime(index) < Math.max(...srcs.map(mtime)) || !fs.existsSync(path.join(distDir, "fonts"));
  if (!stale()) return;
  const lock = path.join(root, "tools", ".export-build.lock");
  for (let i = 0; i < 240; i++) {
    try { fs.mkdirSync(lock); break; } catch { await sleep(1000); }
    if (i === 239) throw new Error("timed out waiting for export bundle build lock");
  }
  try {
    if (stale()) {
      console.error("building export bundle...");
      const tmp = path.join(root, "tools", "export-dist-new");
      fs.rmSync(tmp, { recursive: true, force: true });
      const vite = path.join(root, "node_modules", "vite", "bin", "vite.js");
      const r = spawnSync(process.execPath, [vite, "build", "-c", "tools/export/vite.config.ts", "--outDir", "../export-dist-new"], { cwd: root, stdio: "inherit" });
      if (r.status !== 0) throw new Error("vite build failed");
      const fonts = path.join(root, "node_modules", "@excalidraw", "excalidraw", "dist", "prod", "fonts");
      fs.cpSync(fonts, path.join(tmp, "fonts"), { recursive: true, filter: (p) => !p.includes("Xiaolai") });
      // atomic-ish swap so concurrent renders never see a half-built bundle
      const old = path.join(root, "tools", "export-dist-old");
      fs.rmSync(old, { recursive: true, force: true });
      if (fs.existsSync(distDir)) fs.renameSync(distDir, old);
      fs.renameSync(tmp, distDir);
      fs.rmSync(old, { recursive: true, force: true });
    }
  } finally {
    fs.rmSync(lock, { recursive: true, force: true });
  }
}

const MIME = { ".html": "text/html", ".js": "text/javascript", ".css": "text/css", ".woff2": "font/woff2", ".json": "application/json" };
function serve() {
  const srv = http.createServer((req, res) => {
    const u = decodeURIComponent((req.url || "/").split("?")[0]);
    const p = path.join(distDir, u === "/" ? "index.html" : u);
    if (!p.startsWith(distDir) || !fs.existsSync(p) || fs.statSync(p).isDirectory()) { res.writeHead(404); res.end(); return; }
    res.writeHead(200, { "content-type": MIME[path.extname(p)] || "application/octet-stream" });
    fs.createReadStream(p).pipe(res);
  });
  return new Promise((resolve) => srv.listen(0, "127.0.0.1", () => resolve(srv)));
}

/** Crop jobs for --shots (docs/featured.json) or --crop; null when neither flag is given. */
function cropJobs(args) {
  if (args.shots) {
    const cfg = JSON.parse(fs.readFileSync(path.join(root, "docs", "featured.json"), "utf8"));
    const want = new Set(args.shot);
    const fmt = cfg.format ?? "webp";
    const dir = path.join(root, cfg.outDir ?? "docs/screenshots");
    return cfg.shots.filter((s) => !want.size || want.has(s.name)).map((s) => ({
      name: s.name, file: path.join(diagramsDir, `${s.id}.excalidraw`), crop: s.crop, width: s.width ?? cfg.width ?? 1800, fade: s.fade ?? 0,
      fmt, quality: cfg.quality ?? 0.92, out: path.join(dir, `${s.name}.${fmt}`),
    }));
  }
  if (args.crop) {
    const id = args.only[0];
    if (!id) { console.error("--crop needs --only <id>"); process.exit(2); }
    const dir = path.resolve(args.out || path.join(diagramsDir, "previews", "work"));
    return [{ name: id, file: path.join(diagramsDir, `${id}.excalidraw`), crop: args.crop.split(",").map(Number), width: args.width,
      fmt: args.fmt, quality: 0.92, fade: 0, out: path.join(dir, `${id}.crop.${args.fmt}`) }];
  }
  return null;
}

/** One shared headless-Edge page behind the machine-wide render lock. */
async function openPage() {
  await acquireRenderLock();
  let srv, browser;
  try {
    await ensureBundle();
    srv = await serve();
    browser = await chromium.launch({ channel: "msedge", headless: true });
    const page = await browser.newPage({ viewport: { width: 1200, height: 800 } });
    page.on("pageerror", (e) => console.error("[page error]", e.message));
    await page.goto(`http://127.0.0.1:${srv.address().port}/index.html`);
    await page.waitForFunction(() => window.ready === true, null, { timeout: 60000 });
    return { page, close: async () => { await browser.close(); srv.close(); releaseLock(); } };
  } catch (e) {
    await browser?.close(); srv?.close(); releaseLock();
    throw e;
  }
}

async function runCropJobs(jobs) {
  const { page, close } = await openPage();
  try {
    for (const j of jobs) {
      if (!fs.existsSync(j.file)) { console.error(`missing ${j.file}`); continue; }
      const scene = JSON.parse(fs.readFileSync(j.file, "utf8"));
      const t0 = Date.now();
      const [x, y, w, h] = j.crop;
      const r = await page.evaluate(([s, o]) => window.renderCrop(s, o), [scene, { crop: { x, y, w, h }, outWidth: j.width, format: j.fmt, quality: j.quality, fade: j.fade || 0 }]);
      fs.mkdirSync(path.dirname(j.out), { recursive: true });
      const buf = Buffer.from(r.b64, "base64");
      fs.writeFileSync(j.out, buf);
      console.log(`${j.name}: ${r.width}x${r.height} ${(buf.length / 1024).toFixed(0)} KB (${r.kept} elements drawn) -> ${j.out} (${Date.now() - t0}ms)`);
    }
  } finally {
    await close();
  }
}

async function main() {
  const args = parseArgs(process.argv.slice(2));
  const jobs = cropJobs(args);
  if (jobs) { await runCropJobs(jobs); return; }
  let targets = [];
  if (args.all) {
    targets = fs.readdirSync(diagramsDir).filter((f) => f.endsWith(".excalidraw") && !f.startsWith("_")).map((f) => path.join(diagramsDir, f));
  }
  for (const id of args.only) targets.push(path.join(diagramsDir, `${id}.excalidraw`));
  for (const f of args.files) targets.push(path.resolve(f));
  if (!targets.length) { console.error("nothing to render (use --only <id>, --all or --file <path>)"); process.exit(2); }
  if (args.all) {
    if (!process.argv.includes("--max-side")) args.maxSide = 3600;
    if (!args.thumb) args.thumb = 640;
  }
  const outDir = path.resolve(args.out || (args.all ? path.join(diagramsDir, "previews") : path.join(diagramsDir, "previews", "work")));
  fs.mkdirSync(outDir, { recursive: true });

  await acquireRenderLock();
  await ensureBundle();
  const srv = await serve();
  const url = `http://127.0.0.1:${srv.address().port}/index.html`;
  const browser = await chromium.launch({ channel: "msedge", headless: true });
  try {
    const page = await browser.newPage({ viewport: { width: 1200, height: 800 } });
    page.on("pageerror", (e) => console.error("[page error]", e.message));
    await page.goto(url);
    await page.waitForFunction(() => window.ready === true, null, { timeout: 60000 });
    const [tw, th] = args.tile.split("x").map(Number);
    for (const file of targets) {
      const id = path.basename(file, ".excalidraw");
      if (!fs.existsSync(file)) { console.error(`missing ${file}`); continue; }
      const scene = JSON.parse(fs.readFileSync(file, "utf8"));
      const t0 = Date.now();
      const over = await page.evaluate(([s, o]) => window.renderScene(s, o), [scene, args.all ? {
        // gallery mode: render once at ~2x the thumbnail width, keep only the cropped thumbnail (no PNG round-trip)
        targetWidth: 1320, skipFull: true,
        webps: [{ key: "thumb", maxSide: 660, cropTop: 0.72, q: 0.86 }],
      } : { scale: args.scale, maxSide: args.maxSide }]);
      const png = path.join(outDir, `${id}.png`);
      if (!args.all) fs.writeFileSync(png, Buffer.from(over.full, "base64"));
      for (const [k, b64] of Object.entries(over.webps || {})) fs.writeFileSync(path.join(outDir, `${id}.${k}.webp`), Buffer.from(b64, "base64"));
      for (const f of fs.readdirSync(outDir)) if (f.startsWith(`${id}.tile-`)) fs.rmSync(path.join(outDir, f));
      let ntiles = 0;
      if (!args.all) {
        const g = tileGrid(scene, tw, th);
        const spec = args.tiles.trim();
        let note;
        if (!g.tiled) note = `canvas ${g.W}x${g.H}px fits one tile (overview is at most ${args.maxSide}px; use --max-side ${Math.max(g.W, g.H)} for 1:1)`;
        else if (!spec) note = `full size ${g.W}x${g.H}px = tile grid ${g.cols} cols x ${g.rows} rows (row r = vertical band ${"(r-1)/" + g.rows}..${"r/" + g.rows} of the height); inspect parts with --tiles r<row>c<col>[,...]`;
        else note = `full size ${g.W}x${g.H}px, grid ${g.cols}x${g.rows}`;
        if (spec && g.tiled) {
          const ids = spec === "all" ? "all" : spec.split(",").map((s) => s.trim().toLowerCase());
          const det = await page.evaluate(([s, o]) => window.renderScene(s, o), [scene, { scale: 1, tile: { w: tw, h: th }, tileIds: ids }]);
          for (const t of det.tiles) { fs.writeFileSync(path.join(outDir, `${id}.tile-r${t.r}c${t.c}.png`), Buffer.from(t.b64, "base64")); ntiles++; }
        }
        console.log(`${id}: overview ${over.width}x${over.height} -> ${png}; ${note}${ntiles ? `; wrote ${ntiles} tile(s) ${id}.tile-r*c*.png` : ""} (${Date.now() - t0}ms)`);
      } else {
        console.log(`${id}: ${over.width}x${over.height} -> ${png} (${Date.now() - t0}ms)`);
      }
    }
  } finally {
    await browser.close();
    srv.close();
    releaseLock();
  }
}

main().catch((e) => { console.error(e); process.exit(1); });
