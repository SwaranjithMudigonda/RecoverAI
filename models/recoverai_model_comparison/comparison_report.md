# RecoverAI: Supplementary Model Comparison Report

> **THIS IS A SUPPLEMENTARY EXPERIMENT ONLY.**
> The existing LightGBM + Isotonic pipeline remains the official, frozen RecoverAI model.
> This report does NOT replace, modify, or invalidate the official Step 5F evaluation.

---

## 1. Motivation

This supplementary experiment compares the frozen LightGBM S-Learner (Model A) against a
Logistic Regression S-Learner (Model B) to assess whether a simpler linear model can achieve
comparable performance in the RecoverAI recovery probability prediction task.

Logistic Regression was selected because:
- It provides a transparent, interpretable linear baseline.
- It outputs calibrated probabilities natively (log-odds → sigmoid).
- Comparing against a linear model quantifies the value of non-linear interactions captured by LightGBM.
- It is the standard baseline for binary classification tasks.

## 2. Frozen Model A Description

- **Model:** LightGBM S-Learner (87 boosting rounds, early stopped from 500)
- **Calibration:** Isotonic Regression fitted on validation predictions
- **Artifacts:** Frozen `lgbm_model.pkl`, `isotonic_calibrator.pkl`
- **Status:** Official RecoverAI model — NEVER modified

## 3. Model B Description

- **Model:** `sklearn.linear_model.LogisticRegression(solver='lbfgs', C=1.0, max_iter=1000, random_state=42)`
- **Calibration:** Separate `IsotonicRegression(out_of_bounds='clip')` fitted on Model B's own validation predictions
- **Preprocessing:** OneHotEncoder (categoricals) + StandardScaler (numerics), both fitted on training data only
- **Status:** Supplementary experiment — NOT integrated into any production component

## 4. Data and Split Boundaries

| Split | Path | Rows | Contains action/recovered |
|---|---|---|---|
| Training | `recoverai_ml_training_cases.csv` | 11,051 | Yes (pre-generated, seed=42) |
| Validation | `recoverai_ml_validation_cases.csv` | 2,247 | No (generated at runtime, seed=42) |
| Test | `recoverai_ml_test_cases.csv` | 2,283 | No (CRN evaluation, seed=999) |

Split method: Customer-Grouped Temporal Split (70/15/15). Zero customer overlap across splits.

## 5. Feature Representation

Both models use the same 16 semantic features:
- **12 Numeric:** payment_value, payment_installments, previous_order_count, previous_payment_count,
  previous_success_count, previous_cancelled_count, historical_payment_success_rate,
  historical_average_payment, customer_tenure_before_payment, order_frequency_before_payment,
  hours_since_failure, recovery_attempt_number
- **4 Categorical:** payment_type, failure_category, failure_reason, action

Model A: categoricals as native LightGBM category dtype; numerics raw (no scaling).
Model B: categoricals one-hot encoded; numerics StandardScaler'd. Both fitted on training data only.

Note: `recovery_attempt_number` is constant (all=1) in the training data. It is retained for
semantic feature parity. It contributes zero information to both models.

## 6. Treatment/Action Representation

S-learner design: `action` ∈ {RETRY, NUDGE, ESCALATE} is a feature. STOP never appears in training.
At test time, each model predicts P(recovered | context, action) for all 3 active actions.

## 7. Calibration

- **Model A:** Frozen Isotonic calibrator fitted on LightGBM validation predictions → validation labels.
- **Model B:** Separate Isotonic calibrator fitted on LR validation predictions → same validation labels.
- Both calibrators use `IsotonicRegression(out_of_bounds="clip")`.
- Raw (uncalibrated) LR metrics are also reported below.

## 8. Evaluation Methodology

Identical Step 5F methodology for both models:
- CRN_SEED = 999 (shared uniform draws)
- Same guardrail rules (GR01–GR06)
- Same utility/cost structure
- Same policy selection (argmax utility + negative-utility fallback)
- Same simulator probability formula
- Metrics are policy-coupled: each model evaluated on its own selected actions

## 9. Model A Results (Frozen Step 5F)

| Metric | Value |
|---|---|
| ROC-AUC | 0.687857 |
| Brier Score | 0.222695 |
| ECE | 0.026444 |
| Log Loss | 0.651352 |
| N | 2283 |

## 10. Model B Results

