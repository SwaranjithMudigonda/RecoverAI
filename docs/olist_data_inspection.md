# Olist Real Data Inspection

## Dataset Overview

This document presents the inspection findings of the Brazilian E-Commerce Public Dataset by Olist, stored locally in `data/raw/`. Three core files were inspected:
- `olist_orders_dataset.csv`
- `olist_order_payments_dataset.csv`
- `olist_customers_dataset.csv`

---

## Orders Inspection (`olist_orders_dataset.csv`)

### Summary Metrics
- **Total Rows**: 99,441
- **Total Columns**: 8
- **Unique `order_id`**: 99,441
- **Unique `customer_id`**: 99,441

### Column Schemas, Data Types, and Missing Values

| Column Name | Data Type | Missing Count | Missing % | Description |
|---|---|---|---|---|
| `order_id` | `object` (string) | 0 | 0.00% | Unique identifier for each order |
| `customer_id` | `object` (string) | 0 | 0.00% | Key to the customer dataset (per-order customer key) |
| `order_status` | `object` (string) | 0 | 0.00% | Current status of the order |
| `order_purchase_timestamp` | `object` (string) | 0 | 0.00% | Timestamp when order was placed |
| `order_approved_at` | `object` (string) | 160 | 0.16% | Timestamp when payment was approved |
| `order_delivered_carrier_date` | `object` (string) | 1,783 | 1.79% | Timestamp when order was handed to logistics carrier |
| `order_delivered_customer_date` | `object` (string) | 2,965 | 2.98% | Timestamp when order was delivered to customer |
| `order_estimated_delivery_date` | `object` (string) | 0 | 0.00% | Estimated delivery date promised at checkout |

### Order Status Distribution
- `delivered`: 96,478 (97.02%)
- `shipped`: 1,107 (1.11%)
- `canceled`: 625 (0.63%)
- `unavailable`: 609 (0.61%)
- `invoiced`: 314 (0.32%)
- `processing`: 301 (0.30%)
- `created`: 5 (0.01%)
- `approved`: 2 (0.00%)

### Timestamp Availability
- `order_purchase_timestamp`: 99,441 available (0 missing)
- `order_approved_at`: 99,281 available (160 missing)
- `order_delivered_customer_date`: 96,476 available (2,965 missing)
- `order_estimated_delivery_date`: 99,441 available (0 missing)
- **Canceled Orders**: 625
- **Unavailable Orders**: 609

### Sample Data (5 Rows)
```
                            order_id                       customer_id order_status order_purchase_timestamp    order_approved_at order_delivered_carrier_date order_delivered_customer_date order_estimated_delivery_date
0  e481f51cbdc54678b7cc49136f2d6af7  9ef432eb6251297304e76186b10a928d    delivered      2017-10-02 10:56:33  2017-10-02 11:07:15          2017-10-04 19:55:00           2017-10-10 21:25:13           2017-10-18 00:00:00
1  53cdb2fc8bc7dce0b6741e2150273451  b0830fb4747a6c6d20dea0b8c802d7ef    delivered      2018-07-24 20:41:37  2018-07-26 03:24:27          2018-07-26 14:31:00           2018-08-07 15:27:45           2018-08-13 00:00:00
2  47770eb9100c2d0c44946d9cf07ec65d  41ce2a54c0b03bf3443c3d931a367089    delivered      2018-08-08 08:38:49  2018-08-08 08:55:23          2018-08-08 13:50:00           2018-08-17 18:06:29           2018-09-04 00:00:00
3  949d5b44dbf5de918fe9c16f97b45f8a  f88197465ea7920adcdbec7375364d82    delivered      2017-11-18 19:28:06  2017-11-18 19:45:59          2017-11-22 13:39:59           2017-12-02 00:28:42           2017-12-15 00:00:00
4  ad21c59c0840e6cb83a9ceb5573f8159  8ab97904e6daea8866dbdbc4fb7aad2c    delivered      2018-02-13 21:18:39  2018-02-13 22:20:29          2018-02-14 19:46:34           2018-02-16 18:17:02           2018-02-26 00:00:00
```

