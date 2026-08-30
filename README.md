# RecoverAI: AI Revenue Recovery System
**Track 03: AI Revenue Recovery | Razorpay AI Builder Internship 2026**

> **⚠️ SIMULATED ENVIRONMENT — PROTOTYPE ONLY — NO REAL TRANSACTIONS EXECUTED**  
> **All failure reasons, recovery actions, and recovery outcomes used for model development and policy evaluation are simulated. The Brazilian E-Commerce Public Dataset by Olist provides real transaction context but does not provide gateway decline or recovery labels. This system is a decision-recommendation prototype interface; no real payment gateway transactions or customer communications are executed.**

---

## Executive Summary & Objective

**RecoverAI** is an end-to-end AI-driven payment recovery decision engine designed to optimize post-decline payment recovery strategies. When payment transactions fail (e.g., due to soft declines, network timeouts, or customer authentication issues), merchants face significant revenue loss. Blindly retrying every failed payment leads to high gateway fees, customer annoyance, and risk of fraud escalation.

RecoverAI replaces static rule-based retries with a **Calibrated Machine Learning S-Learner Policy** coupled with an **Action-Selection Net Expected Utility Maximizer** and a strict **Safety Guardrail Engine**.

---

## Complete Project Progression (Steps 4E → 7E)

```
4E Simulation Datasets ──► 5E LightGBM + Calibrator ──► 5F Held-Out Policy Evaluation
                                                                │
  7E Release Verified ◄── 7D System Integration ◄── 7C Dashboard UI / 7B Batch / 7A API ◄── 6D Agent Engine
```

- **Step 4E (Recovery-Case Simulation):** Built real-data foundation using 99,441 Olist transactions augmented with realistic payment failure taxonomy.
- **Step 5E (ML Training & Isotonic Calibration):** Trained a LightGBM S-Learner to predict recovery probability $\hat{P}(Y=1 \mid X, A)$ calibrated via Isotonic Regression.
- **Step 5F (Held-Out Policy Evaluation):** Evaluated policy performance on 2,283 held-out test cases against Rule-Based and Upper-Bound benchmarks.
- **Step 6A–6D (Agent Interface & Audit Logger):** Built feature validator, safety guardrail engine (GR01–GR06), utility optimizer, decision agent, and thread-safe CSV audit logger.
- **Step 7A (REST API):** Developed high-throughput FastAPI service (`POST /api/v1/recommend`, `GET /api/v1/health`) with streaming size protection (2 MB max cap) and IP rate limiting (100 req/min).
- **Step 7B (Batch Recommendation Runner):** Built zero-knowledge CLI batch processor (`run_batch.py`) with memory-bounded streaming via standard-library `csv.DictWriter`.
- **Step 7C (Interactive Web Dashboard):** Created glassmorphic UI displaying context simulator, probability charts, net utility visualization, guardrail monitor, and static artifact-driven Step 5F metrics.
- **Step 7D (End-to-End System Integration):** Passed 18 automated integration tests including 50-worker concurrent load testing and sanitized error handling.
- **Step 7E (Final System Integrity & Release Verification):** Passed 10 release verification tests certifying 100% frozen artifact SHA-256 integrity and deterministic reproducibility.

---

## RecoverAI Architecture & Decision Flow

```
  Step 7C Dashboard UI     External HTTP Clients        Step 7B Batch Runner
  (Interactive Web UI)     (Concurrency & Load)        (CLI Streaming Runner)
        │                           │                           │
        ▼                           ▼                           │
   Step 7A FastAPI REST API Server                              │
     (/api/v1/recommend, /health)                               │
        │                           │                           │
        └─────────────┬─────────────┘                           │
                      ▼                                         ▼
             Step 6D Centralized RecoverAI Agent Decision Engine
                                    │
        ┌───────────────────────────┼───────────────────────────┐
        ▼                           ▼                           ▼
 Step 6B Guardrails         Step 5E LightGBM + Isotonic     Step 6C Expected Utility
 (GR01–GR06 Central Path)   (Frozen Calibrated ML)         (Argmax Selection)
        │                           │                           │
        └───────────────────────────┼───────────────────────────┘
                                    │
                   Thread-Safe Audit Logger (CSV Writer)
```

