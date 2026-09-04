"""
tools/trigger_test_failure.py
==============================

Demo helper for the LIVE Razorpay Test Mode bridge (src/integrations/razorpay_live.py).

Two modes:

1. LIVE (default) — creates a real Razorpay Test Mode Payment Link via the
   sandbox API and prints its URL plus a matching Razorpay-documented test
   card number for the failure scenario you pick. You open the link, pay with
   the test card, and click "Failure" on Razorpay's mock bank page — Razorpay
   then fires a REAL payment.failed webhook at your running
   src/integrations/razorpay_live.py server.

2. --offline-replay — skips Razorpay entirely and POSTs a locally-built,
   correctly-signed webhook payload straight at your local bridge server.
   This exercises the exact same signature-verification -> sanitize -> map ->
   agent.recommend() -> execute code path, with zero dependency on internet
   access or Razorpay's sandbox being reachable during a live demo.

   IMPORTANT: --offline-replay does NOT talk to Razorpay. If you use it in
   front of judges, say so plainly ("this is a rehearsal replay of a real
   webhook shape, not a live sandbox call") — don't present it as live.

Usage:
    # Live mode — creates a real sandbox Payment Link
    python tools/trigger_test_failure.py --scenario insufficient_funds --amount 499

    # Offline replay — no internet / Razorpay dependency, same code path
    python tools/trigger_test_failure.py --offline-replay --scenario authentication_failed --amount 499
"""

import os
import sys
import json
import hmac
import hashlib
import argparse
import uuid
from datetime import datetime, timezone

# Razorpay-documented test cards per error_reason, official as of the docs
# fetched for this project (razorpay.com/docs/payments/payments/test-card-details).
# CVV: any random 3 digits. Expiry: any future date.
SCENARIO_CARDS = {
    "payment_timed_out": {"network": "Visa", "number": "4100 2800 0009 0000"},
    "insufficient_funds": {"network": "Visa", "number": "4100 2800 0008 0001"},
    "payment_cancelled": {"network": "Visa", "number": "4100 2800 0007 0002"},
    "card_declined": {"network": "Visa", "number": "4100 2800 0006 0003"},
    "card_number_invalid": {"network": "Visa", "number": "4100 2800 0001 0008"},
    "gateway_technical_error": {"network": "Visa", "number": "4100 2800 0002 0007"},
    "authentication_failed": {"network": "Visa", "number": "4100 2800 0000 0009"},
}


try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


def create_live_payment_link(amount_rupees: float, scenario: str) -> dict:
    import requests

    key_id = os.environ.get("RAZORPAY_TEST_KEY_ID") or os.environ.get("RAZORPAY_KEY_ID")
    key_secret = os.environ.get("RAZORPAY_TEST_KEY_SECRET") or os.environ.get("RAZORPAY_KEY_SECRET")
    if not key_id or not key_secret:
        raise SystemExit("Set RAZORPAY_TEST_KEY_ID (or RAZORPAY_KEY_ID) and RAZORPAY_TEST_KEY_SECRET (or RAZORPAY_KEY_SECRET) first.")
    if not key_id.startswith("rzp_test_"):
        raise SystemExit("Refusing: key ID must start with 'rzp_test_'.")

    try:
        resp = requests.post(
            "https://api.razorpay.com/v1/payment_links",
            auth=(key_id, key_secret),
            json={
                "amount": int(round(amount_rupees * 100)),
                "currency": "INR",
                "description": f"RecoverAI demo trigger ({scenario})",
                "notes": {"recoverai_demo_scenario": scenario},
            },
            timeout=15,
        )
        if resp.status_code >= 400:
            raise SystemExit(f"Razorpay API error ({resp.status_code}): {resp.text}")
        return resp.json()
    except requests.exceptions.Timeout:
        raise SystemExit("Timed out connecting to Razorpay sandbox API (15s exceeded).")
    except requests.exceptions.RequestException as e:
        raise SystemExit(f"Failed to connect to Razorpay sandbox API: {e}")