---

## Payments Inspection (`olist_order_payments_dataset.csv`)

### Summary Metrics
- **Total Rows**: 103,886
- **Total Columns**: 5
- **Unique `order_id` in Payments**: 99,440 (1 order in orders dataset has no payment record)
- **Orders with Multiple Payment Records**: 2,961 orders

### Column Schemas, Data Types, and Missing Values

| Column Name | Data Type | Missing Count | Missing % | Description |
|---|---|---|---|---|
| `order_id` | `object` (string) | 0 | 0.00% | Identifier linking payment to an order |
| `payment_sequential` | `int64` | 0 | 0.00% | Sequence index for multi-tender split payments |
| `payment_type` | `object` (string) | 0 | 0.00% | Payment method channel used |
| `payment_installments` | `int64` | 0 | 0.00% | Number of installments chosen by customer |
| `payment_value` | `float64` | 0 | 0.00% | Monetary value of the payment record |

### Payment Type Distribution
- `credit_card`: 76,795 (73.92%)
- `boleto`: 19,784 (19.04%)
- `voucher`: 5,775 (5.56%)
- `debit_card`: 1,529 (1.47%)
- `not_defined`: 3 (0.00%)

### Payment Value & Installments Distribution
- **Payment Value Range**: Min = `0.00`, Max = `13,664.08`
- **Payment Installments**: Min = `0`, Max = `24`, Mean = `2.85`, Median (50%) = `1`, 75th Percentile = `4`
  - 1 Installment: 52,546 records
  - 2 Installments: 12,413 records
  - 3 Installments: 10,461 records
  - 4 Installments: 7,098 records
  - 10 Installments: 5,328 records

### Payment Sequential Distribution
`payment_sequential` represents multi-tender split payments (e.g., using a gift voucher plus a credit card for a single checkout):
- `1`: 99,360 records
- `2`: 3,039 records
- `3`: 581 records
- `4`: 278 records
- `5+`: 628 records (Max = 29)

### Sample Data (5 Rows)
```
                            order_id  payment_sequential payment_type  payment_installments  payment_value
0  b81ef226f3fe1789b1e8b2acac839d17                   1  credit_card                     8          99.33
1  a9810da82917af2d9aefd1278f1dcfa0                   1  credit_card                     1          24.39
2  25e8ea4e93396b6fa0d3dd708e76c1bd                   1  credit_card                     1          65.71
3  ba78997921bbcdc1373bb41e913ab953                   1  credit_card                     8         107.78
4  42fdf880ba16b47b59251dd489d4441a                   1  credit_card                     2         128.45
```

---

## Customers Inspection (`olist_customers_dataset.csv`)

### Summary Metrics
- **Total Rows**: 99,441
- **Total Columns**: 5
- **Unique `customer_id`**: 99,441 (per-order customer key)
- **Unique `customer_unique_id`**: 96,096 (true unique customer identity across repeat purchases)
- **Repeat Customers**: 2,997 `customer_unique_id` entries map to multiple orders (max = 17 orders per customer)

### Column Schemas, Data Types, and Missing Values

| Column Name | Data Type | Missing Count | Missing % | Description |
|---|---|---|---|---|
| `customer_id` | `object` (string) | 0 | 0.00% | Per-order customer transaction key |
| `customer_unique_id` | `object` (string) | 0 | 0.00% | Unique identifier of the actual customer |
| `customer_zip_code_prefix` | `int64` | 0 | 0.00% | Customer ZIP code prefix |
| `customer_city` | `object` (string) | 0 | 0.00% | Customer city |
| `customer_state` | `object` (string) | 0 | 0.00% | Customer state |

