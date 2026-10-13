import react from "@vitejs/plugin-react";
import { defineConfig, loadEnv } from "vite";
import tailwindcss from "@tailwindcss/vite";
import path from "node:path";

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), "");
  const apiOrigin = env.API_ORIGIN ?? "http://127.0.0.1:8001";
  const host = env.FRONTEND_HOST ?? "localhost";
  const port = Number(env.FRONTEND_PORT ?? 3000);

  return {
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
    preview: {
      host,
      port,
      proxy: {
        "/api": {
          target: apiOrigin,
          changeOrigin: true,
        },
      },
    },
  };
});
