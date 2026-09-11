import react from "@vitejs/plugin-react";
import { resolve } from "path";
import { defineConfig } from "vite";

export default defineConfig({
  plugins: [react()],
  resolve: {
    tsconfigPaths: true,
  },
  define: { "process.env.NODE_ENV": '"production"' },
  build: {
    outDir: "dist/lib",
    lib: {
      entry: resolve(import.meta.dirname, "src/web-component.tsx"),
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
