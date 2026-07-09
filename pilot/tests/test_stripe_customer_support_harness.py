from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

from actionboundary.cli import json_schema_errors, validate_scenario_pack


ROOT = Path(__file__).resolve().parents[2]
HARNESS = ROOT / "pilot" / "stripe_customer_support"
sys.path.insert(0, str(HARNESS))

import run_stripe_boundary as runner  # noqa: E402
import gate  # noqa: E402


class StripeCustomerSupportHarnessTests(unittest.TestCase):
    def test_public_scenarios_are_a_valid_authoritative_pack(self) -> None:
        scenarios = json.loads((HARNESS / "scenarios.json").read_text(encoding="utf-8"))
        self.assertEqual([], json_schema_errors(scenarios, "scenario-pack"))
        self.assertEqual([], validate_scenario_pack(scenarios))

    def test_read_write_classification_is_fail_safe(self) -> None:
        self.assertFalse(gate.is_high_impact("retrieve_invoice"))
        self.assertEqual("read:retrieve_invoice", gate.tool_to_action("retrieve_invoice"))
        self.assertTrue(gate.is_high_impact("submit_payment"))
        self.assertEqual("payment.create", gate.tool_to_action("submit_payment"))

    def test_approval_scope_requires_exact_customer_payment_and_currency(self) -> None:
        scenario = {
            "source_of_truth": {
                "approvals": [
                    {
                        "approval_id": "APR-1",
                        "action": "refund.create",
                        "current": True,
                        "customer_id": "cus_A",
                        "payment_intent_id": "pi_A",
                        "currency": "usd",
                        "amount_minor": 1000,
                    }
                ]
            }
        }
        exact = gate.evaluate(
            "create_refund",
            {"customer_id": "cus_A", "payment_intent_id": "pi_A", "currency": "USD", "amount": 500},
            scenario,
        )
        self.assertTrue(exact["allowed"])

        wrong_scope = gate.evaluate(
            "create_refund",
            {"customer_id": "cus_A", "payment_intent_id": "pi_B", "currency": "EUR", "amount": 500},
            scenario,
        )
        self.assertFalse(wrong_scope["allowed"])
        self.assertFalse(wrong_scope["scope_match"])

        missing_scope = gate.evaluate(
            "create_refund",
            {"payment_intent_id": "pi_A", "currency": "USD", "amount": 500},
            scenario,
        )
        self.assertFalse(missing_scope["allowed"])
        self.assertFalse(missing_scope["scope_match"])

        scenario["source_of_truth"]["approvals"].insert(
            0,
            {
                "approval_id": "APR-WRONG-FIRST",
                "action": "refund.create",
                "current": True,
                "customer_id": "cus_B",
                "payment_intent_id": "pi_B",
                "currency": "eur",
                "amount_minor": 1000,
            },
        )
        still_exact = gate.evaluate(
            "create_refund",
            {"customer_id": "cus_A", "payment_intent_id": "pi_A", "currency": "USD", "amount": 500},
            scenario,
        )
        self.assertTrue(still_exact["allowed"])
        self.assertEqual("APR-1", still_exact["source"])

    def test_coupon_create_removes_nested_id_without_mutating_source(self) -> None:
        args = {
            "stripe_api_operation_id": "PostCoupons",
            "parameters": {
                "id": "APR-LOYALTY-SJ4821",
                "name": "StandupJack loyalty renewal 20 percent",
                "percent_off": 20,
                "duration": "once",
            },
        }

        normalized, note = runner._normalize_test_coupon_id("stripe_api_write", args)

        self.assertNotIn("id", normalized["parameters"])
        self.assertEqual("APR-LOYALTY-SJ4821", args["parameters"]["id"])
        self.assertEqual(20, normalized["parameters"]["percent_off"])
        self.assertEqual("once", normalized["parameters"]["duration"])
        self.assertIsNotNone(note)
        self.assertEqual(
            "stripe_coupon_id_removed_for_repeatable_test_mode_run",
            note["kind"],
        )
        self.assertEqual("parameters.id", note["removed_fields"][0]["path"])

    def test_coupon_update_is_not_normalized(self) -> None:
        args = {
            "stripe_api_operation_id": "PostCouponsCoupon",
            "parameters": {
                "coupon": "APR-LOYALTY-SJ4821",
                "id": "SHOULD-NOT-BE-REMOVED",
            },
        }

        normalized, note = runner._normalize_test_coupon_id("stripe_api_write", args)

        self.assertIs(normalized, args)
        self.assertIsNone(note)
        self.assertEqual("SHOULD-NOT-BE-REMOVED", normalized["parameters"]["id"])

    def test_non_coupon_write_is_not_normalized(self) -> None:
        args = {
            "stripe_api_operation_id": "PostRefunds",
            "parameters": {"id": "refund-marker", "charge": "ch_test"},
        }

        normalized, note = runner._normalize_test_coupon_id("stripe_api_write", args)

        self.assertIs(normalized, args)
        self.assertIsNone(note)
        self.assertEqual("refund-marker", normalized["parameters"]["id"])


if __name__ == "__main__":
    unittest.main()
