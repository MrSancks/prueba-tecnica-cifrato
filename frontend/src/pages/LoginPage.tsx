import { useForm } from 'react-hook-form';
import { useLocation, Navigate, type Location } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';

interface LoginFormValues {
  email: string;
  password: string;
}

export function LoginPage() {
  const { register, handleSubmit, formState } = useForm<LoginFormValues>({
    defaultValues: { email: '', password: '' }
  });
  const { login, isAuthenticated } = useAuth();
  const location = useLocation();

  if (isAuthenticated) {
    const from = (location.state as { from?: Location })?.from?.pathname ?? '/';
    return <Navigate to={from} replace />;
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-slate-100">
      <div className="w-full max-w-md rounded-lg bg-white shadow p-8">
        <h1 className="text-2xl font-semibold text-slate-900 mb-6">Iniciar sesión</h1>
        <form
          className="space-y-4"
          onSubmit={handleSubmit(async (values) => {
            await login(values.email, values.password);
          })}
        >
          <label className="block text-sm font-medium text-slate-700">
            Correo electrónico
            <input
              type="email"
              {...register('email', { required: true })}
              className="mt-1 w-full rounded border border-slate-300 px-3 py-2 text-sm focus:border-indigo-500 focus:outline-none"
            />
          </label>
          <label className="block text-sm font-medium text-slate-700">
            Contraseña
            <input
              type="password"
              {...register('password', { required: true })}
              className="mt-1 w-full rounded border border-slate-300 px-3 py-2 text-sm focus:border-indigo-500 focus:outline-none"
            />
          </label>
          <button
            type="submit"
            disabled={formState.isSubmitting}
            className="w-full rounded bg-indigo-600 py-2 text-sm font-semibold text-white hover:bg-indigo-500 disabled:opacity-50"
          >
            {formState.isSubmitting ? 'Ingresando…' : 'Ingresar'}
          </button>
        </form>
      </div>
    </div>
  );
}
