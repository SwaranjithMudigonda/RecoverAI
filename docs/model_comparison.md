# RecoverAI: Supplementary Model Comparison — LightGBM vs Logistic Regression

> **THIS IS A SUPPLEMENTARY EXPERIMENT ONLY.**
> The existing LightGBM + Isotonic pipeline remains the official, frozen RecoverAI model.
> This document does NOT replace, modify, or invalidate the official Step 5F evaluation.

---

## 1. Why Logistic Regression Was Selected

Logistic Regression was chosen as the supplementary comparison model because:

- It provides a transparent, fully interpretable linear baseline for binary classification.
- It outputs calibrated probabilities natively through the logistic (sigmoid) function.
- Comparing against a linear model quantifies the value of non-linear feature interactions captured by LightGBM's tree ensemble.
- It is the standard baseline model for binary classification benchmarks.
- It requires minimal hyperparameter specification, reducing the risk of overfitting to the evaluation procedure.

## 2. Exact Training Data Used

| Dataset | Path | Rows | Status |
|---|---|---|---|
| Training | `data/processed/recoverai_ml_training_cases.csv` | 11,051 | Frozen, read-only |
| Validation | `data/processed/recoverai_ml_validation_cases.csv` | 2,247 | Frozen, read-only (action/outcome generated at runtime with seed=42) |
| Test | `data/processed/recoverai_ml_test_cases.csv` | 2,283 | Frozen, read-only |

Split methodology: Customer-Grouped Temporal Split (70/15/15). Zero customer overlap across splits.

## 3. Feature Representation

Both models use the same 16 semantic features in the S-learner design:

**12 Numeric Features:** `payment_value`, `payment_installments`, `previous_order_count`, `previous_payment_count`, `previous_success_count`, `previous_cancelled_count`, `historical_payment_success_rate`, `historical_average_payment`, `customer_tenure_before_payment`, `order_frequency_before_payment`, `hours_since_failure`, `recovery_attempt_number`

**4 Categorical Features:** `payment_type` (4 values), `failure_category` (5 values), `failure_reason` (15 values), `action` (3 values)

### Preprocessing Differences

| Aspect | Model A (LightGBM) | Model B (Logistic Regression) |
|---|---|---|
| Categorical encoding | Native LightGBM categorical dtype | OneHotEncoder (fitted on training only) |
| Numeric scaling | None (trees are scale-invariant) | StandardScaler (fitted on training only) |
| Feature dimensionality | 16 | 39 (12 scaled numeric + 27 one-hot indicators) |

**Why StandardScaler:** LR uses L2 regularization (C=1.0) which penalizes coefficient magnitude proportionally. Without scaling, `payment_value` (range 0.01–6929) would receive disproportionately small coefficients relative to `historical_payment_success_rate` (range 0–1). Scaling preserves rank orderings and does not introduce information unavailable to Model A.

**Note:** `recovery_attempt_number` is constant (all=1) across all data. It is retained for semantic feature parity. It contributes zero information to both models.

## 4. Treatment/Action Representation

S-learner design: `action` ∈ {RETRY, NUDGE, ESCALATE} is included as a feature. STOP never appears in training data. At test time, each model predicts P(recovered=1 | context, action) for all 3 active actions, then selects via utility maximization.

## 5. Train/Validation/Test Boundaries

- Customer-Grouped Temporal Split with zero customer overlap
- Training: 11,051 cases (action+recovered pre-generated via uniform exploration, seed=42)
- Validation: 2,247 cases (action+recovered generated at runtime using same simulator formula + seed=42)
- Test: 2,283 cases (outcomes determined by CRN with seed=999)
- No test information used during training, preprocessing, calibration, or model selection

## 6. Calibration Methodology

| Model | Calibration Method | Details |
|---|---|---|
| Model A | Frozen `isotonic_calibrator.pkl` | Fitted on LightGBM validation predictions → validation labels |
| Model B | Separate `lr_isotonic_calibrator.pkl` | Fitted on LR validation predictions → same validation labels |

Both use `sklearn.isotonic.IsotonicRegression(out_of_bounds="clip")`.

Raw (uncalibrated) LR metrics are also reported for comparison.

## 7. Model A vs Model B Metrics

### Test Set Probability Metrics (N = 2,283)

| Metric | Model A (LightGBM) | Model B (LR, Calibrated) | Model B (LR, Raw) | Better (Cal.) |
|---|---|---|---|---|
| ROC-AUC | 0.6879 | 0.6856 | 0.6880 | Model A |
| Brier Score | 0.2227 | 0.2207 | 0.2226 | Model B |
| ECE | 0.0264 | 0.0338 | 0.0460 | Model A |
| Log Loss | 0.6514 | 0.6295 | 0.6346 | Model B |

