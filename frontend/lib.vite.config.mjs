import react from "@vitejs/plugin-react";
import { resolve } from "path";
import { defineConfig } from "vite";
import tsconfigPaths from "vite-tsconfig-paths";

export default defineConfig({
  plugins: [react(), tsconfigPaths()],
  define: { "process.env.NODE_ENV": '"production"' },
  build: {
    outDir: "dist/lib",
    lib: {
      entry: resolve(__dirname, "src/web-component.tsx"),
      name: "AuditizeWebComponent",
      fileName: "auditize-web-component",
    },
  },
  test: {
    globals: true,
    environment: "jsdom",
    setupFiles: "./vitest.setup.mjs",
  },
});
