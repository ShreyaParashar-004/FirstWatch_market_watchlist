/** Formatting helpers. These never invent values — null input returns null. */

export function formatDateTime(value: string | null | undefined): string | null {
  if (!value) return null;
  const date = new Date(value.endsWith("Z") || value.includes("+") ? value : `${value}Z`);
  if (Number.isNaN(date.getTime())) return null;
  return date.toLocaleString(undefined, {
    year: "numeric",
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export function formatDate(value: string | null | undefined): string | null {
  if (!value) return null;
  const date = new Date(value.endsWith("Z") || value.includes("+") ? value : `${value}Z`);
  if (Number.isNaN(date.getTime())) return null;
  return date.toLocaleDateString(undefined, { year: "numeric", month: "short", day: "numeric" });
}

export function hoursSince(value: string | null | undefined): number | null {
  if (!value) return null;
  const date = new Date(value.endsWith("Z") || value.includes("+") ? value : `${value}Z`);
  if (Number.isNaN(date.getTime())) return null;
  return (Date.now() - date.getTime()) / 3_600_000;
}

export function formatPrice(price: number | null | undefined, currency: string | null | undefined) {
  if (price === null || price === undefined || Number.isNaN(price)) return null;
  try {
    if (currency) {
      return new Intl.NumberFormat(undefined, { style: "currency", currency }).format(price);
    }
  } catch {
    /* unknown currency code */
  }
  return price.toLocaleString(undefined, { maximumFractionDigits: 4 });
}

export function formatPct(value: number | null | undefined) {
  if (value === null || value === undefined || Number.isNaN(value)) return null;
  const sign = value > 0 ? "+" : "";
  return `${sign}${value.toFixed(2)}%`;
}

export function titleize(value: string | null | undefined): string | null {
  if (!value) return null;
  return value
    .replace(/[_-]+/g, " ")
    .replace(/\b\w/g, (c) => c.toUpperCase())
    .trim();
}

export function formatLastDataIST(value: string | null | undefined): string | null {
  if (!value) return null;
  const date = new Date(value.endsWith("Z") || value.includes("+") ? value : `${value}Z`);
  if (Number.isNaN(date.getTime())) return null;
  const formatted = new Intl.DateTimeFormat("en-US", {
    timeZone: "Asia/Kolkata",
    month: "short",
    day: "numeric",
    hour: "numeric",
    minute: "2-digit",
    hour12: true,
  }).format(date);
  return `${formatted} IST`;
}

/** Restrained attention levels derived only from backend-provided fields. */
export type AttentionLevel = "normal" | "worth_watching" | "meaningful" | "high";

export function attentionLevel(input: {
  potential_impact?: string | null;
  confidence?: number | null;
  signal_kind?: string | null;
}): AttentionLevel {
  const impact = (input.potential_impact ?? "").toLowerCase();
  const confidence = typeof input.confidence === "number" ? input.confidence : null;
  const early = (input.signal_kind ?? "").toLowerCase() === "early";

  if (impact === "high" && (confidence === null || confidence >= 0.6)) return "high";
  if (impact === "high") return "meaningful";
  if (impact === "medium" && (confidence ?? 0) >= 0.7) return "meaningful";
  if (impact === "medium" || early) return "worth_watching";
  return "normal";
}

export const attentionLabel: Record<AttentionLevel, string> = {
  normal: "Normal",
  worth_watching: "Worth watching",
  meaningful: "Meaningful",
  high: "High attention",
};
