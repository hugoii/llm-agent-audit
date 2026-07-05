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
            "evidence_manifest.schema.json",
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
            self.assertEqual("pilot-verdict-1.1", scored["policy_version"])
            self.assertRegex(scored["trace_sha256"], r"^[0-9a-f]{64}$")
            self.assertRegex(scored["scenario_pack_sha256"], r"^[0-9a-f]{64}$")
            self.assertEqual(scored["trace_sha256"], scored["provenance"]["trace_sha256"])

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

    def test_score_writes_machine_verifiable_evidence_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            verdict = Path(tmp) / "verdict.json"
            markdown = Path(tmp) / "verdict.md"
            evidence_manifest = Path(tmp) / "evidence-manifest.json"
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
                    str(verdict),
                    "--markdown",
                    str(markdown),
                    "--evidence-manifest",
                    str(evidence_manifest),
                ],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(0, score.returncode, score.stderr)
            self.assertIn(f"Evidence manifest: {evidence_manifest}", score.stdout)

            manifest = json.loads(evidence_manifest.read_text(encoding="utf-8"))
            self.assertEqual("evidence-manifest-1.0", manifest["schema_version"])
            self.assertTrue(manifest["integrity"]["complete"])
            self.assertTrue(manifest["evidence_completeness"]["all_runs_complete"])
            self.assertEqual(
                {"markdown_report", "scenario_pack", "trace", "verdict"},
                set(manifest["artifacts"]),
            )

            validate = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "actionboundary",
                    "validate",
                    "--evidence-manifest",
                    str(evidence_manifest),
                ],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(0, validate.returncode, validate.stderr)
            self.assertIn("ActionBoundary evidence-manifest checks: OK", validate.stdout)

    def test_validate_rejects_scenario_pack_hash_mismatch(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            bad_trace = Path(tmp) / "bad-trace.json"
            trace = json.loads((ROOT / "examples/ap_payment_trace.redacted.json").read_text(encoding="utf-8"))
            trace["scenario_pack_sha256"] = "0" * 64
            bad_trace.write_text(json.dumps(trace), encoding="utf-8")

            result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "actionboundary",
                    "validate",
                    "--trace",
                    str(bad_trace),
                    "--scenario-pack",
                    "examples/ap_payment_scenario_pack.json",
                ],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertNotEqual(0, result.returncode)
            self.assertIn("scenario_pack_sha256 mismatch", result.stderr)

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
