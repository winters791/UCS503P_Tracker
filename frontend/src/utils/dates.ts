// API dates are plain "YYYY-MM-DD" calendar days; keep them out of UTC so a
// week never shifts by a day in the browser's timezone.

export function parseDate(iso: string): Date {
  const [y, m, d] = iso.split("-").map(Number);
  return new Date(y, m - 1, d);
}

export function toISODate(date: Date): string {
  const m = String(date.getMonth() + 1).padStart(2, "0");
  const d = String(date.getDate()).padStart(2, "0");
  return `${date.getFullYear()}-${m}-${d}`;
}

export function addDays(iso: string, days: number): string {
  const date = parseDate(iso);
  date.setDate(date.getDate() + days);
  return toISODate(date);
}

export function formatShort(iso: string): string {
  return parseDate(iso).toLocaleDateString(undefined, { month: "short", day: "numeric" });
}
