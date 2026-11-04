import { useCallback, useEffect, useMemo, useState } from "react";
import { Excalidraw, exportToBlob, exportToSvg, getCommonBounds } from "@excalidraw/excalidraw";
import "@excalidraw/excalidraw/index.css";

type Diagram = {
  id: string;
  title: string;
  section: string;
  group?: string;
  order?: number;
  description: string;
  tags?: string[];
  file: string;
  width: number;
  height: number;
  elements: number;
  updated?: string;
};
type Manifest = {
  generated: string;
  sections: Record<string, { title: string; blurb: string }>;
  diagrams: Diagram[];
};

const abs = (p: string) => new URL(p, document.baseURI).href;
const thumbUrl = (d: Diagram) => abs(`diagrams/previews/${d.id}.thumb.webp`);
const fileUrl = (d: Diagram) => abs(`diagrams/${d.file}`);

function download(blob: Blob, name: string) {
  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob);
  a.download = name;
  a.click();
  setTimeout(() => URL.revokeObjectURL(a.href), 3000);
}

function useRoute(): { view: string | null } {
  const parse = () => {
    const m = /^#\/d\/([\w-]+)/.exec(window.location.hash);
    return { view: m ? m[1] : null };
  };
  const [route, setRoute] = useState(parse);
  useEffect(() => {
    const h = () => setRoute(parse());
    window.addEventListener("hashchange", h);
    return () => window.removeEventListener("hashchange", h);
  }, []);
  return route;
}

function useManifest() {
  const [data, setData] = useState<Manifest | null>(null);
  const [error, setError] = useState<string | null>(null);
  useEffect(() => {
    fetch(abs("diagrams/manifest.json"))
      .then((r) => (r.ok ? r.json() : Promise.reject(new Error(`manifest ${r.status}`))))
      .then(setData)
      .catch((e) => setError(String(e)));
  }, []);
  return { data, error };
}

export default function App() {
  const { data, error } = useManifest();
  const route = useRoute();
  if (error) return <div className="center">Could not load diagrams/manifest.json - run <code>python -m generator.build</code>. ({error})</div>;
  if (!data) return <div className="center">Loading...</div>;
  const current = route.view ? data.diagrams.find((d) => d.id === route.view) : undefined;
  return current ? <Viewer manifest={data} diagram={current} /> : <Gallery manifest={data} />;
}

/* ------------------------------------------------------------------ gallery */
function Gallery({ manifest }: { manifest: Manifest }) {
  const [q, setQ] = useState("");
  const [section, setSection] = useState<string>("all");
  const sections = Object.entries(manifest.sections);
  const matches = useMemo(() => {
    const needle = q.trim().toLowerCase();
    return manifest.diagrams.filter((d) => {
      if (section !== "all" && d.section !== section) return false;
      if (!needle) return true;
      return [d.title, d.description, d.group, ...(d.tags ?? [])].join(" ").toLowerCase().includes(needle);
    });
  }, [manifest, q, section]);
  const counts = useMemo(() => {
    const c: Record<string, number> = {};
    manifest.diagrams.forEach((d) => (c[d.section] = (c[d.section] ?? 0) + 1));
    return c;
  }, [manifest]);

  return (
    <div className="page">
      <header className="hero">
        <img src={abs("favicon.svg")} alt="" className="logo" />
        <div>
          <h1>Microsoft Foundry Explainers</h1>
          <p>
            Hand-drawn <a href="https://excalidraw.com">Excalidraw</a> diagrams that explain every part of Microsoft Foundry - overview,
            agents, models, tools, observability, governance, reference architectures, BCDR, identity, AI Ops and what happens under the hood.
            Every canvas cites Microsoft Learn.
          </p>
          <p className="muted">
            {manifest.diagrams.length} diagrams · open them here, or download the <code>.excalidraw</code> file and edit it in{" "}
            <a href="https://excalidraw.com">excalidraw.com</a> or the VS Code Excalidraw extension. Updated {manifest.generated}.
          </p>
        </div>
      </header>

      <div className="toolbar">
        <input className="search" placeholder="Search diagrams (agents, PTU, landing zone, MCP...)" value={q} onChange={(e) => setQ(e.target.value)} />
        <div className="chips">
          <button className={section === "all" ? "chip on" : "chip"} onClick={() => setSection("all")}>All <b>{manifest.diagrams.length}</b></button>
          {sections.map(([k, s]) => (
            <button key={k} className={section === k ? "chip on" : "chip"} onClick={() => setSection(k)} title={s.blurb}>
              {k}. {s.title} <b>{counts[k] ?? 0}</b>
            </button>
          ))}
        </div>
      </div>

      {sections.map(([k, s]) => {
        const items = matches.filter((d) => d.section === k);
        if (!items.length) return null;
        // show sub-headings only when the section really has several groups; mixed grouped/ungrouped items collapse to one grid
        const named = Array.from(new Set(items.map((d) => d.group ?? "").filter(Boolean)));
        const groups = named.length > 1 ? Array.from(new Set(items.map((d) => d.group ?? ""))) : [""];
        return (
          <section key={k} className="section">
            <h2>
              <span className="num">{k}</span> {s.title}
            </h2>
            <p className="muted">{s.blurb}</p>
            {groups.map((g) => (
              <div key={g}>
                {g && <h3>{g}</h3>}
                <div className="grid">
                  {items.filter((d) => groups.length === 1 || (d.group ?? "") === g).map((d) => (
                    <Card key={d.id} d={d} />
                  ))}
                </div>
              </div>
            ))}
          </section>
        );
      })}
      {!matches.length && <p className="center">No diagram matches "{q}".</p>}

      <footer className="foot">
        Unofficial community explainers - always verify details against the linked Microsoft Learn pages. Inspired by{" "}
        <a href="https://difriedman.github.io/explainers/">Dan Friedman's Fabric explainers</a>. Azure service icons © Microsoft
        (Azure Architecture Icons).
      </footer>
    </div>
  );
}

