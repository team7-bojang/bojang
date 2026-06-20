/** Date -> 'YYYY-MM-DD' (로컬 기준). */
export function toISODate(date: Date): string {
  const offset = date.getTimezoneOffset();
  return new Date(date.getTime() - offset * 60_000).toISOString().slice(0, 10);
}
