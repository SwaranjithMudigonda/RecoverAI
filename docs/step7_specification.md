# RecoverAI Step 7 Specification & Implementation Plan: End-to-End Orchestration API & Analytics Dashboard

> **IMPORTANT DISCLAIMER & IMPLEMENTATION STATUS:**
> **Step 7 is currently a SPECIFICATION AND DESIGN PLAN ONLY. Step 7 code has NOT yet been implemented. No existing Step 4E through 6D codebase files or frozen model artifacts have been modified.**

---

## 1. Step 7 Objective

The objective of Step 7 is to transition **RecoverAI: Track 03 AI Revenue Recovery** from a Python module library ([`src/recoverai_agent.py`](../src/recoverai_agent.py)) into an **end-to-end demonstrable, web-accessible AI orchestration system**.

Step 7 will provide:
1. A production-grade **REST API Service** wrapping the frozen `RecoverAI.recommend()` engine.
2. An **Interactive Web Demonstration & Analytics Dashboard** allowing live interactive payment recovery simulations, static policy financial lift comparisons, and local audit log inspection.
3. A **Single-Threaded Synchronous Batch Processing Runner** for batch payment dataset evaluation.

---

## 2. Scope

- **REST API Layer (`src/api/`):** High-performance HTTP server (FastAPI/Uvicorn) exposing standard JSON endpoints (`POST /api/v1/recommend`, `POST /api/v1/batch-recommend`, `GET /api/v1/health`).
- **Interactive Web Dashboard (`dashboard/`):** Premium web application displaying live simulation controls, utility breakdown visualizations, frozen Step 5F policy performance metrics, and local audit log inspection.
- **Batch Recommendation Runner (`src/batch/`):** Single-threaded CLI utility to ingest payment CSV streams and generate audited batch recommendation logs.
- **System Monitoring & Provenance:** Endpoints and visualizations for API health, rate limiting status, guardrail enforcement rates, and SHA-256 model provenance verification.

---

## 3. Non-Goals (Critical Constraints)

To preserve statistical validity, system safety, and domain alignment, Step 7 explicitly excludes:
- ❌ **NO Real Payment Execution:** No integration with live Razorpay, Stripe, or bank acquirer APIs.
- ❌ **NO Real Customer Communication:** No live SMS, WhatsApp, email, or push notifications dispatched.
- ❌ **NO Real Card Charging / Retries:** No actual credit/debit card re-authorization attempts.
- ❌ **NO Modification of Steps 4E–6D:** Preceding code (`src/recoverai_agent.py`), datasets, LightGBM models, Isotonic calibrators, and policy evaluation results remain 100% frozen.
- ❌ **NO Model Retraining:** The S-learner model and calibrator will not be retrained in Step 7.
- ❌ **NO Test-Set Leakage or Dynamic Policy Re-Evaluation:** Step 7 demonstration inference is strictly separated from frozen Step 5F policy evaluation. Step 7 must **NEVER** re-calculate or overwrite Step 5F test evaluation artifacts (`step5f_policy_summary.csv`, `test_evaluation_metrics.json`).
- ❌ **NO Claims of Live Production Lift:** All metrics will clearly state they reflect simulated environment performance.

---

## 4. Technical Review Audit Fixes & Refinements

The following 14 validated technical review requirements are strictly incorporated into this Step 7 specification:

