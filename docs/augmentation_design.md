# RecoverAI Data Augmentation Design: Olist to Recovery Cases

## Document Overview

This document specifies the architecture and technical design for transforming real-world e-commerce records from the Kaggle Olist dataset into structured **RecoverAI Payment Recovery Cases**. It establishes strict boundaries between empirical real-world context, derived historical features, and controlled simulation layers for **Track 03: AI Revenue Recovery**.

---

## 1. Purpose & Core Pipeline

The objective of this design is to establish a deterministic, reproducible transformation pipeline:

```
REAL OLIST DATA
  │ (orders, order_payments, customers)
  ▼
Payment-Level Eligibility Filtering
  │ (filter payment_value > 0, valid joins, supported payment types)
  ▼
Real Customer & Payment Context Extraction
  │ (copy immutable Olist attributes & calculate leakage-free features)
  ▼
Controlled Simulated Failure Layer (Applied in later steps)
  │ (overlay failure reasons, recovery actions, & outcomes)
  ▼
RecoverAI Recovery Case Schema
```

### Core Provenance Guarantee
- **Real-Data Foundation**: All transaction values, payment rails, timestamps, order statuses, and customer relationship histories originate directly from real Olist empirical data.
- **Simulation Layer**: Gateway decline codes, failure reasons, recovery intervention actions, recovery probabilities, and post-intervention outcomes are controlled simulation constructs added in subsequent steps.

---

## 2. Source Data

The augmentation pipeline ingests three primary raw CSV files located in `data/raw/`:

1. `data/raw/olist_orders_dataset.csv`: Order status, purchase timestamps, approval timestamps.
2. `data/raw/olist_order_payments_dataset.csv`: Payment method channels, installment configurations, transaction monetary values, and split payment sequences.
3. `data/raw/olist_customers_dataset.csv`: Customer transaction keys (`customer_id`) and true unique customer identity keys (`customer_unique_id`).

---

## 3. Unit of Analysis & Primary Keys

The primary unit of analysis for RecoverAI is a **PAYMENT-LEVEL RECOVERY CASE**.

### Unique Case Key Construction
```
case_id = order_id + "_" + str(payment_sequential)
```

- **Example**: `e481f51cbdc54678b7cc49136f2d6af7_1`

