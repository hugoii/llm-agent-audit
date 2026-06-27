from __future__ import annotations

import json
from pathlib import Path
import unittest

from actionboundary.authorization_score import score_submission


ROOT = Path(__file__).resolve().parents[1]


class ApBenignControlLibraryTests(unittest.TestCase):
    def test_ap_payment_manifest_has_substantial_benign_control_library(self) -> None:
        manifest = json.loads((ROOT / "pilot" / "ap_payment_boundary_manifest.json").read_text(encoding="utf-8"))
        scenarios = manifest["scenarios"]
        scenario_ids = [scenario["scenario_id"] for scenario in scenarios]
        benign = [scenario for scenario in scenarios if scenario.get("scenario_type") == "benign_control"]
        titles = " | ".join(scenario["title"].lower() for scenario in benign)

        self.assertEqual(len(scenario_ids), len(set(scenario_ids)))
        self.assertGreaterEqual(len(benign), 12)
        for phrase in (
            "fully authorized normal payment",
            "bank-account change",
            "approved scope",
            "tenant and legal entity",
            "read-only invoice status",
            "duplicate invoice",
            "vendor email reply",
            "existing scheduled payment",
        ):
            self.assertIn(phrase, titles)
        for scenario in benign:
            self.assertEqual("ALLOW", scenario.get("expected_authorization"))
            self.assertTrue(scenario.get("allowed_terminal_states"))
            self.assertTrue(scenario.get("required_runtime_evidence"))

    def test_engineering_example_scores_attack_and_benign_control(self) -> None:
        trace = json.loads((ROOT / "examples" / "ap_payment_trace.redacted.json").read_text(encoding="utf-8"))
        manifest = json.loads((ROOT / "examples" / "ap_payment_scenario_pack.json").read_text(encoding="utf-8"))

        for run in trace["runs"]:
            self.assertIn("observed_actor", run["runtime_evidence"])
            self.assertNotIn("observed_principal", run["runtime_evidence"])

        scored = score_submission(trace, manifest)

        self.assertEqual({"BENIGN_PASS": 1, "BLOCKED": 1}, scored["counts"])

    def test_homepage_surfaces_benign_control_near_ap_finding(self) -> None:
        index = (ROOT / "docs" / "index.html").read_text(encoding="utf-8")

        self.assertIn("Normal AP automation still passes", index)
        self.assertIn("authorized AP operator + matching approval + unchanged vendor-master account", index)
        self.assertIn("pilot/ap_benign_controls.md", index)


if __name__ == "__main__":
    unittest.main()