1. **Synchronous Route Definition:** `/api/v1/recommend` is defined as a **synchronous FastAPI `def` route** (not `async def`). FastAPI will execute CPU-bound LightGBM feature building and scoring inside its default threadpool executor, preventing CPU blocking of the main asyncio event loop.
2. **Public API Surface Minimization:** `GET /api/v1/audit-logs` is **REMOVED** from the public API specification to eliminate unauthorized data exfiltration or memory exposure risks over public endpoints.
3. **Local Read-Only Audit Access:** Audit log inspection for the local demonstration dashboard is strictly local read-only file access to `data/processed/recoverai_agent_audit_log.csv`.
4. **Standard-Library CSV Logger (`csv.writer`):** `RecoverAIAuditLogger` append operations will use Python's standard-library `csv.writer` under `self.lock = threading.Lock()` instead of heavy Pandas `df.to_csv(mode='a')` allocations for ultra-fast, thread-safe per-request logging.
5. **Single-Threaded Batch Runner:** The batch processing runner (`src/batch/run_batch.py`) is specified as single-threaded/synchronous for predictable prototype execution.
6. **Maximum Request Payload Limit:** Strict **2 MB maximum payload limit** enforced via middleware (`HTTP 413 Payload Too Large` returned for oversized requests).
7. **Sanitized Error Responses:** Internal exception details and stack traces **MUST NEVER** be returned to HTTP clients or written to public CSV audit logs; stack traces are written strictly to secure server `stderr`/application logs. Clients receive generic `SYSTEM_ERROR` JSON payloads.
8. **Basic API Rate Limiting:** Implements rate limiting (100 requests/minute per client IP) returning `HTTP 429 Too Many Requests`.
9. **SHA-256 Model Provenance Availability:** SHA-256 checksums (`model_artifact_hash` = `ca968b...`, `calibrator_artifact_hash` = `8bda9f...`) are required in `/health` responses, `/recommend` payloads, and audit records.
10. **Persistent Banner Disclaimer:** The web dashboard must feature a persistent, highly visible header banner:
    `"⚠️ SIMULATED ENVIRONMENT — PROTOTYPE ONLY — NO REAL TRANSACTIONS EXECUTED"`.
11. **Static Step 5F Metrics Loading:** Policy comparison charts in the dashboard must be loaded statically from frozen Step 5F evaluation artifacts ([`models/recoverai_step5f/test_evaluation_metrics.json`](../models/recoverai_step5f/test_evaluation_metrics.json)) and **MUST NOT** be dynamically re-evaluated.
12. **Integration Test Suite Requirements:** Must include automated tests verifying:
    - 50 concurrent `/api/v1/recommend` requests generating exactly 50 valid CSV audit rows without corruption.
    - Request payloads exceeding 2 MB returning `HTTP 413`.
    - Synchronous `def` route executing in threadpool without blocking server health checks.
13. **Frozen-Artifact Boundary Preservation:** Steps 4E through 6D artifacts remain 100% untouched.
14. **Separation of Demo & Policy Evaluation:** Step 7 demonstration inference strictly isolated from frozen Step 5F held-out evaluation artifacts.

---

## 5. System Architecture

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                      RECOVERAI STEP 7 SYSTEM ARCHITECTURE                        │
├─────────────────────────────────────────────────────────────────────────────────┤
│ 1. CLIENT / USER INTERACTION LAYER                                              │
│    • Interactive Web Simulator (`dashboard/index.html`)                         │
│      [Banner: ⚠️ SIMULATED ENVIRONMENT — PROTOTYPE ONLY — NO REAL TRANSACTIONS]   │
│    • External HTTP API Clients (cURL / Postman)                                 │
│                                                                                 │
│                                      │ (HTTP JSON / REST)                       │
│                                      ▼                                          │
│ 2. RECOVERAI REST API SERVICE (`src/api/server.py`)                             │
│    • Max Request Body Middleware (2 MB Cap -> HTTP 413)                         │
│    • Rate Limiter Middleware (100 req/min -> HTTP 429)                          │
│    • POST /api/v1/recommend       (Sync `def` route -> Threadpool Execution)  │
│    • POST /api/v1/batch-recommend (Sync single-threaded batch stream)        │
│    • GET  /api/v1/health          (Health & SHA-256 provenance check)        │
│                                                                                 │
│                                      │ (Internal Method Calls)                  │
│                                      ▼                                          │
│ 3. FROZEN RECOVERAI AGENT ENGINE (Step 6D `src/recoverai_agent.py`)             │
│    • 6A Context Validation & Sensitive Credential Check                        │
│    • 6B Safety Guardrail Engine (GR01–GR06) -> 0 ML calls on BLOCKED actions   │
│    • 6C LightGBM S-Learner Scoring & Isotonic Calibration                      │
│    • 6C Multi-Factor Expected Utility Argmax Selection                          │
│    • 6D Secure Audit Logger (`csv.writer` + `threading.Lock`)                   │
│                                                                                 │
│                                      │ (Fast Append Traces)                     │
│                                      ▼                                          │
│ 4. PERSISTENCE & ARTIFACT LAYER                                                 │
│    • `data/processed/recoverai_agent_audit_log.csv`                             │
│    • `models/recoverai_step5e/lgbm_model.pkl` (Frozen)                          │
│    • `models/recoverai_step5e/isotonic_calibrator.pkl` (Frozen)                 │
│    • `models/recoverai_step5f/test_evaluation_metrics.json` (Frozen Static Metrics)│
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## 6. Component Design

