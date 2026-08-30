# Real Data Inspection: Home Credit Installments Payments

## Overview

This document presents the inspection findings of the raw `installments_payments.csv` dataset from the Kaggle Home Credit Default Risk competition, located at `data/raw/installments_payments.csv`. This dataset is being evaluated as a candidate real-data foundation for RecoverAI.

---

## Exact Inspection Results

| Metric / Attribute | Value |
|---|---|
| **Total Rows** | 13,605,401 |
| **Total Columns** | 8 |
| **Unique Customers (`SK_ID_CURR`)** | 339,587 |
| **Unique Loans/Agreements (`SK_ID_PREV`)** | 997,752 |
| **Minimum Scheduled Installment Amount (`AMT_INSTALMENT`)** | 0.00 |
| **Maximum Scheduled Installment Amount (`AMT_INSTALMENT`)** | 3,771,487.85 |
| **Minimum Actual Payment Amount (`AMT_PAYMENT`)** | 0.00 |
| **Maximum Actual Payment Amount (`AMT_PAYMENT`)** | 3,771,487.85 |
| **Records with Payment Amount Discrepancy (`AMT_PAYMENT` $\neq$ `AMT_INSTALMENT`)** | 1,477,795 (10.86%) |
| **Records with Payment Timing Discrepancy (`DAYS_ENTRY_PAYMENT` $\neq$ `DAYS_INSTALMENT`)** | 10,459,051 (76.87%) |
| **Customers with Multiple Payment Records** | 338,615 (99.71%) |

### Column Schemas, Data Types, and Missing Values

| Column Name | Data Type | Missing Count | Missing % | Description |
|---|---|---|---|---|
| `SK_ID_PREV` | `int64` | 0 | 0.00% | ID of previous credit/loan agreement |
| `SK_ID_CURR` | `int64` | 0 | 0.00% | ID of customer |
| `NUM_INSTALMENT_VERSION` | `float64` | 0 | 0.00% | Version of installment schedule (0 = credit card / flexible schedule) |
| `NUM_INSTALMENT_NUMBER` | `int64` | 0 | 0.00% | Installment sequence number |
| `DAYS_INSTALMENT` | `float64` | 0 | 0.00% | Scheduled installment due date (relative to current application, negative values) |
| `DAYS_ENTRY_PAYMENT` | `float64` | 2,905 | 0.02% | Actual date when installment was paid (relative to current application) |
| `AMT_INSTALMENT` | `float64` | 0 | 0.00% | Scheduled installment amount |
| `AMT_PAYMENT` | `float64` | 2,905 | 0.02% | Actual amount paid for the installment |

### Sample Data (5 Rows)

```
   SK_ID_PREV  SK_ID_CURR  NUM_INSTALMENT_VERSION  NUM_INSTALMENT_NUMBER  DAYS_INSTALMENT  DAYS_ENTRY_PAYMENT  AMT_INSTALMENT  AMT_PAYMENT
0     1054186      161674                     1.0                      6          -1180.0             -1187.0        6948.360     6948.360
1     1330831      151639                     0.0                     34          -2156.0             -2156.0        1716.525     1716.525
2     2085231      193053                     2.0                      1            -63.0               -63.0       25425.000    25425.000
3     2452527      199697                     1.0                      3          -2418.0             -2426.0       24350.130    24350.130
4     2714724      167756                     1.0                      2          -1383.0             -1366.0        2165.040     2160.585
```

---

## Potential RecoverAI Feature Mapping

Original columns in `installments_payments.csv` map directly to payment-context concepts in the RecoverAI schema:

| Original Column | Potential RecoverAI Feature / Role | Concept Mapping |
|---|---|---|
| `SK_ID_CURR` | `customer_id` | Customer Identifier |
| `SK_ID_PREV` | `payment_id` | Payment / Transaction / Agreement Identifier |
| `AMT_INSTALMENT` | `amount_inr` | Scheduled monetary transaction amount |
| `NUM_INSTALMENT_NUMBER` | `attempt_number` | Attempt/sequence number in billing schedule |
| `DAYS_INSTALMENT` | Timing baseline | Scheduled due date context |
| `DAYS_ENTRY_PAYMENT` | Timing difference context | Actual payment date context |
| `AMT_PAYMENT` | Payment completion indicator | Actual historical payment amount received |
| `NUM_INSTALMENT_VERSION` | Schedule flexibility context | Payment schedule modification type |

---

## Suitability for RecoverAI

### A. What This Dataset Provides
1. **Real Payment History**: 13.6 million real-world payment and installment records spanning 339,587 customers.
2. **Behavioral Dynamics**: Authentic patterns of customer payment timing, late payments, partial payments, underpayments, and overpayments over multi-month loan lifecycles.
3. **Sequential Context**: Sequential installment numbering (`NUM_INSTALMENT_NUMBER`) per customer, allowing construction of historical payment reliability features (e.g., past payment success rate, historical delays).
4. **Realistic Value Distributions**: Real-world distributions of transaction sizes, schedule durations, and payment variance across loan types.

### B. What This Dataset Does NOT Provide
1. **Payment Gateway Error Codes**: Does not contain technical payment gateway failure reasons (e.g., `insufficient_funds`, `network_decline`, `authentication_failed`, `expired_card`).
2. **Payment Method Breakdown**: Does not differentiate between digital payment rails like UPI, Net Banking, Credit Card, or Auto-Debit Mandates.
3. **Intervention / Recovery Actions**: Does not contain recorded recovery interventions (e.g., `RETRY`, `NUDGE`, `ESCALATE`, `STOP`).
4. **Subscription Metadata**: Contains installment loan structures rather than recurring SaaS/e-commerce subscription billing metadata.

### C. Why It Is Useful as a Real-Data Foundation
- **Empirical Baseline Distributions**: Provides realistic distributions of payment amounts, timing deltas, customer tenure, and historical delinquency behavior to anchor synthetic data generation.
- **Realistic Customer Repayment Patterns**: Can serve as a realistic empirical backbone upon which domain-specific payment failure categories and recovery action potential outcomes can be synthetically augmented without relying on purely uniform or random distributions.

### D. Important Limitations
- **No Ground-Truth Recovery Actions**: Because historical interventions were not logged in this dataset, action-conditional recovery probabilities $P(\text{recovered} \mid \text{context}, \text{action})$ cannot be trained directly from raw dataset fields alone without synthetic augmentation or counterfactual modeling.
- **Relative Date Encoding**: Dates are encoded as negative integer offsets (`DAYS_INSTALMENT`, `DAYS_ENTRY_PAYMENT`) relative to a reference date, requiring normalization to standard time-of-day / day-of-week feature representations.
