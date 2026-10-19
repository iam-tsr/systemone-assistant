/// <reference types="vite/client" />

const raw = import.meta.env.VITE_API_URL as string | undefined;

const base = raw?.trim().replace(/\/$/, "");

export function apiUrl(path: string): string {
  return `${base}${path.startsWith("/") ? path : `/${path}`}`;
}