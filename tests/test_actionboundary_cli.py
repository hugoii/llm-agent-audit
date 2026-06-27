from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]


class ActionBoundaryCliTests(unittest.TestCase):
    def test_engineering_contract_files_exist(self) -> None:
        for relative in (
            "normalized_trace.schema.json",
            "scenario_pack.schema.json",
            "verdict.schema.json",
            "examples/ap_payment_trace.redacted.json",
            "examples/ap_payment_scenario_pack.json",
            "Makefile",
            "pyproject.toml",
        ):
            self.assertTrue((ROOT / relative).is_file(), relative)

    def test_validate_example_trace(self) -> None:
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "actionboundary",
                "validate",
                "--trace",
                "examples/ap_payment_trace.redacted.json",
                "--scenario-pack",
                "examples/ap_payment_scenario_pack.json",
            ],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertIn("JSON Schema: OK", result.stdout)
        self.assertIn("ActionBoundary scoreability: OK", result.stdout)

    def test_score_example_trace(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "verdict.json"
            result = subprocess.run(
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
                    str(out),
                ],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(0, result.returncode, result.stderr)
            self.assertIn("Scored runs: 2", result.stdout)
            self.assertIn("EXPLOITED: 0", result.stdout)
            self.assertIn("BLOCKED: 1", result.stdout)
            self.assertIn("BENIGN_PASS: 1", result.stdout)
            self.assertIn("INCONCLUSIVE: 0", result.stdout)
            self.assertIn(f"Report: {out}", result.stdout)
            scored = json.loads(out.read_text(encoding="utf-8"))
            self.assertEqual({"BENIGN_PASS": 1, "BLOCKED": 1}, scored["counts"])
            self.assertEqual("pilot-verdict-1.1", scored["schema_version"])

    def test_score_accepts_positional_trace_path(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "verdict.json"
            result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "actionboundary",
                    "score",
                    "examples/ap_payment_trace.redacted.json",
                    "--scenario-pack",
                    "examples/ap_payment_scenario_pack.json",
                    "--out",
                    str(out),
                ],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(0, result.returncode, result.stderr)
            self.assertTrue(out.is_file())

    def test_validate_manifest_backed_l3_l5_trace(self) -> None:
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "actionboundary",
                "validate",
                "--trace",
                "pilot/ap_l3_l5_control_experiment_traces.json",
                "--scenario-pack",
                "pilot/ap_l3_l5_control_experiment_manifest.json",
            ],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertIn("EXPLOITED=3", result.stdout)
        self.assertIn("INCONCLUSIVE=2", result.stdout)


if __name__ == "__main__":
    unittest.main()
