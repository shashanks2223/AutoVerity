import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import { fileURLToPath } from "node:url";

const frontendRoot = fileURLToPath(new URL(".", import.meta.url));

export default defineConfig({
  root: frontendRoot,

  plugins: [react()],

  server: {
    host: "127.0.0.1",
    port: 5173,

    watch: {
      usePolling: true,
      ignored: [
        "**/node_modules/**",
        "**/.git/**",
        "**/backend/**",
        "**/uploads/**",
        "**/AppData/**",
      ],
    },
  },
});