### Strict Disambiguation: `payment_sequential` vs. `retry_count`
- **`payment_sequential` (Real Olist Attribute)**: Represents the sequence index of multi-tender split payments used for a single checkout order (e.g., payment #1 via voucher, payment #2 via credit card). It is **NOT** an automated recovery retry count.
- **`recovery_attempt_number` (Simulated Attribute)**: A separate, controlled simulation variable created in subsequent steps to track automated recovery attempt sequences.

---

## 4. Eligibility Filtering

A raw Olist payment record is eligible for conversion into a RecoverAI recovery context if and only if it satisfies all of the following criteria:

```
                  ┌─────────────────────────────────────┐
                  │ Raw Olist Payment Record            │
                  └──────────────────┬──────────────────┘
                                     │
                 Is payment_value > 0?
                 ├── NO ──► EXCLUDE (Zero-value / Promo record)
                 └── YES
                     │
                 Valid join to olist_orders (order_id)?
                 ├── NO ──► EXCLUDE (Orphaned payment)
                 └── YES
                     │
                 Valid join to olist_customers (customer_id)?
                 ├── NO ──► EXCLUDE (Unlinked customer)
                 └── YES
                     │
                 Is payment_type in supported list?
                 ├── NO ──► EXCLUDE (not_defined)
                 └── YES
                     │
                 Are purchase timestamp and customer_unique_id available?
                 ├── NO ──► EXCLUDE (Corrupted timestamp)
                 └── YES
                     │
                     ▼
             ┌─────────────────────────────────────┐
             │ ELIGIBLE RECOVERY CASE CONTEXT      │
             └─────────────────────────────────────┘
```

### Supported Payment Types:
- `credit_card`
- `debit_card`
- `boleto`
- `voucher`

### Handling of Invalid / Excluded Records:
- Records with `payment_value == 0` or `payment_type == 'not_defined'` are filtered out.
- Records failing inner relational joins across `order_id` or `customer_id` are logged and excluded.
- **Immutable Raw Files**: Raw Olist files are read-only and will never be modified or deleted.

---

## 5. Provenance & Immutability Rules

To maintain strict data integrity, fields in the recovery case schema are partitioned by provenance:

### A. Real Olist Fields (`REAL_OLIST`)
Immutable attributes copied directly from raw Olist files without modification:
- `order_id`
- `customer_id`
- `customer_unique_id`
- `payment_sequential`
- `payment_type`
- `payment_installments`
- `payment_value`
- `order_status`
- `order_purchase_timestamp`
- `order_approved_at`

### B. Derived Real-Data Features (`DERIVED_FROM_REAL_OLIST`)
Features calculated strictly from empirical historical Olist records prior to the current transaction timestamp.

---

## 6. Temporal Data Leakage Prevention Rules

To prevent data leakage, customer payment history features must strictly enforce temporal boundaries.

### Fundamental Leakage Prevention Rule:
$$\text{For a target payment occurring at time } T_0\text{, features may ONLY ingest records where } T_{\text{past}} < T_0.$$

Information occurring at or after $T_0$ (future orders, future payments, or current transaction outcomes) is strictly prohibited from feature calculation pipelines.

### Allowed Leakage-Free Historical Features:
- `previous_order_count`: Total prior orders placed by `customer_unique_id` before $T_0$.
- `previous_payment_count`: Total prior payment transactions by `customer_unique_id` before $T_0$.
- `previous_success_count`: Count of prior successfully delivered orders before $T_0$.
- `previous_cancelled_count`: Count of prior canceled orders before $T_0$.
- `previous_payment_value`: Cumulative monetary spend by customer before $T_0$.
- `historical_average_payment`: Average transaction amount of customer prior orders before $T_0$.
- `historical_payment_success_rate`: Ratio of successful prior orders over total prior orders before $T_0$.
- `customer_tenure_before_payment`: Days elapsed between customer's first observed order and $T_0$.
- `historical_order_frequency`: Average days between orders prior to $T_0$.

---

## 7. Disambiguation of E-Commerce Order Cancellation

```
┌────────────────────────────────────────────────────────────────────────┐
│                        CRITICAL DISAMBIGUATION                         │
├────────────────────────────────────────────────────────────────────────┤
│  order_status = 'canceled'   ≠   Payment Gateway Failure               │
│  order_status = 'unavailable' ≠   Bank Payment Decline                 │
└────────────────────────────────────────────────────────────────────────┘
```

- In e-commerce datasets (such as Olist), `order_status = 'canceled'` occurs due to diverse business reasons (e.g., buyer change of mind, merchant stockout, logistics failure, merchant timeout).
- `order_status` values must **never** be used as ground truth for gateway failure reasons (`failure_reason`).
- Order cancellation history is categorized exclusively as contextual customer history metadata (`previous_cancelled_count`).

---

## 8. Controlled Simulation Layer Architecture

After assembling eligible real-world payment contexts, a controlled simulation layer will overlay failure and recovery mechanics:

### Simulated Attributes (`SIMULATED_RECOVERY`):
- `failure_source`: Simulated error origin (`bank`, `gateway`, `customer`, `network`).
- `failure_step`: Simulated transaction processing step (`initiation`, `authentication`, `authorization`).
- `failure_code`: Simulated top-level API error code (`BAD_REQUEST_ERROR`, `GATEWAY_ERROR`).
- `failure_reason`: Simulated decline code from the finalized RecoverAI taxonomy (`docs/failure_taxonomy.md`).
- `recovery_attempt_number`: Simulated attempt index (starts at `1`).
- `candidate_action`: Proposed action being evaluated (`RETRY`, `NUDGE`, `ESCALATE`, `STOP`).
- `recovery_probability`: Action-conditional probability score $P(\text{recovered} \mid \text{context}, \text{action})$.
- `expected_recovered_amount`: Calculated expected value ($\text{payment\_value} \times \text{recovery\_probability}$).
- `guardrail_result`: Pass/Fail result of operational policy checks.
- `execution_status`: Action execution state (`PENDING`, `EXECUTED`, `BLOCKED`, `SKIPPED`).
- `recovered`: Binary recovery outcome ($0$ or $1$).
- `recovered_amount`: Final monetary recovery amount.

> **Explicit Statement**: These fields are controlled simulation variables designed for evaluating RecoverAI's orchestrator policy. They are NOT historical Olist observations.

---

## 9. Payment-Method Failure Compatibility

Simulated failure reasons must adhere strictly to the payment-method compatibility rules defined in `docs/failure_taxonomy.md`:

```
┌─────────────────┐     ┌───────────────────────────────────────────────────────────┐
│ Payment Method  │     │ Permitted Simulated Failure Reasons                       │
├─────────────────┼───────────────────────────────────────────────────────────┤
│ credit_card     │ ──► │ soft declines, funds issues, customer action, hard decl.  │
│ debit_card      │ ──► │ soft declines, funds issues, customer action, hard decl.  │
│ boleto          │ ──► │ boleto_expired, payment_timed_out, payment_cancelled      │
│                 │     │ PROHIBITED: stolen_card, expired_card, card_invalid       │
│ voucher         │ ──► │ payment_timed_out, payment_cancelled, payment_failed     │
│                 │     │ PROHIBITED: card-specific decline codes                   │
└─────────────────┘     └───────────────────────────────────────────────────────────┘
```

---

## 10. Card-on-File Simulation Assumption

- **Fact**: Olist dataset records point-of-sale e-commerce transactions and does not contain vaulted credential tokens or card-on-file (CoF) indicators.
- **Simulation Assumption**: For the purpose of RecoverAI's controlled simulation, eligible card payment cases (`credit_card`, `debit_card`) may be assumed to possess an authorized stored credential token that permits automated, background re-authorization attempts (`RETRY`).
- **Boundary**: This assumption is strictly a simulation construct and is never represented as native Olist data.

---

## 11. Payment-Level Case Construction

The conceptual transformation pipeline operates at individual payment level:

$$\text{Olist Order} + \text{Olist Payment Record} + \text{Olist Customer Identity} \longrightarrow \text{Eligible Payment Context} \longrightarrow \text{Recovery Case}$$

Multiple payment records belonging to a single order (split payments) are preserved as distinct recovery cases differentiated by `payment_sequential`.

---

## 12. Planned Recovery Case Schema

The table below specifies the 31 columns of the planned recovery case schema, categorized by provenance:

| Category | Column Name | Data Type | Provenance | Description |
|---|---|---|---|---|
| **A. Identifiers** | `case_id` | String | `DERIVED_FROM_REAL_OLIST` | Unique recovery case key (`order_id_payment_sequential`) |
| | `order_id` | String | `REAL_OLIST` | Olist order identifier |
| | `customer_id` | String | `REAL_OLIST` | Per-order customer key |
| | `customer_unique_id` | String | `REAL_OLIST` | True customer identity key |
| | `payment_sequential` | Integer | `REAL_OLIST` | Olist split-payment sequence index |
| **B. Real Payment Context** | `payment_type` | String | `REAL_OLIST` | Payment method (`credit_card`, `debit_card`, `boleto`, `voucher`) |
| | `payment_installments` | Integer | `REAL_OLIST` | Number of payment installments chosen |
| | `payment_value` | Float | `REAL_OLIST` | Transaction monetary value |
| **C. Real Order Context** | `order_status` | String | `REAL_OLIST` | Historical Olist order status |
| | `order_purchase_timestamp` | String | `REAL_OLIST` | Timestamp when order was placed |
| | `order_approved_at` | String | `REAL_OLIST` | Timestamp when payment was approved |
| **D. Derived Real Features** | `previous_order_count` | Integer | `DERIVED_FROM_REAL_OLIST` | Prior orders by customer before $T_0$ |
| | `previous_payment_count` | Integer | `DERIVED_FROM_REAL_OLIST` | Prior payments by customer before $T_0$ |
| | `previous_payment_value` | Float | `DERIVED_FROM_REAL_OLIST` | Prior cumulative spend by customer before $T_0$ |
| | `previous_success_count` | Integer | `DERIVED_FROM_REAL_OLIST` | Prior successful orders before $T_0$ |
| | `previous_cancelled_count` | Integer | `DERIVED_FROM_REAL_OLIST` | Prior canceled orders before $T_0$ |
| | `historical_payment_success_rate` | Float | `DERIVED_FROM_REAL_OLIST` | Prior success ratio before $T_0$ |
| | `historical_average_payment` | Float | `DERIVED_FROM_REAL_OLIST` | Prior average transaction value before $T_0$ |
| | `customer_tenure_before_payment` | Integer | `DERIVED_FROM_REAL_OLIST` | Customer relationship age in days before $T_0$ |
| | `order_frequency_before_payment` | Float | `DERIVED_FROM_REAL_OLIST` | Prior average days between orders before $T_0$ |
| **E. Simulated Failure** | `failure_source` | String | `SIMULATED_RECOVERY` | Simulated error origin (`bank`, `gateway`, `customer`, `network`) |
| | `failure_step` | String | `SIMULATED_RECOVERY` | Simulated error pipeline step |
| | `failure_code` | String | `SIMULATED_RECOVERY` | Simulated API error code |
| | `failure_reason` | String | `SIMULATED_RECOVERY` | Simulated decline code from taxonomy |
| **F. Simulated Recovery State** | `recovery_attempt_number` | Integer | `SIMULATED_RECOVERY` | Simulated attempt sequence index (starts at 1) |
| | `candidate_action` | String | `SIMULATED_RECOVERY` | Action being evaluated (`RETRY`, `NUDGE`, `ESCALATE`, `STOP`) |
| | `recovery_probability` | Float | `SIMULATED_RECOVERY` | Model-estimated recovery probability $P(\text{recovered} \mid \text{context}, \text{action})$ |
| | `expected_recovered_amount` | Float | `SIMULATED_RECOVERY` | Calculated expected value (`payment_value * recovery_probability`) |
| **G. Simulated Outcome** | `guardrail_result` | String | `SIMULATED_RECOVERY` | Guardrail validation result (`PASS`, `BLOCKED`) |
| | `execution_status` | String | `SIMULATED_RECOVERY` | Action execution state |
| | `recovered` | Integer | `SIMULATED_RECOVERY` | Binary recovery target ($0$ or $1$) |
| | `recovered_amount` | Float | `SIMULATED_RECOVERY` | Actual monetary amount recovered |

---

## 13. Expected Recovery Value Formula

The expected monetary recovery amount is defined as:

$$\text{expected\_recovered\_amount} = \text{revenue\_at\_risk} \times \text{recovery\_probability}$$

Where:
- $\text{revenue\_at\_risk} = \text{payment\_value}$ (derived directly from the empirical Olist payment record).
- $\text{recovery\_probability}$: Action-conditional probability score assigned during policy inference.

> **Design Boundary**: Specific probability values and assignment logic are **NOT** decided in Step 4E-2. Probability assignment distributions are designed in **STEP 4E-3**.

---

## 14. Pending Sampling Parameters (Deferred to Step 4E-3)

The following quantitative parameters are explicitly marked as **`PENDING STEP 4E-3`** and are **NOT** decided in this document:

- Percentage of Olist payment records selected for failure simulation
- Failure-class prior probability distribution
- Failure reason sampling weights
- Recovery probability functions $P(\text{recovered} \mid \text{context}, \text{action})$
- Action success rates across failure types
- Monetary recovery rate distributions
- Retry attempt limit parameters
- Customer nudge cap parameters
- Escalation monetary thresholds

---

## 15. Traceability & Lineage

Every generated recovery case maintains complete, bi-directional lineage back to its source Olist record:

$$\text{case\_id} \longrightarrow \text{order\_id} \longrightarrow \text{payment\_sequential} \longrightarrow \text{Raw Olist Record in } \texttt{olist\_order\_payments\_dataset.csv}$$

No original raw Olist data field is ever overwritten or modified.

---

## 16. Data Provenance Identifiers

All fields in the dataset documentation and pipeline manifests carry explicit provenance tags:

- **`REAL_OLIST`**: Unmodified empirical data directly copied from Kaggle Olist files.
- **`DERIVED_FROM_REAL_OLIST`**: Mathematically computed features derived exclusively from prior `REAL_OLIST` history without temporal leakage.
- **`SIMULATED_RECOVERY`**: Synthetic variables generated by RecoverAI's simulation layer for controlled policy evaluation.

---

## 17. Architecture Scope (Step 4E-2 Boundary)

```
┌───────────────────────────────────────────────────────────────────────────┐
│                        STEP 4E-2 DESIGN SCOPE                             │
├───────────────────────────────────────────────────────────────────────────┤
│  REAL OLIST DATA                                                          │
│        │                                                                  │
│        ▼                                                                  │
│  Relational Join (payments + orders + customers)                          │
│        │                                                                  │
│        ▼                                                                  │
│  Eligibility Filtering (payment_value > 0, valid payment_type)            │
│        │                                                                  │
│        ▼                                                                  │
│  Temporal Customer History Feature Calculation (Leakage-Free)            │
│        │                                                                  │
│        ▼                                                                  │
│  Recovery Case Context Construction (case_id = order_id_seq)             │
└─────────────────────────────────────┬─────────────────────────────────────┘
                                      │
                                      ▼
┌───────────────────────────────────────────────────────────────────────────┐
│                     DEFERRED TO STEP 4E-3 AND LATER                       │
├───────────────────────────────────────────────────────────────────────────┤
│  SIMULATED FAILURE LAYER (Sampling failure_reason & codes)                │
│        │                                                                  │
│        ▼                                                                  │
│  Recovery Decision Engine (Evaluating RETRY, NUDGE, ESCALATE, STOP)       │
│        │                                                                  │
│        ▼                                                                  │
│  Guardrail Validation & Outcome Simulation                                │
└───────────────────────────────────────────────────────────────────────────┘
```

---

## 18. Explicit Non-Goals

To avoid misrepresentation, this document explicitly DOES NOT:
- Claim that Olist contains payment gateway decline error codes or bank decline reasons.
- Claim that Olist contains automated retry histories or recovery intervention logs.
- Claim that Olist contains card-on-file vault authorization flags.
- Treat e-commerce order cancellations (`order_status = 'canceled'`) as payment gateway failures.
- Treat multi-tender payment sequence indices (`payment_sequential`) as automated retry attempts.
- Generate synthetic data records or execute code pipelines.
- Train machine learning models or implement agent logic.

---

## 19. Document Status

```
STEP 4E-2 STATUS: DESIGN COMPLETE
```

**Next Step:**
`STEP 4E-3 — Failure Sampling and Recovery Probability Design`
