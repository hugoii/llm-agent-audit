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
        self.assertIn("OK: trace is scoreable", result.stdout)

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
            scored = json.loads(out.read_text(encoding="utf-8"))
            self.assertEqual({"BENIGN_PASS": 1, "BLOCKED": 1}, scored["counts"])
            self.assertEqual("pilot-verdict-1.1", scored["schema_version"])


if __name__ == "__main__":
    unittest.main()
