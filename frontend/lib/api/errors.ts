/** Turn a FastAPI error body (409/404 string detail, or a 422 list) into readable Turkish text. */
export function apiErrorMessage(error: unknown, fallback = "İşlem başarısız oldu."): string {
  const detail = (error as { detail?: unknown } | undefined)?.detail;
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) {
    const messages = detail
      .map((d) => (typeof d?.msg === "string" ? d.msg.replace(/^Value error, /, "") : null))
      .filter(Boolean);
    if (messages.length) return messages.join(" · ");
  }
  return fallback;
}
