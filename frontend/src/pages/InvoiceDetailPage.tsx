import { useParams, Link } from 'react-router-dom';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { AppHeader } from '../components/AppHeader';
import { SuggestionPanel } from '../components/SuggestionPanel';
import { useAuth } from '../hooks/useAuth';
import { fetchInvoiceDetail, requestSuggestions } from '../services/apiClient';
import { formatCurrency } from '../services/formatters';

export function InvoiceDetailPage() {
  const { invoiceId } = useParams<{ invoiceId: string }>();
  const { token } = useAuth();
  const queryClient = useQueryClient();

  const { data: invoice, isLoading } = useQuery({
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

        {isLoading || !invoice ? (
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
            </section>
            <SuggestionPanel
              suggestions={suggestionsQuery.data ?? []}
              invoiceTotal={invoice.total}
              currency={invoice.currency}
              isRefreshing={suggestionsQuery.isRefetching}
              onRefresh={async () => {
                if (!token || !invoiceId) {
                  return;
                }
                await requestSuggestions(token, invoiceId);
                await queryClient.invalidateQueries({ queryKey: ['suggestions', invoiceId] });
              }}
            />
          </div>
        )}
      </main>
    </div>
  );
}
