import axios from 'axios';
import { AISuggestion, InvoiceDetail, InvoiceSummary } from '../types/invoice';

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE ?? 'http://localhost:8000'
});

interface LoginResponse {
  access_token: string;
  token_type: string;
}

interface UserResponse {
  email: string;
}

interface InvoiceSummaryResponse {
  id: string;
  external_id: string;
  issue_date: string;
  supplier_name: string;
  currency: string;
  total_amount: string | number;
  status: InvoiceSummary['status'];
}

interface InvoiceLineResponse {
  line_id: string;
  description: string;
  quantity: string | number;
  unit_price: string | number;
  line_extension_amount: string | number;
  tax_amount: string | number;
}

interface InvoiceTaxResponse {
  type: string;
  amount: string | number;
}

interface InvoiceDetailResponse extends InvoiceSummaryResponse {
  supplier_tax_id: string;
  customer_name: string;
  customer_tax_id: string;
  tax_amount: string | number;
  original_filename: string;
  lines: InvoiceLineResponse[];
  taxes: InvoiceTaxResponse[];
}

interface SuggestionResponse {
  account_code: string;
  rationale: string;
  confidence: number;
}

interface SuggestionsEnvelope {
  invoice_id: string;
  suggestions: SuggestionResponse[];
}

function toNumber(value: string | number): number {
  const numeric = typeof value === 'number' ? value : parseFloat(value);
  return Number.isFinite(numeric) ? numeric : 0;
}

function mapInvoiceSummary(payload: InvoiceSummaryResponse): InvoiceSummary {
  return {
    id: payload.id,
    externalId: payload.external_id,
    supplierName: payload.supplier_name,
    issueDate: payload.issue_date,
    total: toNumber(payload.total_amount),
    currency: payload.currency,
    status: payload.status
  };
}

function mapInvoiceDetail(payload: InvoiceDetailResponse): InvoiceDetail {
  return {
    ...mapInvoiceSummary(payload),
    lines: payload.lines.map((line) => ({
      id: line.line_id,
      description: line.description,
      quantity: toNumber(line.quantity),
      unitPrice: toNumber(line.unit_price),
      taxAmount: toNumber(line.tax_amount),
      total: toNumber(line.line_extension_amount)
    })),
    taxes: payload.taxes.map((tax) => ({
      type: tax.type,
      amount: toNumber(tax.amount)
    }))
  };
}

function mapSuggestion(payload: SuggestionResponse): AISuggestion {
  return {
    accountCode: payload.account_code,
    rationale: payload.rationale,
    confidence: payload.confidence
  };
}

export async function loginRequest(email: string, password: string): Promise<LoginResponse> {
  const response = await api.post<LoginResponse>('/auth/login', { email, password });
  return response.data;
}

export async function meRequest(token: string): Promise<UserResponse> {
  const response = await api.get<UserResponse>('/auth/me', {
    headers: { Authorization: `Bearer ${token}` }
  });
  return response.data;
}

export async function fetchInvoices(token: string): Promise<InvoiceSummary[]> {
  const response = await api.get<InvoiceSummaryResponse[]>('/invoices', {
    headers: { Authorization: `Bearer ${token}` }
  });
  return response.data.map(mapInvoiceSummary);
}

export async function fetchInvoiceDetail(token: string, invoiceId: string): Promise<InvoiceDetail> {
  const response = await api.get<InvoiceDetailResponse>(`/invoices/${invoiceId}`, {
    headers: { Authorization: `Bearer ${token}` }
  });
  return mapInvoiceDetail(response.data);
}

export async function uploadInvoice(token: string, file: File): Promise<InvoiceDetail> {
  const formData = new FormData();
  formData.append('file', file);

  const response = await api.post<InvoiceDetailResponse>('/invoices/upload', formData, {
    headers: { Authorization: `Bearer ${token}` }
  });

  return mapInvoiceDetail(response.data);
}

export async function requestSuggestions(token: string, invoiceId: string): Promise<AISuggestion[]> {
  const response = await api.get<SuggestionsEnvelope>(`/invoices/${invoiceId}/suggest`, {
    headers: { Authorization: `Bearer ${token}` }
  });
  return (response.data.suggestions ?? []).map(mapSuggestion);
}

export async function exportInvoices(token: string): Promise<Blob> {
  const response = await api.get('/invoices/export', {
    headers: { Authorization: `Bearer ${token}` },
    responseType: 'blob'
  });
  return response.data;
}
