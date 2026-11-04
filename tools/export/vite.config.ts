import { defineConfig } from "vite";

// Builds the tiny export page (tools/export) into tools/export-dist. Fonts are copied by tools/render.mjs.
export default defineConfig({
  root: "tools/export",
  base: "./",
  logLevel: "warn",
  define: { "process.env.IS_PREACT": JSON.stringify("false") },
  build: { outDir: "../export-dist", emptyOutDir: true, target: "es2022", chunkSizeWarningLimit: 8000 },
});
