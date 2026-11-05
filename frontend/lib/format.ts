import type { CargoType, SelectionStatus } from "@/lib/api/types";

// The API sends money and miles as decimal strings; format them for display only.
export function formatMoney(value: string | null | undefined): string {
  if (value == null) return "—";
  return `$${Number(value).toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
}

export function formatMiles(value: string | null | undefined): string {
  if (value == null) return "Bilinmiyor";
  // No thousands separator, so tables match the backend's reason texts ("1190 mil").
  return `${Number(value).toLocaleString("tr-TR", { useGrouping: false })} mil`;
}

// The backend stores UTC timestamps without a zone suffix; treat them as UTC.
export function formatDateTime(iso: string): string {
  const date = new Date(/[zZ]|[+-]\d\d:\d\d$/.test(iso) ? iso : `${iso}Z`);
  return date.toLocaleString("tr-TR", { dateStyle: "short", timeStyle: "short" });
}

export const CARGO_LABELS: Record<CargoType, string> = {
  Dry: "Kuru yük (Dry)",
  Reefer: "Soğutmalı (Reefer)",
  Hazardous: "Tehlikeli madde (Hazardous)",
};

export const STATUS_LABELS: Record<SelectionStatus, string> = {
  selected: "Taşıyıcı seçildi",
  no_carrier: "Uygun taşıyıcı yok",
  unknown_route: "Rota mesafesi bilinmiyor",
  invalid_order: "Geçersiz sipariş",
};

export const DISTANCE_SOURCE_LABELS: Record<"table" | "api", string> = {
  table: "Case tablosu",
  api: "Mesafe API",
};