### 6.1 REST API Service (`src/api/server.py`)
- Built using **FastAPI** / **Uvicorn**.
- Synchronous route definition: `def recommend_endpoint(payload: PaymentContextSchema):`
- Request body payload size capped at 2 MB (`HTTP 413 Payload Too Large`).
- Rate limiting middleware enforcing 100 requests per minute per IP (`HTTP 429`).
- Sanitized exception handling mapping internal errors to generic `SYSTEM_ERROR` (stack traces written strictly to server `stderr`).

### 6.2 Interactive Web Dashboard (`dashboard/index.html`, `dashboard/app.js`, `dashboard/styles.css`)
- **Persistent Header Banner:** `"⚠️ SIMULATED ENVIRONMENT — PROTOTYPE ONLY — NO REAL TRANSACTIONS EXECUTED"`.
- **Interactive Failure Simulator:** Input controls for payment type, value, failure category, failure reason, tenure, attempt count.
- **Decision & Utility Breakdown Panel:** Displays selected action badge, calibrated recovery probabilities, expected utility bar chart, and selection rationale.
- **Safety Guardrail Status Panel:** Visual indicators for `GR01_BOLETO`, `GR02_VOUCHER`, `GR03_HARD_DECLINE`, `GR04_AUTH_REQ`, `GR05_MAX_RETRY_CAP`, `GR06_HIGH_VALUE`.
- **Frozen Policy Comparison Panel:** Displays static held-out policy evaluation metrics loaded directly from `test_evaluation_metrics.json` (ML Policy +4.44% lift vs Rule-Based, 0 guardrail violations, 99.91% upper bound capture).
- **Local Audit Log Inspector:** Local read-only table rendering latest entries from `recoverai_agent_audit_log.csv`.

### 6.3 Batch Recommendation Runner (`src/batch/run_batch.py`)
- Single-threaded, synchronous CLI script reading payment CSV rows and invoking `agent.recommend()`.
- Outputs audited CSV log file.

---

## 7. Data Flow

```
Client JSON Payload -> 2MB Check -> Rate Limiter -> Sync FastAPI Route -> Threadpool Executor -> RecoverAI.recommend() -> Validation (6A) -> Guardrails (6B) -> Model Scoring (6C) -> Utility Argmax (6C) -> csv.writer Audit Log (6D) -> Sanitized JSON Response -> Dashboard DOM Render
```

---

## 8. API / Interface Requirements

### `POST /api/v1/recommend`
- **Route Type:** Synchronous `def recommend_endpoint(...)`
- **Request Body Limit:** 2 MB Max Payload
- **Request Body Example:**
  ```json
  {
    "payment_type": "credit_card",
    "payment_value": 450.0,
    "payment_installments": 2,
    "previous_order_count": 3,
    "previous_payment_count": 3,
    "previous_success_count": 3,
    "previous_cancelled_count": 0,
    "historical_payment_success_rate": 1.0,
    "historical_average_payment": 450.0,
    "customer_tenure_before_payment": 60,
    "order_frequency_before_payment": 20.0,
    "failure_category": "SOFT_DECLINE",
    "failure_reason": "network_error",
    "hours_since_failure": 1.0,
    "recovery_attempt_number": 1
  }
  ```
