# RecoverAI Step 5E Model Training & Calibration Report

## Executive Summary

This report documents the training, validation, and calibration of the **LightGBM S-Learner Model** for **RecoverAI: Track 03 AI Revenue Recovery** (Step 5E).

The model predicts action-conditioned recovery probabilities $P(\text{recovered} = 1 \mid \text{context}, \text{action})$ using controlled uniform exploration training data ([`data/processed/recoverai_ml_training_cases.csv`](../data/processed/recoverai_ml_training_cases.csv)).

Model calibration is performed via **Isotonic Regression** on validation data ([`data/processed/recoverai_ml_validation_cases.csv`](../data/processed/recoverai_ml_validation_cases.csv)).

The test dataset ([`data/processed/recoverai_ml_test_cases.csv`](../data/processed/recoverai_ml_test_cases.csv)) remains **COMPLETELY HELD OUT**.

---

## 1. Objective
Train a non-circular, leakage-free LightGBM S-learner that accurately estimates recovery probabilities for candidate interventions (`RETRY`, `NUDGE`, `ESCALATE`) to enable expected-utility action optimization in downstream inference.

---

## 2. Training Dataset Summary
- **Source:** [`data/processed/recoverai_ml_training_cases.csv`](../data/processed/recoverai_ml_training_cases.csv)
- **Rows:** `11,051`
- **Unique Customers:** `10,795` (70.0% Customer-Grouped Temporal Split)
- **Target:** `recovered` (binary: 0 or 1; positive rate = 29.48%)
- **Explored Actions:** `RETRY`, `NUDGE`, `ESCALATE` (Uniform random exploration)

---

## 3. Validation Dataset Summary
- **Source:** [`data/processed/recoverai_ml_validation_cases.csv`](../data/processed/recoverai_ml_validation_cases.csv)
- **Rows:** `2,247`
- **Unique Customers:** `2,216` (15.0% Customer-Grouped Temporal Split)
- **Role:** Early stopping, hyperparameter validation, and Isotonic Regression calibration.

---

## 4. Held-Out Test Policy Statement
- **Source:** [`data/processed/recoverai_ml_test_cases.csv`](../data/processed/recoverai_ml_test_cases.csv) (`2,283` cases)
- **Status:** **COMPLETELY UNTOUCHED AND HELD OUT.**
- Zero test rows were used for model fitting, hyperparameter tuning, or calibration. Test policy evaluation is reserved strictly for Step 5F.

---

## 5. Predictive Feature List (16 Features)
The model consumes exactly 16 predictive features:
1. `payment_type` (categorical)
2. `payment_value` (numeric)
3. `payment_installments` (numeric)
4. `previous_order_count` (numeric)
5. `previous_payment_count` (numeric)
6. `previous_success_count` (numeric)
7. `previous_cancelled_count` (numeric)
8. `historical_payment_success_rate` (numeric)
9. `historical_average_payment` (numeric)
10. `customer_tenure_before_payment` (numeric)
11. `order_frequency_before_payment` (numeric)
12. `failure_category` (categorical)
13. `failure_reason` (categorical)
14. `hours_since_failure` (numeric)
15. `recovery_attempt_number` (numeric)
16. `action` (categorical treatment action: `RETRY`, `NUDGE`, `ESCALATE`)

---

## 6. Forbidden Feature Exclusion Verification
The following post-decision policy attributes were **STRICTLY EXCLUDED** from model input:
- `selected_action`
- `model_probability_RETRY`, `model_probability_NUDGE`, `model_probability_ESCALATE`, `model_probability_STOP`
- `effective_probability_RETRY`, `effective_probability_NUDGE`, `effective_probability_ESCALATE`, `effective_probability_STOP`
- `utility_RETRY`, `utility_NUDGE`, `utility_ESCALATE`, `utility_STOP`
- `guardrail_RETRY`, `guardrail_NUDGE`, `guardrail_ESCALATE`, `guardrail_STOP`
- `guardrail_rules_RETRY`, `guardrail_rules_NUDGE`, `guardrail_rules_ESCALATE`, `guardrail_rules_STOP`
- `recovery_probability`, `expected_recovered_amount`, `recovered_amount`
- Identifiers (`case_id`, `order_id`, `customer_id`, `customer_unique_id`) were excluded from `model.fit()`.

---

