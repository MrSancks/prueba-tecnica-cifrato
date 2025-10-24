import { AISuggestion } from '../types/invoice';
import { formatCurrency } from '../services/formatters';

interface SuggestionPanelProps {
  suggestions: AISuggestion[];
  invoiceTotal: number;
  currency: string;
  onRefresh: () => Promise<void>;
  isRefreshing: boolean;
}

export function SuggestionPanel({ suggestions, invoiceTotal, currency, onRefresh, isRefreshing }: SuggestionPanelProps) {
  return (
    <aside className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-base font-semibold text-slate-900">Sugerencias contables</h2>
          <p className="text-sm text-slate-500">
            Basadas en los XML y PDF reales de <code>backend/app/assessment-files/</code> para afinar la cuenta contable.
          </p>
        </div>
        <button
          type="button"
          onClick={onRefresh}
          disabled={isRefreshing}
          className="rounded bg-indigo-600 px-3 py-1.5 text-xs font-semibold text-white hover:bg-indigo-500 disabled:opacity-50"
        >
          {isRefreshing ? 'Recalculando…' : 'Recalcular'}
        </button>
      </div>
      <div className="mt-4 space-y-3">
        {suggestions.length === 0 ? (
          <p className="text-sm text-slate-500">No hay sugerencias registradas para esta factura.</p>
        ) : (
          suggestions.map((suggestion) => (
            <div key={suggestion.accountCode} className="rounded border border-slate-100 p-3">
              <p className="text-sm font-semibold text-slate-900">{suggestion.accountCode}</p>
              <p className="mt-1 text-sm text-slate-600">{suggestion.rationale}</p>
              <p className="mt-2 text-xs uppercase text-slate-500">
                Confianza: {(suggestion.confidence * 100).toFixed(0)}%
              </p>
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