def build_offline_payload(scenario: str, amount_rupees: float) -> dict:
    """Build a realistic-shaped (but clearly labeled) payment.failed event body
    for offline replay. Field names/shape follow Razorpay's documented
    payment.failed webhook entity structure."""
    reason_meta = {
        "payment_timed_out": ("bank", "payment_authorization"),
        "insufficient_funds": ("bank", "payment_authorization"),
        "payment_cancelled": ("customer", "payment_initiation"),
        "card_declined": ("bank", "payment_authorization"),
        "card_number_invalid": ("customer", "payment_initiation"),
        "gateway_technical_error": ("gateway", "payment_authorization"),
        "authentication_failed": ("customer", "payment_authentication"),
    }
    source, step = reason_meta.get(scenario, ("bank", "payment_authorization"))
    payment_id = f"pay_OFFLINEREPLAY{uuid.uuid4().hex[:14]}"

    return {
        "event": "payment.failed",
        "payload": {
            "payment": {
                "entity": {
                    "id": payment_id,
                    "entity": "payment",
                    "amount": int(round(amount_rupees * 100)),
                    "currency": "INR",
                    "status": "failed",
                    "method": "card",
                    "card": {"type": "credit"},
                    "error_code": "BAD_REQUEST_ERROR",
                    "error_description": f"[OFFLINE REPLAY FIXTURE] simulated {scenario}",
                    "error_source": source,
                    "error_step": step,
                    "error_reason": scenario,
                    "contact": "+919900000000",
                    "email": "demo@example.com",
                    "_offline_replay": True,
                    "_replayed_at": datetime.now(timezone.utc).isoformat(),
                }
            }
        },
    }


def post_to_bridge(payload: dict, bridge_url: str):
    import requests

    webhook_secret = os.environ.get("RAZORPAY_WEBHOOK_SECRET")
    if not webhook_secret and os.environ.get("RECOVERAI_DEMO_MODE") == "true":
        webhook_secret = "recoverai_test_webhook_secret_2026"
    if not webhook_secret:
        raise SystemExit("Set RAZORPAY_WEBHOOK_SECRET (or enable RECOVERAI_DEMO_MODE=true) to the same value your local bridge server uses.")

    raw_body = json.dumps(payload).encode("utf-8")
    signature = hmac.new(webhook_secret.encode("utf-8"), raw_body, hashlib.sha256).hexdigest()

    try:
        resp = requests.post(
            bridge_url,
            data=raw_body,
            headers={"Content-Type": "application/json", "X-Razorpay-Signature": signature},
            timeout=15,
        )
        print(f"Bridge responded {resp.status_code}:")
        try:
            print(json.dumps(resp.json(), indent=2))
        except Exception:
            print(resp.text)
    except requests.exceptions.ConnectionError:
        raise SystemExit(f"Could not connect to live bridge at {bridge_url}. Is 'uvicorn src.integrations.razorpay_live:app --port 8010' running?")
    except requests.exceptions.Timeout:
        raise SystemExit(f"Timed out waiting for response from live bridge at {bridge_url} (15s).")
    except Exception as e:
        raise SystemExit(f"Error posting to bridge: {e}")


def main():
    parser = argparse.ArgumentParser(description="Trigger a Razorpay Test Mode payment failure for the RecoverAI live demo.")
    parser.add_argument("--scenario", choices=list(SCENARIO_CARDS.keys()), default="insufficient_funds")
    parser.add_argument("--amount", type=float, default=499.0, help="Amount in INR")
    parser.add_argument("--offline-replay", action="store_true", help="Skip Razorpay; POST a local replay payload directly to the bridge")
    parser.add_argument("--bridge-url", default="http://localhost:8010/webhook/razorpay")
    args = parser.parse_args()

    if args.offline_replay:
        print("[OFFLINE REPLAY MODE — no Razorpay API call, no live webhook]")
        payload = build_offline_payload(args.scenario, args.amount)
        post_to_bridge(payload, args.bridge_url)
        return

    card = SCENARIO_CARDS[args.scenario]
    link = create_live_payment_link(args.amount, args.scenario)
    print(f"Created LIVE Razorpay Test Mode payment link: {link.get('short_url')}")
    print(f"Open it, choose Card, enter:")
    print(f"  Network: {card['network']}")
    print(f"  Card number: {card['number']}")
    print(f"  CVV: any 3 digits, Expiry: any future date")
    print("On the mock bank result screen, click 'Failure'.")
    print("Razorpay will then fire a real payment.failed webhook at your running bridge server.")


if __name__ == "__main__":
    main()
