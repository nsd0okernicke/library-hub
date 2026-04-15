import { useEffect } from 'react';
import { cn } from '@/lib/utils';

interface ToastProps {
  message: string;
  type: 'success' | 'error';
  onDismiss: () => void;
}

/** Auto-dismiss duration in milliseconds. */
const TOAST_DURATION_MS = 4000;

/**
 * Transient notification banner that auto-dismisses after TOAST_DURATION_MS.
 * Uses aria-live so screen readers announce the message without stealing focus.
 */
export function Toast({ message, type, onDismiss }: ToastProps): JSX.Element {
  useEffect(() => {
    const timer = setTimeout(onDismiss, TOAST_DURATION_MS);
    return () => clearTimeout(timer);
  }, [onDismiss]);

  return (
    <div
      role={type === 'error' ? 'alert' : 'status'}
      aria-live={type === 'error' ? 'assertive' : 'polite'}
      className={cn(
        'fixed bottom-4 right-4 flex items-center gap-3 rounded-lg px-4 py-3 text-sm text-white shadow-lg',
        type === 'success' ? 'bg-green-600' : 'bg-red-600'
      )}
    >
      <span>{message}</span>
      <button
        type="button"
        onClick={onDismiss}
        aria-label="Dismiss notification"
        className="ml-2 font-bold opacity-75 hover:opacity-100"
      >
        ×
      </button>
    </div>
  );
}

