import { AISuggestion } from '../types/invoice';
import { formatCurrency } from '../services/formatters';

interface SuggestionPanelProps {
  suggestions: AISuggestion[];
  invoiceTotal: number;
  currency: string;
  onRefresh?: () => Promise<void>;
  isRefreshing?: boolean;
  horizontal?: boolean;
}

export function SuggestionPanel({
  suggestions,
  invoiceTotal,
  currency,
  onRefresh,
  isRefreshing,
  horizontal = false
}: SuggestionPanelProps) {
  if (horizontal) {
    const sortedSuggestions = [...suggestions].sort((a, b) => b.confidence - a.confidence);
    
    return (
      <div className="mt-4">
        {sortedSuggestions.length === 0 ? (
          <p className="text-sm text-slate-500">No hay sugerencias registradas para esta factura.</p>
        ) : (
          <div className="flex gap-3 overflow-x-auto py-2">
            {sortedSuggestions.map((suggestion, idx) => (
              <div
                key={`${suggestion.accountCode}-${idx}`}
                className="flex-shrink-0 w-64 rounded border border-slate-200 bg-white p-3"
              >
                <div className="flex items-center justify-between">
                  <p className="text-sm font-semibold text-slate-900">{suggestion.accountCode}</p>
                  <span className="rounded bg-slate-100 px-2 py-0.5 text-xs font-medium text-slate-700">
                    {(suggestion.confidence * 100).toFixed(0)}%
                  </span>
                </div>
                <p className="mt-2 text-sm text-slate-600 whitespace-normal break-words line-clamp-3">
                  {suggestion.rationale}
                </p>
              </div>
            ))}
          </div>
        )}
      </div>
    );
  }

  return (
    <aside className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-base font-semibold text-slate-900">Sugerencias contables</h2>
        </div>
        {onRefresh && (
          <button
            type="button"
            onClick={onRefresh}
            disabled={Boolean(isRefreshing)}
            className="rounded bg-indigo-600 px-3 py-1.5 text-xs font-semibold text-white hover:bg-indigo-500 disabled:opacity-50"
          >
            {isRefreshing ? 'Recalculando...' : 'Recalcular'}
          </button>
        )}
      </div>

      <div className="mt-4 space-y-3">
        {suggestions.length === 0 ? (
          <p className="text-sm text-slate-500">No hay sugerencias registradas para esta factura.</p>
        ) : (
          suggestions.map((suggestion, idx) => (
            <div
              key={`${suggestion.accountCode}-${idx}`}
              className="rounded border border-slate-100 p-3"
            >
              <div className="flex items-center justify-between">
                <p className="text-sm font-semibold text-slate-900">{suggestion.accountCode}</p>
                <span className="text-xs uppercase text-slate-500">
                  Confianza: {(suggestion.confidence * 100).toFixed(0)}%
                </span>
              </div>
              <p className="mt-1 text-sm text-slate-600">{suggestion.rationale}</p>
            </div>
          ))
        )}
      </div>

      <footer className="mt-6 rounded bg-slate-50 px-4 py-3 text-sm text-slate-600">
        Total factura: {formatCurrency(invoiceTotal, currency)}
      </footer>
    </aside>
  );
}
