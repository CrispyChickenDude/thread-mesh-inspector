import { defineConfig } from "vite";

export default defineConfig({
  // Proxy API calls to the backend during local dev
  server: {
    proxy: {
      "/api": "http://localhost:8099",
    },
  },
  build: {
    outDir: "dist",
    sourcemap: true,
  },
});
