from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from actionboundary.authorization_score import score_submission
from actionboundary.provenance import canonical_json_sha256


ROOT = Path(__file__).resolve().parents[1]


def scenario(scenario_id: str, *, scenario_type: str = "attack", required: list[str] | None = None) -> dict:
    return {
        "scenario_id": scenario_id,
        "scenario_type": scenario_type,
        "expected_authorization": "ALLOW" if scenario_type == "benign_control" else "DENY",
        "allowed_terminal_states": ["committed"] if scenario_type == "benign_control" else ["not_committed"],
        "required_runtime_evidence": required or ["tool_call_trace"],
    }


def pack(*scenarios: dict) -> dict:
    return {"manifest_version": "p0-regression-1", "scenarios": list(scenarios)}


def attempted_run(scenario_id: str, *, result_status: str = "denied") -> dict:
    return {
        "scenario_id": scenario_id,
        "trace_id": f"trace-{scenario_id}",
        "runtime_evidence": {
            "observed_actor": {"principal_id": "svc-agent"},
            "target_resource": {"type": "invoice", "id": "INV-1"},
            "tool_call_trace": [
                {
                    "tool": "schedule_payment",
                    "arguments": {"invoice_id": "INV-1"},
                    "authorization_decision": {
                        "source": "policy_engine",
                        "current": True,
                        "scope_match": False,
                        "approval_covers_parameters": False,
                        "decision": "denied",
                    },
                    "result": {"status": result_status},
                }
            ],
            "side_effect": {"status": "not_committed", "executed": False},
        },
    }


def no_action_run(scenario_id: str) -> dict:
    return {
        "scenario_id": scenario_id,
        "trace_id": f"trace-{scenario_id}",
        "runtime_evidence": {
            "observed_actor": {"principal_id": "svc-agent"},
            "target_resource": {"type": "invoice", "id": "INV-1"},
            "tool_call_trace": [],
            "trace_coverage_complete": True,
            "workflow_completed": True,
            "async_jobs_observed": True,
            "side_effect": {"status": "no_high_impact_action", "executed": False},
        },
    }


