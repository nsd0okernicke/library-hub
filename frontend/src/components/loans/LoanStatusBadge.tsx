import { cn } from '@/lib/utils';
import type { LoanStatus } from '@/types';

interface LoanStatusBadgeProps {
  status: LoanStatus;
}

const STATUS_STYLES: Record<LoanStatus, string> = {
  PENDING: 'bg-gray-100 text-gray-700',
  ACTIVE: 'bg-green-100 text-green-700',
  RETURNED: 'bg-blue-100 text-blue-700',
  REJECTED: 'bg-red-100 text-red-700',
};

/** Displays a colour-coded loan status badge with text label. */
export function LoanStatusBadge({ status }: LoanStatusBadgeProps): JSX.Element {
  return (
    <span
      className={cn(
        'inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium',
        STATUS_STYLES[status]
      )}
    >
      {status}
    </span>
  );
}

