# RecoverAI Recovery Case Generation Report

## Executive Summary

This report documents the generation, post-audit correction, and validation of the primary evaluation dataset for **RecoverAI: Track 03 AI Revenue Recovery** (Step 4E-4).

The generated dataset is stored at [`data/processed/recoverai_recovery_cases.csv`](../data/processed/recoverai_recovery_cases.csv).

---

## 1. Generation Pipeline Overview

```
REAL OLIST RAW DATA (orders, order_payments, customers)
  │ (103,877 eligible payment cases)
  ▼
Leakage-Free Customer History Calculation (T_past < T0)
  │ (derived prior success rates, tenure, order counts)
  ▼
Stratified Deterministic Failure Sampling (15.0% sampling rate, SEED = 42)
  │ (15,581 simulated failed cases; hours_since_failure bounded 0.5-72.0 hrs)
  ▼
Action-Conditional Recovery Scoring & Multi-Factor Expected Utility Maximization
  │ (Evaluating ALL 4 ACTIONS: RETRY, NUDGE, ESCALATE, STOP under guardrails)
  ▼
Simulated Outcome Realization & 30 Mandatory Validation Checks
  │ (ALL 30 VALIDATION CHECKS PASSED)
  ▼
Dataset Export & 100% Reproducibility Verification
```

---

## 2. Dataset Dimensions & Summary Metrics

| Metric / Property | Value | Provenance |
|---|---|---|
| **Raw Input Files** | `olist_orders_dataset.csv`<br>`olist_order_payments_dataset.csv`<br>`olist_customers_dataset.csv` | `REAL_OLIST` |
| **Total Eligible Olist Cases** | 103,877 | `REAL_OLIST` |
| **Sampled Recovery Cases** | **15,581** | `SIMULATION PARAMETER` (15.0%) |
| **Total Columns** | **51** | Mixed (6 Real, 8 Derived, 34 Simulated, 3 Config) |
| **Unique `case_id`** | 15,581 | `DERIVED_FROM_REAL_OLIST` |
| **Unique `order_id`** | 15,354 | `REAL_OLIST` |
| **Unique `customer_unique_id`** | 15,264 | `REAL_OLIST` |
| **Global Random Seed** | `SEED = 42` | `SIMULATION_CONFIGURATION` |
| **Provenance Version** | `v1.0-olist-augmented` | `SIMULATION_CONFIGURATION` |

---

## 3. Data Provenance Partitioning

The dataset strict boundary separates empirical real-world context from simulation variables:

### A. Real Olist Fields (`REAL_OLIST`)
- `order_id`, `customer_id`, `customer_unique_id`, `payment_type`, `payment_value`, `payment_installments`, `payment_sequential`, `order_purchase_timestamp`

### B. Derived Real-Data Features (`DERIVED_FROM_REAL_OLIST`)
- `previous_order_count`, `previous_payment_count`, `previous_success_count`, `previous_cancelled_count`, `historical_payment_success_rate`, `historical_average_payment`, `customer_tenure_before_payment`, `order_frequency_before_payment`

### C. Simulated Failure & Recovery Features (`SIMULATED_RECOVERY`)
- `failure_category`, `failure_reason`, `failure_timestamp`, `hours_since_failure`, `recovery_attempt_number`, `model_probability_RETRY`, `model_probability_NUDGE`, `model_probability_ESCALATE`, `model_probability_STOP`, `effective_probability_RETRY`, `effective_probability_NUDGE`, `effective_probability_ESCALATE`, `effective_probability_STOP`, `utility_RETRY`, `utility_NUDGE`, `utility_ESCALATE`, `utility_STOP`, `guardrail_RETRY`, `guardrail_NUDGE`, `guardrail_ESCALATE`, `guardrail_STOP`, `guardrail_rules_RETRY`, `guardrail_rules_NUDGE`, `guardrail_rules_ESCALATE`, `guardrail_rules_STOP`, `selected_action`, `recovery_probability`, `revenue_at_risk`, `expected_recovered_amount`, `execution_status`, `recovered`, `recovered_amount`

---

## 4. 4E-4 Post-Audit Corrections

Following an external technical audit of the initial Step 4E-4 implementation, the pipeline was corrected to address serialization aliasing, hardcoded parameters, and missing counterfactual evaluations:

1. **Candidate Action Aliasing Removed**:
   - The field `candidate_action` (which previously mirrored `selected_action`) was removed to prevent aliasing.
   - The dataset now explicitly exposes counterfactual evaluations for **ALL FOUR CANDIDATE ACTIONS** (`RETRY`, `NUDGE`, `ESCALATE`, `STOP`).

2. **Complete 4-Action Evaluation Schema Preserved**:
   - Added `model_probability_a` for all 4 actions (unconstrained model score).
   - Added `effective_probability_a` for all 4 actions ($0.00$ if guardrail blocked or `STOP`).
   - Added `utility_a` for all 4 actions (multi-factor expected utility).

3. **Independent Per-Action Guardrail Logging**:
   - Guardrails are now evaluated and logged independently per candidate action (`guardrail_RETRY`, `guardrail_NUDGE`, `guardrail_ESCALATE`, `guardrail_STOP`).
   - Rule IDs are stored per action (`guardrail_rules_RETRY`, etc.).
   - Results show `RETRY` was **BLOCKED** in 49.2% of cases due to Boleto, Voucher, hard declines, or customer authentication requirements, while `NUDGE`, `ESCALATE`, and `STOP` passed initial safety checks.

4. **Hours-Since-Failure Hardcoding Fixed**:
   - Removed hardcoded `1.0` hour parameter.
   - Generated a realistic, reproducible simulation distribution bounded between `0.5` and `72.0` hours using `SEED = 42` (Mean: 36.38 hrs, Median: 36.6 hrs, 716 unique values).

5. **Time-Decay Dynamics Verified**:
   - Verified that `hours_since_failure` actively decays model probabilities ($\beta_{\text{time}} = 0.02$). Cases evaluated at later elapsed times experience lower recovery probabilities.

6. **Selected Action Strictly Maximizes Valid Utility**:
   - Validated that `selected_action == argmax(utility_a)` for all actions where `guardrail_a == PASSED`.
   - 100% of rows verified (`Selected action equals highest valid utility: True`).

7. **Outcome Generation Bound to Selected Action Probability**:
   - Verified that `recovered ~ Bernoulli(recovery_probability)` uses strictly `effective_probability_<selected_action>`.

---

## 5. Payment-Type Distribution

Sampling was stratified across Olist payment methods to preserve empirical value distributions while oversampling minority rails for statistical evaluation balance:

| Payment Type | Sample Count | Sample % | Empirical Olist % | Target Sample Share |
|---|---|---|---|---|
| `credit_card` | 10,907 | 69.99% | 74.0% | 70.0% |
| `boleto` | 3,116 | 20.00% | 19.0% | 20.0% |
| `voucher` | 1,091 | 7.00% | 5.5% | 7.0% |
| `debit_card` | 467 | 3.00% | 1.5% | 3.0% |
| **Total** | **15,581** | **100.0%** | **100.0%** | **100.0%** |

---

## 6. Failure Reason & Category Breakdown

Failure reasons were assigned using canonical names strictly matching `docs/failure_taxonomy.md`:

### Failure Category Distribution
- **`CUSTOMER_ACTION_REQUIRED`**: 6,240 cases (40.05%)
- **`SOFT_DECLINE`**: 4,003 cases (25.69%)
- **`FUNDS_ISSUE`**: 2,788 cases (17.89%)
- **`GENERIC_DECLINE`**: 1,447 cases (9.29%)
- **`HARD_DECLINE`**: 1,103 cases (7.08%)

### Granular Failure Reason Breakdown (Canonical Names)

