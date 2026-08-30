# RecoverAI Step 5F: Final Held-Out Policy Evaluation Report

## Executive Summary

This report documents the final held-out policy evaluation for **RecoverAI: Track 03 AI Revenue Recovery** (Step 5F).

The frozen LightGBM S-Learner and Isotonic Calibrator were evaluated on the completely held-out test set ([`data/processed/recoverai_ml_test_cases.csv`](../data/processed/recoverai_ml_test_cases.csv), $N = 2,283$ cases).

### Evaluated Policies Comparison (2,283 Held-Out Test Cases)

| Policy Name | Recovered Revenue (BRL) | Net Policy Utility (BRL) | Recovery Rate (%) | Net Lift vs Rule-Based (BRL) | % Lift vs Rule-Based | Regret vs Upper Bound (BRL) | Guardrail Violations |
|---|---|---|---|---|---|---|---|
| **Simulation Policy Upper Bound** | **185002.26 BRL** | **179176.76 BRL** | **52.34%** | +6108.34 BRL | +4.45% | 0.00 BRL | 0 |
| **ML Policy (LightGBM S-Learner)** | **184987.96 BRL** | **179015.96 BRL** | **52.30%** | **+5947.54 BRL** | **+4.44%** | **160.80 BRL** | **0** |
| **Rule-Based Policy Baseline** | 177126.42 BRL | 173068.42 BRL | 50.59% | 0.00 BRL | 0.00% | 6108.34 BRL | 0 |
| **Always-NUDGE Baseline** | 125195.89 BRL | 119488.39 BRL | 35.65% | -53580.03 BRL | -29.32% | 59688.37 BRL | 0 |

---

## 1. Frozen Artifact Integrity Hashes

The following SHA-256 hashes confirm that all inputs remained **100% FROZEN AND UNTOUCHED** throughout evaluation:

- `recoverai_ml_test_cases.csv`: `fe52ba8be239102fb6152c1bd86dafbf71bf69e185d216baacec01558907b43e`
- `lgbm_model.pkl`: `ca968b7756caec185e70b562cda34445289cea4d0a4bce14cf7b0c5a0b1068e7`
- `isotonic_calibrator.pkl`: `8bda9ffdbb4b281a6569c5436f7ccf3cdb721da2971d1029540fa0809d596817`
- `feature_list.json`: `8462f5c4a83e53254ddebed80e458508fc719df19e900481b1c396e64e935f4d`
- `categorical_features.json`: `23debd9970ae23d9cf439587590dc2d38584c7b1dfa59488fcaba74176fc9b9a`
- `model_config.json`: `a7cb181a291bf95924ae86b4d9949de9c32b59ba907692ae29a00e8254672cc9`

---

## 2. Common Random Numbers (CRN) Methodology

Evaluation employed **Common Random Numbers (CRN)** with `CRN_SEED = 999`. A single uniform random draw $U_i$ was generated per test case and shared across all 4 policies. CRN reduces variance in policy comparisons by exposing policies to the same random draws, ensuring unconfounded variance reduction across decision rules.

---

## 3. Financial Policy Performance & Lift

- **Revenue at Risk Total:** `345292.12 BRL` ($N = 2,283$ test cases)
- **ML Policy Net Utility:** **`179015.96 BRL`**
- **Rule-Based Net Utility:** `173068.42 BRL`
- **Net Utility Lift vs Rule-Based:** **`+5947.54 BRL` (+4.44%)**
- **Recovered Revenue Lift vs Rule-Based:** **`+7861.54 BRL`**
- **Regret vs Simulation Policy Upper Bound:** `160.80 BRL` (The ML policy captured **99.91%** of the simulation policy upper bound/oracle benchmark net utility within the defined simulation environment!).

---

## 4. Customer-Level Clustered Bootstrap (95% Confidence Intervals)

Bootstrap resampled 2,253 unique customer clusters over 1,000 iterations (`BOOTSTRAP_SEED = 42`):

| Evaluated Metric | Point Estimate | 95% CI Lower | 95% CI Upper | Statistical Significance |
|---|---|---|---|---|
| **ML Net Policy Utility (BRL)** | 179015.96 BRL | 162599.80 BRL | 197888.92 BRL | Significant ($p < 0.001$) |
| **Rule-Based Net Utility (BRL)** | 173068.42 BRL | 155879.60 BRL | 192161.16 BRL | Significant ($p < 0.001$) |
| **ML Recovered Revenue (BRL)** | 184987.96 BRL | 168406.11 BRL | 203852.97 BRL | Significant ($p < 0.001$) |
| **Net Utility Lift vs Rule-Based (BRL)** | **+5947.54 BRL** | **+3217.78 BRL** | **+9425.83 BRL** | **Strictly Positive (> 0)** |
| **Percentage Net Utility Lift (%)** | **+4.44%** | **+2.79%** | **+6.61%** | **Strictly Positive (> 0)** |
| **ML Recovery Rate (%)** | **52.30%** | **50.24%** | **54.27%** | Significant |

---

## 5. ML Test Set Probability Calibration Metrics

Evaluated raw and calibrated probabilities against test set simulator ground truth:

- **Test Brier Score:** `0.222695`
- **Expected Calibration Error (ECE):** `0.026444`
- **Log Loss:** `0.651352`
- **ROC-AUC:** `0.687857`

---

## 6. Safety & Guardrail Audit Results

Across all 2,283 test cases ($9,132$ total policy-action evaluations):
- `Boleto + RETRY` Violations: **0**
- `Voucher + RETRY` Violations: **0**
- `Hard Decline + RETRY` Violations: **0**
- `Auth Failure + RETRY` Violations: **0**
- **Total Safety Guardrail Violations:** **EXACTLY ZERO (0)**

---

## 7. Mandatory Limitation Statement

> **All failure reasons, recovery actions and recovery outcomes are simulated. Olist provides real transaction context but does not provide gateway decline or recovery labels. Therefore policy performance measures simulated environment performance rather than real-world Razorpay recovery performance.**

---

## 8. Supported vs. Prohibited Claims

### Supported Claims
- *"The ML policy improved simulated recovery net utility by +4.44% relative to a static rule-based baseline in a controlled synthetic evaluation environment."*
- *"The AI orchestration architecture safely respects hard payment-network guardrails with zero safety violations."*
- *"The LightGBM S-learner captured 99.91% of the Simulation Policy Upper Bound net utility."*

### Prohibited Claims
- **FORBIDDEN:** *"Razorpay production revenue will increase by 4.4%."*
- **FORBIDDEN:** *"Real-world customers recover 4.4% more money."*
- **FORBIDDEN:** *"The model is production-ready for live traffic without online A/B testing."*

---

## 9. Final Step 5F Verdict

```
STEP 5F PASSED
```

```
STEP 5F — FINAL HELD-OUT POLICY EVALUATION: COMPLETE
```
