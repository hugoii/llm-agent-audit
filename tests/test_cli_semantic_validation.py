from __future__ import annotations

import unittest

from actionboundary.cli import (
    validate_scenario_pack,
    validate_trace_submission,
    validate_verdict,
)


class CliSemanticValidationTests(unittest.TestCase):
    def test_trace_run_missing_expected_authorization_and_tool_trace_fails(self) -> None:
        errors = validate_trace_submission({"runs": [{"scenario_id": "AP-PAY-1"}]})

        self.assertIn("runs[1].expected_authorization is required", errors)
        self.assertIn("runs[1].tool_call_trace is required", errors)

    def test_scenario_pack_duplicate_scenario_id_fails(self) -> None:
        errors = validate_scenario_pack(
            {
                "manifest_version": "pilot-scenario-pack-1.1",
                "scenarios": [
                    {
                        "scenario_id": "AP-PAY-1",
                        "expected_authorization": "DENY",
                        "required_runtime_evidence": ["approval_lookup"],
                        "allowed_terminal_states": ["routed_to_review"],
                    },
                    {
                        "scenario_id": "AP-PAY-1",
                        "expected_authorization": "ALLOW",
                        "required_runtime_evidence": ["approval_lookup"],
                        "allowed_terminal_states": ["committed"],
                    },
                ],
            }
        )

        self.assertIn("duplicate scenario_id: AP-PAY-1", errors)

    def test_verdict_run_with_unknown_overall_status_fails(self) -> None:
        errors = validate_verdict(
            {
                "schema_version": "pilot-verdict-1.4",
                "contract_set_version": "actionboundary-contract-set-1.2",
                "counts": {},
                "runs": [
                    {
                        "scenario_id": "AP-PAY-1",
                        "verdict": {"overall": "BOGUS"},
                    }
                ],
            }
        )

        self.assertIn("verdict runs[1].verdict.overall has unknown status: 'BOGUS'", errors)


if __name__ == "__main__":
    unittest.main()
