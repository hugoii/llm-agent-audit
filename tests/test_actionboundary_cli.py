from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import zipfile

from jsonschema import Draft202012Validator


ROOT = Path(__file__).resolve().parents[1]


class ActionBoundaryCliTests(unittest.TestCase):
    def test_engineering_contract_files_exist(self) -> None:
        for relative in (
            "normalized_trace.schema.json",
            "scenario_pack.schema.json",
            "verdict.schema.json",
            "evidence_manifest.schema.json",
            "public_evidence_bundle.schema.json",
            ".github/workflows/public-evidence-bundle.yml",
            "VERIFY-EVIDENCE.md",
            "examples/ap_payment_trace.redacted.json",
            "examples/ap_payment_scenario_pack.json",
            "pilot/customer_execution_attestation.schema.json",
            "pilot/customer_execution_attestation.sample.json",
            "scripts/build_public_evidence_bundle.py",
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
            self.assertEqual("pilot-verdict-1.2", scored["schema_version"])
            self.assertEqual("pilot-verdict-1.2", scored["policy_version"])
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
            pdf = Path(tmp) / "verdict.pdf"
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
                    "--pdf",
                    str(pdf),
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
            self.assertEqual("evidence-manifest-1.1", manifest["schema_version"])
            self.assertTrue(manifest["integrity"]["complete"])
            checks = {item["name"]: item["status"] for item in manifest["integrity"]["checks"]}
            self.assertEqual(
                "PASS",
                checks["verdict_semantically_matches_trace_and_scenario_pack"],
            )
            self.assertTrue(manifest["evidence_completeness"]["all_runs_complete"])
            self.assertEqual(
                {"markdown_report", "pdf_report", "scenario_pack", "trace", "verdict"},
                set(manifest["artifacts"]),
            )
            self.assertTrue(pdf.read_bytes().startswith(b"%PDF"))

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

    def test_public_evidence_bundle_builder_outputs_verifiable_bundle(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_dir = Path(tmp)
            generated_dir = tmp_dir / "public-evidence"
            bundle_dir = tmp_dir / "bundle"
            zip_path = tmp_dir / "actionboundary-public-evidence-bundle.zip"
            generated_dir.mkdir()

            score = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "actionboundary",
                    "score",
                    "examples/ap_payment_trace.redacted.json",
                    "--scenario-pack",
                    "examples/ap_payment_scenario_pack.json",
                    "--out",
                    str(generated_dir / "actionboundary-scored-example.json"),
                    "--markdown",
                    str(generated_dir / "actionboundary-scored-example.md"),
                    "--pdf",
                    str(generated_dir / "actionboundary-scored-example.pdf"),
                    "--evidence-manifest",
                    str(generated_dir / "actionboundary-evidence-manifest.json"),
                ],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(0, score.returncode, score.stderr)

            rescore = subprocess.run(
                [
                    sys.executable,
                    "scripts/rescore_public_snapshots.py",
                    "--output-dir",
                    str(generated_dir),
                ],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(0, rescore.returncode, rescore.stderr)

            build = subprocess.run(
                [
                    sys.executable,
                    "scripts/build_public_evidence_bundle.py",
                    "--generated-dir",
                    str(generated_dir),
                    "--output-dir",
                    str(bundle_dir),
                    "--zip",
                    str(zip_path),
                    "--git-sha",
                    "test-sha",
                    "--github-repository",
                    "hugoii/llm-agent-audit",
                    "--github-ref",
                    "refs/heads/master",
                    "--github-workflow",
                    "Public evidence bundle",
                    "--github-run-id",
                    "12345",
                    "--github-run-attempt",
                    "1",
                ],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(0, build.returncode, build.stderr)
            self.assertTrue(zip_path.is_file())
            self.assertTrue((bundle_dir / "SHA256SUMS").is_file())
            self.assertTrue((bundle_dir / "PUBLIC-EVIDENCE-BUNDLE.json").is_file())
            self.assertTrue((bundle_dir / "tmp/public-evidence/actionboundary-evidence-manifest.json").is_file())
            self.assertTrue((bundle_dir / "tmp/public-evidence/public-snapshot-rescore-summary.json").is_file())
            self.assertTrue(
                (
                    bundle_dir
                    / "pilot/stripe_customer_support/out/snapshots/2026-07-04-stripe-l3-coupon/submission_haiku_STRIPE-AUTH-5.json"
                ).is_file()
            )
            self.assertTrue((bundle_dir / "VERIFY-EVIDENCE.md").is_file())

            portable_manifest = json.loads(
                (
                    bundle_dir
                    / "tmp/public-evidence/actionboundary-evidence-manifest.json"
                ).read_text(encoding="utf-8")
            )
            for kind in ("verdict", "markdown_report", "pdf_report"):
                self.assertTrue(
                    portable_manifest["artifacts"][kind]["path"].startswith(
                        "tmp/public-evidence/"
                    )
                )

            bundle_manifest = json.loads((bundle_dir / "PUBLIC-EVIDENCE-BUNDLE.json").read_text(encoding="utf-8"))
            bundle_schema = json.loads((ROOT / "public_evidence_bundle.schema.json").read_text(encoding="utf-8"))
            bundle_errors = sorted(
                Draft202012Validator(bundle_schema).iter_errors(bundle_manifest),
                key=lambda item: tuple(item.absolute_path),
            )
            self.assertEqual([], [error.message for error in bundle_errors])
            self.assertEqual("public-evidence-bundle-1.1", bundle_manifest["schema_version"])
            self.assertEqual(
                "actionboundary-contract-set-1.0",
                bundle_manifest["contract_set_version"],
            )
            self.assertEqual("test-sha", bundle_manifest["git_sha"])
            self.assertEqual(
                "tmp/public-evidence/actionboundary-evidence-manifest.json",
                bundle_manifest["evidence_manifest_path"],
            )
            self.assertEqual(
                "tmp/public-evidence/public-snapshot-rescore-summary.json",
                bundle_manifest["snapshot_rescore_summary_path"],
            )
            self.assertEqual("12345", bundle_manifest["ci"]["run_id"])

            with zipfile.ZipFile(zip_path) as archive:
                names = set(archive.namelist())
            self.assertIn("SHA256SUMS", names)
            self.assertIn("PUBLIC-EVIDENCE-BUNDLE.json", names)
            self.assertIn("tmp/public-evidence/actionboundary-evidence-manifest.json", names)

            generated_dir.rename(tmp_dir / "source-artifacts-not-available")

            validate = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "actionboundary",
                    "validate",
                    "--evidence-root",
                    str(bundle_dir),
                    "--evidence-manifest",
                    str(bundle_dir / "tmp/public-evidence/actionboundary-evidence-manifest.json"),
                ],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(0, validate.returncode, validate.stderr)
            self.assertIn("ActionBoundary evidence-manifest checks: OK", validate.stdout)

    def test_customer_execution_attestation_sample_matches_schema(self) -> None:
        schema = json.loads((ROOT / "pilot/customer_execution_attestation.schema.json").read_text(encoding="utf-8"))
        sample = json.loads((ROOT / "pilot/customer_execution_attestation.sample.json").read_text(encoding="utf-8"))
        errors = sorted(
            Draft202012Validator(schema).iter_errors(sample),
            key=lambda item: tuple(item.absolute_path),
        )
        self.assertEqual([], [error.message for error in errors])

    def test_customer_executed_manifest_binds_attestation(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            verdict = Path(tmp) / "verdict.json"
            evidence_manifest = Path(tmp) / "evidence-manifest.json"
            result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "actionboundary",
                    "score",
                    "--trace",
                    "pilot/sample_flexible_client_trace.json",
                    "--scenario-pack",
                    "pilot/ap_payment_boundary_manifest.json",
                    "--out",
                    str(verdict),
                    "--evidence-manifest",
                    str(evidence_manifest),
                    "--execution-profile",
                    "customer_executed",
                    "--customer-execution-attestation",
                    "pilot/customer_execution_attestation.sample.json",
                ],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(0, result.returncode, result.stderr)
            manifest = json.loads(evidence_manifest.read_text(encoding="utf-8"))
            self.assertEqual("customer_executed", manifest["execution_profile"])
            self.assertIn("customer_execution_attestation", manifest["artifacts"])
            checks = {item["name"]: item["status"] for item in manifest["integrity"]["checks"]}
            self.assertEqual("PASS", checks["customer_attestation_trace_hash_matches"])
            self.assertEqual("PASS", checks["customer_attestation_scenario_pack_hash_matches"])

    def test_customer_executed_manifest_rejects_mismatched_attestation(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            attestation_path = Path(tmp) / "attestation.json"
            attestation = json.loads(
                (ROOT / "pilot/customer_execution_attestation.sample.json").read_text(
                    encoding="utf-8"
                )
            )
            attestation["trace_sha256"] = "0" * 64
            attestation_path.write_text(json.dumps(attestation), encoding="utf-8")
            result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "actionboundary",
                    "score",
                    "--trace",
                    "pilot/sample_flexible_client_trace.json",
                    "--scenario-pack",
                    "pilot/ap_payment_boundary_manifest.json",
                    "--out",
                    str(Path(tmp) / "verdict.json"),
                    "--evidence-manifest",
                    str(Path(tmp) / "evidence-manifest.json"),
                    "--execution-profile",
                    "customer_executed",
                    "--customer-execution-attestation",
                    str(attestation_path),
                ],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertNotEqual(0, result.returncode)
            self.assertIn("customer_attestation_trace_hash_matches", result.stderr)

    def test_public_snapshots_fresh_rescore_without_markdown_drift(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            result = subprocess.run(
                [
                    sys.executable,
                    "scripts/rescore_public_snapshots.py",
                    "--output-dir",
                    tmp,
                ],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(0, result.returncode, result.stderr)
            summary = json.loads(
                (Path(tmp) / "public-snapshot-rescore-summary.json").read_text(
                    encoding="utf-8"
                )
            )
            self.assertEqual(9, summary["snapshot_count"])
            registered = {item["submission"] for item in summary["results"]}
            discovered = {
                path.relative_to(ROOT).as_posix()
                for path in ROOT.glob(
                    "pilot/**/snapshots/**/submission_*.json"
                )
            }
            self.assertEqual(discovered, registered)

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
