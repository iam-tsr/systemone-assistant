/// <reference types="vite/client" />

const raw = import.meta.env.VITE_API_URL as string | undefined;

// Empty string from `VITE_API_URL=` in deploy.yml should fall back.
const base = (raw?.trim() || "https://systemone-assistant.onrender.com").replace(/\/$/, "");

export function apiUrl(path: string): string {
  return `${base}${path.startsWith("/") ? path : `/${path}`}`;
}
