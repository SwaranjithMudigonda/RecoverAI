"""
tools/collect_razorpay_samples.py
==================================

Tier B: Razorpay Test Mode Schema Collection & Sanitization Utility.

This tool is DELIBERATELY isolated from RecoverAI's frozen ML/decision pipeline
(src/recoverai_agent.py, src/api/server.py, src/batch/run_batch.py,
frontend/src/lib/api.ts never import this module — enforced by
tests/test_razorpay_schema.py::test_isolated_architecture_zero_imports_in_core_engine).

It has two responsibilities:

1. sanitize_payment_payload(raw) — strips/masks any customer-identifying or
   credential-adjacent fields from a raw Razorpay Test Mode payment object
   before it is ever written to disk, logged, or shown in a demo. Raises
   ValueError if a genuinely prohibited credential field (cvv/otp/pin/etc.)
   is present, since those should never appear in a Test Mode payload at all.

2. map_to_recoverai_taxonomy(error_source, error_step, error_reason) —
   deterministically translates Razorpay's (error_source, error_step,
   error_reason) triplet into RecoverAI's internal
   (failure_category, failure_reason) taxonomy, per
   docs/razorpay_schema_mapping.md section 3.

Also provides a small CLI (`python tools/collect_razorpay_samples.py --payment-id pay_xxx`)
that fetches a single payment by ID from the Razorpay Test Mode API using
RAZORPAY_TEST_KEY_ID / RAZORPAY_TEST_KEY_SECRET, sanitizes it, maps it, and
saves it as a fixture under data/test_mode_examples/. This is optional and is
never required for RecoverAI's core decision engine or Step 5F evaluation to run.
"""

import os
import sys
import json
import argparse
from datetime import datetime, timezone

# ---------------------------------------------------------------------------
# Prohibited credential keys — presence of ANY of these in a raw payload is a
# hard abort, not a sanitization target. Test Mode payloads should never
# contain these; if one appears, something upstream is misconfigured.
# ---------------------------------------------------------------------------
PROHIBITED_CREDENTIAL_KEYS = [
    "cvv", "cvc", "otp", "pin", "password",
    "card_number", "bank_account_number", "auth_secret", "payment_token",
]

# Fields that are fully replaced with fixed placeholders (never derived from
# the real input, so no partial real data can ever leak through masking math).
_FIXED_REPLACEMENTS = {
    "contact": "+9198765*****",
    "email": "test_customer@example.com",
    "card_id": "card_test_mock_token",
}


def sanitize_payment_payload(raw: dict) -> dict:
    """
    Sanitize a raw Razorpay Test Mode payment entity for safe storage/display.

    Raises:
        ValueError: if a prohibited credential key is present in `raw`.
    """
    for key in PROHIBITED_CREDENTIAL_KEYS:
        if key in raw:
            raise ValueError(
                f"Security violation: Prohibited credential key '{key}' present "
                f"in raw Razorpay payload. Aborting sanitization."
            )

    sanitized = dict(raw)

    for field, placeholder in _FIXED_REPLACEMENTS.items():
        if field in sanitized:
            sanitized[field] = placeholder

    if "acquirer_data" in sanitized:
        sanitized["acquirer_data"] = {}

    return sanitized


# ---------------------------------------------------------------------------
# Razorpay error_reason -> RecoverAI taxonomy mapping.
#
# Keyed primarily on error_reason (Razorpay's most specific field), since a
# given error_reason maps deterministically to one RecoverAI failure_reason
# regardless of which error_source/error_step it arrived through. This
# mirrors docs/razorpay_schema_mapping.md section 3's mapping table and keeps
# every mapped failure_reason inside recoverai_agent.CANONICAL_FAILURE_REASONS
# so the frozen LightGBM model never sees an unseen category at inference time.
# ---------------------------------------------------------------------------
_REASON_MAP = {
    "network_error":            ("SOFT_DECLINE", "network_error"),
    "gateway_error":             ("SOFT_DECLINE", "gateway_error"),
    "gateway_technical_error":   ("SOFT_DECLINE", "gateway_error"),
    "bank_technical_error":      ("SOFT_DECLINE", "bank_technical_error"),
    "timed_out":                 ("SOFT_DECLINE", "payment_timed_out"),
    "payment_timed_out":         ("SOFT_DECLINE", "payment_timed_out"),
    "insufficient_funds":        ("FUNDS_ISSUE", "insufficient_funds"),
    "insufficient_fund":         ("FUNDS_ISSUE", "insufficient_funds"),
    "withdrawal_limit_exceeded": ("FUNDS_ISSUE", "withdrawal_limit_exceeded"),
    "invalid_otp":               ("CUSTOMER_ACTION_REQUIRED", "authentication_failed"),
    "authentication_failed":     ("CUSTOMER_ACTION_REQUIRED", "authentication_failed"),
    "expired_card":              ("CUSTOMER_ACTION_REQUIRED", "expired_card"),
    "card_disabled_for_online_payments": ("CUSTOMER_ACTION_REQUIRED", "card_not_enrolled"),
    "payment_cancelled":         ("GENERIC_DECLINE", "payment_cancelled"),
    "do_not_honor":              ("GENERIC_DECLINE", "do_not_honor"),
    "card_declined":             ("GENERIC_DECLINE", "payment_failed"),
    "card_number_invalid":       ("HARD_DECLINE", "card_number_invalid"),
    "compliance_violation":      ("HARD_DECLINE", "compliance_violation"),
    "stolen_card":                ("HARD_DECLINE", "stolen_card"),
    "boleto_expired":            ("HARD_DECLINE", "boleto_expired"),
}

