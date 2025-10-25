import { useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { AppHeader } from '../components/AppHeader';
import { SuggestionPanel } from '../components/SuggestionPanel';
import { useAuth } from '../hooks/useAuth';
import { fetchInvoiceDetail, requestSuggestions, regenSuggestions, selectSuggestion } from '../services/apiClient';
import { formatCurrency } from '../services/formatters';

export function InvoiceDetailPage() {
  const { invoiceId } = useParams<{ invoiceId: string }>();
  const { token } = useAuth();
  const queryClient = useQueryClient();
  const [feedback, setFeedback] = useState<{ tone: 'error' | 'success'; text: string } | null>(null);

  const {
    data: invoice,
    isLoading,
    isError,
    error
  } = useQuery({
    queryKey: ['invoice', invoiceId],
    queryFn: async () => {
      if (!token || !invoiceId) {
        return null;
      }
      return fetchInvoiceDetail(token, invoiceId);
    },
    enabled: Boolean(token && invoiceId)
  });

  const suggestionsQuery = useQuery({
    queryKey: ['suggestions', invoiceId],
    queryFn: async () => {
      if (!token || !invoiceId) {
        return [];
      }
      return requestSuggestions(token, invoiceId);
    },
    enabled: Boolean(token && invoiceId)
  });

  return (
    <div className="min-h-screen bg-slate-100">
      <AppHeader />
      <main className="mx-auto max-w-5xl space-y-6 px-6 py-8">
        <Link to="/" className="text-sm text-indigo-600 hover:text-indigo-500">
          ← Volver al listado
        </Link>

        {feedback && (
          <div
            className={
              feedback.tone === 'error'
                ? 'rounded border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700'
                : 'rounded border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-700'
            }
          >
            {feedback.text}
          </div>
        )}

        {isError ? (
          <p className="text-sm text-red-600">
            {error instanceof Error
              ? `No se pudo recuperar la factura: ${error.message}`
              : 'No se pudo recuperar la factura solicitada.'}
          </p>
        ) : isLoading || !invoice ? (
          <p className="text-sm text-slate-500">Cargando factura…</p>
        ) : (
          <div className="grid grid-cols-1 gap-6 lg:grid-cols-[2fr_1fr]">
            <section className="space-y-6">
              <article className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
                <header className="flex flex-wrap items-end justify-between gap-4">
                  <div>
                    <h2 className="text-xl font-semibold text-slate-900">{invoice.supplierName}</h2>
                    <p className="text-sm text-slate-500">Factura #{invoice.externalId}</p>
                  </div>
                  <div className="text-right">
                    <p className="text-xs uppercase text-slate-500">Total</p>
                    <p className="text-lg font-semibold text-slate-900">
                      {formatCurrency(invoice.total, invoice.currency)}
                    </p>
                  </div>
                </header>

                <div className="mt-6">
                  <h3 className="text-sm font-semibold text-slate-700">Detalle de líneas</h3>
                  <table className="mt-3 w-full divide-y divide-slate-200 text-sm">
                    <thead className="bg-slate-50">
                      <tr>
                        <th className="px-3 py-2 text-left font-medium text-slate-500">Descripción</th>
                        <th className="px-3 py-2 text-right font-medium text-slate-500">Cantidad</th>
                        <th className="px-3 py-2 text-right font-medium text-slate-500">Precio unitario</th>
                        <th className="px-3 py-2 text-right font-medium text-slate-500">Impuestos</th>
                        <th className="px-3 py-2 text-right font-medium text-slate-500">Total</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100">
                      {invoice.lines.map((line) => (
                        <tr key={line.id}>
                          <td className="px-3 py-2 text-slate-700">{line.description}</td>
                          <td className="px-3 py-2 text-right text-slate-600">{line.quantity}</td>
                          <td className="px-3 py-2 text-right text-slate-600">
                            {formatCurrency(line.unitPrice, invoice.currency)}
                          </td>
                          <td className="px-3 py-2 text-right text-slate-600">
                            {formatCurrency(line.taxAmount, invoice.currency)}
                          </td>
                          <td className="px-3 py-2 text-right font-medium text-slate-700">
                            {formatCurrency(line.total, invoice.currency)}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>

                <div className="mt-6">
                  <h3 className="text-sm font-semibold text-slate-700">Impuestos calculados</h3>
                  <ul className="mt-2 space-y-2 text-sm text-slate-600">
                    {invoice.taxes.map((tax) => (
                      <li key={tax.type} className="flex items-center justify-between rounded border border-slate-100 px-3 py-2">
                        <span>{tax.type}</span>
                        <span>{formatCurrency(tax.amount, invoice.currency)}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              </article>

                {/* Suggestion selection row: moved under the invoice summary as a horizontal list */}
                <SuggestionPanel
                  suggestions={suggestionsQuery.data ?? []}
                  invoiceTotal={invoice.total}
                  currency={invoice.currency}
                  horizontal
                  onSelect={async (lineNumber: number, accountCode: string) => {
                    if (!token || !invoiceId) return;
                    try {
                      await selectSuggestion(token, invoiceId, lineNumber, accountCode);
                      await queryClient.invalidateQueries({ queryKey: ['suggestions', invoiceId] });
                      setFeedback({ tone: 'success', text: 'Sugerencia seleccionada.' });
                    } catch (err) {
                      const message = err instanceof Error ? err.message : 'No fue posible seleccionar la sugerencia.';
                      setFeedback({ tone: 'error', text: message });
                    }
                  }}
                />
              </section>

              {/* Right column: show only the selected suggestion and the Recalcular button */}
              <aside>
                {suggestionsQuery.isError && (
                  <p className="text-sm text-red-600">
                    No se pudieron cargar las sugerencias iniciales. Puedes intentar recalcularlas manualmente.
                  </p>
                )}

                <div className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
                  <div className="flex items-center justify-between">
                    <h2 className="text-base font-semibold text-slate-900">Sugerencia seleccionada</h2>
                    <button
                      type="button"
                      onClick={async () => {
                        if (!token || !invoiceId) return;
                        try {
                          await regenSuggestions(token, invoiceId);
                          await queryClient.invalidateQueries({ queryKey: ['suggestions', invoiceId] });
                          setFeedback({ tone: 'success', text: 'Se recalcularon las sugerencias contables.' });
                        } catch (err) {
                          const message = err instanceof Error ? err.message : 'No fue posible recalcular las sugerencias.';
                          setFeedback({ tone: 'error', text: message });
                        }
                      }}
                      disabled={suggestionsQuery.isRefetching}
                      className="rounded bg-indigo-600 px-3 py-1.5 text-xs font-semibold text-white hover:bg-indigo-500 disabled:opacity-50"
                    >
                      {suggestionsQuery.isRefetching ? 'Recalculando…' : 'Recalcular'}
                    </button>
                  </div>

                  <div className="mt-4">
                    {(() => {
                      const selected = (suggestionsQuery.data ?? []).find((s) => s.isSelected);
                      if (!selected) {
                        return <p className="text-sm text-slate-500">No se ha escogido ninguna.</p>;
                      }
                      return (
                        <div className="rounded border border-slate-100 p-3">
                          <p className="text-sm font-semibold text-slate-900">{selected.accountCode}</p>
                          <p className="mt-1 text-sm text-slate-600">{selected.rationale}</p>
                          <p className="mt-2 text-xs uppercase text-slate-500">Confianza: {(selected.confidence * 100).toFixed(0)}%</p>
                          {selected.lineNumber != null && (
                            <p className="mt-1 text-xs text-slate-500">Línea #{selected.lineNumber}</p>
                          )}
                        </div>
                      );
                    })()}
                  </div>
                </div>
              </aside>
          </div>
        )}
      </main>
    </div>
  );
}