### Sample Data (5 Rows)
```
                         customer_id                customer_unique_id  customer_zip_code_prefix          customer_city customer_state
0  06b8999e2fba1a1fbc88172c00ba8bc7  861eff4711a542e4b93843c6dd7febb0                     14409                 franca             SP
1  18955e83d337fd6b2def6b18a428ac77  290c77bc529b7ac935b93aa66c333dc3                      9790  sao bernardo do campo             SP
2  4e7b3e00288586ebd08712fdd0374a03  060e732b5b29e8181a18229c7b0b2b5e                      1151              sao paulo             SP
3  b2b6027bc5c5109e529d4dc6358b12c3  259dac757896d24d7702b9acbbff3f3c                      8775        mogi das cruzes             SP
4  4f2d8ab171c80ec8364f7c12e35b23ad  345ecd01c38d18a9036ed96c73b8d066                     13056               campinas             SP
```

---

## RecoverAI Feature Mapping

| Olist Field | RecoverAI Feature Concept | Feature Role & Notes |
|---|---|---|
| `customer_unique_id` | `customer_id` | Identifier linking repeat customer history |
| `order_id` | `payment_id` | Identifier for transaction / order |
| `payment_value` | `amount_inr` | Transaction amount in currency |
| `payment_type` | `payment_method` | Categorical payment channel (`credit_card`, `debit_card`, `boleto`, `voucher`) |
| `order_purchase_timestamp` | `hour_of_day`, `day_of_week` | Time & day context at order placement |
| `order_approved_at` | Payment approval latency | Approval delay calculation (`approved_at` - `purchase_timestamp`) |
| `customer_state`, `city` | Customer location context | Demographic context feature |

---

## What Olist Provides

1. **E-Commerce Payment Rails**: Real distributions of modern payment channels (`credit_card`, `debit_card`, `boleto`, `voucher`).
2. **True Customer Identity**: `customer_unique_id` enables building multi-transaction customer history metrics (`previous_successes`, `customer_tenure_days`, `customer_lifetime_value_inr`).
3. **Exact Order & Approval Timestamps**: High-resolution purchase and payment approval timestamps suitable for extracting hour-of-day and day-of-week timing features.
4. **Multi-Tender Payment Patterns**: Split-payment structures where customers combine multiple payment vouchers or cards.

---

## What Olist Does NOT Provide

1. **Payment Gateway Decline Reasons**: Does not contain technical decline error codes (e.g., `insufficient_funds`, `authentication_failed`, `expired_card`).
2. **Automated Payment Retries**: `payment_sequential` represents multi-tender split payments at checkout, NOT automated recovery retry attempts over time.
3. **Confirmed Payment Failures**: `order_status` = `canceled` includes non-payment cancellations (buyer regret, inventory shortage, shipping cancellation). It is NOT a clean log of failed payment transactions.
4. **Recovery Interventions**: Does not log recovery actions (`RETRY`, `NUDGE`, `ESCALATE`, `STOP`).
5. **Recovered Amounts**: Does not contain post-intervention recovery outcomes.

---

## Suitability for RecoverAI

The combination of the three Olist files provides an authentic e-commerce foundation for constructing **payment context features**, **customer lifetime spend history**, and **payment method distributions**. However, because it lacks gateway decline error codes and recovery intervention logs, it requires synthetic data augmentation to generate target recovery outcomes and action-conditional probabilities.

---

## Limitations

- **Absence of Bank Decline Metadata**: No raw error codes or bank decline responses are recorded.
- **Split Payments vs. Retries**: `payment_sequential` must not be mistaken for retry attempts.
- **No Ground-Truth Recovery Actions**: Policy training for $P(\text{recovered} \mid \text{context}, \text{action})$ requires synthetic augmentation.

---

## License / Usage Notes

- **Dataset Name**: Brazilian E-Commerce Public Dataset by Olist
- **Source**: Kaggle ([https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce))
- **License**: CC0 1.0 Universal (Public Domain Dedication). Verified from Kaggle source release by Olist.

---

## Final Recommendation

### **KEEP AS REAL-DATA FOUNDATION**

**Reasoning**:
The Olist dataset provides authentic e-commerce transaction attributes—specifically real payment method distributions (`credit_card`, `debit_card`, `boleto`), purchase timing, multi-order customer histories via `customer_unique_id`, and realistic order value distributions. While synthetic augmentation remains necessary to overlay gateway failure codes and recovery actions, Olist offers a realistic, public-domain empirical backbone for RecoverAI's e-commerce payment context.
