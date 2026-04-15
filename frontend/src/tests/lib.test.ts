import { describe, it, expect } from 'vitest';
import { formatDate, daysOverdue } from '@/lib/formatters';
import { cn } from '@/lib/utils';

describe('formatDate', () => {
  it('formats a valid ISO date string', () => {
    expect(formatDate('2026-04-15')).toMatch(/15/);
  });

  it('returns "—" for null', () => {
    expect(formatDate(null)).toBe('—');
  });

  it('returns "—" for undefined', () => {
    expect(formatDate(undefined)).toBe('—');
  });
});

describe('daysOverdue', () => {
  it('returns a positive number for a past date', () => {
    expect(daysOverdue('2020-01-01')).toBeGreaterThan(0);
  });

  it('returns a negative number for a future date', () => {
    const future = new Date();
    future.setFullYear(future.getFullYear() + 1);
    expect(daysOverdue(future.toISOString().split('T')[0]!)).toBeLessThan(0);
  });
});

describe('cn', () => {
  it('merges class names', () => {
    expect(cn('foo', 'bar')).toBe('foo bar');
  });

  it('resolves Tailwind conflicts', () => {
    expect(cn('p-2', 'p-4')).toBe('p-4');
  });

  it('handles conditional classes', () => {
    expect(cn('base', false && 'ignored', 'added')).toBe('base added');
  });
});