function Card({ d }: { d: Diagram }) {
  return (
    <article className="card">
      <a href={`#/d/${d.id}`} className="thumb">
        <img
          loading="lazy"
          src={thumbUrl(d)}
          alt={d.title}
        />
      </a>
      <div className="body">
        <h4>
          <a href={`#/d/${d.id}`}>{d.title}</a>
        </h4>
        <p>{d.description}</p>
        <div className="tags">{(d.tags ?? []).slice(0, 5).map((t) => <span key={t}>{t}</span>)}</div>
        <div className="actions">
          <a className="btn primary" href={`#/d/${d.id}`}>Open</a>
          <a className="btn" href={fileUrl(d)} download>.excalidraw</a>
          <span className="meta">{d.width}×{d.height}</span>
        </div>
      </div>
    </article>
  );
}

/* ------------------------------------------------------------------ viewer */
function Viewer({ manifest, diagram }: { manifest: Manifest; diagram: Diagram }) {
  const [scene, setScene] = useState<any>(null);
  const [api, setApi] = useState<any>(null);
  const siblings = useMemo(() => manifest.diagrams, [manifest]);
  const idx = siblings.findIndex((d) => d.id === diagram.id);
  const prev = idx > 0 ? siblings[idx - 1] : null;
  const next = idx < siblings.length - 1 ? siblings[idx + 1] : null;
  const isLocal = ["localhost", "127.0.0.1"].includes(window.location.hostname);

  useEffect(() => {
    setScene(null);
    setApi(null);
    fetch(fileUrl(diagram))
      .then((r) => r.json())
      .then(setScene);
    document.title = `${diagram.title} - Foundry Explainers`;
    return () => {
      document.title = "Microsoft Foundry Explainers";
    };
  }, [diagram.id]);

  /** Zoom + scroll so the canvas fills the viewport width, starting at the top-left. Tall canvases stay readable. */
  const fitWidth = useCallback(() => {
    if (!api || !scene) return;
    const els = api.getSceneElements();
    if (!els.length) return;
    const [x0, y0, x1] = getCommonBounds(els) as [number, number, number, number, number];
    const st = api.getAppState();
    const z = Math.min(1.5, Math.max(0.05, ((st.width - 32) / Math.max(x1 - x0, 1))));
    api.updateScene({ appState: { zoom: { value: z }, scrollX: 16 / z - x0, scrollY: 16 / z - y0 } });
  }, [api, scene]);

  const fitAll = useCallback(() => {
    if (api && scene) api.scrollToContent(api.getSceneElements(), { fitToViewport: true, viewportZoomFactor: 0.96, animate: false });
  }, [api, scene]);

  // default view: fit everything when that is still legible (zoom >= ~55% of fit-width), otherwise fit the width
  const fit = useCallback(() => {
    if (!api || !scene) return;
    const els = api.getSceneElements();
    if (!els.length) return;
    const [x0, y0, x1, y1] = getCommonBounds(els) as [number, number, number, number, number];
    const st = api.getAppState();
    const zw = (st.width - 32) / Math.max(x1 - x0, 1);
    const za = Math.min(zw, (st.height - 32) / Math.max(y1 - y0, 1));
    if (za >= zw * 0.55) fitAll();
    else fitWidth();
  }, [api, scene, fitAll, fitWidth]);

  useEffect(() => {
    if (!api || !scene) return;
    const t = window.setTimeout(fit, 250);
    return () => window.clearTimeout(t);
  }, [api, scene, fit]);

  const exportPng = useCallback(async () => {
    if (!api) return;
    const blob = await exportToBlob({
      elements: api.getSceneElements(),
      appState: { ...api.getAppState(), exportBackground: true, viewBackgroundColor: "#ffffff" },
      files: api.getFiles(),
      mimeType: "image/png",
      exportPadding: 32,
      getDimensions: (w: number, h: number) => ({ width: Math.round(w * 1.5), height: Math.round(h * 1.5), scale: 1.5 }),
    });
    download(blob, `${diagram.id}.png`);
  }, [api, diagram.id]);

  const exportSvg = useCallback(async () => {
    if (!api) return;
    const svg = await exportToSvg({
      elements: api.getSceneElements(),
      appState: { ...api.getAppState(), exportBackground: true, viewBackgroundColor: "#ffffff" },
      files: api.getFiles(),
      exportPadding: 32,
    });
    download(new Blob([new XMLSerializer().serializeToString(svg)], { type: "image/svg+xml" }), `${diagram.id}.svg`);
  }, [api, diagram.id]);

  useEffect(() => {
    const k = (e: KeyboardEvent) => {
      if (e.key === "Escape") window.location.hash = "#/";
      if (e.key === "ArrowLeft" && e.altKey && prev) window.location.hash = `#/d/${prev.id}`;
      if (e.key === "ArrowRight" && e.altKey && next) window.location.hash = `#/d/${next.id}`;
    };
    window.addEventListener("keydown", k);
    return () => window.removeEventListener("keydown", k);
  }, [prev, next]);

  return (
    <div className="viewer">
      <div className="topbar">
        <a className="btn" href="#/">← All diagrams</a>
        <div className="crumb">
          <span className="muted">{manifest.sections[diagram.section]?.title}{diagram.group ? ` › ${diagram.group}` : ""}</span>
          <h1>{diagram.title}</h1>
        </div>
        <div className="spacer" />
        {prev && <a className="btn" href={`#/d/${prev.id}`} title={prev.title}>‹ Prev</a>}
        {next && <a className="btn" href={`#/d/${next.id}`} title={next.title}>Next ›</a>}
        <button className="btn" onClick={fitWidth} disabled={!api} title="Fill the width, start at the top (best for tall canvases)">Fit width</button>
        <button className="btn" onClick={fitAll} disabled={!api} title="Show the whole canvas">Fit all</button>
        <a className="btn" href={fileUrl(diagram)} download>.excalidraw</a>
        <button className="btn" onClick={exportPng} disabled={!api} title="Render a PNG in your browser (1.5x)">PNG</button>
        <button className="btn" onClick={exportSvg} disabled={!api} title="Render an SVG with embedded fonts">SVG</button>
        {!isLocal && (
          <a className="btn primary" target="_blank" rel="noreferrer" href={`https://excalidraw.com/#url=${encodeURIComponent(fileUrl(diagram))}`}>
            Edit in Excalidraw
          </a>
        )}
      </div>
      <div className="canvas">
        {scene ? (
          <Excalidraw
            key={diagram.id}
            excalidrawAPI={setApi}
            viewModeEnabled
            zenModeEnabled={false}
            initialData={{
              elements: scene.elements,
              files: scene.files,
              appState: { viewBackgroundColor: "#ffffff" },
              scrollToContent: true,
            }}
            UIOptions={{ canvasActions: { loadScene: false, saveToActiveFile: false, clearCanvas: false, changeViewBackgroundColor: false } }}
          />
        ) : (
          <div className="center">Loading {diagram.title}...</div>
        )}
        <div className="hint">Drag to pan · Ctrl/⌘ + scroll to zoom · click the small link icon on an element to open its Microsoft Learn page · Alt+←/→ previous/next</div>
      </div>
    </div>
  );
}