**Summary:** Model A wins on ROC-AUC (discrimination) and ECE (calibration). Model B wins on Brier Score and Log Loss. All differences are small in absolute terms.

## 8. Policy Comparison

This comparison uses the exact Step 5F evaluation methodology (same CRN seed=999, same guardrails GR01–GR06, same utility/cost structure, same policy selection logic, same simulator probability formula).

**Cross-check:** Rule-Based and Upper Bound baselines computed independently by Model B's evaluation match the frozen Step 5F values exactly (within floating-point precision), confirming identical evaluation environments.

| Metric | Model A (LightGBM) | Model B (LR) | Rule-Based | Upper Bound |
|---|---|---|---|---|
| Net Utility (BRL) | 179,015.96 | 154,694.06 | 173,068.42 | 179,176.76 |
| Recovered Revenue (BRL) | 184,987.96 | 158,177.56 | — | — |
| Recovery Rate (%) | 52.30 | 45.16 | — | — |
| Regret vs Upper Bound (BRL) | 160.80 | 24,482.70 | — | 0.00 |

**Key Finding:** Model A (LightGBM) substantially outperforms Model B (LR) in policy evaluation:
- +24,321.90 BRL higher net utility
- +26,810.40 BRL more recovered revenue
- +7.14 percentage points higher recovery rate
- 152× lower regret vs the oracle upper bound

Model B performs **worse than the Rule-Based baseline** on net utility (−18,374.36 BRL below Rule-Based), while Model A outperforms it (+5,947.54 BRL above Rule-Based).

### Model B Bootstrap 95% Confidence Intervals

| Metric | Mean | 95% CI Lower | 95% CI Upper |
|---|---|---|---|
| LR Net Utility (BRL) | 154,605.23 | 139,119.89 | 170,716.22 |
| LR Recovery Rate (%) | 45.17 | 43.02 | 47.18 |
| Net Utility Lift vs RB (BRL) | −18,374.37 | −27,653.99 | −10,621.27 |
| Regret vs UB (BRL) | 24,531.50 | 16,975.56 | 33,600.19 |

The 95% confidence interval for LR's net utility lift vs Rule-Based is entirely negative, confirming that Model B's policy underperformance is statistically significant.

## 9. Interpretation

The comparison reveals a nuanced picture:

**Probability metrics are mixed:** LR achieves comparable or slightly better Brier Score and Log Loss, suggesting that its probability estimates are reasonable. However, its ECE is worse, indicating poorer calibration — the raw probabilities from the Isotonic calibrator are less well-aligned with observed frequencies.

**Policy performance strongly favors LightGBM:** Despite similar probability-level metrics, LightGBM's policy vastly outperforms LR's. This is because:

1. **Non-linear interactions matter:** The simulator's ground-truth probability depends on action×category interactions (e.g., RETRY is highly effective for SOFT_DECLINE but harmful for HARD_DECLINE). LightGBM can learn these interaction effects via tree splits, while LR can only model them through the one-hot encoded main effects.

2. **Policy metrics amplify discrimination differences:** Small differences in ROC-AUC (0.0023) translate to large differences in action selection quality. LightGBM more accurately identifies which action has the highest recovery probability for each case, leading to better utility-maximizing decisions.

3. **LR selects suboptimal actions:** LR's less accurate probability estimates lead to selecting lower-utility actions more frequently, compounding into substantially lower recovered revenue and higher regret.

## 10. Limitations

1. All outcomes are simulated. Performance measures simulated environment recovery, not real-world behavior.
2. Test metrics are policy-coupled: each model is evaluated on its own selected actions.
3. LightGBM has a structural advantage from native categorical handling vs. one-hot encoding.
4. StandardScaler is applied for LR only — this is model-appropriate, not a confound.
5. `recovery_attempt_number` is constant, providing zero information to either model.
6. LR hyperparameters (C=1.0) were not tuned. Validation-set tuning might improve LR, but test-set tuning was correctly avoided.
7. The comparison uses a single CRN realization (seed=999).

## 11. Supplementary Experimentation Statement

This model comparison is a **supplementary scientific experiment**. It was conducted to evaluate whether a simpler linear model could achieve comparable performance to the frozen LightGBM model within the RecoverAI simulation environment.

The results are informational only. They do NOT constitute a recommendation to replace, modify, or extend the frozen production pipeline.

## 12. Frozen Pipeline Statement

**The existing LightGBM + Isotonic Calibration pipeline remains the official, frozen RecoverAI model.**

The following artifacts remain byte-identical (verified via SHA-256 before and after the experiment):
- All datasets (raw cases, training, validation, test, Step 5F results)
- LightGBM model and Isotonic calibrator
- Feature list, categorical features, model config
- RecoverAI agent, REST API server, batch runner

Model B has NOT been integrated into any production or prototype component.
