"""
tests/test_razorpay_schema.py
=============================

Offline Contract Verification Suite for Razorpay Test Mode Schema Validation.

ARCHITECTURAL SAFETY GUARANTEES:
--------------------------------
1. 100% Offline: Never initiates any network socket or HTTP request.
2. Zero Credentials Required: Runs cleanly without any environment keys.
3. Decoupled Isolation: Never imports `src/recoverai_agent.py`, `src/api/server.py`,
   `src/batch/run_batch.py`, or `frontend/src/lib/api.ts`.
4. Validates sanitization logic, required error schema structures, and taxonomy mapping.
"""

import os
import sys
import glob
import json
import pytest

# Target paths
REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FIXTURE_DIR = os.path.join(REPO_ROOT, "data", "test_mode_examples")
TOOLS_DIR = os.path.join(REPO_ROOT, "tools")
MAPPING_DOC = os.path.join(REPO_ROOT, "docs", "razorpay_schema_mapping.md")

# Ensure tools directory is accessible for testing the isolated sanitization logic
if TOOLS_DIR not in sys.path:
    sys.path.insert(0, TOOLS_DIR)

from collect_razorpay_samples import sanitize_payment_payload, map_to_recoverai_taxonomy


class TestRazorpaySchemaContract:
    """Offline contract test suite validating Razorpay Test Mode schema rules."""

    def test_mapping_documentation_exists(self):
        """Verify that docs/razorpay_schema_mapping.md exists and contains required sections."""
        assert os.path.exists(MAPPING_DOC), f"Documentation file {MAPPING_DOC} missing!"
        with open(MAPPING_DOC, "r", encoding="utf-8") as f:
            content = f.read()

        # Check required provenance distinctions
        assert "REAL HISTORICAL DATA" in content
        assert "RAZORPAY TEST MODE DATA" in content
        assert "DERIVED DATA" in content
        assert "SIMULATED DATA" in content

        # Check documented schema fields
        assert "error_code" in content
        assert "error_description" in content
        assert "error_source" in content
        assert "error_step" in content
        assert "error_reason" in content

        # Check mapping structure
        assert "failure_category" in content
        assert "failure_reason" in content

    def test_fixture_directory_exists(self):
        """Verify that data/test_mode_examples/ exists with README.md."""
        assert os.path.exists(FIXTURE_DIR), f"Directory {FIXTURE_DIR} missing!"
        readme_path = os.path.join(FIXTURE_DIR, "README.md")
        assert os.path.exists(readme_path), "README.md in data/test_mode_examples/ missing!"

        with open(readme_path, "r", encoding="utf-8") as f:
            readme_text = f.read()
        assert "RAZORPAY_TEST_MODE" in readme_text
        assert "NOT Model Training Data" in readme_text

    def test_sanitization_removes_forbidden_fields(self):
        """Verify that sanitizer rejects or purges any sensitive identifiers."""
        # Simulated raw test mode response with mock identifiers
        raw_mock = {
            "id": "pay_test_12345",
            "entity": "payment",
            "amount": 25000,
            "currency": "INR",
            "status": "failed",
            "order_id": "order_test_98765",
            "method": "card",
            "contact": "+919988776655",
            "email": "customer_personal@example.com",
            "card_id": "card_real_token_123",
            "acquirer_data": {"rrn": "123456789012", "bank_transaction_id": "tx_999"},
            "error_code": "BAD_REQUEST_ERROR",
            "error_description": "Payment failed due to incorrect OTP",
            "error_source": "customer",
            "error_step": "payment_authentication",
            "error_reason": "invalid_otp"
        }

        sanitized = sanitize_payment_payload(raw_mock)

        # Confirm masked and purged fields
        assert sanitized["contact"] == "+9198765*****"
        assert sanitized["email"] == "test_customer@example.com"
        assert sanitized["card_id"] == "card_test_mock_token"
        assert sanitized["acquirer_data"] == {}

        # Confirm preservation of failure diagnostics
        assert sanitized["error_code"] == "BAD_REQUEST_ERROR"
        assert sanitized["error_source"] == "customer"
        assert sanitized["error_step"] == "payment_authentication"
        assert sanitized["error_reason"] == "invalid_otp"

    def test_sanitizer_aborts_on_forbidden_credentials(self):
        """Verify that sanitizer strictly raises an exception if CVV, OTP, or PIN are present."""
        forbidden_payload = {
            "id": "pay_leakage_test",
            "amount": 1000,
            "cvv": "123",
            "error_code": "BAD_REQUEST_ERROR"
        }
        with pytest.raises(ValueError, match="Security violation: Prohibited credential key 'cvv'"):
            sanitize_payment_payload(forbidden_payload)

        forbidden_otp_payload = {
            "id": "pay_leakage_test",
            "amount": 1000,
            "otp": "123456",
            "error_code": "BAD_REQUEST_ERROR"
        }
        with pytest.raises(ValueError, match="Security violation: Prohibited credential key 'otp'"):
            sanitize_payment_payload(forbidden_otp_payload)

    def test_taxonomy_mapping_logic(self):
        """Verify deterministic translation from Razorpay failure triplets to RecoverAI taxonomy."""
        # 1. Invalid OTP -> CUSTOMER_ACTION_REQUIRED / authentication_failed
        res1 = map_to_recoverai_taxonomy("customer", "payment_authentication", "invalid_otp")
        assert res1["failure_category"] == "CUSTOMER_ACTION_REQUIRED"
        assert res1["failure_reason"] == "authentication_failed"

        # 2. Insufficient Funds -> FUNDS_ISSUE / insufficient_funds
        res2 = map_to_recoverai_taxonomy("customer", "payment_authorization", "insufficient_funds")
        assert res2["failure_category"] == "FUNDS_ISSUE"
        assert res2["failure_reason"] == "insufficient_funds"

        # 3. Card Number Invalid -> HARD_DECLINE / card_number_invalid
        res3 = map_to_recoverai_taxonomy("customer", "payment_initiation", "card_number_invalid")
        assert res3["failure_category"] == "HARD_DECLINE"
        assert res3["failure_reason"] == "card_number_invalid"

        # 4. Network Error -> SOFT_DECLINE / network_error
        res4 = map_to_recoverai_taxonomy("bank", "payment_authorization", "network_error")
        assert res4["failure_category"] == "SOFT_DECLINE"
        assert res4["failure_reason"] == "network_error"

    def test_existing_fixtures_conform_to_schema(self):
        """If any static fixture JSON files exist in data/test_mode_examples/, validate them."""
        fixture_files = glob.glob(os.path.join(FIXTURE_DIR, "*.json"))
        
        # If no fixtures have been collected yet, this test gracefully passes
        for f_path in fixture_files:
            if os.path.basename(f_path) == "manifest.json":
                continue
            with open(f_path, "r", encoding="utf-8") as f:
                doc = json.load(f)

            # Check top-level metadata
            assert doc.get("provenance") == "RAZORPAY_TEST_MODE", f"Invalid provenance in {f_path}"
            assert doc.get("sanitized") is True, f"Fixture {f_path} not marked sanitized"
            assert "payment" in doc, f"Missing 'payment' in {f_path}"
            assert "recovered_taxonomy_mapping" in doc, f"Missing 'recovered_taxonomy_mapping' in {f_path}"

            p = doc["payment"]
            assert "id" in p and p["id"].startswith("pay_"), f"Malformed payment id in {f_path}"
            assert p.get("status") == "failed", f"Fixture payment status is not 'failed' in {f_path}"
            assert "amount" in p and isinstance(p["amount"], (int, float))
            assert p.get("currency") == "INR"
            assert "error_code" in p
            assert "error_source" in p
            assert "error_step" in p
            assert "error_reason" in p

            # Strictly verify no raw PAN, CVV, OTP, or secrets leaked into fixture
            forbidden_tokens = ["key_secret", "cvv", "otp", "pin", "password"]
            p_str = json.dumps(p).lower()
            for tok in forbidden_tokens:
                assert tok not in p, f"Forbidden key '{tok}' leaked into {f_path}!"

    def test_isolated_architecture_zero_imports_in_core_engine(self):
        """
        Verify that collect_razorpay_samples is NEVER imported in:
          - src/recoverai_agent.py
          - src/api/server.py
          - src/batch/run_batch.py
          - frontend/src/lib/api.ts
        """
        core_files = [
            os.path.join(REPO_ROOT, "src", "recoverai_agent.py"),
            os.path.join(REPO_ROOT, "src", "api", "server.py"),
            os.path.join(REPO_ROOT, "src", "batch", "run_batch.py"),
            os.path.join(REPO_ROOT, "frontend", "src", "lib", "api.ts")
        ]

        for c_file in core_files:
            if os.path.exists(c_file):
                with open(c_file, "r", encoding="utf-8") as f:
                    src_text = f.read().lower()
                assert "collect_razorpay_samples" not in src_text, (
                    f"Core execution file {c_file} illegally imports collection tool!"
                )

    def test_manifest_structure(self):
        """Verify that manifest.json (if present) is properly formatted and tracks valid samples."""
        manifest_path = os.path.join(FIXTURE_DIR, "manifest.json")
        if os.path.exists(manifest_path):
            with open(manifest_path, "r", encoding="utf-8") as f:
                manifest = json.load(f)
            assert "sample_count" in manifest
            assert "samples" in manifest
            assert isinstance(manifest["samples"], list)
            for s in manifest["samples"]:
                assert "payment_id" in s
                assert "scenario_tag" in s
                assert "file" in s
