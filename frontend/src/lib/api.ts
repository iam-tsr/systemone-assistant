/// <reference types="vite/client" />

const raw = import.meta.env.VITE_API_URL as string | undefined;

const base = (raw?.trim().replace(/\/$/, "") ?? "") || undefined;

export function apiUrl(path: string): string {
  const suffix = path.startsWith("/") ? path : `/${path}`;
  return base ? `${base}${suffix}` : suffix;
}