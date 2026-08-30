# RecoverAI Technical Architecture Specification

## 1. System Overview & Technical Flow

**RecoverAI** is structured as a layered, decoupled decision-recommendation architecture. It transforms payment decline metadata into net expected utility-maximizing recovery action recommendations.

```
                         [ CLIENT ENTRYPOINTS ]
       ┌───────────────────────────┬───────────────────────────┐
       │                           │                           │
  Step 7C Dashboard UI     Step 7B Batch Runner       External HTTP Clients
  (Interactive Web UI)     (CLI Streaming Runner)    (Concurrency & Load)
       │                           │                           │
       └───────────────────────────┼───────────────────────────┘
                                   │
                     Step 7A FastAPI REST API Server
                        (/api/v1/recommend, /health)
                                   │
                        Synchronous Threadpool
                                   │
                   Step 6D RecoverAI Decision Engine
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

---

## 2. Layered Component Specifications

### 2.1 Entrypoint Layer (Step 7 - Active Demonstration Interfaces)
- **Interactive Web Dashboard (Step 7C):** Glassmorphic web UI providing context simulation, real-time probability & utility visualization, guardrail monitoring, and static Step 5F policy evaluation display loaded from frozen artifacts (`test_evaluation_metrics.json`).
- **Batch Recommendation Runner (Step 7B):** Single-threaded CLI tool (`run_batch.py`) utilizing standard-library `csv.DictWriter` for memory-bounded row-by-row streaming processing over arbitrary dataset sizes.
- **REST API Server (Step 7A):** High-throughput FastAPI application exposing `POST /api/v1/recommend` and `GET /api/v1/health`. Implements bounded request body streaming (2 MB max, `HTTP 413`), `asyncio.Lock` rate limiting (100 req/min/IP, `HTTP 429`), and sanitized exception handling (`HTTP 500 SYSTEM_ERROR`). Routes requests via synchronous `def` endpoints to prevent event-loop blocking.

### 2.2 Orchestration Layer (Step 6D - Frozen Agent Engine)
- **RecoverAI Agent Interface (`RecoverAI.recommend()`):** Top-level decision orchestrator coordinating input validation, guardrail evaluation, ML scoring, probability calibration, expected utility calculation, action selection, and audit logging.

### 2.3 Feature Validation Layer (Step 6A - Frozen Feature Builder)
- **Context Builder & Validation:** Formats 15 payment context attributes into exact feature vectors. Strips prohibited sensitive credentials (`card_number`, `cvv`, `otp`, `bank_account_number`, `password`, `auth_secret`, `payment_token`, `pin`) returning `SENSITIVE_FIELD_REJECTED`, and rejects post-decision leakage attributes (`selected_action`, `utility_*`, `model_probability_*`, `recovered`) returning `LEAKAGE_FIELD_REJECTED`.

### 2.4 Safety Guardrail Layer (Step 6B - Frozen Safety Engine)
- **Guardrail Engine:** Evaluates candidate actions (`RETRY`, `NUDGE`, `ESCALATE`, `STOP`) against hard business rules:
  - `GR01_BOLETO`: `boleto` + `RETRY` $\rightarrow$ `BLOCKED`
  - `GR02_VOUCHER`: `voucher` + `RETRY` $\rightarrow$ `BLOCKED`
  - `GR03_HARD_DECLINE`: `HARD_DECLINE` + `RETRY` $\rightarrow$ `BLOCKED`
  - `GR04_AUTH_REQ`: `authentication_failed` + `RETRY` $\rightarrow$ `BLOCKED`
  - `GR05_MAX_RETRY_CAP`: `recovery_attempt_number > 3` + `RETRY` $\rightarrow$ `BLOCKED`
  - `GR06_HIGH_VALUE`: `payment_value > 5000.0` + `payment_failed` + `RETRY` $\rightarrow$ `BLOCKED`
  - `STOP Invariant`: `STOP` recovery probability $P = 0.0$ and expected utility $EU = 0.0$.
  - Blocked actions bypass ML scoring and set utility = $-999,999.0$.

### 2.5 Machine Learning & Calibration Layer (Step 5E - Frozen ML Pipeline)
- **LightGBM S-Learner (`lgbm_model.pkl`):** Predicts recovery probability $\hat{P}(Y=1 \mid X, A)$ using 16 pre-decision features.
- **Isotonic Calibrator (`isotonic_calibrator.pkl`):** Calibrates raw model probabilities to produce well-calibrated probabilities $P = \text{Calibrator}(\hat{P})$.

### 2.6 Net Expected Utility Optimization Layer (Step 6C - Frozen Utility Engine)
- **Utility Optimizer:** Calculates net expected financial gain:
  $$EU(A, X) = P(A, X) \cdot V - C(A)$$
  where $V = \text{payment\_value}$ and execution cost $C(A)$ is configured as:
  - $C(\text{RETRY}) = \text{R\$ } 1.50$
  - $C(\text{NUDGE}) = \text{R\$ } 0.50$
  - $C(\text{ESCALATE}) = \text{R\$ } 5.00$
  - $C(\text{STOP}) = \text{R\$ } 0.00$
- **Action Selection:** Selects action $A^* = \arg\max_A EU(A, X)$.

### 2.7 Audit Logging Layer (Step 6D - Frozen Audit Engine)
- **RecoverAIAuditLogger:** Appends atomic decision records to `recoverai_agent_audit_log.csv` using Python's standard `csv.writer` guarded by `threading.Lock`.

---

## 3. Component Immutability Boundaries

| Component Group | Component Name | Implementation Step | Immutability Status |
|---|---|---|---|
| ML & Calibration | LightGBM Model & Isotonic Calibrator | Step 5E | **FROZEN** |
| Datasets & Policy | Training/Test Datasets & Step 5F Policy Metrics | Step 4E & Step 5F | **FROZEN** |
| Agent Engine | Feature Validator, Guardrail & Utility Engines | Step 6A, 6B, 6C, 6D | **FROZEN** |
| REST API | FastAPI Server (`server.py`) | Step 7A | **FROZEN** |
| Batch Processor | Streaming Batch Runner (`run_batch.py`) | Step 7B | **FROZEN** |
| Web UI | Interactive Glassmorphic Dashboard | Step 7C | **FROZEN** |
| Integration Tests | Integration Test Suite (`test_step7d_integration.py`) | Step 7D | **FROZEN** |
| Release Verification | Final Release Suite (`test_step7e_release_verification.py`) | Step 7E | **FROZEN** |
