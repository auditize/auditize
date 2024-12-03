import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";
import tsconfigPaths from "vite-tsconfig-paths";

export default defineConfig({
  plugins: [react(), tsconfigPaths()],
  resolve: {
    alias: {
      // FIXME: workaround regression introduced in @tabler/icons 3.19.0
      // (see https://github.com/tabler/tabler-icons/issues/1233#issuecomment-2428245119)
      // /esm/icons/index.mjs only exports the icons statically, so no separate chunks are created
      "@tabler/icons-react": "@tabler/icons-react/dist/esm/icons/index.mjs",
    },
  },
  server: {
    proxy: {
      "/api/": "http://localhost:8000",
    },
  },
  build: {
    outDir: "dist/app",
  },
  test: {
    globals: true,
    environment: "jsdom",
    setupFiles: "./vitest.setup.mjs",
  },
});
