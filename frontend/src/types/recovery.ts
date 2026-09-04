export type ActionType = 'RETRY' | 'NUDGE' | 'ESCALATE' | 'STOP';

export type PaymentMethod = 'credit_card' | 'debit_card' | 'boleto' | 'voucher';

export type FailureCategory =
  | 'SOFT_DECLINE'
  | 'FUNDS_ISSUE'
  | 'CUSTOMER_ACTION_REQUIRED'
  | 'HARD_DECLINE'
  | 'GENERIC_DECLINE';

export interface PaymentContext {
  payment_type: PaymentMethod;
  payment_value: number;
  payment_installments: number;
  previous_order_count: number;
  previous_payment_count: number;
  previous_success_count: number;
  previous_cancelled_count: number;
  historical_payment_success_rate: number;
  historical_average_payment: number;
  customer_tenure_before_payment: number;
  order_frequency_before_payment: number;
  failure_category: FailureCategory;
  failure_reason: string;
  hours_since_failure: number;
  recovery_attempt_number: number;
}

export interface ActionDetail {
  guardrail_result: 'PASSED' | 'BLOCKED';
  guardrail_rule_ids: string[];
  raw_probability?: number;
  probability: number;
  utility: number;
  cost: number;
}

export interface RecommendationDecision {
  selected_action: ActionType;
  expected_utility: number;
  recovery_probability: number;
  selection_reason: string;
}

export interface RecommendationResponse {
  status: 'SUCCESS' | 'INVALID_INPUT' | 'SYSTEM_ERROR';
  request_id?: string;
  decision: RecommendationDecision;
  actions: Record<ActionType, ActionDetail>;
  fallback_triggered: boolean;
  error_code?: string;
  message?: string;
}

export interface HealthResponse {
  status: string;
  service: string;
  version: string;
  model_artifact_hash: string;
  calibrator_artifact_hash: string;
  audit_log_active: boolean;
}

export interface PolicySummaryRow {
  policy_name: string;
  policy_tag: string;
  total_cases: number;
  revenue_at_risk_brl: number;
  recovered_revenue_brl: number;
  net_policy_utility_brl: number;
  recovery_rate_pct: number;
  avg_recovered_per_case_brl: number;
  abs_revenue_lift_vs_rb_brl: number;
  pct_revenue_lift_vs_rb: number;
  net_utility_lift_vs_rb_brl: number;
  regret_vs_upper_bound_brl: number;
  guardrail_violations: number;
}

export interface BootstrapCI {
  mean: number;
  ci_95_low: number;
  ci_95_high: number;
}

export interface FrozenStep5FData {
  summary: PolicySummaryRow[];
  metrics: {
    test_ml_metrics: {
      brier_score: number;
      ece: number;
      log_loss: number;
      roc_auc: number;
      sample_count: number;
    };
    bootstrap_confidence_intervals: {
      ml_net_utility: BootstrapCI;
      rb_net_utility: BootstrapCI;
      ml_recovered_revenue: BootstrapCI;
      rb_recovered_revenue: BootstrapCI;
      ml_recovery_rate_pct: BootstrapCI;
      abs_revenue_lift_brl: BootstrapCI;
      pct_revenue_lift: BootstrapCI;
      net_utility_lift_brl: BootstrapCI;
      regret_brl: BootstrapCI;
    };
  };
}

export interface FrozenModelComparisonData {
  aucA: number;
  brierA: number;
  eceA: number;
  lossA: number;
  rateA: string;
  utilA: string;
  regretA: string;

  aucB: number;
  brierB: number;
  eceB: number;
  lossB: number;
  rateB: string;
  utilB: string;
  regretB: string;
}

export type RequestStatus = 'IDLE' | 'REQUESTING' | 'SUCCESS' | 'ERROR';
