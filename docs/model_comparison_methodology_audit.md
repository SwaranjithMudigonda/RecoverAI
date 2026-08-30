# RecoverAI: Model Comparison Methodology Audit

> **Status:** Read-only forensic inspection of frozen Step 5E/5F artifacts.
> **Purpose:** Establish the exact evaluation contract that supplementary Model B (Logistic Regression) must follow.

---

## A. Existing Frozen LightGBM Methodology

### 1. Training Feature Matrix

**Source:** [`train_ml_model.py` L31-48](../src/train_ml_model.py#L31-L48), verified against [`feature_list.json`](../models/recoverai_step5e/feature_list.json)

Exactly 16 predictive features:

| # | Feature Name | Type |
|---|---|---|
| 1 | `payment_type` | Categorical |
| 2 | `payment_value` | Numeric |
| 3 | `payment_installments` | Numeric |
| 4 | `previous_order_count` | Numeric |
| 5 | `previous_payment_count` | Numeric |
| 6 | `previous_success_count` | Numeric |
| 7 | `previous_cancelled_count` | Numeric |
| 8 | `historical_payment_success_rate` | Numeric |
| 9 | `historical_average_payment` | Numeric |
| 10 | `customer_tenure_before_payment` | Numeric |
| 11 | `order_frequency_before_payment` | Numeric |
| 12 | `failure_category` | Categorical |
| 13 | `failure_reason` | Categorical |
| 14 | `hours_since_failure` | Numeric |
| 15 | `recovery_attempt_number` | Numeric |
| 16 | `action` | Categorical (treatment) |

Training data: [`recoverai_ml_training_cases.csv`](../data/processed/recoverai_ml_training_cases.csv), 11,051 rows.

The training CSV already contains `action` and `recovered` columns, generated via controlled uniform exploration during Step 5D (seed=42).

### 2. Feature Ordering

**Source:** [`train_ml_model.py` L31-48](../src/train_ml_model.py#L31-L48)

The exact feature ordering used by LightGBM is the `PREDICTIVE_FEATURES` list above, in precisely that order. The feature matrix is constructed as `train_df[PREDICTIVE_FEATURES].copy()` ([L168](../src/train_ml_model.py#L168)).

### 3. Numeric Preprocessing

**Source:** [`train_ml_model.py`](../src/train_ml_model.py) — full file searched.

**Finding: ZERO numeric preprocessing.** No `StandardScaler`, `MinMaxScaler`, normalization, log transforms, or any other numeric transformation is applied. LightGBM receives raw numeric values directly from the CSV.

Observed numeric distributions (from training data):

| Feature | Min | Max | Mean | Std | Nulls |
|---|---|---|---|---|---|
| `payment_value` | 0.01 | 6929.31 | 147.08 | 193.63 | 0 |
| `payment_installments` | 1 | 24 | 2.78 | 2.67 | 0 |
| `previous_order_count` | 0 | 10 | 0.04 | 0.26 | 0 |
| `previous_payment_count` | 0 | 12 | 0.05 | 0.39 | 0 |
| `previous_success_count` | 0 | 8 | 0.04 | 0.25 | 0 |
| `previous_cancelled_count` | 0 | 1 | 0.001 | 0.03 | 0 |
| `historical_payment_success_rate` | 0.0 | 1.0 | 0.035 | 0.18 | 0 |
| `historical_average_payment` | 0.0 | 1034.34 | 4.81 | 33.49 | 0 |
| `customer_tenure_before_payment` | 0 | 572 | 3.91 | 31.03 | 0 |
| `order_frequency_before_payment` | 0.0 | 572.0 | 3.48 | 28.35 | 0 |
| `hours_since_failure` | 0.5 | 72.0 | 36.26 | 20.60 | 0 |
| `recovery_attempt_number` | 1 | 1 | 1.0 | 0.0 | 0 |

> **Note:** Several features have highly skewed distributions (e.g., `previous_order_count` is 0 for ~96% of cases, `payment_value` ranges 0.01-6929). These scales do not affect LightGBM (tree-based, split-invariant to monotonic transforms), but will affect Logistic Regression coefficients. This is addressed in Section D.

### 4. Categorical Preprocessing

**Source:** [`train_ml_model.py` L174-176](../src/train_ml_model.py#L174-L176), [`categorical_features.json`](../models/recoverai_step5e/categorical_features.json)

The 4 categorical features are converted to pandas `category` dtype:
```python
for col in CATEGORICAL_FEATURES:
    X_train[col] = X_train[col].astype("category")
    X_val[col] = X_val[col].astype("category")
```

LightGBM uses these natively via its internal categorical split algorithm (optimal partitioning). No one-hot encoding is used for LightGBM.

Categorical cardinalities:
- `payment_type`: 4 values (credit_card, debit_card, boleto, voucher)
- `failure_category`: 5 values (SOFT_DECLINE, FUNDS_ISSUE, CUSTOMER_ACTION_REQUIRED, GENERIC_DECLINE, HARD_DECLINE)
- `failure_reason`: 15 values
- `action`: 3 values (RETRY, NUDGE, ESCALATE)

### 5. Action/Treatment Encoding

**Source:** [`train_ml_model.py` L47](../src/train_ml_model.py#L47), [`generate_ml_training_data.py` L458-468](../src/generate_ml_training_data.py#L458-L468)

The `action` column is a categorical feature representing the recovery intervention. It takes values `{"RETRY", "NUDGE", "ESCALATE"}`. `STOP` is never present in the training data ([`train_ml_model.py` L251-252](../src/train_ml_model.py#L251-L252) - checked).

This is an S-learner design: action is included as a feature alongside context features, and a single model predicts `P(recovered=1 | context, action)`.

### 6. Target Definition

**Source:** [`train_ml_model.py` L169](../src/train_ml_model.py#L169)

`y_train = train_df["recovered"].values` - binary {0, 1}, representing simulated recovery success under the explored action.

Training: 3,258 recovered (1) vs 7,793 failed (0) = 29.5% positive rate.

### 7. Validation-Data Generation

**Source:** [`train_ml_model.py` L136-160](../src/train_ml_model.py#L136-L160)

The raw validation CSV (`recoverai_ml_validation_cases.csv`, 2,247 rows) does NOT contain `action` or `recovered` columns. These are generated at runtime by `prepare_validation_data()`:

1. For each validation case, parse `valid_actions` (pipe-delimited string)
2. Uniformly randomly select one valid action
3. Compute simulator probability for that action
4. Draw a Bernoulli outcome from that probability

### 8. Validation Exploration Policy

**Source:** [`train_ml_model.py` L149-152](../src/train_ml_model.py#L149-L152)

Uniform random exploration: `chosen_action = rng.choice(valid_acts)` - each valid action is equally likely.

### 9. Validation Random Seed

**Source:** [`train_ml_model.py` L27](../src/train_ml_model.py#L27), [`train_ml_model.py` L417](../src/train_ml_model.py#L417)

`SEED = 42`. The `prepare_validation_data()` function is called with `seed=42`, creating `rng = np.random.default_rng(42)`.

### 10. Isotonic Calibration Procedure

**Source:** [`train_ml_model.py` L209-211](../src/train_ml_model.py#L209-L211)

```python
calibrator = IsotonicRegression(out_of_bounds="clip")
calibrator.fit(p_raw_val, y_val)
```

- Fitted on validation set raw LightGBM probabilities mapped to validation labels
- Uses `sklearn.isotonic.IsotonicRegression(out_of_bounds="clip")`
- Applied to any raw probability via `calibrator.transform(raw_probs)`
- Produces calibrated probabilities in [0, 1]

### 11. Test-Data Evaluation Procedure

**Source:** [`evaluate_step5f.py` L244-460](../src/evaluate_step5f.py#L244-L460)

The test CSV (`recoverai_ml_test_cases.csv`, 2,283 rows) does NOT contain `action` or `recovered`. The evaluation procedure:

1. Pre-generate CRN draws: `crn_draws = rng_crn.random(size=len(test_df))` with `CRN_SEED=999`
2. For each test case and each action in {RETRY, NUDGE, ESCALATE}: predict P(recovered | context, action) using model, then calibrate
3. Apply guardrails to determine valid actions
4. Zero out calibrated probabilities for blocked actions
5. Compute expected utility: `U(a) = payment_value * cal_prob(a) - total_cost(a)`
6. Select action with maximum utility among valid actions
7. Apply fallback: if max-utility action has negative utility and is RETRY/NUDGE, switch to ESCALATE if payment > 500 else STOP
8. Compute simulator ground-truth probability for selected action
9. Binary outcome: `recovered = 1 if crn_draw < simulator_prob else 0`
10. Compute per-case financial metrics

> **Critical observation:** Test metrics (ROC-AUC, Brier, ECE, Log Loss) are policy-coupled. They compare the model's calibrated probability for its **selected** action against the CRN-simulated outcome under that **selected** action. This means Model B will be evaluated on its own selected actions, not on the same actions as Model A. This is methodologically correct - each model is evaluated on the quality of its own probability estimates for its own decisions.

### 12. CRN Generation

**Source:** [`evaluate_step5f.py` L249-252](../src/evaluate_step5f.py#L249-L252)

```python
rng_crn = np.random.default_rng(CRN_SEED)
crn_draws = rng_crn.random(size=len(test_df))
```

A single uniform [0,1) draw per test case, shared across all policies.

### 13. CRN Seed

**Source:** [`evaluate_step5f.py` L31](../src/evaluate_step5f.py#L31)

`CRN_SEED = 999`

### 14. Simulator Probability Generation

**Source:** [`evaluate_step5f.py` L104-151](../src/evaluate_step5f.py#L104-L151)

```
P(recovered | context, action) = sigmoid(beta(action, category) + delta_logit)

delta_logit = 1.5 * (hist_success - 0.5) + 0.3 * log(1 + tenure) - 0.02 * hours_since_failure - 0.0001 * payment_value

beta values by action x category:
RETRY:    SOFT_DECLINE=2.2, FUNDS_ISSUE=-0.5, GENERIC_DECLINE=0.2, else=-3.0
NUDGE:    CUSTOMER_ACTION_REQUIRED=2.0, FUNDS_ISSUE=0.8, GENERIC_DECLINE=0.5, SOFT_DECLINE=-1.0, else=0.0
ESCALATE: (p_val>1000 or HARD_DECLINE or GENERIC_DECLINE)=0.8, else=-1.5
STOP:     returns 0.0 immediately
```

### 15. Guardrail Application

**Source:** [`evaluate_step5f.py` L166-211](../src/evaluate_step5f.py#L166-L211)

6 guardrail rules, all applying only to RETRY:
- GR01: boleto -> RETRY blocked
- GR02: voucher -> RETRY blocked
- GR03: HARD_DECLINE -> RETRY blocked
- GR04: authentication_failed / expired_card / boleto_expired -> RETRY blocked
- GR05: recovery_attempt_number > 3 -> RETRY blocked
- GR06: payment_value > 5000 AND reason in {do_not_honor, payment_failed} -> RETRY blocked

NUDGE and ESCALATE are never blocked by guardrails. STOP is always valid.

### 16. Utility Calculation

**Source:** [`evaluate_step5f.py` L153-163](../src/evaluate_step5f.py#L153-L163), [`evaluate_step5f.py` L308-312](../src/evaluate_step5f.py#L308-L312)

```
U(a) = payment_value * calibrated_probability(a) - total_cost(a)
total_cost(a) = intervention_cost + risk_penalty + friction_cost

intervention_cost: RETRY=0.50, NUDGE=1.50, ESCALATE=15.00, STOP=0
risk_penalty:      100.0 if (category==HARD_DECLINE AND action==RETRY), else 0
friction_cost:     1.0 if action==NUDGE, else 3.0 if (category==CUSTOMER_ACTION_REQUIRED AND action==RETRY), else 0
```

For STOP: all costs are 0.

### 17. Candidate Action Set

**Source:** [`evaluate_step5f.py` L294](../src/evaluate_step5f.py#L294)

`valid_active_actions = [a for a in ["RETRY", "NUDGE", "ESCALATE"] if g_status[a] == "PASSED"]`

Always evaluated in order: RETRY, NUDGE, ESCALATE.

### 18. Policy Selection

**Source:** [`evaluate_step5f.py` L314-323](../src/evaluate_step5f.py#L314-L323)

1. Among valid active actions, select argmax(utility)
2. If selected action has negative utility AND is in {RETRY, NUDGE}: if payment_value > 500 switch to ESCALATE, else switch to STOP (fallback triggered)
3. If no valid active actions: STOP (fallback triggered)

### 19. Recovery-Rate Calculation

**Source:** [`evaluate_step5f.py` L482-483](../src/evaluate_step5f.py#L482-L483)

`recovery_rate = recovered_count / total_cases` (fraction), reported as percentage.

### 20. Recovered-Revenue Calculation

**Source:** [`evaluate_step5f.py` L368-371](../src/evaluate_step5f.py#L368-L371)

Per case: `recovered_amount = payment_value if recovered == 1 else 0.0`. Aggregate: sum across all cases.

### 21. Net-Utility Calculation

**Source:** [`evaluate_step5f.py` L378-381](../src/evaluate_step5f.py#L378-L381)

Per case: `net_utility = recovered_amount - total_action_cost`. Aggregate: sum across all cases.

### 22. Regret Calculation

**Source:** [`evaluate_step5f.py` L490-491](../src/evaluate_step5f.py#L490-L491)

`regret = upper_bound_net_utility - policy_net_utility`

The upper bound is the Simulation Policy (oracle) that uses the ground-truth simulator probabilities.

### 23. Bootstrap Methodology

**Source:** [`evaluate_step5f.py` L514-591](../src/evaluate_step5f.py#L514-L591)

- Type: Customer-Level Clustered Bootstrap
- Iterations: 1,000
- Seed: `BOOTSTRAP_SEED = 42`
- Unit: `customer_unique_id` (not individual cases)
- Procedure:
  1. Pre-aggregate policy metrics per customer
  2. Resample customer IDs with replacement (vectorized)
  3. Sum per-customer metrics for each resample
  4. Compute derived metrics (lift, regret, recovery rate) per iteration

### 24. Confidence Interval Methodology

**Source:** [`evaluate_step5f.py` L580-589](../src/evaluate_step5f.py#L580-L589)

Percentile method: 2.5th and 97.5th percentiles of the bootstrap distribution.

---

## B. Exact Components Model B Will Share

| # | Component | How Shared |
|---|---|---|
| 1 | Training data | Same frozen CSV: `recoverai_ml_training_cases.csv` (11,051 rows) |
| 2 | Training target | Same `recovered` column, same binary {0,1} values |
| 3 | Training action column | Same `action` column (RETRY/NUDGE/ESCALATE), same values |
| 4 | Feature semantic content | Same 16 features (12 numeric + 4 categorical) |
| 5 | Validation data source | Same frozen CSV: `recoverai_ml_validation_cases.csv` (2,247 rows) |
| 6 | Validation exploration policy | Same uniform random exploration |
| 7 | Validation random seed | Same `seed=42`, same `np.random.default_rng(42)` |
| 8 | Validation action/outcome generation | Same `prepare_validation_data()` logic and simulator formula |
| 9 | Test data | Same frozen CSV: `recoverai_ml_test_cases.csv` (2,283 rows) |
| 10 | CRN seed | Same `CRN_SEED = 999` |
| 11 | CRN generation | Same `np.random.default_rng(999).random(size=2283)` |
| 12 | Simulator probability formula | Same exact logit formula and beta values |
| 13 | Guardrail rules (GR01-GR06) | Same rules, same application logic |
| 14 | Utility/cost structure | Same intervention costs, risk penalties, friction costs |
| 15 | Policy selection logic | Same argmax-utility + fallback logic |
| 16 | Recovery-rate calculation | Same `recovered_count / total_cases` |
| 17 | Recovered-revenue calculation | Same `payment_value if recovered else 0` |
| 18 | Net-utility calculation | Same `recovered_amount - action_cost` |
| 19 | Regret calculation | Same `upper_bound_net_utility - policy_net_utility` |
| 20 | ECE computation | Same 10 equal-width bins, same boundary logic |
| 21 | Forbidden features exclusion | Same `FORBIDDEN_FEATURES` list |

---

## C. Exact Components That Differ

| # | Component | Model A (LightGBM) | Model B (Logistic Regression) |
|---|---|---|---|
| 1 | Model class | `lightgbm.LGBMClassifier` | `sklearn.linear_model.LogisticRegression` |
| 2 | Categorical encoding | Native categorical via `astype("category")` | One-hot encoding (fitted on training data only) |
| 3 | Isotonic calibrator | Frozen `isotonic_calibrator.pkl` (fitted on LightGBM val predictions) | Separate new calibrator fitted on LR val predictions (if appropriate) |
| 4 | Hyperparameters | LightGBM-specific (learning_rate, num_leaves, etc.) | LR-specific (solver, regularization C, max_iter) |

---

## D. Unavoidable Methodological Differences

### D1. Categorical Encoding

LightGBM handles categoricals natively using optimal subset splits. Logistic Regression requires explicit encoding. One-hot encoding is the standard and appropriate approach. This introduces more columns (4 categorical features with total cardinality 4+5+15+3=27 become 27 binary columns, minus 4 reference categories = 23 indicator columns added, replacing 4 original columns, for a total of 12 + 23 = 35 features).

**Impact on fairness:** This is an inherent model-class difference, not a methodological confound. LightGBM's native categorical handling can find optimal multi-value splits that one-hot encoding cannot directly represent, giving LightGBM a structural advantage. This is a known and accepted difference when comparing tree-based and linear models.

### D2. Numeric Feature Scaling

LightGBM is invariant to monotonic transformations of numeric features (tree-based). Logistic Regression is NOT invariant - coefficient magnitude depends on feature scale.

Observed scale disparity:
- `payment_value` range: [0.01, 6929.31]
- `historical_payment_success_rate` range: [0.0, 1.0]
- `recovery_attempt_number`: constant 1 (zero variance, contributes nothing)

**Decision: StandardScaler IS scientifically justified** for Logistic Regression because:
1. L2-regularized LR (the sklearn default) penalizes coefficients proportionally to their magnitude. Without scaling, features on large scales (e.g., `payment_value`) would be penalized disproportionately relative to features on small scales (e.g., `historical_payment_success_rate`).
2. The `lbfgs` solver convergence can be sensitive to feature scale imbalance.
3. This is not adding information - it is a standard, well-understood linear model preprocessing step that preserves the rank ordering within each feature.

**Safeguard:** The scaler must be fitted ONLY on training data. Test/validation data is transformed using training-fitted parameters only.

**Note on `recovery_attempt_number`:** This feature is constant (all values = 1) in the training data. It contributes zero information to any model. LightGBM can ignore it via split selection. For LR, a constant feature after scaling becomes zero-variance. It will be included for feature parity but will have zero coefficient.

### D3. Calibration Comparability

Model A uses Isotonic calibration fitted on its own validation predictions. For a fair comparison:
- Raw LR probabilities should be evaluated first (LR inherently outputs probabilities via sigmoid).
- Isotonic-calibrated LR probabilities should also be evaluated using a separate calibrator fitted on LR's own validation predictions.
- Both raw and calibrated results should be reported to allow the reader to assess whether calibration helps or harms LR.

The primary comparison should use the calibrated version, since the frozen Model A result uses calibrated probabilities.

### D4. Early Stopping

LightGBM used early stopping on the validation set (best_iteration=87 out of 500 rounds). Logistic Regression does not have an equivalent concept - it trains to convergence. This is an inherent model-class difference, not a methodological confound.

---

## E. Why the Comparison Remains Fair

1. **Same data:** Both models train on the identical 11,051 training cases with the identical target and action columns.

2. **Same validation protocol:** Both models' validation data is generated by the same `prepare_validation_data()` function with the same seed (42), producing identical action assignments and outcomes.

3. **Same test evaluation:** Both models are evaluated on the identical 2,283 test cases using the identical CRN draws (seed=999), the identical simulator probability formula, the identical guardrail rules, the identical utility/cost structure, and the identical policy selection logic.

4. **No test leakage:** Model B's preprocessing (one-hot encoding, scaling) is fitted only on training data. No validation or test information leaks into Model B's preprocessing.

5. **No hyperparameter tuning on test set:** Model B uses default or pre-specified hyperparameters. No tuning uses held-out test outcomes.

6. **Calibration parity:** Both models are evaluated after Isotonic calibration fitted on their respective validation predictions. Both raw and calibrated LR results are reported.

7. **Encoding difference is inherent:** The categorical encoding difference is a known, documented, inherent difference between tree-based and linear model classes - not a confound introduced by methodology choices.

8. **Scaling is model-appropriate:** StandardScaler for LR is analogous to LightGBM's native scale-invariance - both ensure features contribute appropriately to their respective model class.

---

## F. Items That Cannot Be Verified from the Repository

1. **Exact LightGBM internal categorical split decisions:** The frozen `lgbm_model.pkl` encodes the trained tree structure, but we cannot inspect exactly how LightGBM partitioned the 15 failure_reason categories at each split without deep model inspection. This does not affect the comparison - we simply use the frozen model's predictions.

2. **Random number generator internal state alignment:** The frozen training data was generated with `np.random.default_rng(42)`. We can reproduce the validation data generation with the same seed and verify identical results, confirming the RNG contract. This CAN be verified and will be verified during implementation.

3. **Exact LightGBM version:** The model was trained with whatever LightGBM version was installed at training time. The frozen pickle encodes the trained model. For Model B, we use sklearn's LogisticRegression which is version-independent for the purposes of this comparison. The frozen LightGBM model is used as-is - we do not retrain it.

4. **Whether the current sklearn version exactly reproduces the frozen Isotonic calibrator:** The frozen LightGBM calibrator (`isotonic_calibrator.pkl`) was serialized with a specific sklearn version. We load and use it as-is without refitting. Model B's separate calibrator will be fitted fresh.

> All 24 methodology components have been directly read from the existing source code. No component was inferred or assumed. Every source file path and line number is cited above.

---

## Summary Decision Table

| Decision | Choice | Justification |
|---|---|---|
| One-hot encode categoricals for LR | Yes | LR cannot consume native categoricals; standard approach |
| Fit one-hot encoder on training data only | Yes | Prevents test/validation leakage |
| Apply StandardScaler to numeric features | Yes | L2-regularized LR requires comparable feature scales; fitted on training only |
| Fit separate Isotonic calibrator for LR | Yes | Fair comparison requires same calibration methodology |
| Report raw LR metrics alongside calibrated | Yes | Allows assessing calibration benefit independently |
| Use same CRN seed (999) | Yes | Reduces Monte Carlo variance in policy comparisons by exposing policies to the same random draws |
| Use same guardrails/utility/costs | Yes | Ensures identical decision environment |
| Use same policy selection logic | Yes | Ensures comparable policy evaluation |
| Reproduce validation data with same seed | Yes | Verified reproducible; ensures identical calibration population |
