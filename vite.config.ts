import { defineConfig, type Plugin } from "vite";
import react from "@vitejs/plugin-react";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const root = path.dirname(fileURLToPath(import.meta.url));
const diagramsDir = path.join(root, "diagrams");
const workDir = path.join(diagramsDir, "previews", "work");
const fontsDir = path.join(root, "node_modules", "@excalidraw", "excalidraw", "dist", "prod", "fonts");

const MIME: Record<string, string> = {
  ".json": "application/json", ".excalidraw": "application/json", ".png": "image/png", ".webp": "image/webp",
  ".woff2": "font/woff2", ".svg": "image/svg+xml",
};

/** Serves ./diagrams and Excalidraw's font assets in dev; copies them into dist on build. */
function foundryStatic(): Plugin {
  const mounts: [string, string][] = [["/diagrams/", diagramsDir], ["/excalidraw-assets/fonts/", fontsDir]];
  return {
    name: "foundry-static",
    configureServer(server) {
      server.middlewares.use((req, res, next) => {
        const url = decodeURIComponent((req.url || "").split("?")[0]);
        for (const [prefix, dir] of mounts) {
          if (!url.startsWith(prefix)) continue;
          const file = path.join(dir, url.slice(prefix.length));
          if (file.startsWith(dir) && fs.existsSync(file) && fs.statSync(file).isFile()) {
            res.setHeader("content-type", MIME[path.extname(file)] || "application/octet-stream");
            fs.createReadStream(file).pipe(res);
            return;
          }
        }
        next();
      });
    },
    closeBundle() {
      const out = path.join(root, "dist");
      if (!fs.existsSync(out)) return;
      fs.cpSync(diagramsDir, path.join(out, "diagrams"), {
        recursive: true,
        filter: (p) => p !== workDir && !p.startsWith(workDir + path.sep) && !path.basename(p).startsWith("_"),
      });
      fs.cpSync(fontsDir, path.join(out, "excalidraw-assets", "fonts"), { recursive: true, filter: (p) => !p.includes("Xiaolai") });
    },
  };
}

export default defineConfig({
  base: "./",
  plugins: [react(), foundryStatic()],
  define: { "process.env.IS_PREACT": JSON.stringify("false") },
  build: { outDir: "dist", chunkSizeWarningLimit: 8000 },
  server: { port: 5391 },
});