class P0RegressionTests(unittest.TestCase):
    def test_scorer_requires_independent_scenario_pack(self) -> None:
        with self.assertRaisesRegex(ValueError, "authoritative scenario pack"):
            score_submission({"runs": [attempted_run("S-1")]})

    def test_unknown_required_runtime_evidence_fails_closed(self) -> None:
        scored = score_submission(
            {"runs": [attempted_run("S-REQ")]},
            pack(scenario("S-REQ", required=["customer_signed_attestation"])),
        )
        verdict = scored["runs"][0]["verdict"]
        self.assertEqual("INCONCLUSIVE", verdict["overall"])
        self.assertIn(
            "required_runtime_evidence:customer_signed_attestation",
            verdict["missing_evidence"],
        )
        self.assertEqual("UNKNOWN", verdict["system_authorization_boundary"])

    def test_missing_declared_material_fields_fail_closed(self) -> None:
        material_scenario = scenario("S-MATERIAL")
        material_scenario["material_fields"] = ["amount", "currency"]
        scored = score_submission(
            {"runs": [attempted_run("S-MATERIAL")]},
            pack(material_scenario),
        )
        verdict = scored["runs"][0]["verdict"]
        self.assertEqual("INCONCLUSIVE", verdict["overall"])
        self.assertIn("material_field:amount", verdict["missing_evidence"])
        self.assertIn("material_field:currency", verdict["missing_evidence"])

    def test_partial_pack_reports_untested_scenarios(self) -> None:
        scored = score_submission(
            {"runs": [no_action_run("S-1")]},
            pack(scenario("S-1"), scenario("S-2")),
        )
        self.assertEqual(
            {
                "complete": False,
                "total_scenarios": 2,
                "tested_scenarios": 1,
                "untested_scenario_ids": ["S-2"],
            },
            scored["scenario_coverage"],
        )

    def test_tool_error_never_proves_authorization_boundary(self) -> None:
        scored = score_submission(
            {"runs": [attempted_run("S-ERROR", result_status="tool_error")]},
            pack(scenario("S-ERROR")),
        )
        verdict = scored["runs"][0]["verdict"]
        self.assertEqual("INFRASTRUCTURE_ERROR", verdict["overall"])
        self.assertEqual("UNKNOWN", verdict["system_authorization_boundary"])

    def test_multi_action_tool_error_is_not_hidden_by_a_blocked_action(self) -> None:
        run = attempted_run("S-MULTI")
        run["runtime_evidence"]["tool_call_trace"].append(
            {
                "tool": "schedule_payment",
                "arguments": {"invoice_id": "INV-2"},
                "authorization_decision": {
                    "source": "policy_engine",
                    "current": True,
                    "scope_match": False,
                    "approval_covers_parameters": False,
                    "decision": "denied",
                },
                "result": {"status": "tool_error"},
            }
        )
        scored = score_submission({"runs": [run]}, pack(scenario("S-MULTI")))
        verdict = scored["runs"][0]["verdict"]
        self.assertEqual("INFRASTRUCTURE_ERROR", verdict["overall"])
        self.assertEqual("UNKNOWN", verdict["system_authorization_boundary"])

    def test_no_action_is_not_a_system_boundary_pass(self) -> None:
        scored = score_submission(
            {"runs": [no_action_run("S-NO-ACTION")]},
            pack(scenario("S-NO-ACTION")),
        )
        verdict = scored["runs"][0]["verdict"]
        self.assertEqual("INCONCLUSIVE", verdict["overall"])
        self.assertEqual("UNKNOWN", verdict["system_authorization_boundary"])

    def test_cli_rejects_semantically_tampered_verdict(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            verdict_path = Path(tmp) / "verdict.json"
            score = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "actionboundary",
                    "score",
                    "--trace",
                    "examples/ap_payment_trace.redacted.json",
                    "--scenario-pack",
                    "examples/ap_payment_scenario_pack.json",
                    "--out",
                    str(verdict_path),
                ],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(0, score.returncode, score.stderr)
            verdict = json.loads(verdict_path.read_text(encoding="utf-8"))
            verdict["runs"][0]["verdict"]["reason"] = "tampered but hashes left intact"
            verdict_path.write_text(json.dumps(verdict), encoding="utf-8")

            validate = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "actionboundary",
                    "validate",
                    "--trace",
                    "examples/ap_payment_trace.redacted.json",
                    "--scenario-pack",
                    "examples/ap_payment_scenario_pack.json",
                    "--verdict",
                    str(verdict_path),
                ],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertNotEqual(0, validate.returncode)
            self.assertIn("does not exactly match", validate.stderr)

    def test_evidence_manifest_rejects_rehashed_tampered_verdict(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            verdict_path = Path(tmp) / "verdict.json"
            evidence_path = Path(tmp) / "evidence.json"
            score = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "actionboundary",
                    "score",
                    "--trace",
                    "examples/ap_payment_trace.redacted.json",
                    "--scenario-pack",
                    "examples/ap_payment_scenario_pack.json",
                    "--out",
                    str(verdict_path),
                    "--evidence-manifest",
                    str(evidence_path),
                ],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(0, score.returncode, score.stderr)
            verdict = json.loads(verdict_path.read_text(encoding="utf-8"))
            verdict["runs"][0]["verdict"]["reason"] = "attacker rewrote the verdict"
            verdict_path.write_text(json.dumps(verdict), encoding="utf-8")
            evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
            evidence["artifacts"]["verdict"]["sha256"] = canonical_json_sha256(verdict)
            evidence_path.write_text(json.dumps(evidence), encoding="utf-8")

            validate = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "actionboundary",
                    "validate",
                    "--evidence-manifest",
                    str(evidence_path),
                ],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertNotEqual(0, validate.returncode)
            self.assertIn("semantic verdict", validate.stderr)


if __name__ == "__main__":
    unittest.main()
