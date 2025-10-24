export interface InvoiceLine {
  id: string;
  description: string;
  quantity: number;
  unitPrice: number;
  taxAmount: number;
  total: number;
  accountSuggestion?: string;
}

export interface InvoiceSummary {
  id: string;
  externalId: string;
  supplierName: string;
  issueDate: string;
  total: number;
  currency: string;
  status: 'pendiente' | 'procesada' | 'exportada';
}

export interface InvoiceDetail extends InvoiceSummary {
  lines: InvoiceLine[];
  taxes: Array<{ type: string; amount: number }>;
}

export interface AISuggestion {
  accountCode: string;
  rationale: string;
  confidence: number;
}
