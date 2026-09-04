export interface ScoreFactor {
  factor: string;
  impact: number;
  description: string;
}

export interface Playbook {
  action: 'retry_now' | 'retry_scheduled' | 'notify_customer' | 'escalate_human' | 'do_not_retry';
  channel: 'email' | 'sms' | 'whatsapp' | 'in_app' | 'none';
  retry_delay_hours: number;
  max_retries: number;
  rationale: string;
}

export interface PolicyOverride {
  rule: string;
  reason: string;
  original_value: any;
  overridden_value: any;
}

export interface Transaction {
  transaction_id: string;
  customer_id: string;
  customer_segment: 'new' | 'regular' | 'high_value';
  amount: number;
  currency: string;
  gateway: string;
  decline_code: string;
  decline_message: string;
  timestamp: string;
  is_subscription: boolean;
  previous_retry_count: number;
  fraud_flag: boolean;
  is_synthetic: boolean;
  edge_case_tag?: string | null;

  root_cause?: string | null;
  root_cause_rationale?: string | null;
  recoverability_score?: number | null;
  score_factors?: ScoreFactor[] | null;

  proposed_action?: string | null;
  proposed_playbook?: Playbook | null;

  policy_gate_verdict?: 'PASSED' | 'OVERRIDDEN' | null;
  policy_overrides?: PolicyOverride[] | null;
  final_action?: string | null;
  final_playbook?: Playbook | null;

  simulated_outcome_ai?: 'RECOVERED' | 'FAILED' | 'SKIPPED' | null;
  simulated_retries_ai?: number;
  simulated_outcome_baseline?: 'RECOVERED' | 'FAILED' | null;
  simulated_retries_baseline?: number;
  false_retry_avoided?: boolean;
  analyzed_at?: string | null;
}

export interface SimulationMetrics {
  seed: number;
  total_transactions: number;
  amount_at_risk: number;
  amount_recovered_ai: number;
  amount_recovered_baseline: number;
  recovery_rate_ai: number;
  recovery_rate_baseline: number;
  recovery_rate_uplift_pct: number;
  false_retries_avoided: number;
  policy_overrides_count: number;
  simulated_at?: string | null;
  root_cause_breakdown?: Record<string, number>;
  action_breakdown?: Record<string, number>;
}

export interface AuditLog {
  id: number;
  transaction_id: string;
  customer_id: string;
  proposed_action: string;
  proposed_playbook: Playbook;
  policy_verdict: 'PASSED' | 'OVERRIDDEN';
  rules_fired: string[];
  override_reasons: string[];
  final_action: string;
  final_playbook: Playbook;
  created_at: string;
}

export interface TransactionListResponse {
  total: number;
  page: number;
  page_size: number;
  transactions: Transaction[];
}

export interface AuditLogListResponse {
  total: number;
  page: number;
  page_size: number;
  logs: AuditLog[];
}