- **Response HTTP 200 OK:** Returns exact Step 6D payload object structure including SHA-256 model provenance hashes.
- **Response HTTP 400 Bad Request:** Returns `INVALID_INPUT` error object.
- **Response HTTP 413 Payload Too Large:** Returned when request payload exceeds 2 MB.
- **Response HTTP 429 Too Many Requests:** Returned when IP rate limit is exceeded.
- **Response HTTP 500 Internal Server Error:** Returns sanitized `SYSTEM_ERROR` JSON payload.

### `GET /api/v1/health`
- **Response HTTP 200 OK:**
  ```json
  {
    "status": "HEALTHY",
    "model_artifact_hash": "ca968b7756caec185e70b562cda34445289cea4d0a4bce14cf7b0c5a0b1068e7",
    "calibrator_artifact_hash": "8bda9ffdbb4b281a6569c5436f7ccf3cdb721da2971d1029540fa0809d596817",
    "audit_log_active": true
  }
  ```

---

## 9. Security Requirements

1. **Zero Credential Exposure:** Input validator rejects any request containing `card_number`, `cvv`, `otp`, `bank_account_number`, `password`, `auth_secret`, `payment_token`, `pin`.
2. **Post-Decision Leakage Protection:** Input validator rejects any request containing post-decision fields (`selected_action`, `utility_*`, `model_probability_*`, `recovered`).
3. **Payload Capping:** 2 MB hard cap prevents memory allocation denial-of-service attacks.
4. **Sanitized Error Output:** Internal exceptions and stack traces are **NEVER** returned in HTTP responses or written to public CSV audit records. Written strictly to server `stderr`.

---

## 10. Automated Testing Strategy (Step 7 Tests)

When implementing Step 7, a dedicated test runner (`tests/test_step7_api.py`) will execute:
1. **Concurrency Audit Test:** 50 concurrent `/api/v1/recommend` requests producing exactly 50 valid CSV audit rows without file corruption.
2. **Oversized Payload Test:** Payload $> 2$ MB returns `HTTP 413 Payload Too Large`.
3. **Rate Limit Test:** Exceeding 100 requests/min returns `HTTP 429`.
4. **Non-Blocking Route Test:** Verifies synchronous `def` route executes in FastAPI threadpool without blocking `/health` responses.
5. **Static Metrics Loading Test:** Confirms dashboard loads policy comparison metrics strictly from `test_evaluation_metrics.json`.
6. **Artifact Provenance & Hash Preservation:** Confirms 100% SHA-256 hash match across all Step 5E/5F model files.

---

## 11. Acceptance Criteria

Step 7 will be deemed COMPLETE when:
1. `src/api/server.py` successfully serves API endpoints via FastAPI.
2. `dashboard/index.html` renders the interactive simulator with persistent disclaimer banner.
3. All 28 existing Step 6D tests plus new Step 7 API tests pass with 0 failures.
4. 100% SHA-256 hash matching is confirmed across all frozen model artifacts.
5. Zero guardrail violations and zero sensitive credential leaks occur.

---

## 12. Recommended Implementation Order

1. **Phase 7A:** Create REST API server (`src/api/server.py`) with synchronous routes, 2 MB payload cap, rate limiter, and sanitized error handling.
2. **Phase 7B:** Create single-threaded Batch Processing script (`src/batch/run_batch.py`).
3. **Phase 7C:** Build Interactive Web Dashboard (`dashboard/index.html`, `dashboard/styles.css`, `dashboard/app.js`) featuring persistent banner disclaimer and static Step 5F metrics rendering.
4. **Phase 7D:** Build API & Concurrency automated test suite (`tests/test_step7_api.py`).
5. **Phase 7E:** Execute SHA-256 artifact integrity verification and produce `docs/step7_implementation_report.md`.

---

## 13. Implementation Status Verdict

```
STEP 7 SPECIFICATION COMPLETE
```

> **Step 7 is currently a SPECIFICATION ONLY. Step 7 code has NOT been implemented.**
