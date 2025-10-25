import { AISuggestion } from '../types/invoice';
import { formatCurrency } from '../services/formatters';

interface SuggestionPanelProps {
  suggestions: AISuggestion[];
  invoiceTotal: number;
  currency: string;
  onRefresh?: () => Promise<void>;
  isRefreshing?: boolean;
  // Handler invoked when user selects a suggestion: (lineNumber, accountCode)
  onSelect?: (lineNumber: number, accountCode: string) => Promise<void>;
  isSelecting?: boolean;
  // When true, render a compact horizontal row suitable to be placed under the invoice summary
  horizontal?: boolean;
}

export function SuggestionPanel({
  suggestions,
  invoiceTotal,
  currency,
  onRefresh,
  isRefreshing,
  onSelect,
  isSelecting,
  horizontal = false
}: SuggestionPanelProps) {
  // Group suggestions by line number (use 0 for null/undefined)
  const suggestionsByLine = suggestions.reduce((acc: Record<number, AISuggestion[]>, s) => {
    const line = s.lineNumber ?? 0;
    if (!acc[line]) acc[line] = [];
    acc[line].push(s);
    return acc;
  }, {} as Record<number, AISuggestion[]>);

  const lineKeys = Object.keys(suggestionsByLine).sort((a, b) => Number(a) - Number(b));

  if (horizontal) {
    // Compact horizontal layout for selection under the invoice summary
    return (
      <div className="mt-4">
        {suggestions.length === 0 ? (
          <p className="text-sm text-slate-500">No hay sugerencias registradas para esta factura.</p>
        ) : (
          <div className="-mx-2 flex gap-3 overflow-x-auto py-2">
            {suggestions.map((suggestion, idx) => (
              <div
                key={`${suggestion.accountCode}-${suggestion.lineNumber ?? 0}-${idx}`}
                // fixed width and prevent growing so long text wraps inside the card instead of expanding horizontally
                className={`flex-shrink-0 w-64 rounded border p-3 ${suggestion.isSelected ? 'border-blue-300 bg-blue-50' : 'border-slate-100 bg-white'}`}
              >
                <div className="flex items-center justify-between">
                  <p className="text-sm font-semibold text-slate-900">{suggestion.accountCode}</p>
                  {suggestion.isSelected && (
                    <span className="rounded bg-blue-100 px-2 py-0.5 text-xs font-medium text-blue-700">Seleccionada ✓</span>
                  )}
                </div>
                <p className="mt-1 text-sm text-slate-600 whitespace-normal break-words">{suggestion.rationale}</p>
                <div className="mt-3 flex items-center justify-between gap-2">
                  <span className="text-xs uppercase text-slate-500">{(suggestion.confidence * 100).toFixed(0)}%</span>
                  <button
                    type="button"
                    onClick={async () => {
                      if (!onSelect || suggestion.lineNumber == null) return;
                      await onSelect(suggestion.lineNumber, suggestion.accountCode);
                    }}
                    disabled={!onSelect || suggestion.isSelected || suggestion.lineNumber == null || Boolean(isSelecting)}
                    className="rounded bg-emerald-600 px-2 py-1 text-xs font-semibold text-white hover:bg-emerald-500 disabled:opacity-50"
                  >
                    {suggestion.isSelected ? 'Seleccionada' : 'Seleccionar'}
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    );
  }

  // Full vertical panel (used previously as sidebar)
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
            {isRefreshing ? 'Recalculando…' : 'Recalcular'}
          </button>
        )}
      </div>

      <div className="mt-4 space-y-3">
        {suggestions.length === 0 ? (
          <p className="text-sm text-slate-500">No hay sugerencias registradas para esta factura.</p>
        ) : (
          lineKeys.map((lineKey) => {
            const lineNum = Number(lineKey);
            const group = suggestionsByLine[lineNum];
            return (
              <div key={`line-${lineKey}`} className="space-y-2">
                <h4 className="text-sm font-semibold text-slate-700">Línea {lineNum === 0 ? '—' : lineNum}</h4>
                <div className="space-y-2">
                  {group.map((suggestion, idx) => (
                    <div
                      key={`${suggestion.accountCode}-${lineNum}-${idx}`}
                      className="rounded border border-slate-100 p-3 flex items-start justify-between gap-4"
                    >
                      <div className="flex-1">
                        <div className="flex items-center gap-3">
                          <p className="text-sm font-semibold text-slate-900">{suggestion.accountCode}</p>
                          {suggestion.isSelected && (
                            <span className="rounded bg-blue-100 px-2 py-0.5 text-xs font-medium text-blue-700">Seleccionada ✓</span>
                          )}
                        </div>
                        <p className="mt-1 text-sm text-slate-600">{suggestion.rationale}</p>
                        <p className="mt-2 text-xs uppercase text-slate-500">
                          Confianza: {(suggestion.confidence * 100).toFixed(0)}%
                        </p>
                      </div>
                      <div className="flex flex-col items-end gap-2">
                        {suggestion.lineNumber != null && (
                          <span className="text-xs text-slate-500">Línea #{suggestion.lineNumber}</span>
                        )}
                        <button
                          type="button"
                          onClick={async () => {
                            if (!onSelect || suggestion.lineNumber == null) return;
                            await onSelect(suggestion.lineNumber, suggestion.accountCode);
                          }}
                          disabled={!onSelect || suggestion.isSelected || suggestion.lineNumber == null || Boolean(isSelecting)}
                          className="rounded bg-emerald-600 px-3 py-1 text-xs font-semibold text-white hover:bg-emerald-500 disabled:opacity-50"
                        >
                          {suggestion.isSelected ? 'Seleccionada' : 'Seleccionar'}
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            );
          })
        )}
      </div>

      <footer className="mt-6 rounded bg-slate-50 px-4 py-3 text-sm text-slate-600">
        Total factura: {formatCurrency(invoiceTotal, currency)}
      </footer>
    </aside>
  );
}
