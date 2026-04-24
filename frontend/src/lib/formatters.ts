const DATE_FORMAT = new Intl.DateTimeFormat('en-GB', {
  day: '2-digit',
  month: 'short',
  year: 'numeric',
});

/**
 * Formats an ISO date string to a human-readable short date (e.g. "15 Apr 2026").
 * Returns "—" for null/undefined values.
 */
export function formatDate(isoDate: string | null | undefined): string {
  if (!isoDate) return '—';
  return DATE_FORMAT.format(new Date(isoDate));
}

/**
 * Returns the number of days between today and a given ISO due date.
 * Positive = overdue, negative = days remaining, 0 = due today.
 */
export function daysOverdue(dueDateIso: string): number {
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  const due = new Date(dueDateIso);
  due.setHours(0, 0, 0, 0);
  return Math.floor((today.getTime() - due.getTime()) / (1000 * 60 * 60 * 24));
}

