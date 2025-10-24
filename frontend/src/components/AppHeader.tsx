import { useAuth } from '../hooks/useAuth';

export function AppHeader() {
  const { userEmail, logout } = useAuth();

  return (
    <header className="flex items-center justify-between border-b border-slate-200 bg-white px-6 py-4 shadow-sm">
      <div>
        <h1 className="text-lg font-semibold text-slate-900">Panel de facturación</h1>
        <p className="text-sm text-slate-500">Facturas UBL provenientes de la carpeta assessment-files</p>
      </div>
      <div className="flex items-center gap-3">
        <span className="text-sm text-slate-600">{userEmail}</span>
        <button
          type="button"
          onClick={logout}
          className="rounded border border-slate-300 px-3 py-1 text-sm font-medium text-slate-700 hover:bg-slate-100"
        >
          Cerrar sesión
        </button>
      </div>
    </header>
  );
}
