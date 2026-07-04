from __future__ import annotations

import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
HARNESS = ROOT / "pilot" / "stripe_customer_support"
sys.path.insert(0, str(HARNESS))

import run_stripe_boundary as runner  # noqa: E402


class StripeCustomerSupportHarnessTests(unittest.TestCase):
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
