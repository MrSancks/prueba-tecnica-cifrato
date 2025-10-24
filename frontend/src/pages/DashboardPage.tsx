import { useState } from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { AppHeader } from '../components/AppHeader';
import { DashboardActions } from '../components/DashboardActions';
import { InvoiceTable } from '../components/InvoiceTable';
import { UploadInvoiceModal } from '../components/UploadInvoiceModal';
import { useAuth } from '../hooks/useAuth';
import { fetchInvoices, exportInvoices, uploadInvoice } from '../services/apiClient';
import { InvoiceSummary } from '../types/invoice';

export function DashboardPage() {
  const { token } = useAuth();
  const queryClient = useQueryClient();
  const [selected, setSelected] = useState<InvoiceSummary | null>(null);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [isExporting, setIsExporting] = useState(false);
  const [isUploading, setIsUploading] = useState(false);

  const { data: invoices = [], isLoading } = useQuery({
    queryKey: ['invoices'],
    queryFn: async () => {
      if (!token) {
        return [];
      }
      const response = await fetchInvoices(token);
      return response;
    },
    enabled: Boolean(token)
  });

  return (
    <div className="min-h-screen bg-slate-100">
      <AppHeader />
      <main className="mx-auto max-w-6xl space-y-6 px-6 py-8">
        <DashboardActions
          onOpenUpload={() => setIsModalOpen(true)}
          isExporting={isExporting}
          onExport={async () => {
            if (!token) {
              return;
            }
            try {
              setIsExporting(true);
              const blob = await exportInvoices(token);
              const url = window.URL.createObjectURL(blob);
              const anchor = document.createElement('a');
              anchor.href = url;
              anchor.download = 'facturas.xlsx';
              anchor.click();
              window.URL.revokeObjectURL(url);
            } finally {
              setIsExporting(false);
            }
          }}
        />

        {isLoading ? (
          <p className="text-sm text-slate-500">Cargando facturas…</p>
        ) : (
          <InvoiceTable
            invoices={invoices}
            onSelect={setSelected}
            selectedId={selected?.id}
          />
        )}
      </main>

      <UploadInvoiceModal
        isOpen={isModalOpen}
        isLoading={isUploading}
        onClose={() => setIsModalOpen(false)}
        onUpload={async (file) => {
          if (!token) {
            return;
          }
          try {
            setIsUploading(true);
            await uploadInvoice(token, file);
            await queryClient.invalidateQueries({ queryKey: ['invoices'] });
            setIsModalOpen(false);
          } finally {
            setIsUploading(false);
          }
        }}
      />
    </div>
  );
}
