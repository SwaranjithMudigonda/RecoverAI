import type { FrozenStep5FData, FrozenModelComparisonData } from '../types/recovery';

export const LIGHTGBM_MODEL_HASH = "ca968b7756caec185e70b562cda34445289cea4d0a4bce14cf7b0c5a0b1068e7";
export const ISOTONIC_CALIBRATOR_HASH = "8bda9ffdbb4b281a6569c5436f7ccf3cdb721da2971d1029540fa0809d596817";

export const FROZEN_STEP5F_ARTIFACT_DATA: FrozenStep5FData = {
  summary: [
    {
      policy_name: "Simulation Policy Upper Bound",
      policy_tag: "UPPER_BOUND",
      total_cases: 2283,
      revenue_at_risk_brl: 345292.12,
      recovered_revenue_brl: 185002.26,
      net_policy_utility_brl: 179176.76,
      recovery_rate_pct: 52.3434,
      avg_recovered_per_case_brl: 81.0347,
      abs_revenue_lift_vs_rb_brl: 7875.84,
      pct_revenue_lift_vs_rb: 4.4465,
      net_utility_lift_vs_rb_brl: 6108.34,
      regret_vs_upper_bound_brl: 0.0,
      guardrail_violations: 0
    },
    {
      policy_name: "ML Policy (LightGBM S-Learner)",
      policy_tag: "ML",
      total_cases: 2283,
      revenue_at_risk_brl: 345292.12,
      recovered_revenue_brl: 184987.96,
      net_policy_utility_brl: 179015.96,
      recovery_rate_pct: 52.2996,
      avg_recovered_per_case_brl: 81.0285,
      abs_revenue_lift_vs_rb_brl: 7861.54,
      pct_revenue_lift_vs_rb: 4.4384,
      net_utility_lift_vs_rb_brl: 5947.54,
      regret_vs_upper_bound_brl: 160.80,
      guardrail_violations: 0
    },
    {
      policy_name: "Rule-Based Policy Baseline",
      policy_tag: "RULE_BASED",
      total_cases: 2283,
      revenue_at_risk_brl: 345292.12,
      recovered_revenue_brl: 177126.42,
      net_policy_utility_brl: 173068.42,
      recovery_rate_pct: 50.5913,
      avg_recovered_per_case_brl: 77.5849,
      abs_revenue_lift_vs_rb_brl: 0.0,
      pct_revenue_lift_vs_rb: 0.0,
      net_utility_lift_vs_rb_brl: 0.0,
      regret_vs_upper_bound_brl: 6108.34,
      guardrail_violations: 0
    },
    {
      policy_name: "Always-NUDGE Baseline",
      policy_tag: "ALWAYS_NUDGE",
      total_cases: 2283,
      revenue_at_risk_brl: 345292.12,
      recovered_revenue_brl: 125195.89,
      net_policy_utility_brl: 119488.39,
      recovery_rate_pct: 35.6548,
      avg_recovered_per_case_brl: 54.8383,
      abs_revenue_lift_vs_rb_brl: -51930.53,
      pct_revenue_lift_vs_rb: -29.3183,
      net_utility_lift_vs_rb_brl: -53580.03,
      regret_vs_upper_bound_brl: 59688.37,
      guardrail_violations: 0
    }
  ],
  metrics: {
    test_ml_metrics: {
      brier_score: 0.222695,
      ece: 0.026444,
      log_loss: 0.651352,
      roc_auc: 0.687857,
      sample_count: 2283
    },
    bootstrap_confidence_intervals: {
      ml_net_utility: { mean: 178776.12, ci_95_low: 162926.10, ci_95_high: 196091.84 },
      rb_net_utility: { mean: 172832.00, ci_95_low: 157416.26, ci_95_high: 190087.36 },
      ml_recovered_revenue: { mean: 184747.56, ci_95_low: 169058.99, ci_95_high: 202161.82 },
      rb_recovered_revenue: { mean: 176886.99, ci_95_low: 161448.32, ci_95_high: 194140.05 },
      ml_recovery_rate_pct: { mean: 52.31, ci_95_low: 50.42, ci_95_high: 54.26 },
      abs_revenue_lift_brl: { mean: 7860.57, ci_95_low: 4974.46, ci_95_high: 11181.81 },
      pct_revenue_lift: { mean: 4.45, ci_95_low: 2.75, ci_95_high: 6.38 },
      net_utility_lift_brl: { mean: 5944.12, ci_95_low: 3130.62, ci_95_high: 9101.72 },
      regret_brl: { mean: 156.35, ci_95_low: -622.47, ci_95_high: 942.07 }
    }
  }
};

export const FROZEN_MODEL_COMPARISON_DATA: FrozenModelComparisonData = {
  aucA: 0.687857,
  brierA: 0.222695,
  eceA: 0.026444,
  lossA: 0.651352,
  rateA: "52.30%",
  utilA: "R$ 179,015.96",
  regretA: "R$ 160.80",
  
  aucB: 0.685551,
  brierB: 0.220716,
  eceB: 0.033844,
  lossB: 0.629494,
  rateB: "45.16%",
  utilB: "R$ 154,694.06",
  regretB: "R$ 24,482.70"
};
