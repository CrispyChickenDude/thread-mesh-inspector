import { defineConfig } from "vite";

export default defineConfig({
  // Relative base so built asset URLs work under the HA ingress sub-path
  // (e.g. /api/hassio_ingress/<token>/) instead of resolving to the site root.
  base: "./",
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
