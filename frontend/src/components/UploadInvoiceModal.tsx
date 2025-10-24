import { useRef } from 'react';

interface UploadInvoiceModalProps {
  isOpen: boolean;
  onClose: () => void;
  onUpload: (file: File) => Promise<void>;
  isLoading: boolean;
}

export function UploadInvoiceModal({ isOpen, onClose, onUpload, isLoading }: UploadInvoiceModalProps) {
  const fileInputRef = useRef<HTMLInputElement | null>(null);

  if (!isOpen) {
    return null;
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/50 p-4">
      <div className="w-full max-w-lg rounded-lg bg-white p-6 shadow-lg">
        <h2 className="text-lg font-semibold text-slate-900">Subir factura XML</h2>
        <p className="mt-1 text-sm text-slate-500">
          Selecciona uno de los archivos UBL entregados en <code>backend/app/assessment-files/</code>. Puedes cargar también
          versiones generadas por el backend para comprobar su consistencia.
        </p>
        <input
          ref={fileInputRef}
          type="file"
          accept=".xml"
          className="mt-4 block w-full text-sm text-slate-600"
        />
        <div className="mt-6 flex justify-end gap-3">
          <button
            type="button"
            onClick={onClose}
            className="rounded border border-slate-300 px-4 py-2 text-sm font-medium text-slate-700 hover:bg-slate-100"
          >
            Cancelar
          </button>
          <button
            type="button"
            disabled={isLoading}
            onClick={async () => {
              const file = fileInputRef.current?.files?.[0];
              if (file) {
                await onUpload(file);
              }
            }}
            className="rounded bg-indigo-600 px-4 py-2 text-sm font-semibold text-white hover:bg-indigo-500 disabled:opacity-50"
          >
            {isLoading ? 'Subiendo…' : 'Subir'}
          </button>
        </div>
      </div>
    </div>
  );
}