_DEFAULT_MAPPING = ("GENERIC_DECLINE", "payment_failed")


def map_to_recoverai_taxonomy(error_source: str, error_step: str, error_reason: str) -> dict:
    """
    Deterministically map a Razorpay (error_source, error_step, error_reason)
    triplet to RecoverAI's (failure_category, failure_reason) taxonomy.

    error_source and error_step are accepted for API-contract completeness and
    future refinement (e.g. distinguishing bank- vs gateway-sourced network
    errors) but the current mapping is keyed on error_reason, which is
    Razorpay's most specific and most stable diagnostic field.
    """
    category, reason = _REASON_MAP.get(error_reason, _DEFAULT_MAPPING)
    return {
        "failure_category": category,
        "failure_reason": reason,
        "source_triplet": {
            "error_source": error_source,
            "error_step": error_step,
            "error_reason": error_reason,
        },
        "mapping_matched": error_reason in _REASON_MAP,
    }


def build_fixture(sanitized_payment: dict, scenario_tag: str) -> dict:
    """Wrap a sanitized payment + its taxonomy mapping into a fixture document."""
    mapping = map_to_recoverai_taxonomy(
        sanitized_payment.get("error_source", "unknown"),
        sanitized_payment.get("error_step", "unknown"),
        sanitized_payment.get("error_reason", "unknown"),
    )
    return {
        "provenance": "RAZORPAY_TEST_MODE",
        "sanitized": True,
        "scenario_tag": scenario_tag,
        "collected_at": datetime.now(timezone.utc).isoformat(),
        "payment": sanitized_payment,
        "recovered_taxonomy_mapping": mapping,
    }


def save_fixture(fixture: dict, out_dir: str) -> str:
    os.makedirs(out_dir, exist_ok=True)
    payment_id = fixture["payment"].get("id", "unknown")
    filename = f"{fixture['scenario_tag']}_{payment_id}.json"
    out_path = os.path.join(out_dir, filename)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(fixture, f, indent=2)

    manifest_path = os.path.join(out_dir, "manifest.json")
    manifest = {"sample_count": 0, "samples": []}
    if os.path.exists(manifest_path):
        with open(manifest_path, "r", encoding="utf-8") as f:
            manifest = json.load(f)
    manifest["samples"].append({
        "payment_id": payment_id,
        "scenario_tag": fixture["scenario_tag"],
        "file": filename,
    })
    manifest["sample_count"] = len(manifest["samples"])
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    return out_path


def _fetch_payment_from_razorpay(payment_id: str) -> dict:
    """Fetch a real payment entity from the Razorpay Test Mode API. Requires
    RAZORPAY_TEST_KEY_ID / RAZORPAY_TEST_KEY_SECRET env vars (rzp_test_... keys)."""
    import requests  # local import: only needed for the live CLI path

    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass

    key_id = os.environ.get("RAZORPAY_TEST_KEY_ID") or os.environ.get("RAZORPAY_KEY_ID")
    key_secret = os.environ.get("RAZORPAY_TEST_KEY_SECRET") or os.environ.get("RAZORPAY_KEY_SECRET")
    if not key_id or not key_secret:
        raise RuntimeError(
            "RAZORPAY_TEST_KEY_ID (or RAZORPAY_KEY_ID) / RAZORPAY_TEST_KEY_SECRET not set. "
            "Get test-mode keys (rzp_test_...) from the Razorpay Dashboard "
            "under Settings > API Keys (Test Mode)."
        )
    if not key_id.startswith("rzp_test_"):
        raise RuntimeError(
            "Refusing to run: RAZORPAY_TEST_KEY_ID does not start with 'rzp_test_'. "
            "This tool must never be pointed at live-mode keys."
        )

    try:
        resp = requests.get(
            f"https://api.razorpay.com/v1/payments/{payment_id}",
            auth=(key_id, key_secret),
            timeout=15,
        )
        if resp.status_code >= 400:
            raise RuntimeError(f"Razorpay API error ({resp.status_code}): {resp.text}")
        return resp.json()
    except requests.exceptions.Timeout:
        raise RuntimeError("Timed out fetching payment from Razorpay API (15s exceeded).")
    except requests.exceptions.RequestException as e:
        raise RuntimeError(f"Failed to connect to Razorpay API: {e}")


def main():
    parser = argparse.ArgumentParser(description="Collect and sanitize a Razorpay Test Mode payment sample.")
    parser.add_argument("--payment-id", required=True, help="Razorpay Test Mode payment ID (pay_...)")
    parser.add_argument("--scenario-tag", default="manual_capture", help="Short label for this scenario, e.g. 'insufficient_funds'")
    parser.add_argument("--out-dir", default=None, help="Output directory (default: data/test_mode_examples)")
    args = parser.parse_args()

    repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    out_dir = args.out_dir or os.path.join(repo_root, "data", "test_mode_examples")

    raw = _fetch_payment_from_razorpay(args.payment_id)
    sanitized = sanitize_payment_payload(raw)
    fixture = build_fixture(sanitized, args.scenario_tag)
    out_path = save_fixture(fixture, out_dir)
    print(f"Saved sanitized fixture: {out_path}")
    print(json.dumps(fixture["recovered_taxonomy_mapping"], indent=2))


if __name__ == "__main__":
    main()
