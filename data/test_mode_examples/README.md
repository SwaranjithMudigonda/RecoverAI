# data/test_mode_examples/

Sanitized, schema-validation fixtures captured from the **Razorpay Test Mode**
sandbox (`rzp_test_...` keys) via `tools/collect_razorpay_samples.py`.

**Provenance tag on every fixture: `RAZORPAY_TEST_MODE`**

## What this directory is

Static evidence that RecoverAI's failure-taxonomy mapping
(`docs/razorpay_schema_mapping.md`) correctly interprets real Razorpay sandbox
error schemas — `error_code`, `error_source`, `error_step`, `error_reason` —
and translates them into RecoverAI's internal `failure_category` /
`failure_reason` taxonomy.

## What this directory is **NOT** — NOT Model Training Data

- These fixtures are **NOT Model Training Data**. The frozen LightGBM S-Learner
  (`models/recoverai_step5e/`) and the Step 5F held-out evaluation
  (`data/processed/step5f_policy_summary.csv`) are trained and benchmarked
  exclusively on the Olist-derived simulation dataset. Nothing in this
  directory has ever been used to fit, calibrate, or evaluate that model.
- They contain **no real money movement, no live-mode transactions, and no
  real customer PII** — see `sanitize_payment_payload()` in
  `tools/collect_razorpay_samples.py` for the exact sanitization rules
  (contact/email/card_id are replaced with fixed placeholders; `acquirer_data`
  is stripped entirely; any payload containing a genuine credential field
  such as `cvv`/`otp`/`pin` is rejected outright rather than sanitized).

## Format

Each `*.json` fixture (except `manifest.json`) has the shape:

```json
{
  "provenance": "RAZORPAY_TEST_MODE",
  "sanitized": true,
  "scenario_tag": "insufficient_funds",
  "collected_at": "2026-09-03T00:00:00+00:00",
  "payment": { "...sanitized Razorpay payment entity..." },
  "recovered_taxonomy_mapping": { "failure_category": "...", "failure_reason": "..." }
}
```

`manifest.json` (if present) indexes every fixture by `payment_id`,
`scenario_tag`, and `file`.

This directory may be empty in a fresh checkout — fixtures are generated
on demand with `tools/collect_razorpay_samples.py` and are optional evidence,
not a build requirement.
