import { createRoot } from "react-dom/client";
import App from "./App";
import "./styles.css";

// Heading font: Excalidraw's own hand-drawn Excalifont (Latin subset), loaded from the bundled font assets.
const fontBase = (window as unknown as { EXCALIDRAW_ASSET_PATH: string }).EXCALIDRAW_ASSET_PATH;
const face = new FontFace(
  "Excalifont",
  `url(${fontBase}fonts/Excalifont/Excalifont-Regular-a88b72a24fb54c9f94e3b5fdaa7481c9.woff2)`,
);
face.load().then((f) => document.fonts.add(f)).catch(() => undefined);

createRoot(document.getElementById("root")!).render(<App />);
