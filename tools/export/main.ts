import { exportToBlob, getCommonBounds } from "@excalidraw/excalidraw";

type Scene = { elements: any[]; appState?: any; files?: any };
type Opts = { scale?: number; padding?: number; tile?: { w: number; h: number } | null; tileIds?: string[] | "all"; maxSide?: number; targetWidth?: number; skipFull?: boolean; thumb?: number; webps?: { key: string; maxSide: number; q: number; cropTop?: number }[] };

type CropOpts = { crop: { x: number; y: number; w: number; h: number }; outWidth: number; format?: "png" | "webp"; quality?: number; border?: boolean; fade?: number };

declare global {
  interface Window {
    renderScene: (scene: Scene, opts: Opts) => Promise<{ width: number; height: number; full: string; thumb?: string; webps?: Record<string, string>; tiles: { r: number; c: number; b64: string }[] }>;
    renderCrop: (scene: Scene, opts: CropOpts) => Promise<{ width: number; height: number; b64: string; kept: number }>;
    measureText: (items: { text: string; size: number; family: string }[]) => Promise<number[]>;
    boundsReport: (elements: any[]) => { common: number[]; offenders: { id: string; type: string; text?: string; own: number[]; excal: number[] }[] };
    ready: boolean;
  }
}

const FAMILY_CSS: Record<number, string> = { 1: "Virgil", 3: "Cascadia", 5: "Excalifont", 6: "Nunito", 8: "Comic Shanns" };

async function blobToBase64(blob: Blob): Promise<string> {
  const buf = new Uint8Array(await blob.arrayBuffer());
  let s = "";
  for (let i = 0; i < buf.length; i += 0x8000) s += String.fromCharCode(...buf.subarray(i, i + 0x8000));
  return btoa(s);
}

async function warmFonts(elements: any[]) {
  // make sure every font family used by the scene is actually loaded before drawing to canvas
  const used = new Set<number>();
  for (const e of elements) if (e.type === "text") used.add(e.fontFamily);
  const loads: Promise<unknown>[] = [];
  for (const fam of used) {
    const css = FAMILY_CSS[fam] ?? "Excalifont";
    const sample = elements.filter((e) => e.type === "text" && e.fontFamily === fam).map((e) => e.text).join("").slice(0, 4000);
    loads.push(document.fonts.load(`20px "${css}"`, sample).catch(() => {}));
  }
  await Promise.all(loads);
  await document.fonts.ready;
}

