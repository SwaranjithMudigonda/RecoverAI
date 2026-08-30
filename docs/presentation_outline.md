# RecoverAI Project Presentation Outline
**Track 03: AI Revenue Recovery | Razorpay AI Builder Internship 2026**

---

### Slide 1: Title & Executive Summary
- **Title:** RecoverAI: AI-Driven Revenue Recovery Decision Engine
- **Subtitle:** Maximizing Post-Decline Net Utility via Calibrated S-Learner ML & Safety Guardrails
- **Author / Track:** Razorpay AI Builder Internship 2026 — Track 03: AI Revenue Recovery
- **Key Takeaway:** An end-to-end reproducible prototype that optimizes payment recovery actions (`RETRY`, `NUDGE`, `ESCALATE`, `STOP`) yielding **+4.44% revenue lift** over static rule-based retries while guaranteeing zero guardrail violations.

---

### Slide 2: The Business Problem — Post-Decline Revenue Loss
- **Industry Context:** 5% to 15% of online payment transactions fail due to soft declines, network errors, or customer authentication issues.
- **The Pitfalls of Naive Retries:**
  - High Payment Gateway Fees: Repeated retries incur unnecessary transaction processing costs.
  - Customer Frustration: Excessive retry notifications lead to churn and complaints.
  - Fraud Escalation: Retrying fraud-related declines risks chargebacks and scheme fines.
- **Objective:** Build an intelligent decision engine that selects the optimal recovery action maximizing **Net Expected Utility**.

---

### Slide 3: Real Data Foundation — Olist E-Commerce Dataset
- **Dataset Source:** Brazilian E-Commerce Public Dataset by Olist (99,441 real transaction context records).
- **Realistic Failure Taxonomy:** Augmented with realistic payment failure categories (`SOFT_DECLINE`, `HARD_DECLINE`, `CUSTOMER_ACTION_REQUIRED`, `GENERIC_DECLINE`).
- **Simulated Recovery Outcomes:** Realistic recovery probabilities modeled across 4 candidate actions (`RETRY`, `NUDGE`, `ESCALATE`, `STOP`).
- **Disclaimer:** Olist provides real transaction context; failure reasons and recovery outcomes are simulated for research prototyping.

---

### Slide 4: Pre-Decision Feature Engineering Schema
- **16 Pre-Decision Features:**
  - Transaction Attributes: `payment_type`, `payment_value`, `payment_installments`
  - Customer History: `previous_order_count`, `previous_payment_count`, `previous_success_count`, `previous_cancelled_count`
  - Success Rates: `historical_payment_success_rate`, `historical_average_payment`
  - Behavioral Metrics: `customer_tenure_before_payment`, `order_frequency_before_payment`
  - Decline Context: `failure_category`, `failure_reason`, `hours_since_failure`, `recovery_attempt_number`
- **Zero Leakage:** Strictly excludes post-decision fields (`selected_action`, `recovered`, `utility_*`).

---

### Slide 5: Machine Learning Methodology — LightGBM S-Learner
- **Causal S-Learner Framework:** Models recovery probability $P(Y=1 \mid X, A)$ by concatenating context features $X$ and candidate action $A$.
- **Model Architecture:** LightGBM Binary Classifier trained on 77,280 training cases.
- **Isotonic Calibration:** Fits an Isotonic Regression model on validation predictions to transform raw model scores into well-calibrated probabilities.
- **Calibration Performance:** ECE (Expected Calibration Error) = `0.0264`, Brier Score = `0.2227`, ROC-AUC = `0.6879`.

---

### Slide 6: Action-Selection & Net Expected Utility Maximization
- **Net Utility Formula:**
  $$EU(A, X) = P(A, X) \cdot V - C(A)$$
  where $V = \text{payment\_value}$ and $C(A)$ is the execution cost:
  - $C(\text{RETRY}) = \text{R\$ } 1.50$ (Gateway retry fee)
  - $C(\text{NUDGE}) = \text{R\$ } 0.50$ (SMS/WhatsApp prompt cost)
  - $C(\text{ESCALATE}) = \text{R\$ } 5.00$ (Manual agent intervention)
  - $C(\text{STOP}) = \text{R\$ } 0.00$ (Zero execution cost)
- **Selection Rule:** $A^* = \arg\max_A EU(A, X)$ subject to safety guardrails.

---

### Slide 7: Safety Guardrail Engine (Rules GR01–GR06)
- **Hard Business Rules:**
  - `GR01_BOLETO`: `boleto` + `RETRY` $\rightarrow$ `BLOCKED`
  - `GR02_VOUCHER`: `voucher` + `RETRY` $\rightarrow$ `BLOCKED`
  - `GR03_HARD_DECLINE`: `HARD_DECLINE` + `RETRY` $\rightarrow$ `BLOCKED`
  - `GR04_AUTH_REQ`: `authentication_failed` + `RETRY` $\rightarrow$ `BLOCKED`
  - `GR05_MAX_RETRY_CAP`: Attempt count $> 3$ + `RETRY` $\rightarrow$ `BLOCKED`
  - `GR06_HIGH_VALUE`: Value $> \text{R\$ } 5000.00$ + `payment_failed` + `RETRY` $\rightarrow$ `BLOCKED`
