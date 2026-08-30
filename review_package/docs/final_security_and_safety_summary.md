# RecoverAI Security, Safety & Privacy Summary

## Executive Summary

This document details the security controls, safety guardrails, privacy protections, and network isolation policies enforced across **RecoverAI: Track 03 AI Revenue Recovery**.

The system implements multi-layered security controls to protect payment data, prevent post-decision feature leakage, guard against denial-of-service (DoS) attacks, ensure thread-safe auditability, and guarantee zero external execution or credential storage.

---

## 1. Data Privacy & Credential Stripping Controls

### 1.1 Sensitive Credential Rejection
RecoverAI enforces strict zero-trust credential stripping at both the API endpoint layer (`server.py`) and the Agent Engine layer (`recoverai_agent.py`).

If an incoming payload contains any prohibited sensitive payment credential:
- Prohibited Fields: `card_number`, `cvv`, `cvc`, `otp`, `pin`, `bank_account_number`, `password`, `auth_secret`, `payment_token`.
- System Response: `HTTP 400 Bad Request`
- Error Code: `SENSITIVE_FIELD_REJECTED`
- Message: `Sensitive credential fields detected and rejected.`
- Audit Verification: Confirmed zero sensitive credential values enter the API response, memory logs, batch output CSVs, or local audit CSV files.

### 1.2 Post-Decision Feature Leakage Rejection
To prevent target leakage or post-decision context pollution during pre-decision inference, incoming payloads are validated against post-decision attributes:
- Prohibited Post-Decision Fields: `selected_action`, `candidate_action`, `utility_*`, `model_probability_*`, `effective_probability_*`, `guardrail_*`, `recovery_probability`, `expected_recovered_amount`, `recovered_amount`, `recovered`.
- System Response: `HTTP 400 Bad Request`
- Error Code: `LEAKAGE_FIELD_REJECTED`

---

## 2. Safety Guardrail Engine (Rules GR01–GR06)

All decision requests are routed through the centralized guardrail engine before any ML scoring occurs:

```
INPUT CONTEXT ──► Safety Guardrails (GR01–GR06)
                        │
         ┌──────────────┴──────────────┐
         ▼                             ▼
   [ PASSED ]                     [ BLOCKED ]
         │                             │
Scored via ML              Bypasses LightGBM & Isotonic
Calibrated Utility          Probability = 0.0
Argmax Selection            Utility = -999,999.0
```

### Verified Guardrail Rules:
1. `GR01_BOLETO`: `boleto` + `RETRY` $\rightarrow$ `BLOCKED` (Prevents automatic retry on expired paper slips).
2. `GR02_VOUCHER`: `voucher` + `RETRY` $\rightarrow$ `BLOCKED` (Prevents retry on gift cards/vouchers).
3. `GR03_HARD_DECLINE`: `HARD_DECLINE` + `RETRY` $\rightarrow$ `BLOCKED` (Blocks retries on stolen cards/invalid numbers).
4. `GR04_AUTH_REQ`: `authentication_failed` + `RETRY` $\rightarrow$ `BLOCKED` (Blocks retries requiring customer 3DS auth).
5. `GR05_MAX_RETRY_CAP`: `recovery_attempt_number > 3` + `RETRY` $\rightarrow$ `BLOCKED` (Caps maximum retries at 3).
6. `GR06_HIGH_VALUE`: `payment_value > 5000.0` + `payment_failed` + `RETRY` $\rightarrow$ `BLOCKED` (Escalates high-value declines).
7. `STOP Action Invariant`: `STOP` action probability $P = 0.0$ and net utility $EU = 0.0$ (Zero execution cost).

---

## 3. Network & Denial-of-Service Defense Controls

### 3.1 Bounded Request Payload Protection (2 MB Limit)
Implemented via `RequestPayloadSizeLimitMiddleware` in `server.py`:
- Enforces strict 2 MB maximum body cap across all HTTP requests.
- Evaluates `Content-Length` headers immediately.
- Implements streaming chunked payload consumption for requests lacking `Content-Length` headers, aborting immediately once accumulated bytes exceed 2 MB.
- System Response: `HTTP 413 Payload Too Large` (`PAYLOAD_TOO_LARGE`).

### 3.2 Rate Limiting Middleware
Implemented via `RateLimiterMiddleware` in `server.py`:
- Enforces sliding window rate limit of 100 requests per minute per client IP address.
- Synchronized using `asyncio.Lock` to guarantee thread safety under concurrent request load.
- System Response: `HTTP 429 Too Many Requests` (`RATE_LIMIT_EXCEEDED`).

### 3.3 Global Exception Sanitization
Implemented via `@app.exception_handler(Exception)` in `server.py`:
- Traps all unhandled runtime exceptions during recommendation execution.
- System Response: `HTTP 500 Internal Server Error`
- Response Payload: `{"status": "SYSTEM_ERROR", "error_code": "INTERNAL_ORCHESTRATION_ERROR", "message": "Internal orchestration error."}`
- Security Guarantee: **ZERO** stack traces, filesystem paths (`S:\...`), Python exception details, or LightGBM model internals are exposed to clients. Raw stack traces are logged exclusively to server `stderr`.

---

## 4. Auditability, Provenance & File Integrity Controls

### 4.1 Thread-Safe Local CSV Audit Logging
- Standard-library `csv.writer` guarded by Python's `threading.Lock` guarantees thread-safe, atomic appends to `data/processed/recoverai_agent_audit_log.csv`.
- Operates locally; no public REST API endpoint exposes audit logs.

### 4.2 Model SHA-256 Provenance Hash Tracking
- Computes SHA-256 hashes of `lgbm_model.pkl` (`ca968b77...`) and `isotonic_calibrator.pkl` (`8bda9ff...`) at startup.
- Includes provenance hashes in health check endpoints, API responses, batch outputs, and audit log records.

### 4.3 Frozen Artifact Protection Mandate
- All 14 preceding workspace artifacts (datasets, models, calibrators, schemas, agent engine, server, batch runner) remain 100% byte-identical against master reference hashes.