window.renderScene = async (scene, opts) => {
  const scale = opts.scale ?? 1;
  const padding = opts.padding ?? 32;
  await warmFonts(scene.elements);
  const run = async (getDimensions: (w: number, h: number) => { width: number; height: number; scale: number }) =>
    exportToBlob({
      elements: scene.elements,
      appState: { ...(scene.appState || {}), exportBackground: true, viewBackgroundColor: "#ffffff", exportWithDarkMode: false },
      files: scene.files || {},
      mimeType: "image/png",
      exportPadding: padding,
      getDimensions,
    });
  // cheap 64px warm-up export so every font face is resident before the one real export (avoids a second full-size pass)
  await run((w, h) => {
    const s = 64 / Math.max(w, h);
    return { width: Math.max(1, Math.ceil(w * s)), height: Math.max(1, Math.ceil(h * s)), scale: s };
  });
  await document.fonts.ready;
  const blob = await run((w, h) => {
    let s = scale;
    if (opts.targetWidth) s = Math.min(1, opts.targetWidth / w);
    else if (opts.maxSide) s = Math.min(s, opts.maxSide / Math.max(w, h));
    return { width: Math.ceil(w * s), height: Math.ceil(h * s), scale: s };
  });
  const bmp = await createImageBitmap(blob);
  const out: any = { width: bmp.width, height: bmp.height, full: opts.skipFull ? "" : await blobToBase64(blob), tiles: [] as any[], webps: {} as Record<string, string> };
  for (const w of opts.webps ?? []) {
    // cropTop = keep only the top (width * cropTop) rows: a readable gallery thumbnail of the title + first section
    let sh = bmp.height;
    let k: number;
    if (w.cropTop) {
      sh = Math.min(bmp.height, Math.round(bmp.width * w.cropTop));
      k = Math.min(1, w.maxSide / bmp.width);
    } else {
      k = Math.min(1, w.maxSide / Math.max(bmp.width, bmp.height));
    }
    const cv = document.createElement("canvas");
    cv.width = Math.max(1, Math.round(bmp.width * k));
    cv.height = Math.max(1, Math.round(sh * k));
    const ctx = cv.getContext("2d")!;
    ctx.fillStyle = "#fff";
    ctx.fillRect(0, 0, cv.width, cv.height);
    ctx.imageSmoothingQuality = "high";
    ctx.drawImage(bmp, 0, 0, bmp.width, sh, 0, 0, cv.width, cv.height);
    const tb: Blob = await new Promise((res) => cv.toBlob((b) => res(b!), "image/webp", w.q));
    out.webps[w.key] = await blobToBase64(tb);
  }
  if (opts.tile && opts.tileIds && (bmp.width > opts.tile.w * 1.15 || bmp.height > opts.tile.h * 1.15)) {
    const cols = Math.ceil(bmp.width / opts.tile.w);
    const rows = Math.ceil(bmp.height / opts.tile.h);
    const tw = Math.ceil(bmp.width / cols);
    const th = Math.ceil(bmp.height / rows);
    const ov = 40; // overlap so text cut by a tile edge is readable in the neighbour
    for (let r = 0; r < rows; r++) {
      for (let c = 0; c < cols; c++) {
        if (opts.tileIds !== "all" && !opts.tileIds.includes(`r${r + 1}c${c + 1}`)) continue;
        const sx = Math.max(0, c * tw - (c ? ov : 0));
        const sy = Math.max(0, r * th - (r ? ov : 0));
        const sw = Math.min(bmp.width - sx, tw + (c ? ov : 0) + ov);
        const sh = Math.min(bmp.height - sy, th + (r ? ov : 0) + ov);
        const cv = document.createElement("canvas");
        cv.width = sw;
        cv.height = sh;
        cv.getContext("2d")!.drawImage(bmp, sx, sy, sw, sh, 0, 0, sw, sh);
        const tb: Blob = await new Promise((res) => cv.toBlob((b) => res(b!), "image/png"));
        out.tiles.push({ r: r + 1, c: c + 1, b64: await blobToBase64(tb) });
      }
    }
  }
  return out;
};

/**
 * Render one rectangular region of a scene (scene px, origin = top-left of the content bounds) at an exact output width.
 * Only elements near the region are drawn; two invisible 1px "pins" make the export bounds cover the region, and the
 * result is cropped from the bitmap, so the output is pixel-exact and independent of the rest of the canvas.
 */
