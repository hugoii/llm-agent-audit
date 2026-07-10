"""Fresh-score every declared public snapshot and reject published verdict drift."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from actionboundary.authorization_score import markdown_summary, score_submission
from actionboundary.cli import (
    json_schema_errors,
    validate_scenario_pack,
    validate_trace_integrity,
    validate_trace_submission,
    validate_verdict,
)
from actionboundary.contracts import CONTRACT_SET_VERSION
from actionboundary.provenance import scenario_pack_sha256, trace_submission_sha256


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REGISTRY = ROOT / "public_snapshot_suites.json"


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path}: top-level JSON value must be an object")
    return value


def validate_registry(value: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if value.get("schema_version") != "public-snapshot-suites-1.0":
        errors.append("registry schema_version must be public-snapshot-suites-1.0")
    if value.get("contract_set_version") != CONTRACT_SET_VERSION:
        errors.append(f"registry contract_set_version must be {CONTRACT_SET_VERSION}")
    suites = value.get("suites")
    if not isinstance(suites, list) or not suites:
        errors.append("registry suites[] must contain at least one suite")
        return errors
    seen: set[str] = set()
    declared_submissions: set[Path] = set()
    for index, suite in enumerate(suites, start=1):
        if not isinstance(suite, dict):
            errors.append(f"suites[{index}] must be an object")
            continue
        for field in (
            "suite_id",
            "snapshot_dir",
            "scenario_pack",
            "submission_glob",
            "verdict_prefix",
        ):
            if not suite.get(field):
                errors.append(f"suites[{index}].{field} is required")
        suite_id = str(suite.get("suite_id") or "")
        if suite_id in seen:
            errors.append(f"duplicate suite_id: {suite_id}")
        seen.add(suite_id)
        snapshot_dir = (ROOT / str(suite.get("snapshot_dir") or "")).resolve()
        try:
            snapshot_dir.relative_to(ROOT)
        except ValueError:
            errors.append(f"suite {suite_id}: snapshot_dir must stay inside the repository")
            continue
        for submission in snapshot_dir.glob(str(suite.get("submission_glob") or "")):
            resolved = submission.resolve()
            if resolved in declared_submissions:
                errors.append(
                    f"public snapshot submission is covered by more than one suite: "
                    f"{submission.relative_to(ROOT).as_posix()}"
                )
            declared_submissions.add(resolved)

    public_submissions = {
        path.resolve()
        for path in ROOT.glob("pilot/**/snapshots/**/submission_*.json")
    }
    for submission in sorted(public_submissions - declared_submissions):
        errors.append(
            "unregistered public snapshot submission: "
            + submission.relative_to(ROOT).as_posix()
        )
    return errors


def rescore(
    registry_path: Path,
    output_dir: Path,
    *,
    update_markdown: bool = False,
) -> dict[str, Any]:
    registry = load_json(registry_path)
    registry_errors = validate_registry(registry)
    if registry_errors:
        raise ValueError("; ".join(registry_errors))

    output_dir.mkdir(parents=True, exist_ok=True)
    results: list[dict[str, Any]] = []
    drifted: list[str] = []

    for suite in registry["suites"]:
        suite_id = str(suite["suite_id"])
        snapshot_dir = ROOT / str(suite["snapshot_dir"])
        pack_path = ROOT / str(suite["scenario_pack"])
        scenario_pack = load_json(pack_path)
        pack_errors = json_schema_errors(scenario_pack, "scenario-pack")
        pack_errors.extend(validate_scenario_pack(scenario_pack))
        if pack_errors:
            raise ValueError(f"{suite_id}: invalid scenario pack: {'; '.join(pack_errors)}")

        submissions = sorted(snapshot_dir.glob(str(suite["submission_glob"])))
        if not submissions:
            raise ValueError(f"{suite_id}: no public snapshot submissions matched")

        suite_output = output_dir / suite_id
        suite_output.mkdir(parents=True, exist_ok=True)
        for trace_path in submissions:
            trace = load_json(trace_path)
            trace_errors = json_schema_errors(trace, "trace")
            trace_errors.extend(validate_trace_submission(trace, scenario_pack))
            trace_errors.extend(validate_trace_integrity(trace, scenario_pack))
            if trace_errors:
                raise ValueError(f"{trace_path}: invalid trace: {'; '.join(trace_errors)}")

            trace_hash = trace_submission_sha256(trace)
            pack_hash = scenario_pack_sha256(scenario_pack)
            scored = score_submission(
                trace,
                scenario_pack,
                trace_sha256=trace_hash,
                scenario_pack_sha256=pack_hash,
            )
            verdict_errors = json_schema_errors(scored, "verdict")
            verdict_errors.extend(validate_verdict(scored))
            if verdict_errors:
                raise ValueError(f"{trace_path}: invalid rescored verdict: {'; '.join(verdict_errors)}")

            suffix = trace_path.stem.removeprefix("submission_")
            verdict_name = f"{suite['verdict_prefix']}{suffix}.md"
            committed_markdown_path = snapshot_dir / verdict_name
            generated_markdown = markdown_summary(scored)
            if update_markdown:
                committed_markdown_path.write_text(generated_markdown, encoding="utf-8")
            elif not committed_markdown_path.is_file():
                drifted.append(f"missing {committed_markdown_path.relative_to(ROOT).as_posix()}")
            elif committed_markdown_path.read_text(encoding="utf-8") != generated_markdown:
                drifted.append(committed_markdown_path.relative_to(ROOT).as_posix())

            (suite_output / f"verdict_{suffix}.json").write_text(
                json.dumps(scored, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )
            (suite_output / verdict_name).write_text(generated_markdown, encoding="utf-8")
            results.append(
                {
                    "suite_id": suite_id,
                    "submission": trace_path.relative_to(ROOT).as_posix(),
                    "scenario_pack": pack_path.relative_to(ROOT).as_posix(),
                    "trace_sha256": trace_hash,
                    "scenario_pack_sha256": pack_hash,
                    "counts": scored["counts"],
                    "scenario_coverage": scored["scenario_coverage"],
                }
            )

    if drifted:
        raise ValueError(
            "public snapshot Markdown drift detected: "
            + ", ".join(drifted)
            + "; run with --update-markdown and review the evidence change"
        )

    summary = {
        "schema_version": "public-snapshot-rescore-1.0",
        "contract_set_version": CONTRACT_SET_VERSION,
        "registry": registry_path.relative_to(ROOT).as_posix(),
        "snapshot_count": len(results),
        "results": results,
    }
    (output_dir / "public-snapshot-rescore-summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return summary


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--registry", default=str(DEFAULT_REGISTRY))
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--update-markdown", action="store_true")
    args = parser.parse_args()

    summary = rescore(
        Path(args.registry).resolve(),
        Path(args.output_dir).resolve(),
        update_markdown=args.update_markdown,
    )
    print(f"Fresh rescored public snapshots: {summary['snapshot_count']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
