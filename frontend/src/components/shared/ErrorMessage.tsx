interface ErrorMessageProps {
  message: string;
}

/** Displays a user-friendly error message. */
export function ErrorMessage({ message }: ErrorMessageProps): JSX.Element {
  return (
    <div role="alert" className="rounded-md border border-red-200 bg-red-50 p-4 text-red-700">
      <p className="font-medium">Something went wrong</p>
      <p className="mt-1 text-sm">{message}</p>
    </div>
  );
}