window.renderCrop = async (scene, o) => {
  await warmFonts(scene.elements);
  const live = scene.elements.filter((e: any) => !e.isDeleted);
  const map = new Map(live.map((e: any) => [e.id, e]));
  const bounds = (els: any[]) => getCommonBounds(els, map as any) as unknown as number[];
  const [ox, oy] = bounds(live);
  const cx0 = ox + o.crop.x, cy0 = oy + o.crop.y, cx1 = cx0 + o.crop.w, cy1 = cy0 + o.crop.h;
  const m = 48;
  const keep = live.filter((e: any) => {
    const b = bounds([e]);
    return b[2] >= cx0 - m && b[0] <= cx1 + m && b[3] >= cy0 - m && b[1] <= cy1 + m;
  });
  const tpl = live.find((e: any) => e.type === "rectangle");
  if (!tpl) throw new Error("scene has no rectangle to clone as a bounds pin");
  const pin = (id: string, x: number, y: number) => ({
    ...tpl, id, x, y, width: 1, height: 1, strokeColor: "transparent", backgroundColor: "transparent", opacity: 0,
    boundElements: null, link: null, groupIds: [], frameId: null, text: undefined,
  });
  const els = [...keep, pin("crop-pin-a", cx0, cy0), pin("crop-pin-b", cx1 - 1, cy1 - 1)];
  const [bx0, by0, bx1, by1] = bounds(els);
  const s = o.outWidth / o.crop.w;
  if ((bx1 - bx0) * s > 16000 || (by1 - by0) * s > 16000) throw new Error(`crop export would be ${Math.round((bx1 - bx0) * s)}x${Math.round((by1 - by0) * s)}px; lower the width`);
  const exp = (getDimensions: (w: number, h: number) => { width: number; height: number; scale: number }) =>
    exportToBlob({
      elements: els,
      appState: { ...(scene.appState || {}), exportBackground: true, viewBackgroundColor: "#ffffff", exportWithDarkMode: false },
      files: scene.files || {},
      mimeType: "image/png",
      exportPadding: 0,
      getDimensions,
    });
  await exp((w, h) => {
    const k = 64 / Math.max(w, h);
    return { width: Math.max(1, Math.ceil(w * k)), height: Math.max(1, Math.ceil(h * k)), scale: k };
  });
  await document.fonts.ready;
  const blob = await exp((w, h) => ({ width: Math.ceil(w * s), height: Math.ceil(h * s), scale: s }));
  const bmp = await createImageBitmap(blob);
  const k = bmp.width / (bx1 - bx0);
  const outW = Math.round(o.outWidth);
  const outH = Math.round((outW * o.crop.h) / o.crop.w);
  const cv = document.createElement("canvas");
  cv.width = outW;
  cv.height = outH;
  const ctx = cv.getContext("2d")!;
  ctx.fillStyle = "#fff";
  ctx.fillRect(0, 0, outW, outH);
  ctx.imageSmoothingQuality = "high";
  ctx.drawImage(bmp, (cx0 - bx0) * k, (cy0 - by0) * k, o.crop.w * k, o.crop.h * k, 0, 0, outW, outH);
  if (o.fade) {
    // crop cuts through content: fade the bottom edge to white so it reads as "continues" instead of a sliced card
    const f = Math.min(o.fade, outH);
    const g = ctx.createLinearGradient(0, outH - f, 0, outH);
    g.addColorStop(0, "rgba(255,255,255,0)");
    g.addColorStop(1, "rgba(255,255,255,1)");
    ctx.fillStyle = g;
    ctx.fillRect(0, outH - f, outW, f);
  }
  if (o.border !== false) {
    ctx.strokeStyle = "#d0d7de";
    ctx.lineWidth = 2;
    ctx.strokeRect(1, 1, outW - 2, outH - 2);
  }
  const fmt = o.format ?? "webp";
  const out: Blob = await new Promise((res) => cv.toBlob((b) => res(b!), `image/${fmt}`, o.quality ?? 0.92));
  return { width: outW, height: outH, b64: await blobToBase64(out), kept: keep.length };
};

window.measureText = async (items) => {
  const cv = document.createElement("canvas").getContext("2d")!;
  await document.fonts.ready;
  const out: number[] = [];
  for (const it of items) {
    await document.fonts.load(`${it.size}px "${it.family}"`, it.text);
    cv.font = `${it.size}px "${it.family}"`;
    out.push(cv.measureText(it.text).width);
  }
  return out;
};

// Diagnostic: elements whose Excalidraw bounds extend well beyond the bounds implied by our own geometry.
window.boundsReport = (elements) => {
  const own = (e: any): number[] => {
    if (e.points?.length) {
      const xs = e.points.map((p: number[]) => e.x + p[0]);
      const ys = e.points.map((p: number[]) => e.y + p[1]);
      return [Math.min(...xs), Math.min(...ys), Math.max(...xs), Math.max(...ys)];
    }
    return [e.x, e.y, e.x + e.width, e.y + e.height];
  };
  const map = new Map(elements.map((e: any) => [e.id, e]));
  const offenders: any[] = [];
  for (const e of elements) {
    const o = own(e);
    const b = getCommonBounds([e], map as any) as unknown as number[];
    const slack = 24;
    if (b[0] < o[0] - slack || b[1] < o[1] - slack || b[2] > o[2] + slack || b[3] > o[3] + slack) {
      offenders.push({ id: e.id, type: e.type, text: e.text?.slice(0, 30), own: o.map(Math.round), excal: b.map(Math.round) });
    }
  }
  return { common: (getCommonBounds(elements, map as any) as unknown as number[]).map(Math.round), offenders };
};

window.ready = true;
