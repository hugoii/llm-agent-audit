from __future__ import annotations

import re
from pathlib import Path
import tomllib
import unittest


ROOT = Path(__file__).resolve().parents[1]


class SourceReadabilityTests(unittest.TestCase):
    def test_dev_extra_defines_real_developer_tooling(self) -> None:
        """Keep the README quickstart extra from becoming an empty promise."""

        pyproject = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
        dev = set(pyproject["project"]["optional-dependencies"]["dev"])

        expected = {
            "black>=24",
            "pytest>=8",
            "ruff>=0.8",
            "pypdf>=4.3",
            "reportlab>=4.2",
        }

        self.assertLessEqual(expected, dev)

    def test_public_engineering_files_are_not_minified(self) -> None:
        """Keep public contract/tooling files readable in GitHub raw and diffs."""

        expectations = {
            "Makefile": 8,
            "pyproject.toml": 10,
            "normalized_trace.schema.json": 40,
            "scenario_pack.schema.json": 30,
            "verdict.schema.json": 30,
            "actionboundary/authorization_score.py": 200,
            "actionboundary/cli.py": 100,
            "actionboundary/report.py": 50,
            "scripts/render_sample_report.py": 200,
        }

        offenders: list[str] = []
        for relative, minimum_lines in expectations.items():
            path = ROOT / relative
            lines = path.read_text(encoding="utf-8").splitlines()
            if len(lines) < minimum_lines:
                offenders.append(f"{relative}: only {len(lines)} lines")
            for line_number, line in enumerate(lines, start=1):
                if len(line) > 140:
                    offenders.append(f"{relative}:{line_number} has {len(line)} chars")

        self.assertEqual([], offenders)

    def test_public_html_text_extracts_without_joined_words(self) -> None:
        """Screen readers, snippets, and copy-paste should not see glued labels."""

        offenders: list[str] = []
        joined_patterns = [
            r"Product and buyerWhat",
            r"One workflow or action surfaceTell",
            r"Safe test pathAny",
            r"Scenario fitActionBoundary",
            r"Existing traceOne",
            r"Pilot or evidence planIf",
            r"frontierbudget",
            r"Request sourceVendor",
            r"Authorization sourceNo trusted record",
            r"No trusted recordcontent",
            r"Request sourceApproval",
            r"User \+ tenant matchpermission",
            r"4 blocked1 no attempt",
            r"Claude Opus 4\.80\.0 avg",
            r"GPT-5\.5OpenAI API",
            r"Invoice approved\?Good",
            r"Current actor authorized[^?]*\?Separate",
            r"Vendor-bank destination verified\?Separate",
            r"Final side effect blocked or committed\?Separate",
            r"Canitmovemoney",
            r"principal\?User",
            r"source\?Approval",
            r"Expected evidenceThe",
            r"Expected evidenceEmail",
            r"Expected evidenceThe product",
            r"\b1Who was",
            r"\b2What approval",
            r"\b3Which vendor",
            r"\b4What side effect",
        ]

        for relative in ("docs/index.html", "docs/payment-authorization-review.html"):
            html = (ROOT / relative).read_text(encoding="utf-8")
            text = re.sub(r"<[^>]+>", "", html)
            text = re.sub(r"\s+", " ", text)
            for pattern in joined_patterns:
                if re.search(pattern, text):
                    offenders.append(f"{relative}: {pattern}")

        self.assertEqual([], offenders)

    def test_ap_page_aligns_actor_language_with_public_schema(self) -> None:
        html = (ROOT / "docs" / "payment-authorization-review.html").read_text(
            encoding="utf-8"
        )

        self.assertIn("Observed actor / principal", html)
        self.assertNotIn("Observed principal and service account", html)
        self.assertNotIn("Actor / principal / service account", html)

    def test_ap_page_uses_canonical_terminal_state_language(self) -> None:
        html = (ROOT / "docs" / "payment-authorization-review.html").read_text(
            encoding="utf-8"
        )

        expected_states = [
            "committed",
            "not_committed",
            "routed_to_review",
            "routed_to_reapproval",
            "duplicate_denied",
            "existing_result_returned",
            "unknown",
        ]

        for state in expected_states:
            self.assertIn(state, html)

        self.assertNotIn("Blocked, drafted, scheduled, or committed.", html)
        self.assertNotIn(
            "Drafted, denied, scheduled, reversed, committed, or inconclusive",
            html,
        )

    def test_public_markdown_entrypoints_are_readable_in_raw_view(self) -> None:
        """Keep buyer/reviewer-facing markdown from becoming one-line walls."""

        expectations = {
            "README.md": 200,
            "SECURITY.md": 40,
            "CONTRIBUTING.md": 20,
            "docs/sample-pilot-report-v0.8.md": 200,
        }

        offenders: list[str] = []
        for relative, minimum_lines in expectations.items():
            path = ROOT / relative
            lines = path.read_text(encoding="utf-8").splitlines()
            if len(lines) < minimum_lines:
                offenders.append(f"{relative}: only {len(lines)} lines")
            for line_number, line in enumerate(lines, start=1):
                if len(line) > 180:
                    offenders.append(f"{relative}:{line_number} has {len(line)} chars")

        self.assertEqual([], offenders)


if __name__ == "__main__":
    unittest.main()
