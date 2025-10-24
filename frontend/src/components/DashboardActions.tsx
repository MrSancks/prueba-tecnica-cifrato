interface DashboardActionsProps {
  onOpenUpload: () => void;
  onExport: () => Promise<void>;
  isExporting: boolean;
}

export function DashboardActions({ onOpenUpload, onExport, isExporting }: DashboardActionsProps) {
  return (
    <div className="flex flex-wrap items-center justify-between gap-3 rounded-lg border border-slate-200 bg-white px-4 py-3 shadow-sm">
      <div>
        <h2 className="text-base font-semibold text-slate-900">Facturas cargadas</h2>
        <p className="text-sm text-slate-500">Administra las facturas derivadas de los XML y PDF de assessment-files.</p>
      </div>
      <div className="flex items-center gap-2">
        <button
          type="button"
          onClick={onOpenUpload}
          className="rounded border border-slate-300 px-4 py-2 text-sm font-medium text-slate-700 hover:bg-slate-100"
        >
          Subir XML
        </button>
        <button
          type="button"
          onClick={onExport}
          disabled={isExporting}
          className="rounded bg-indigo-600 px-4 py-2 text-sm font-semibold text-white hover:bg-indigo-500 disabled:opacity-50"
        >
          {isExporting ? 'Generando…' : 'Exportar Excel'}
        </button>
      </div>
    </div>
  );
}