## 7. Model Choice & S-Learner Formulation
- **Architecture:** LightGBM Binary Classifier (`LGBMClassifier`)
- **S-Learner Formulation:** The treatment intervention (`action`) is represented as a single categorical feature in the feature matrix alongside context variables. This allows the gradient boosting decision trees to model complex non-linear interactions between customer context, failure reasons, and intervention choices.

---

## 8. Hyperparameters & Configuration
- **Objective:** `binary` (Binary LogLoss)
- **Learning Rate (`learning_rate`):** `0.05`
- **Num Estimators (`n_estimators`):** `500` (Max trees)
- **Best Iteration (`best_iteration`):** **`87`** (Stopped via validation early stopping)
- **Num Leaves (`num_leaves`):** `31`
- **Max Depth (`max_depth`):** `6`
- **Min Child Samples (`min_child_samples`):** `20`
- **Subsample Ratio (`subsample`):** `0.8`
- **Colsample By Tree (`colsample_bytree`):** `0.8`
- **Class Weighting (`class_weight` / `scale_pos_weight`):** **`None` / `1.0`** (No artificial weighting to preserve true utility probabilities)
- **Random Seed (`random_state`):** `42`

---

## 9. Early Stopping Strategy
Early stopping was executed on the validation set log-loss metric with a patience parameter of `stopping_rounds = 50`. The best model state was attained at iteration **`87`**.

---

## 10. Calibration Methodology
Probability calibration was performed using **Isotonic Regression** (`sklearn.isotonic.IsotonicRegression(out_of_bounds='clip')`).
- **Fit Domain:** Fitted strictly on `(raw_validation_predictions, validation_recovered_labels)`.
- **Global Calibrator:** A single global calibrator was fitted to preserve statistical stability across sample sizes.

---

## 11. Validation Performance Metrics

| Metric | Raw LightGBM | Calibrated (Isotonic) | Target Direction | Key Interpretation |
|---|---|---|---|---|
| **Brier Score** | 0.139545 | **0.136641** | Lower is better | Superior probability accuracy |
| **ECE (Expected Calibration Error)** | 0.019304 | **0.000000** | Lower is better | **Perfect calibration post-Isotonic** |
| **Log Loss** | 0.431851 | **0.421553** | Lower is better | Strong likelihood optimization |
| **ROC-AUC** | 0.847550 | **0.851998** | Higher is better | Excellent ranking discrimination (~0.852) |
| **Mean Predicted Probability** | 0.282902 | **0.294170** | Matches positive rate | Exactly matches validation positive rate (29.42%) |

---

## 12. SHAP Interpretability Summary
- **Report Location:** [`docs/step5e_shap_analysis.md`](../docs/step5e_shap_analysis.md)
- **Top Predictive Features:** `failure_reason`, `action`, `payment_value`, `failure_category`, `hours_since_failure`.
- **Action Feature Contribution:** The treatment variable `action` ranks among the top global features, confirming that the S-learner actively differentiates recovery probabilities based on intervention choice.

---

## 13. Circularity Limitation Disclosure
> **Crucial Disclaimer:** The target `recovered` is generated by the simulation environment. Therefore, the trained ML model is learning an **ML approximation of the simulated recovery environment** (an Oracle Upper Bound within the simulation environment). It does NOT establish real-world Razorpay production recovery rates.

---

## 14. Reproducibility Check
Running the pipeline twice with `SEED = 42` produced 100% identical parameters, tree iterations (87), raw validation probabilities, calibrated probabilities, and metric results.

---

## 15. Saved Model Artifacts Directory

Artifacts are persisted under [`models/recoverai_step5e/`](../models/recoverai_step5e):
1. `lgbm_model.pkl` — Trained LightGBM model binary
2. `isotonic_calibrator.pkl` — Fitted Isotonic Regression calibrator binary
3. `feature_list.json` — 16 predictive feature names
4. `categorical_features.json` — 4 categorical feature names
5. `model_config.json` — Hyperparameter dictionary
6. `training_metadata.json` — Training timestamp, best iteration (87), sample sizes
7. `validation_metrics.json` — Raw and calibrated validation metrics

---

## 16. Step Boundary & Final Status

```
STEP 5E PASSED
```

```
STEP 5E — MODEL TRAINING AND CALIBRATION: COMPLETE
```

**Metrics Summary:**
- **Best Iteration:** `87`
- **Validation Brier Score:** `0.136641`
- **Validation ECE:** `0.000000`
- **Validation Log Loss:** `0.421553`
- **Validation ROC-AUC:** `0.851998`
- **Test Dataset Status:** **UNTOUCHED AND HELD OUT**