| Failure Reason | Category | Count | % of Total | Compatible Payment Methods |
|---|---|---|---|---|
| `insufficient_funds` | `FUNDS_ISSUE` | 2,260 | 14.50% | credit_card, debit_card |
| `authentication_failed` | `CUSTOMER_ACTION_REQUIRED` | 1,760 | 11.30% | credit_card, debit_card |
| `network_error` | `SOFT_DECLINE` | 1,718 | 11.03% | credit_card, debit_card |
| `payment_cancelled` | `CUSTOMER_ACTION_REQUIRED` | 1,526 | 9.79% | credit_card, debit_card, boleto, voucher |
| `boleto_expired` | `CUSTOMER_ACTION_REQUIRED` | 1,496 | 9.60% | boleto |
| `bank_technical_error` | `SOFT_DECLINE` | 1,153 | 7.40% | credit_card, debit_card |
| `gateway_error` | `SOFT_DECLINE` | 1,132 | 7.27% | credit_card, debit_card |
| `payment_failed` | `GENERIC_DECLINE` | 1,101 | 7.07% | credit_card, debit_card, boleto, voucher |
| `payment_timed_out` | `CUSTOMER_ACTION_REQUIRED` | 859 | 5.51% | credit_card, debit_card, boleto, voucher |
| `expired_card` | `CUSTOMER_ACTION_REQUIRED` | 599 | 3.84% | credit_card, debit_card |
| `withdrawal_limit_exceeded` | `FUNDS_ISSUE` | 528 | 3.39% | credit_card, debit_card |
| `card_number_invalid` | `HARD_DECLINE` | 444 | 2.85% | credit_card, debit_card |
| `stolen_card` | `HARD_DECLINE` | 443 | 2.84% | credit_card, debit_card |
| `do_not_honor` | `GENERIC_DECLINE` | 346 | 2.22% | credit_card, debit_card |
| `compliance_violation` | `HARD_DECLINE` | 216 | 1.39% | credit_card, debit_card |

---

## 7. Counterfactual Action Evaluation & Guardrail Summary

### Guardrail Status Distribution per Candidate Action

| Action | PASSED Count | PASSED % | BLOCKED Count | BLOCKED % | Key Triggered Rules |
|---|---|---|---|---|---|
| **`RETRY`** | 7,912 | 50.78% | 7,669 | 49.22% | `GR01_BOLETO`, `GR02_VOUCHER`, `GR03_HARD_DECLINE`, `GR04_AUTH_REQ` |
| **`NUDGE`** | 15,581 | 100.00% | 0 | 0.00% | None |
| **`ESCALATE`**| 15,581 | 100.00% | 0 | 0.00% | None |
| **`STOP`** | 15,581 | 100.00% | 0 | 0.00% | None |

### Action Utility & Probability Summary

| Action | Mean Model Prob | Mean Effective Prob | Mean Expected Utility (BRL) | Min Utility | Max Utility |
|---|---|---|---|---|---|
| **`RETRY`** | 0.4075 | 0.2071 | **24.34 BRL** | -100.50 BRL | 1,960.57 BRL |
| **`NUDGE`** | 0.3810 | 0.3810 | **52.08 BRL** | -2.50 BRL | 2,391.50 BRL |
| **`ESCALATE`**| 0.1111 | 0.1111 | **3.32 BRL** | -15.00 BRL | 1,490.25 BRL |
| **`STOP`** | 0.0000 | 0.0000 | **0.00 BRL** | 0.00 BRL | 0.00 BRL |

### Selected Action Distribution
- **`NUDGE`**: 10,523 cases (67.54%) — Selected for customer action required, funds issues, and boleto/voucher recovery.
- **`RETRY`**: 4,063 cases (26.08%) — Selected for soft technical declines on card rails.
- **`ESCALATE`**: 844 cases (5.42%) — Selected for high monetary exposure (> 1,000 BRL) or model uncertainty.
- **`STOP`**: 151 cases (0.97%) — Selected for hard decline fraud/invalid card cases.

---

## 8. Financial Realization Summary

| Financial Metric | Amount (BRL) | Description |
|---|---|---|
| **Revenue at Risk Total** | **2,337,778.37 BRL** | Sum of `payment_value` across all sampled failed cases |
| **Expected Recovered Amount Total** | **1,253,584.44 BRL** | Sum of risk-adjusted expected values ($\sum V_i \cdot P_i$) |
| **Actual Simulated Recovered Amount** | **1,241,832.12 BRL** | Realized monetary recovery under Bernoulli outcome sampling |
| **Simulated Recovery Rate** | **53.76%** | 8,377 successful recoveries out of 15,581 cases |

---

## 9. Mandatory Validation Results (30 Invariants)

All 30 mandatory validation checks were executed prior to saving the dataset:

| # | Validation Rule | Status | Detail / Result |
|---|---|---|---|
| 1 | Non-empty dataset | **PASSED** | 15,581 rows generated |
| 2 | Unique `case_id` | **PASSED** | 15,581 unique case identifiers |
| 3 | One row per `case_id` | **PASSED** | No exploded rows |
| 4 | ~15% sampling rate | **PASSED** | 15,581 / 103,877 = 15.00% |
| 5 | `payment_value > 0` | **PASSED** | Zero non-positive amounts |
| 6 | Supported payment types | **PASSED** | credit_card, debit_card, boleto, voucher only |
| 7 | Payment compatibility | **PASSED** | Zero card-specific failure codes on Boleto or Voucher |
| 8 | Boleto RETRY safety | **PASSED** | Exactly 0 Boleto RETRY actions selected |
| 9 | Voucher RETRY safety | **PASSED** | Exactly 0 Voucher RETRY actions selected |
| 10 | Hard decline RETRY safety | **PASSED** | Exactly 0 hard decline RETRY actions selected |
| 11 | Probabilities in [0, 1] | **PASSED** | All model/effective probabilities strictly bounded |
| 12 | Guardrail zero-effective rule | **PASSED** | Blocked actions forced to 0.00 effective probability |
| 13 | Passed action effective prob | **PASSED** | `effective_prob == model_prob` for passed actions |
| 14 | 4 Action utilities exist | **PASSED** | `utility_RETRY/NUDGE/ESCALATE/STOP` present for all rows |
| 15 | 4 Guardrail states exist | **PASSED** | `guardrail_RETRY/NUDGE/ESCALATE/STOP` present for all rows |
| 16 | Valid selected action | **PASSED** | Exactly one of {RETRY, NUDGE, ESCALATE, STOP} |
| 17 | Selected action valid | **PASSED** | `guardrail_<selected_action> == PASSED` for 100% of rows |
| 18 | Selected action max utility | **PASSED** | `selected_action == argmax(valid utilities)` for 100% of rows |
| 19 | Probability alignment | **PASSED** | `recovery_probability == effective_probability_<selected_action>` |
| 20 | Expected amount formula | **PASSED** | $\text{expected\_amount} == \text{payment\_value} \times P$ |
| 21 | Non-negative recovered amount | **PASSED** | All amounts $\ge 0.00$ BRL |
| 22 | Amount cap | **PASSED** | All recovered amounts $\le \text{payment\_value}$ |
| 23 | `recovered=0` condition | **PASSED** | 100% of unrecovered cases have `recovered_amount = 0.00` |
| 24 | `recovered=1` condition | **PASSED** | 100% of recovered cases have `recovered_amount = payment_value` |
| 25 | Zero temporal leakage | **PASSED** | Customer history computed using $T_{\text{past}} < T_0$ only |
| 26 | Attempt independence | **PASSED** | `recovery_attempt_number` independent of `payment_sequential` |
| 27 | Hours variation | **PASSED** | `hours_since_failure` has std=20.7, 716 unique values |
| 28 | Time decay active | **PASSED** | Higher hours_since_failure reduces probability |
| 29 | Reproducibility test | **PASSED** | Pass 1 and Pass 2 outputs 100% byte-identical |
| 30 | Raw input protection | **PASSED** | Raw Olist SHA256 checksums verified unchanged |

---

## 10. Simulation vs. Real-World Evidence Statement

```
┌────────────────────────────────────────────────────────────────────────┐
│                 SIMULATION VS. REAL-WORLD EVIDENCE                     │
├────────────────────────────────────────────────────────────────────────┤
│ • Olist supplies the empirical transaction foundation (payment_value,   │
│   payment_type, timestamps, customer identity).                        │
│ • Failure reasons, recovery probabilities, recovery actions,          │
│   guardrails, and recovery outcomes are CONTROLLED SIMULATION          │
│   CONSTRUCTS engineered for policy evaluation.                         │
│ • This dataset is NOT a log of historical Olist payment failures.      │
│ • The 53.76% recovery rate is a SIMULATED EVALUATION METRIC, not a     │
│   historical Olist or production Razorpay recovery rate.               │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 11. Document & Step Status

```
STEP 4E-4 STATUS: CORRECTED IMPLEMENTATION COMPLETE
```

**Next Step:** `DATASET REVIEW BEFORE MODEL DEVELOPMENT`
*(No model development or agent code has been started).*