- **STOP Action Invariant:** `STOP` probability $P = 0.0$ and utility $EU = 0.0$.
- **Bypass Mandate:** Blocked candidate actions bypass ML scoring and receive utility = $-999,999.0$.

---

### Slide 8: Technical Architecture & System Integration
- **FastAPI REST API (Step 7A):** Synchronous `def` route handling `POST /api/v1/recommend` with 2 MB payload cap and 100 req/min rate limit.
- **Streaming Batch Runner (Step 7B):** Zero-knowledge CLI batch processor (`run_batch.py`) utilizing `csv.DictWriter` for memory-bounded streaming.
- **Interactive Web Dashboard (Step 7C):** Glassmorphic web UI displaying context simulator, probability/utility charts, guardrail status, and artifact-driven Step 5F metrics.
- **Thread-Safe Audit Logger (Step 6D):** Writes atomic CSV decision logs guarded by `threading.Lock`.

---

### Slide 9: Held-Out Policy Evaluation Results (Step 5F)

> **Note:** Point estimates are from `step5f_policy_summary.csv`. Bootstrap means & 95% CIs are from `test_evaluation_metrics.json`.

- **Evaluated Set:** 2,283 held-out test set cases (R$ 345,292.12 revenue at risk).

#### POINT ESTIMATES (`step5f_policy_summary.csv`)
| Metric | ML Policy (Argmax EU) | Rule-Based Baseline | Lift (ML vs Rule-Based) |
|---|---|---|---|
| **Net Policy Utility** | **R$ 179,015.96** | R$ 173,068.42 | **+R$ 5,947.54 (+3.44%)** |
| **Recovered Revenue** | **R$ 184,987.96** | R$ 177,126.42 | **+R$ 7,861.54 (+4.44%)** |
| **Recovery Rate** | **52.30%** | 50.59% | **+1.71 percentage points absolute** |
| **Regret vs Upper Bound** | **R$ 160.80** | R$ 6,108.34 | **-97.4% regret reduction** |

#### BOOTSTRAP MEANS & 95% CIs (`test_evaluation_metrics.json`)
- **ML Net Utility Mean:** R$ 178,776.12 (95% CI: [R$ 162,926.10, R$ 196,091.84])
- **Net Utility Lift Mean:** +R$ 5,944.12 (95% CI: [+R$ 3,130.62, +R$ 9,101.72])
- **Absolute Revenue Lift Mean:** +R$ 7,860.57 (95% CI: [+R$ 4,974.46, +R$ 11,181.81])

---

### Slide 10: Security, Privacy & Denial-of-Service Defense
- **Sensitive Credential Stripping:** HTTP 400 `SENSITIVE_FIELD_REJECTED` for payloads containing `card_number`, `cvv`, `otp`, `pin`, `bank_account_number`, `password`.
- **Post-Decision Leakage Protection:** HTTP 400 `LEAKAGE_FIELD_REJECTED`.
- **Payload & Rate Protections:** 2 MB body cap (`HTTP 413`), 100 req/min/IP rate limit (`HTTP 429`).
- **Sanitized Global Error Handling:** HTTP 500 `SYSTEM_ERROR` with zero stack trace/path leakage.

---

### Slide 11: End-to-End System Verification (Steps 7D & 7E)
- **Step 7D Integration Suite:** 18/18 integration tests passed (50-worker concurrent load test, audit concurrency safety).
- **Step 7E Release Verification:** 10/10 release tests passed.
- **100% Frozen Artifact SHA-256 Integrity:** All 14 workspace files matched master reference checksums.
- **Deterministic Reproducibility:** 10/10 repeated inference runs produced identical decision outputs.

---

### Slide 12: Prototype Scope & Limitations
- **Simulation Disclaimer:** Prototype decision-recommendation engine; no real gateway charges or customer communications are executed.
- **Data Scope:** Failure labels and recovery outcomes are simulated over real Olist transaction metadata.
- **Evaluation Boundary:** Step 5F results reflect held-out simulation dataset performance.

---

### Slide 13: Conclusion & Final Deliverables
- **Project Verdict:** `RECOVERAI RELEASE VERIFIED & COMPLETE`
- **Completed Deliverables:**
  - Decoupled REST API Server Prototype (`src/api/server.py`)
  - Streaming Batch Runner (`src/batch/run_batch.py`)
  - Interactive Web Dashboard (`dashboard/index.html`)
  - Comprehensive Test Suites (`test_step7d_integration.py`, `test_step7e_release_verification.py`)
  - Complete Technical Documentation Package (`README.md`, `technical_architecture.md`, `final_results_summary.md`, `final_security_and_safety_summary.md`)
