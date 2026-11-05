import "server-only";

import { io } from "next/cache";

import { api } from "./client";
import type { Carrier, Rules, SelectionRecord, SelectionSummary } from "./types";

// Server Components read from the backend on every request: history changes with each selection.
// `io()` keeps these reads out of the prerendered static shell (Cache Components is enabled).

export async function fetchSelections(limit: number): Promise<SelectionSummary[]> {
  await io();
  const { data, error } = await api.GET("/selections", { params: { query: { limit } }, cache: "no-store" });
  if (error || !data) throw new Error("Seçim geçmişi alınamadı");
  return data;
}

export async function fetchCarriers(): Promise<Carrier[]> {
  await io();
  const { data, error } = await api.GET("/carriers", { cache: "no-store" });
  if (error || !data) throw new Error("Taşıyıcılar alınamadı");
  return data;
}

export async function fetchRules(): Promise<Rules> {
  await io();
  const { data, error } = await api.GET("/rules", { cache: "no-store" });
  if (error || !data) throw new Error("Kurallar alınamadı");
  return data;
}

/** The stored Selection, or null when it does not exist. */
export async function fetchSelection(id: number): Promise<SelectionRecord | null> {
  await io();
  const { data, response } = await api.GET("/selections/{selection_id}", {
    params: { path: { selection_id: id } },
    cache: "no-store",
  });
  if (response.status === 404) return null;
  if (!data) throw new Error("Seçim alınamadı");
  return data;
}
