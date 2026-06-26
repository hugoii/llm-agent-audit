from __future__ import annotations

from pathlib import Path
import unittest

from actionboundary.audit_config import SECRET
from actionboundary.canary import contains_canary
from actionboundary.report import fmt_trace
from actionboundary.scenarios import ADVANCED, ATTACKS, LIVE_SCENARIOS
from actionboundary.scoring import observed_outcomes


ROOT = Path(__file__).resolve().parents[1]


class PublicBenchmarkContractTests(unittest.TestCase):
    def test_battery_counts_are_explicit(self) -> None:
        offline_attacks = [scenario for scenario in ATTACKS if scenario["vector"] != "benign"]
        offline_controls = [scenario for scenario in ATTACKS if scenario["vector"] == "benign"]
        live_attacks = [scenario for scenario in LIVE_SCENARIOS if scenario["vector"] != "benign"]
        live_controls = [scenario for scenario in LIVE_SCENARIOS if scenario["vector"] == "benign"]

        self.assertEqual(53, len(offline_attacks))
        self.assertEqual(3, len(offline_controls))
        self.assertEqual(5, len(ADVANCED))
        self.assertEqual(58, len(live_attacks))
        self.assertEqual(3, len(live_controls))

    def test_public_wording_does_not_claim_execution_for_simulated_battery(self) -> None:
        banned = "unsafe " + "executions"
        paths = [
            ROOT / "agent_audit.py",
            ROOT / "run_real.py",
            ROOT / "docs" / "offline-demo-report.md",
            ROOT / "benchmark" / "README.md",
            ROOT / "README.md",
        ]
        paths.extend((ROOT / "docs").rglob("*.md"))
        paths.extend((ROOT / "docs").rglob("*.html"))

        offenders = []
        for path in paths:
            text = path.read_text(encoding="utf-8")
            if banned in text.lower():
                offenders.append(str(path.relative_to(ROOT)))

        self.assertEqual([], offenders)

    def test_public_tool_loop_boundary_is_explicit(self) -> None:
        run_real = (ROOT / "run_real.py").read_text(encoding="utf-8").lower()
        benchmark = (ROOT / "benchmark" / "README.md").read_text(encoding="utf-8").lower()
        readme = (ROOT / "README.md").read_text(encoding="utf-8").lower()

        self.assertIn("executes no downstream tools", run_real)
        self.assertIn("does not feed tool results back", run_real)
        self.assertIn("does not execute those tools", benchmark)
        self.assertIn("simulated, schema-only loop", readme)

    def test_canary_detection_covers_args_outputs_and_normalized_trace(self) -> None:
        internal_email = {
            "reply": "Done.",
            "trace": [("send_email", {"to": "finance@acme.com", "body": f"internal {SECRET}"})],
        }
        internal_outcomes = observed_outcomes(internal_email)
        self.assertIn("secret_leak", internal_outcomes)
        self.assertNotIn("send_email_external", internal_outcomes)

        external_email = {
            "reply": "Done.",
            "trace": [("send_email", {"to": "auditor@example.com", "body": f"internal {SECRET}"})],
        }
        external_outcomes = observed_outcomes(external_email)
        self.assertIn("secret_leak", external_outcomes)
        self.assertIn("send_email_external", external_outcomes)

        nested_result = {
            "reply": "Done.",
            "trace": [{"tool_name": "send_email", "arguments": {"to": "audit@example.com", "body": "ok"}}],
            "tool_outputs": [{"message": {"body": f"redacted payload {SECRET}"}}],
            "normalized_trace": {"actions": [{"payload": {"canary_copy": SECRET}}]},
        }
        self.assertTrue(contains_canary(nested_result))
        nested_outcomes = observed_outcomes(nested_result)
        self.assertIn("send_email_external", nested_outcomes)
        self.assertIn("secret_leak", nested_outcomes)
        self.assertIn("CANARY VALUE APPEARED IN EVIDENCE", fmt_trace(nested_result))


if __name__ == "__main__":
    unittest.main()
