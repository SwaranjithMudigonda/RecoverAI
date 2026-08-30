# RecoverAI Step 6A Implementation Report: Agent Input & Feature Builder

## Executive Summary

This report documents the implementation and validation of **Step 6A: RecoverAI Agent Input & Feature Builder** for **RecoverAI: Track 03 AI Revenue Recovery**.

The newly created module ([`src/recoverai_agent.py`](../src/recoverai_agent.py)) provides a robust, leakage-free context validation and feature construction pipeline for failed-payment transaction inputs.

Generated Artifacts:
1. Agent Module: [`src/recoverai_agent.py`](../src/recoverai_agent.py)
2. Report Document: [`docs/step6a_agent_feature_builder_report.md`](../docs/step6a_agent_feature_builder_report.md)

---

## 1. Frozen Artifacts Loaded

The agent loads and enforces the exact frozen model artifacts from Step 5E ([`models/recoverai_step5e/`](../models/recoverai_step5e)):
- `lgbm_model.pkl` (Trained LightGBM S-Learner)
- `isotonic_calibrator.pkl` (Fitted Isotonic Calibrator)
- `feature_list.json` (Exact 16 predictive features schema)
- `categorical_features.json` (4 categorical features: `payment_type`, `failure_category`, `failure_reason`, `action`)

---

## 2. Feature Schema & Types (16 Predictive Features)

| Feature Name | Data Type | Role in Model | Valid Range / Categories |
|---|---|---|---|
| `payment_type` | Categorical | Payment Method | `credit_card`, `debit_card`, `boleto`, `voucher` |
| `payment_value` | Float64 | Transaction Value | Numeric > 0.0 BRL |
| `payment_installments` | Int64 | Installments Count | Numeric $\ge 1$ |
| `previous_order_count` | Int64 | Historical Orders | Numeric $\ge 0$ |
| `previous_payment_count` | Int64 | Historical Payments | Numeric $\ge 0$ |
| `previous_success_count` | Int64 | Historical Successes | Numeric $\ge 0$ |
| `previous_cancelled_count` | Int64 | Historical Cancels | Numeric $\ge 0$ |
| `historical_payment_success_rate` | Float64 | Historical Reliability | Numeric $[0.0, 1.0]$ |
| `historical_average_payment` | Float64 | Historical Ticket | Numeric $\ge 0.0$ BRL |
| `customer_tenure_before_payment` | Int64 | Tenure (Days) | Numeric $\ge 0$ |
| `order_frequency_before_payment` | Float64 | Frequency (Days/Order) | Numeric $\ge 0.0$ |
| `failure_category` | Categorical | Failure Subtype | `SOFT_DECLINE`, `FUNDS_ISSUE`, `CUSTOMER_ACTION_REQUIRED`, `HARD_DECLINE`, `GENERIC_DECLINE` |
| `failure_reason` | Categorical | Decline Reason | 16 Canonical failure reasons |
| `hours_since_failure` | Float64 | Failure Age | Numeric $\ge 0.0$ hours |
| `recovery_attempt_number` | Int64 | Attempt Index | Numeric $\ge 1$ |
| `action` | Categorical | Treatment Intervention | `RETRY`, `NUDGE`, `ESCALATE` |

---

## 3. Validation Rules & Rejection Logic

1. **Rejection of Forbidden Leakage Fields:** Any input context containing post-decision policy fields (e.g. `selected_action`, `model_probability_*`, `effective_probability_*`, `utility_*`, `guardrail_*`, `recovery_probability`, `expected_recovered_amount`, `recovered_amount`, `recovered`) is immediately flagged and rejected as INVALID.
2. **Identifier Exclusion:** Case and customer identifiers (`case_id`, `order_id`, `customer_id`, `customer_unique_id`) are excluded from model input features.
3. **Bound Checks:** Numeric features are checked for type validity and valid value ranges ($V_i > 0$, success rate $\in [0, 1]$, etc.).
4. **Categorical Consistency:** Categorical attributes are validated against allowed canonical values and encoded with Pandas `category` dtype.

---

## 4. Self-Test Result

The module contains a self-test loading 1 valid context from `recoverai_ml_test_cases.csv` (excluding outcome columns):

```json
{
  "status": "VALID",
  "features_validated": true,
  "available_actions": [
    "RETRY",
    "NUDGE",
    "ESCALATE"
  ]
}
```

- **Status:** **PASSED**
- **Feature DataFrame:** Constructed 1-row DataFrame matching the exact 16 feature columns and dtypes.

---

## 5. Artifact Protection & Step Boundaries

- **Steps 4E–5F Files:** **100% UNTOUCHED AND UNMODIFIED.**
- **Model Training:** **NO model re-training or hyperparameter modification.**
- **Action Selection & Utility:** Deferred to Step 6B.

---

## 6. Step Boundary Verdict

```
STEP 6A PASSED
```

```
STEP 6A — RECOVERAI AGENT INPUT & FEATURE BUILDER: COMPLETE
```
