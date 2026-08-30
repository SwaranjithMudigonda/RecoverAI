# RecoverAI ML Training Data Construction Report (Controlled Uniform Exploration)

## Executive Summary

This report documents the construction and validation of the machine learning training, validation, and test datasets for **RecoverAI: Track 03 AI Revenue Recovery** (Step 5D).

To prevent policy circularity and training bias, ML training observations are generated using **Controlled Uniform Exploration** over valid active recovery actions. The existing evaluation dataset ([`data/processed/recoverai_recovery_cases.csv`](../data/processed/recoverai_recovery_cases.csv)) remains **COMPLETELY UNCHANGED**.

Generated Artifacts:
1. Script: [`src/generate_ml_training_data.py`](../src/generate_ml_training_data.py)
2. Training Dataset: [`data/processed/recoverai_ml_training_cases.csv`](../data/processed/recoverai_ml_training_cases.csv) (11,051 cases)
3. Validation Dataset: [`data/processed/recoverai_ml_validation_cases.csv`](../data/processed/recoverai_ml_validation_cases.csv) (2,247 cases)
4. Test Dataset: [`data/processed/recoverai_ml_test_cases.csv`](../data/processed/recoverai_ml_test_cases.csv) (2,283 cases)

---

## 1. Objective

The objective of Step 5D is to construct a non-circular, unbiased ML training dataset where action selection is governed by uniform random exploration over guardrail-valid actions rather than by the deterministic decision policy being evaluated.

---

## 2. Source Data

- **Raw Empirical Inputs:** Kaggle Olist Brazilian E-Commerce dataset (`olist_orders_dataset.csv`, `olist_order_payments_dataset.csv`, `olist_customers_dataset.csv`).
- **Eligible Cases:** 103,877 real Olist payment records (`payment_value > 0`, supported payment types, valid timestamps).
- **Sampled Cases:** 15,581 failure cases sampled via deterministic stratified random sampling (15.0% sample rate, `SEED = 42`).

---

## 3. Split Methodology & Customer Grouping

To guarantee zero customer leakage and respect temporal ordering, a **Customer-Grouped Temporal Split** was implemented:

1. Customers (`customer_unique_id`) were sorted chronologically by their earliest observed purchase timestamp ($T_{\text{first}}$).
2. The sorted customer base was partitioned into:
   - **Train Split:** First 70.0% of customer timeline (67,265 unique customers)
   - **Validation Split:** Next 15.0% of customer timeline (14,414 unique customers)
   - **Test Split:** Final 15.0% of customer timeline (14,414 unique customers)
3. All cases belonging to a customer are assigned strictly to that customer's partition.

---

## 4. Uniform Exploration Methodology

For cases in the **Train Split**:
1. Guardrails are applied to determine active valid actions from `['RETRY', 'NUDGE', 'ESCALATE']`. (`STOP` is excluded from ML training actions).
2. Exactly **ONE** action is selected uniformly at random: $a_{\text{train}} \sim \text{Uniform}(\text{valid\_actions})$.
3. Exactly **ONE** simulated outcome ($y \in \{0, 1\}$) is generated using Bernoulli sampling on the simulation environment's probability model for $a_{\text{train}}$.

---

## 5. Valid-Action Filtering

Safety guardrails strictly filter candidate actions prior to uniform selection:
- **`RETRY`** is **BLOCKED** for:
  - `payment_type == 'boleto'` (`GR01_BOLETO`)
  - `payment_type == 'voucher'` (`GR02_VOUCHER`)
  - `failure_category == 'HARD_DECLINE'` (`GR03_HARD_DECLINE`)
  - `failure_reason \in {'authentication_failed', 'expired_card', 'boleto_expired'}` (`GR04_AUTH_REQ`)
  - `payment_value > 5000.0` with ambiguous decline (`GR06_HIGH_VALUE`)
- **`NUDGE`** & **`ESCALATE`** pass initial safety guardrails as valid intervention options.

---

## 6. Outcome Generation

The binary outcome `recovered` is generated via Bernoulli trial:
$$\text{recovered} \sim \text{Bernoulli}(P_{\text{effective}}(a_{\text{train}}))$$
No probability scores or utilities are saved in the ML feature set.

---

## 7. Feature Schema & Target Definition

### Predictive Features (`data/processed/recoverai_ml_training_cases.csv`)
- `payment_type` (categorical)
- `payment_value` (numeric)
- `payment_installments` (numeric)
- `previous_order_count` (numeric)
- `previous_payment_count` (numeric)
- `previous_success_count` (numeric)
- `previous_cancelled_count` (numeric)
- `historical_payment_success_rate` (numeric)
- `historical_average_payment` (numeric)
- `customer_tenure_before_payment` (numeric)
- `order_frequency_before_payment` (numeric)
- `failure_category` (categorical)
- `failure_reason` (categorical)
- `hours_since_failure` (numeric)
- `recovery_attempt_number` (numeric)
- `action` (explored action: `RETRY`, `NUDGE`, `ESCALATE`)

### ML Target
- `recovered` (binary: 0 = failed, 1 = recovered)

### Audit & Tracing Columns
- `case_id`, `order_id`, `customer_id`, `customer_unique_id`, `order_purchase_timestamp`, `valid_actions_count`, `valid_actions`, `split`, `simulation_seed`, `provenance_version`

