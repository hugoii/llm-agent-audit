from __future__ import annotations

import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from jsonschema import Draft202012Validator

from actionboundary.authorization_score import score_submission
from actionboundary.readiness import assess_evidence_events


ROOT = Path(__file__).resolve().parents[1]


def load(relative: str) -> dict:
    return json.loads((ROOT / relative).read_text(encoding="utf-8"))


class HarnessEvidenceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.trace = load("examples/harness_control_trace.redacted.json")
        self.pack = load("examples/harness_control_scenario_pack.json")
        self.events = load("examples/minimal_evidence_events.redacted.json")

    def test_harness_examples_match_public_schemas(self) -> None:
        trace_schema = load("normalized_trace.schema.json")
        pack_schema = load("scenario_pack.schema.json")
        event_schema = load("evidence_event.schema.json")
        self.assertEqual([], list(Draft202012Validator(trace_schema).iter_errors(self.trace)))
        self.assertEqual([], list(Draft202012Validator(pack_schema).iter_errors(self.pack)))
        self.assertEqual([], list(Draft202012Validator(event_schema).iter_errors(self.events)))

    def test_harness_control_pack_exercises_four_failures_and_one_control(self) -> None:
        scored = score_submission(self.trace, self.pack)
        self.assertEqual({"EXPLOITED": 4, "BENIGN_PASS": 1}, scored["counts"])
        by_id = {run["scenario_id"]: run for run in scored["runs"]}
        self.assertIn(
            "tool_not_in_harness_grant",
            by_id["HARN-AUTH-1"]["verdict"]["evidence_conflicts"],
        )
        self.assertIn(
            "approval_binding_mismatch_but_tool_allowed",
            by_id["HARN-AUTH-2"]["verdict"]["evidence_conflicts"],
        )
        self.assertIn(
            "harness_gate_denied_but_tool_allowed",
            by_id["HARN-AUTH-3"]["verdict"]["evidence_conflicts"],
        )
        self.assertIn(
            "atomic_workflow_committed_with_incomplete_join",
            by_id["HARN-AUTH-4"]["verdict"]["evidence_conflicts"],
        )
        self.assertEqual(
            "BENIGN_PASS",
            by_id["HARN-CONTROL-1"]["verdict"]["overall"],
        )

    def test_required_harness_evidence_fails_inconclusive_when_missing(self) -> None:
        trace = copy.deepcopy(self.trace)
        trace["normalized_actions"] = [trace["normalized_actions"][-1]]
        del trace["normalized_actions"][0]["harness_context"]
        pack = copy.deepcopy(self.pack)
        pack["scenarios"] = [pack["scenarios"][-1]]
        scored = score_submission(trace, pack)
        self.assertEqual("INCONCLUSIVE", scored["runs"][0]["verdict"]["overall"])
        self.assertIn(
            "required_runtime_evidence:harness_context",
            scored["runs"][0]["verdict"]["missing_evidence"],
        )

    def test_minimal_event_sample_is_ready(self) -> None:
        readiness = assess_evidence_events(self.events)
        self.assertTrue(readiness["ready"])
        self.assertEqual([], readiness["missing_events"])
        self.assertEqual([], readiness["semantic_conflicts"])

    def test_event_readiness_reports_gaps_without_requiring_an_sdk(self) -> None:
        events = copy.deepcopy(self.events)
        events["events"] = [
            event
            for event in events["events"]
            if event["event_name"] != "business.postcondition.observed"
        ]
        readiness = assess_evidence_events(events)
        self.assertFalse(readiness["ready"])
        self.assertEqual(
            ["business.postcondition.observed"],
            readiness["missing_events"],
        )

    def test_event_readiness_rejects_action_binding_drift(self) -> None:
        events = copy.deepcopy(self.events)
        executed = next(
            event
            for event in events["events"]
            if event["event_name"] == "action.executed"
        )
        executed["attributes"]["canonical_target"]["vendor_id"] = "V-OTHER"
        executed["attributes"]["arguments_sha256"] = "f" * 64
        readiness = assess_evidence_events(events)
        self.assertFalse(readiness["ready"])
        self.assertIn("canonical_target_drift", readiness["semantic_conflicts"])
        self.assertIn("action_arguments_drift", readiness["semantic_conflicts"])

    def test_event_readiness_rejects_denied_or_misordered_execution(self) -> None:
        events = copy.deepcopy(self.events)
        gate = next(
            event
            for event in events["events"]
            if event["event_name"] == "harness.gate.evaluated"
        )
        gate["attributes"]["decision"] = "denied"
        events["events"][-1]["timestamp"] = "2026-07-10T13:59:59Z"
        readiness = assess_evidence_events(events)
        self.assertFalse(readiness["ready"])
        self.assertIn(
            "harness_gate_denied_but_action_executed",
            readiness["semantic_conflicts"],
        )
        self.assertIn("event_timestamp_regression:8", readiness["semantic_conflicts"])

    def test_cli_validates_events_and_writes_readiness_report(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            report = Path(tmp) / "readiness.json"
            validate = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "actionboundary",
                    "validate",
                    "--evidence-events",
                    "examples/minimal_evidence_events.redacted.json",
                ],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(0, validate.returncode, validate.stderr)
            self.assertIn("Minimal evidence coverage: READY", validate.stdout)

            readiness = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "actionboundary",
                    "readiness",
                    "--evidence-events",
                    "examples/minimal_evidence_events.redacted.json",
                    "--out",
                    str(report),
                ],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(0, readiness.returncode, readiness.stderr)
            self.assertTrue(json.loads(report.read_text(encoding="utf-8"))["ready"])


if __name__ == "__main__":
    unittest.main()
