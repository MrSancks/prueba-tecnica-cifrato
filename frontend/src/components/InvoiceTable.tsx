import { InvoiceSummary } from '../types/invoice';
import { formatCurrency, formatDate } from '../services/formatters';
import { Link } from 'react-router-dom';

interface InvoiceTableProps {
  invoices: InvoiceSummary[];
  onSelect: (invoice: InvoiceSummary) => void;
  selectedId?: string;
}

export function InvoiceTable({ invoices, onSelect, selectedId }: InvoiceTableProps) {
  if (!invoices.length) {
    return (
      <div className="rounded-lg border border-dashed border-slate-300 p-10 text-center text-sm text-slate-500">
        Aún no hay facturas cargadas. Utiliza el botón "Subir XML" para comenzar con los archivos entregados.
      </div>
    );
  }

  return (
    <div className="overflow-hidden rounded-lg border border-slate-200 shadow-sm">
      <table className="min-w-full divide-y divide-slate-200">
        <thead className="bg-slate-50">
          <tr>
            <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide text-slate-500">Proveedor</th>
            <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide text-slate-500">Identificador</th>
            <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide text-slate-500">Fecha</th>
            <th className="px-4 py-3 text-right text-xs font-semibold uppercase tracking-wide text-slate-500">Total</th>
            <th className="px-4 py-3 text-center text-xs font-semibold uppercase tracking-wide text-slate-500">Estado</th>
            <th className="px-4 py-3" />
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-100 bg-white">
          {invoices.map((invoice) => {
            const isSelected = invoice.id === selectedId;
            return (
              <tr
                key={invoice.id}
                className={isSelected ? 'bg-indigo-50' : 'hover:bg-slate-50'}
                onClick={() => onSelect(invoice)}
              >
                <td className="px-4 py-3 text-sm text-slate-700">{invoice.supplierName}</td>
                <td className="px-4 py-3 text-sm text-slate-500">{invoice.externalId}</td>
                <td className="px-4 py-3 text-sm text-slate-500">{formatDate(invoice.issueDate)}</td>
                <td className="px-4 py-3 text-right text-sm font-medium text-slate-900">
                  {formatCurrency(invoice.total, invoice.currency)}
                </td>
                <td className="px-4 py-3 text-center">
                  <span className="inline-flex items-center rounded-full bg-slate-100 px-2.5 py-0.5 text-xs font-medium text-slate-600">
                    {invoice.status}
                  </span>
                </td>
                <td className="px-4 py-3 text-right text-sm">
                  <Link to={`/invoices/${invoice.id}`} className="text-indigo-600 hover:text-indigo-500">
                    Ver detalle
                  </Link>
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
