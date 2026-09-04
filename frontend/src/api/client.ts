import type {
  AuditLogListResponse,
  SimulationMetrics,
  Transaction,
  TransactionListResponse,
} from '../types';

const API_BASE = '/api';

export async function seedDataset(): Promise<{ status: string; count: number; seed: number; message: string }> {
  const res = await fetch(`${API_BASE}/transactions/seed`, { method: 'POST' });
  if (!res.ok) throw new Error(`Failed to seed data: ${res.statusText}`);
  return res.json();
}

export async function getTransactions(params: {
  root_cause?: string;
  segment?: string;
  action?: string;
  fraud_flag?: boolean;
  edge_case_only?: boolean;
  search?: string;
  page?: number;
  page_size?: number;
} = {}): Promise<TransactionListResponse> {
  const query = new URLSearchParams();
  if (params.root_cause) query.set('root_cause', params.root_cause);
  if (params.segment) query.set('segment', params.segment);
  if (params.action) query.set('action', params.action);
  if (params.fraud_flag !== undefined) query.set('fraud_flag', String(params.fraud_flag));
  if (params.edge_case_only) query.set('edge_case_only', 'true');
  if (params.search) query.set('search', params.search);
  if (params.page) query.set('page', String(params.page));
  if (params.page_size) query.set('page_size', String(params.page_size));

  const res = await fetch(`${API_BASE}/transactions?${query.toString()}`);
  if (!res.ok) throw new Error(`Failed to fetch transactions: ${res.statusText}`);
  return res.json();
}

export async function getTransaction(id: string): Promise<Transaction> {
  const res = await fetch(`${API_BASE}/transactions/${id}`);
  if (!res.ok) throw new Error(`Failed to fetch transaction ${id}: ${res.statusText}`);
  return res.json();
}

export async function analyzeTransaction(id: string): Promise<Transaction> {
  const res = await fetch(`${API_BASE}/transactions/${id}/analyze`, { method: 'POST' });
  if (!res.ok) throw new Error(`Failed to analyze transaction ${id}: ${res.statusText}`);
  return res.json();
}

export async function runBatchSimulation(): Promise<SimulationMetrics> {
  const res = await fetch(`${API_BASE}/simulate/batch`, { method: 'POST' });
  if (!res.ok) throw new Error(`Failed to run simulation: ${res.statusText}`);
  return res.json();
}

export async function getMetrics(): Promise<SimulationMetrics> {
  const res = await fetch(`${API_BASE}/metrics`);
  if (!res.ok) throw new Error(`Failed to fetch metrics: ${res.statusText}`);
  return res.json();
}

export async function getAuditLogs(params: {
  verdict?: string;
  action?: string;
  customer_id?: string;
  transaction_id?: string;
  search?: string;
  page?: number;
  page_size?: number;
} = {}): Promise<AuditLogListResponse> {
  const query = new URLSearchParams();
  if (params.verdict) query.set('verdict', params.verdict);
  if (params.action) query.set('action', params.action);
  if (params.customer_id) query.set('customer_id', params.customer_id);
  if (params.transaction_id) query.set('transaction_id', params.transaction_id);
  if (params.search) query.set('search', params.search);
  if (params.page) query.set('page', String(params.page));
  if (params.page_size) query.set('page_size', String(params.page_size));

  const res = await fetch(`${API_BASE}/audit-log?${query.toString()}`);
  if (!res.ok) throw new Error(`Failed to fetch audit logs: ${res.statusText}`);
  return res.json();
}
