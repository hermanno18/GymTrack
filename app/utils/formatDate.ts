/**
 * SQLite stores performedAt as either a date-only string ("2026-10-07",
 * from the HTML date input) or a full "YYYY-MM-DD HH:MM:SS" UTC timestamp
 * (from the `current_timestamp` default).
 *
 * These need different handling: a full timestamp is a real UTC instant
 * and should convert to local time normally. A date-only value has no
 * time/timezone info at all -- treating it as UTC midnight and letting
 * the browser convert to local time rolls it back a calendar day in any
 * negative-UTC-offset timezone (e.g. "2026-10-07" became "Oct 6, 8pm" in
 * UTC-4). It must be built from local date parts instead.
 */
export function parseSessionDate(raw: string): Date {
  if (raw.includes(' ')) {
    return new Date(`${raw.replace(' ', 'T')}Z`)
  }
  const [year, month, day] = raw.split('-').map(Number)
  return new Date(year, month - 1, day)
}

export function formatSessionDate(raw: string, opts: Intl.DateTimeFormatOptions): string {
  return parseSessionDate(raw).toLocaleString(undefined, opts)
}