1. **Feature Validation (Step 6A):** Validates input schema, strips forbidden credentials (`card_number`, `cvv`, `otp`, `pin`), and rejects post-decision leakage fields.
2. **Safety Guardrails (Step 6B):** Evaluates candidate actions (`RETRY`, `NUDGE`, `ESCALATE`, `STOP`). If an action triggers a rule (e.g., `GR01_BOLETO`, `GR03_HARD_DECLINE`), ML scoring is bypassed and utility is set to $-999,999.0$.
3. **ML Inference & Calibration (Step 5E/6C):** Evaluates non-blocked candidate actions through LightGBM S-Learner and Isotonic Calibrator to yield calibrated probability $P = \text{Calibrator}(\text{LightGBM}(X, A))$.
4. **Net Expected Utility Optimization (Step 6C):** Computes expected net utility:
   $$EU(A, X) = P(A, X) \cdot V - C(A)$$
   where $V$ is transaction value and $C(A)$ represents action execution cost ($C_{\text{RETRY}} = 1.50$, $C_{\text{NUDGE}} = 0.50$, $C_{\text{ESCALATE}} = 5.00$, $C_{\text{STOP}} = 0.00$).
5. **Action Selection & Audit Logging (Step 6D):** Selects $\arg\max_A EU(A, X)$ and writes atomic, thread-safe CSV audit records.

---

## Verified Evaluation Results (Step 5F Held-Out Test Set)

> **Note on Methodology:** Point estimates are taken directly from [`data/processed/step5f_policy_summary.csv`](data/processed/step5f_policy_summary.csv). Bootstrap means and confidence intervals are reported separately from [`models/recoverai_step5f/test_evaluation_metrics.json`](models/recoverai_step5f/test_evaluation_metrics.json) and must not be interpreted as identical to the point estimates.

Evaluated on **2,283 held-out test set cases** (R$ 345,292.12 total revenue at risk):

### 1. POINT ESTIMATES — Frozen Step 5F Policy Summary (`step5f_policy_summary.csv`)

| Performance Metric | ML Policy (Argmax EU) | Rule-Based Baseline | Simulation Policy Upper Bound | Lift (ML vs Rule-Based) |
|---|---|---|---|---|
| **Net Policy Utility** | **R$ 179,015.96** | R$ 173,068.42 | R$ 179,176.76 | **+R$ 5,947.54 (+3.44%)** |
| **Recovered Revenue** | **R$ 184,987.96** | R$ 177,126.42 | R$ 185,002.26 | **+R$ 7,861.54 (+4.44%)** |
| **Recovery Rate** | **52.30%** | 50.59% | 52.34% | **+1.71 percentage points absolute** |
| **Average Recovered / Case** | **R$ 81.03** | R$ 77.58 | R$ 81.03 | **+R$ 3.45 / case** |
| **Regret vs Upper Bound** | **R$ 160.80** | R$ 6,108.34 | R$ 0.00 | **-97.4% regret reduction** |
| **Guardrail Violations** | **0** | 0 | 0 | **0 violations** |

### 2. BOOTSTRAP RESULTS — Frozen Metrics (`test_evaluation_metrics.json`)

| Metric | Bootstrap Mean | 95% Bootstrap Confidence Interval (Low, High) |
|---|---|---|
| **ML Net Utility** | R$ 178,776.12 | [R$ 162,926.10, R$ 196,091.84] |
| **Rule-Based Net Utility** | R$ 172,832.00 | [R$ 157,416.26, R$ 190,087.36] |
| **ML Recovered Revenue** | R$ 184,747.56 | [R$ 169,058.99, R$ 202,161.82] |
| **Net Utility Lift** | +R$ 5,944.12 | [+R$ 3,130.62, +R$ 9,101.72] (+3.43% mean lift) |
| **Absolute Revenue Lift** | +R$ 7,860.57 | [+R$ 4,974.46, +R$ 11,181.81] (+4.45% mean lift) |

### 3. ML MODEL CALIBRATION & DISCRIMINATION METRICS

| Metric | Verified Value | Target / Threshold | Status |
|---|---|---|---|
| **ROC-AUC** | **0.6879** | $> 0.6500$ | **PASSED** |
| **Brier Score** | **0.2227** | $< 0.2500$ | **PASSED** |
| **Expected Calibration Error (ECE)** | **0.0264** | $< 0.0500$ | **PASSED** |
| **Log Loss** | **0.6514** | $< 0.7000$ | **PASSED** |
| **Test Set Sample Count** | **2,283 cases** | N/A | **VERIFIED** |

---

## Safety & Security Protections

- **Sensitive Credential Rejection:** HTTP 400 `SENSITIVE_FIELD_REJECTED` for payloads containing `card_number`, `cvv`, `otp`, `bank_account_number`, `password`, `auth_secret`, `payment_token`, `pin`.
- **Post-Decision Leakage Protection:** HTTP 400 `LEAKAGE_FIELD_REJECTED` for payloads containing `selected_action`, `utility_*`, `model_probability_*`, `recovered`.
- **Safety Guardrail Rules (GR01–GR06):** Hard cap blocks `RETRY` on `boleto` (GR01), `voucher` (GR02), `HARD_DECLINE` (GR03), `authentication_failed` (GR04), attempt count $> 3$ (GR05), and payment value $> \text{R\$ } 5000.00$ (GR06).
- **Network & Denial-of-Service Defense:** Bounded 2 MB payload limit (`HTTP 413 Payload Too Large`), rate-limiting at 100 req/min per IP (`HTTP 429 Too Many Requests`), and sanitized global exception handling (`HTTP 500 SYSTEM_ERROR`, zero stack traces leaked).

