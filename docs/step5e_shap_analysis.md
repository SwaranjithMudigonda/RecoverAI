# RecoverAI Step 5E: SHAP Interpretability Analysis Report

## Overview
This report presents the SHAP (SHapley Additive exPlanations) interpretability analysis for the trained **LightGBM S-learner model** (Step 5E).

The analysis was computed on the validation dataset (`data/processed/recoverai_ml_validation_cases.csv`, 2247 cases) using `shap.TreeExplainer`.

> **Disclaimer on Causality:**
> SHAP values describe how model features influence the model's predicted recovery probability within the simulated environment. They do not establish causal effects in real-world payment behavior.

---

## 1. Global Feature Importance Ranking

Top features ranked by mean absolute SHAP value:

| Rank | Feature Name | Feature Type | Mean Absolute SHAP | Importance Category |
|---|---|---|---|---|
| 1 | `action` | Categorical | 0.874690 | High |
| 2 | `failure_category` | Categorical | 0.393818 | High |
| 3 | `hours_since_failure` | Numeric | 0.282309 | High |
| 4 | `failure_reason` | Categorical | 0.168827 | High |
| 5 | `payment_value` | Numeric | 0.055092 | High |
| 6 | `historical_payment_success_rate` | Numeric | 0.049419 | Medium |
| 7 | `historical_average_payment` | Numeric | 0.015847 | Medium |
| 8 | `payment_type` | Categorical | 0.015153 | Medium |
| 9 | `payment_installments` | Numeric | 0.014090 | Medium |
| 10 | `customer_tenure_before_payment` | Numeric | 0.013021 | Medium |
| 11 | `previous_order_count` | Numeric | 0.010706 | Low |
| 12 | `previous_success_count` | Numeric | 0.007031 | Low |
| 13 | `order_frequency_before_payment` | Numeric | 0.006658 | Low |
| 14 | `previous_payment_count` | Numeric | 0.001404 | Low |
| 15 | `previous_cancelled_count` | Numeric | 0.000000 | Low |
| 16 | `recovery_attempt_number` | Numeric | 0.000000 | Low |

---

## 2. Key Insights & Action Feature Contribution

1. **`action` Contribution:**
   - The categorical treatment feature `action` ranks among the top features, demonstrating that the S-learner actively conditions its recovery probability predictions on the selected recovery intervention (`RETRY`, `NUDGE`, `ESCALATE`).

2. **Contextual Drivers:**
   - `failure_reason` and `failure_category` provide major predictive signal, differentiating technical soft declines from customer authentication issues.
   - `payment_value` and `hours_since_failure` provide continuous logit moderation.

---

## 3. Summary Statement
The SHAP analysis confirms that the LightGBM S-learner has successfully learned feature relationships from the controlled uniform exploration dataset without utilizing forbidden post-decision fields.
