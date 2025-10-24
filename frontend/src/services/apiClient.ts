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
  const response = await api.get<InvoiceSummary[]>('/invoices', {
    headers: { Authorization: `Bearer ${token}` }
  });
  return response.data;
}

export async function fetchInvoiceDetail(token: string, invoiceId: string): Promise<InvoiceDetail> {
  const response = await api.get<InvoiceDetail>(`/invoices/${invoiceId}`, {
    headers: { Authorization: `Bearer ${token}` }
  });
  return response.data;
}

export async function uploadInvoice(token: string, file: File): Promise<InvoiceDetail> {
  const formData = new FormData();
  formData.append('file', file);

  const response = await api.post<InvoiceDetail>('/invoices/upload', formData, {
    headers: { Authorization: `Bearer ${token}` }
  });

  return response.data;
}

export async function requestSuggestions(token: string, invoiceId: string): Promise<AISuggestion[]> {
  const response = await api.get<AISuggestion[]>(`/invoices/${invoiceId}/suggest`, {
    headers: { Authorization: `Bearer ${token}` }
  });
  return response.data;
}

export async function exportInvoices(token: string): Promise<Blob> {
  const response = await api.get('/invoices/export', {
    headers: { Authorization: `Bearer ${token}` },
    responseType: 'blob'
  });
  return response.data;
}