---

## 100% Frozen Artifact SHA-256 Integrity Hashes

Every workspace artifact is verified byte-identical against master reference hashes:

| Artifact File | Master SHA-256 Checksum | Verification Status |
|---|---|---|
| `data/processed/recoverai_recovery_cases.csv` | `973c8fa9d6034be43d0985b23867ff0988dcdaf442d9886706a50dc85094918d` | **MATCHED (100% Frozen)** |
| `data/processed/recoverai_ml_training_cases.csv` | `7c03d6e2c16dd51b4e8715a9313a8eadf4e8d3b9b334d35652878853f5d2fd7b` | **MATCHED (100% Frozen)** |
| `data/processed/recoverai_ml_validation_cases.csv` | `8f495e5d219463b502d90470d5d92723e9c20a2b45415c07aaf0fa51b6f56ee2` | **MATCHED (100% Frozen)** |
| `data/processed/recoverai_ml_test_cases.csv` | `fe52ba8be239102fb6152c1bd86dafbf71bf69e185d216baacec01558907b43e` | **MATCHED (100% Frozen)** |
| `data/processed/step5f_policy_summary.csv` | `57d684e6e584f92f7502c244b926e3af0584abc7fb1a5ba6da070db66262774f` | **MATCHED (100% Frozen)** |
| `models/recoverai_step5f/test_evaluation_metrics.json` | `812ad91aeda91d520832682f7bd53f433c10699c160984885081cecb374d2c74` | **MATCHED (100% Frozen)** |
| `models/recoverai_step5e/lgbm_model.pkl` | `ca968b7756caec185e70b562cda34445289cea4d0a4bce14cf7b0c5a0b1068e7` | **MATCHED (100% Frozen)** |
| `models/recoverai_step5e/isotonic_calibrator.pkl` | `8bda9ffdbb4b281a6569c5436f7ccf3cdb721da2971d1029540fa0809d596817` | **MATCHED (100% Frozen)** |
| `models/recoverai_step5e/feature_list.json` | `8462f5c4a83e53254ddebed80e458508fc719df19e900481b1c396e64e935f4d` | **MATCHED (100% Frozen)** |
| `models/recoverai_step5e/categorical_features.json` | `23debd9970ae23d9cf439587590dc2d38584c7b1dfa59488fcaba74176fc9b9a` | **MATCHED (100% Frozen)** |
| `models/recoverai_step5e/model_config.json` | `a7cb181a291bf95924ae86b4d9949de9c32b59ba907692ae29a00e8254672cc9` | **MATCHED (100% Frozen)** |
| `src/recoverai_agent.py` | `2585fd25516f94ed9a316a28fc98a2df940af70969ebb8f324f230eed81d190d` | **MATCHED (100% Frozen)** |
| `src/api/server.py` | `6850709b78922e788682e97efe604c201287364a7746ae9c0bdf66382f446a5b` | **MATCHED (100% Frozen)** |
| `src/batch/run_batch.py` | `bb12f639a1668386cc7b84beea07e8069765e3ea4a781a82337ac8a25ed7a12b` | **MATCHED (100% Frozen)** |

---

## Limitations & Scope Disclaimers

1. **Prototype Decision Engine Only:** RecoverAI outputs recommended actions (`RETRY`, `NUDGE`, `ESCALATE`, `STOP`). It does not execute live gateway charges or customer communications.
2. **Simulated Labels:** Failure categories, recovery actions, and outcomes are simulated over real Olist transaction metadata.
3. **Evaluation Boundaries:** Step 5F metrics reflect held-out simulation dataset performance and should not be interpreted as live production gateway figures.

---

## Quick Start & Verification Instructions

### 1. Run REST API Server
```bash
python -m uvicorn src.api.server:app --host 127.0.0.1 --port 8000
```
- Health Check: `GET http://127.0.0.1:8000/api/v1/health`
- Recommendation Endpoint: `POST http://127.0.0.1:8000/api/v1/recommend`

### 2. Run Batch Processor
```bash
python src/batch/run_batch.py --input data/processed/recoverai_ml_test_cases.csv --output data/processed/recoverai_batch_output.csv
```

### 3. Launch Interactive Dashboard
Open `dashboard/index.html` in any web browser.

### 4. Execute Full Verification Test Suites
```bash
python tests/test_step7d_integration.py
python tests/test_step7e_release_verification.py
```

---

## Final Project Verdict

```
RECOVERAI RELEASE VERIFIED & COMPLETE — 100% FROZEN
```
