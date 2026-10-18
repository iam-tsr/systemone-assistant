/// <reference types="vite/client" />

const base = ("https://systemone-assistant.onrender.com").replace(/\/$/, "");

export function apiUrl(path: string): string {
  return `${base}${path.startsWith("/") ? path : `/${path}`}`;
}