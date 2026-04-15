import { useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { useNavigate } from 'react-router-dom';
import { ErrorBoundary } from '@/components/shared/ErrorBoundary';
import { useUser } from '@/hooks/useUser';

const registerSchema = z.object({
  name: z.string().min(1, 'Name is required'),
  email: z
    .string()
    .min(1, 'Email is required')
    .email('Must be a valid email address'),
});

type RegisterFormData = z.infer<typeof registerSchema>;

interface RegisterApiResponse {
  user_id: string;
  name: string;
  email: string;
}

/** FE-6 – New user registration form. */
export default function RegisterPage(): JSX.Element {
  const navigate = useNavigate();
  const { setUser } = useUser();
  const [apiError, setApiError] = useState<string | null>(null);

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<RegisterFormData>({
    resolver: zodResolver(registerSchema),
  });

  const onSubmit = async (data: RegisterFormData): Promise<void> => {
    setApiError(null);
    try {
      const res = await fetch('/api/loan/users', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data),
      });
      if (res.status === 409) {
        setApiError('This e-mail is already registered');
        return;
      }
      if (!res.ok) {
        setApiError('Registration failed. Please try again.');
        return;
      }
      const body = (await res.json()) as RegisterApiResponse;
      setUser({ userId: body.user_id, name: body.name, email: body.email });
      navigate('/');
    } catch {
      setApiError('Network error. Please try again.');
    }
  };

  return (
    <ErrorBoundary>
      <main className="mx-auto max-w-lg px-4 py-8">
        <h1 className="mb-6 text-2xl font-bold">Register</h1>
        <form onSubmit={handleSubmit(onSubmit)} noValidate>
          <div className="mb-4">
            <label htmlFor="name" className="block mb-1 font-medium">
              Name
            </label>
            <input
              id="name"
              type="text"
              autoComplete="name"
              aria-describedby={errors.name ? 'name-error' : undefined}
              className="w-full rounded border px-3 py-2"
              {...register('name')}
            />
            {errors.name && (
              <p id="name-error" role="alert" className="mt-1 text-sm text-red-600">
                {errors.name.message}
              </p>
            )}
          </div>

          <div className="mb-4">
            <label htmlFor="email" className="block mb-1 font-medium">
              Email
            </label>
            <input
              id="email"
              type="email"
              autoComplete="email"
              aria-describedby={errors.email ? 'email-error' : undefined}
              className="w-full rounded border px-3 py-2"
              {...register('email')}
            />
            {errors.email && (
              <p id="email-error" role="alert" className="mt-1 text-sm text-red-600">
                {errors.email.message}
              </p>
            )}
          </div>

          {apiError && (
            <p role="alert" className="mb-4 text-sm text-red-600">
              {apiError}
            </p>
          )}

          <button
            type="submit"
            disabled={isSubmitting}
            className="rounded bg-blue-600 px-4 py-2 text-white disabled:bg-gray-400"
          >
            {isSubmitting ? 'Registering…' : 'Register'}
          </button>
        </form>
      </main>
    </ErrorBoundary>
  );
}