### Calibrated (Primary Comparison)

| Metric | Value |
|---|---|
| ROC-AUC | 0.685551 |
| Brier Score | 0.220716 |
| ECE | 0.033844 |
| Log Loss | 0.629494 |
| N | 2283 |

### Raw (Uncalibrated)

| Metric | Value |
|---|---|
| ROC-AUC | 0.688000 |
| Brier Score | 0.222571 |
| ECE | 0.046020 |
| Log Loss | 0.634609 |
| N | 2283 |

## 11. Metric-by-Metric Comparison

| Metric | Model A | Model B (Cal.) | Abs Diff | Rel Diff (%) | Better |
|---|---|---|---|---|---|
| ROC-AUC | 0.687857 | 0.685551 | -0.002307 | -0.34% | Model A |
| Brier Score | 0.222695 | 0.220716 | -0.001979 | -0.89% | Model B |
| ECE | 0.026444 | 0.033844 | +0.007400 | +27.98% | Model A |
| Log Loss | 0.651352 | 0.629494 | -0.021858 | -3.36% | Model B |

## 12. Policy Comparison

This comparison is valid because it uses the exact same Step 5F evaluation methodology
(identical CRN, guardrails, utility/cost structure, policy selection, simulator formula).

| Metric | Model A (LightGBM) | Model B (LR) | Rule-Based | Upper Bound |
|---|---|---|---|---|
| Net Utility (BRL) | 179015.96 | 154694.06 | 173068.42 | 179176.76 |
| Recovered Revenue (BRL) | 184987.96 | 158177.56 | — | — |
| Recovery Rate (%) | 52.30 | 45.16 | — | — |
| Regret vs Upper Bound (BRL) | 160.80 | 24482.70 | — | 0.00 |

### Model B Bootstrap 95% Confidence Intervals

| Metric | Mean | 95% CI Lower | 95% CI Upper |
|---|---|---|---|
| LR Net Utility (BRL) | 154605.23 | 139119.89 | 170716.22 |
| LR Recovered Revenue (BRL) | 158087.11 | 142570.73 | 174181.18 |
| LR Recovery Rate (%) | 45.17 | 43.02 | 47.18 |
| Net Utility Lift vs RB (BRL) | -18374.37 | -27653.99 | -10621.27 |
| Regret vs UB (BRL) | 24531.50 | 16975.56 | 33600.19 |

## 13. Interpretation

The comparison shows the relative performance of a non-linear tree ensemble (LightGBM) versus
a linear model (Logistic Regression) on the same prediction task using the same evaluation protocol.

Both models were given identical training data, the same semantic features, and were evaluated
under the same controlled conditions. The only intended differences are the model class,
the required categorical encoding, and the numeric scaling.

## 14. Limitations

1. All outcomes are simulated. Performance measures simulated environment recovery, not real-world behavior.
2. Test metrics are policy-coupled: each model is evaluated on its own selected actions. Direct metric
   comparison is meaningful but not equivalent to evaluating both models on the same fixed action set.
3. LightGBM has a structural advantage from native categorical handling (optimal subset splits)
   compared to one-hot encoding used by LR.
4. StandardScaler is applied for LR but not for LightGBM — this is model-appropriate, not a confound.
5. `recovery_attempt_number` is constant (all=1), providing zero information to either model.
6. The comparison is based on a single CRN realization (seed=999). Different seeds would produce
   different outcome realizations, though the expected-value comparison remains stable.
7. Model B hyperparameters (C=1.0) were not tuned. A grid search on validation data might improve LR,
   but this was not performed to avoid any risk of test-set influence.

## 15. Final Conclusion

This supplementary experiment provides a controlled comparison between the frozen LightGBM model
and a Logistic Regression baseline under identical evaluation conditions.

The results above should be interpreted as evidence of relative model performance within the
RecoverAI simulation environment. They do NOT change any official Step 5F result.

## 16. Official Status Statement

**The existing LightGBM + Isotonic Calibration pipeline remains the official, frozen RecoverAI model.**

This Logistic Regression experiment is supplementary scientific analysis only. It has NOT been:
- Integrated into the RecoverAI agent
- Integrated into the REST API
- Integrated into the batch runner
- Integrated into the dashboard
- Used to replace or modify any frozen artifact

All 14 frozen artifact SHA-256 hashes have been verified byte-identical before and after this experiment.