---

## 8. Forbidden Features Verification

The following post-decision policy fields are **STRICTLY EXCLUDED** from the ML feature matrix:
- `selected_action`
- `model_probability_RETRY`, `model_probability_NUDGE`, `model_probability_ESCALATE`, `model_probability_STOP`
- `effective_probability_RETRY`, `effective_probability_NUDGE`, `effective_probability_ESCALATE`, `effective_probability_STOP`
- `utility_RETRY`, `utility_NUDGE`, `utility_ESCALATE`, `utility_STOP`
- `guardrail_RETRY`, `guardrail_NUDGE`, `guardrail_ESCALATE`, `guardrail_STOP`
- `guardrail_rules_RETRY`, `guardrail_rules_NUDGE`, `guardrail_rules_ESCALATE`, `guardrail_rules_STOP`
- `recovery_probability`, `expected_recovered_amount`, `recovered_amount`

---

## 9. Dataset Sizes & Partition Summary

| Dataset Partition | Rows (Cases) | Unique Customers | Unique Orders | Role in Pipeline |
|---|---|---|---|---|
| **`recoverai_ml_training_cases.csv`** | **11,051** | 10,795 | 10,904 | Model Training (Uniform Exploration) |
| **`recoverai_ml_validation_cases.csv`** | **2,247** | 2,216 | 2,229 | Hyperparameter Tuning |
| **`recoverai_ml_test_cases.csv`** | **2,283** | 2,253 | 2,267 | Held-out Policy Evaluation |
| **Total Sampled** | **15,581** | **15,264** | **15,354** | |

---

## 10. Uniform Exploration Diagnostics

Action selection distribution verified per valid action count:

### Conditioned on `valid_actions_count == 2` (5,562 cases: NUDGE, ESCALATE)
- **`NUDGE`**: 2,797 (50.29%)
- **`ESCALATE`**: 2,765 (49.71%)
*(Verified 50/50 uniform distribution)*

### Conditioned on `valid_actions_count == 3` (5,489 cases: RETRY, NUDGE, ESCALATE)
- **`ESCALATE`**: 1,836 (33.45%)
- **`RETRY`**: 1,830 (33.34%)
- **`NUDGE`**: 1,823 (33.21%)
*(Verified 33.3/33.3/33.3 uniform distribution)*

### Overall Training Action Proportions
- **`NUDGE`**: 4,620 (41.81%)
- **`ESCALATE`**: 4,601 (41.63%)
- **`RETRY`**: 1,830 (16.56%)

### Overall Target Distribution
- **Failed (`recovered = 0`)**: 7,793 (70.52%)
- **Recovered (`recovered = 1`)**: 3,258 (29.48%)

---

## 11. Mandatory Leakage & Quality Validation Checks (14 Invariants)

| # | Validation Rule | Status | Detail / Result |
|---|---|---|---|
| 1 | Zero customer overlap across splits | **PASSED** | 0 customer IDs overlap between train, val, test |
| 2 | Zero forbidden post-decision columns | **PASSED** | 100% excluded from feature matrix |
| 3 | No `STOP` action in training set | **PASSED** | Exactly 0 STOP actions in training set |
| 4 | Valid training action per case | **PASSED** | 100% of actions belong to valid_actions set |
| 5 | Boleto + RETRY count == 0 | **PASSED** | Exactly 0 Boleto RETRY actions |
| 6 | Voucher + RETRY count == 0 | **PASSED** | Exactly 0 Voucher RETRY actions |
| 7 | Hard decline + RETRY count == 0 | **PASSED** | Exactly 0 Hard decline RETRY actions |
| 8 | Auth failure + RETRY count == 0 | **PASSED** | Exactly 0 Auth failure RETRY actions |
| 9 | 1 training action per case | **PASSED** | 100% unique `case_id`s in training set |
| 10 | 1 outcome per observation | **PASSED** | Zero missing outcome labels |
| 11 | Binary target | **PASSED** | `recovered` $\in \{0, 1\}$ |
| 12 | Zero missing values | **PASSED** | 0 nulls in required ML feature columns |
| 13 | Reproducibility | **PASSED** | Pass 1 and Pass 2 outputs 100% byte-identical |
| 14 | Original dataset unchanged | **PASSED** | `data/processed/recoverai_recovery_cases.csv` checksum verified |

---

## 12. Simulation & Provenance Statement

```
┌────────────────────────────────────────────────────────────────────────┐
│                 SIMULATION VS. REAL-WORLD EVIDENCE                     │
├────────────────────────────────────────────────────────────────────────┤
│ • Olist supplies the empirical transaction context (payment_value,      │
│   payment_type, timestamps, customer identity, prior history).         │
│ • Failure reasons, explored actions, and target recovery outcomes      │
│   are CONTROLLED SIMULATION CONSTRUCTS engineered for non-circular     │
│   counterfactual policy learning.                                      │
│ • This dataset is created specifically for ML model training, not      │
│   historical Olist recovery observation.                               │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 13. Document & Step Status

```
STEP 5D PASSED
```

```
STEP 5D — ML TRAINING DATA CONSTRUCTION: COMPLETE
```

**Next Step:** `MODEL TRAINING / STEP 5E`
*(No ML models have been trained; no model files have been created).*
