import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";
import tailwindcss from "@tailwindcss/vite";
import path from "node:path";
import * as dotenv from "dotenv";

dotenv.config();

const apiOrigin = process.env.API_ORIGIN;
const host = process.env.FRONTEND_HOST;
const port = Number(process.env.FRONTEND_PORT);

export default defineConfig({
  plugins: [react(), tailwindcss()],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
  server: {
    host,
    port,
    proxy: {
      "/api": {
        target: apiOrigin,
        changeOrigin: true,
      },
    },
  },
});
