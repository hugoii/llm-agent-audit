"""Small CLI for validating and scoring ActionBoundary trace artifacts."""

from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path
import sys
from typing import Any

from jsonschema import Draft202012Validator
from jsonschema.exceptions import SchemaError

from .contracts import (
    CANONICAL_SCHEMA_FILES,
    CUSTOMER_EXECUTED_PROFILE,
    EXECUTION_PROFILES,
    REPOSITORY_SYNTHETIC_PROFILE,
    VERDICT_SCHEMA_VERSION,
)
from .authorization_score import (
    apply_manifest_defaults,
    has_trace,
    manifest_oracle_conflicts,
    manifest_scenarios,
    markdown_summary,
    score_submission,
    validate_verdict_matches_recomputed,
)
from .provenance import (
    build_evidence_manifest,
    iter_declared_trace_hashes,
    is_sha256,
    scenario_pack_sha256 as compute_scenario_pack_sha256,
    trace_submission_sha256,
    validate_evidence_manifest,
)
from .readiness import assess_evidence_events
from .report_pdf import render_verdict_pdf


FINAL_STATUSES = {
    "EXPLOITED",
    "BLOCKED",
    "BENIGN_PASS",
    "BENIGN_REGRESSION",
    "INCONCLUSIVE",
    "INFRASTRUCTURE_ERROR",
    "NOT_TESTED",
}

SUMMARY_STATUSES = (
    "EXPLOITED",
    "BLOCKED",
    "BENIGN_PASS",
    "BENIGN_REGRESSION",
    "INCONCLUSIVE",
)

SCHEMA_FILES = {
    "trace": CANONICAL_SCHEMA_FILES["trace"],
    "evidence-events": CANONICAL_SCHEMA_FILES["evidence_events"],
    "scenario-pack": CANONICAL_SCHEMA_FILES["scenario_pack"],
    "verdict": CANONICAL_SCHEMA_FILES["verdict"],
    "evidence-manifest": CANONICAL_SCHEMA_FILES["evidence_manifest"],
}


def load_json(path: str | Path) -> dict[str, Any]:
    source = Path(path)
    try:
        value = json.loads(source.read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise ValueError(f"{source}: file not found") from None
    except json.JSONDecodeError as exc:
        raise ValueError(f"{source}: invalid JSON at line {exc.lineno}, column {exc.colno}: {exc.msg}") from None
    if not isinstance(value, dict):
        raise ValueError(f"{source}: top-level JSON value must be an object")
    return value


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def schema_path(name: str) -> Path:
    return repo_root() / SCHEMA_FILES[name]


def json_path(parts: tuple[Any, ...]) -> str:
    if not parts:
        return "$"
    out = "$"
    for part in parts:
        out += f"[{part}]" if isinstance(part, int) else f".{part}"
    return out


def json_schema_errors(value: dict[str, Any], name: str) -> list[str]:
    schema = load_json(schema_path(name))
    try:
        Draft202012Validator.check_schema(schema)
    except SchemaError as exc:
        return [f"{name} schema is invalid: {exc.message}"]
    validator = Draft202012Validator(schema)
    return [
        f"{name} {json_path(tuple(error.absolute_path))}: {error.message}"
        for error in sorted(validator.iter_errors(value), key=lambda item: tuple(item.absolute_path))
    ]


def validate_trace_submission(trace: dict[str, Any], manifest: dict[str, Any] | None = None) -> list[str]:
    errors: list[str] = []
    runs = trace.get("runs")
    normalized_actions = trace.get("normalized_actions")
    if not isinstance(runs, list) and not isinstance(normalized_actions, list):
        errors.append("trace must contain either runs[] or normalized_actions[]")
        return errors

    if isinstance(runs, list):
        if not runs:
            errors.append("runs must contain at least one run")
        scenario_manifest = manifest_scenarios(manifest)
        for index, run in enumerate(runs, start=1):
            if not isinstance(run, dict):
                errors.append(f"runs[{index}] must be an object")
                continue
            if not run.get("scenario_id"):
                errors.append(f"runs[{index}].scenario_id is required")
            scenario = scenario_manifest.get(str(run.get("scenario_id") or ""))
            if manifest is not None and scenario is None:
                errors.append(
                    f"runs[{index}].scenario_id is not declared by the scenario pack: "
                    f"{run.get('scenario_id')!r}"
                )
            conflicts = manifest_oracle_conflicts(run, scenario)
            if conflicts:
                errors.append(
                    f"runs[{index}] conflicts with authoritative scenario-pack oracle fields: "
                    + ", ".join(conflicts)
                )
            run_with_defaults = apply_manifest_defaults(
                run,
                scenario,
            )
            if not run_with_defaults.get("expected_authorization"):
                errors.append(f"runs[{index}].expected_authorization is required")
            if not has_trace(run_with_defaults):
                errors.append(f"runs[{index}].tool_call_trace is required")
            elif "tool_call_trace" in run_with_defaults and not isinstance(run_with_defaults.get("tool_call_trace"), list):
                errors.append(f"runs[{index}].tool_call_trace must be an array")
            if "runtime_evidence" in run and not isinstance(run.get("runtime_evidence"), dict):
                errors.append(f"runs[{index}].runtime_evidence must be an object when present")

    if isinstance(normalized_actions, list):
        if not normalized_actions:
            errors.append("normalized_actions must contain at least one action")
        for index, action in enumerate(normalized_actions, start=1):
            if not isinstance(action, dict):
                errors.append(f"normalized_actions[{index}] must be an object")
                continue
            for field in ("scenario_id", "action", "authorization", "tool_result", "business_outcome"):
                if field not in action:
                    errors.append(f"normalized_actions[{index}].{field} is required")
    return errors


def validate_scenario_pack(manifest: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if not manifest.get("manifest_version"):
        errors.append("scenario pack manifest_version is required")
    scenarios = manifest.get("scenarios")
    if not isinstance(scenarios, list) or not scenarios:
        errors.append("scenario pack scenarios[] must contain at least one scenario")
        return errors

    seen: set[str] = set()
    for index, scenario in enumerate(scenarios, start=1):
        if not isinstance(scenario, dict):
            errors.append(f"scenarios[{index}] must be an object")
            continue
        scenario_id = str(scenario.get("scenario_id") or "")
        if not scenario_id:
            errors.append(f"scenarios[{index}].scenario_id is required")
        elif scenario_id in seen:
            errors.append(f"duplicate scenario_id: {scenario_id}")
        seen.add(scenario_id)
        for field in ("expected_authorization", "allowed_terminal_states"):
            if field not in scenario:
                errors.append(f"scenarios[{index}].{field} is required")
        if "required_runtime_evidence" not in scenario and "required_runtime_evidence" not in manifest:
            errors.append(
                f"scenarios[{index}].required_runtime_evidence is required when no pack-level default exists"
            )
    return errors


def validate_verdict(scored: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if scored.get("schema_version") != VERDICT_SCHEMA_VERSION:
        errors.append(f"verdict schema_version must be {VERDICT_SCHEMA_VERSION}")
    counts = scored.get("counts")
    if not isinstance(counts, dict):
        errors.append("verdict counts object is required")
    for field in ("scenario_pack_sha256", "trace_sha256"):
        value = scored.get(field)
        if value is not None and (not isinstance(value, str) or not is_sha256(value)):
            errors.append(f"verdict {field} must be a lowercase sha256 hex digest")
    policy_version = scored.get("policy_version")
    if policy_version is not None and policy_version != scored.get("schema_version"):
        errors.append("verdict policy_version must match schema_version")
    runs = scored.get("runs")
    if not isinstance(runs, list):
        errors.append("verdict runs[] is required")
        return errors
    for index, run in enumerate(runs, start=1):
        if not isinstance(run, dict):
            errors.append(f"verdict runs[{index}] must be an object")
            continue
        verdict = run.get("verdict")
        if not isinstance(verdict, dict):
            errors.append(f"verdict runs[{index}].verdict is required")
            continue
        overall = verdict.get("overall")
        if overall not in FINAL_STATUSES:
            errors.append(f"verdict runs[{index}].verdict.overall has unknown status: {overall!r}")
        if verdict.get("system_authorization_boundary") == "PASS" and verdict.get("missing_evidence"):
            errors.append(f"verdict runs[{index}] declares PASS with missing evidence")
    if isinstance(counts, dict):
        expected_counts = dict(sorted(Counter(
            run.get("verdict", {}).get("overall")
            for run in runs
            if isinstance(run, dict) and isinstance(run.get("verdict"), dict)
        ).items()))
        if counts != expected_counts:
            errors.append(
                f"verdict counts mismatch: expected {expected_counts!r}, observed {counts!r}"
            )
    return errors


def validate_trace_integrity(trace: dict[str, Any], manifest: dict[str, Any] | None = None) -> list[str]:
    errors: list[str] = []
    observed_trace_hash = trace_submission_sha256(trace)
    for declared in sorted(set(iter_declared_trace_hashes(trace))):
        if declared != observed_trace_hash:
            errors.append(
                "trace trace_sha256 mismatch: "
                f"expected {observed_trace_hash}, observed {declared}"
            )
    if manifest is not None:
        observed_pack_hash = compute_scenario_pack_sha256(manifest)
        declared_pack_hash = trace.get("scenario_pack_sha256")
        if declared_pack_hash and declared_pack_hash != observed_pack_hash:
            errors.append(
                "trace scenario_pack_sha256 mismatch: "
                f"expected {observed_pack_hash}, observed {declared_pack_hash}"
            )
    return errors


def validate_verdict_integrity(
    verdict: dict[str, Any],
    trace: dict[str, Any] | None = None,
    manifest: dict[str, Any] | None = None,
) -> list[str]:
    errors: list[str] = []
    if trace is not None:
        observed_trace_hash = trace_submission_sha256(trace)
        if verdict.get("trace_sha256") != observed_trace_hash:
            errors.append(
                "verdict trace_sha256 mismatch: "
                f"expected {observed_trace_hash}, observed {verdict.get('trace_sha256')}"
            )
    if manifest is not None:
        observed_pack_hash = compute_scenario_pack_sha256(manifest)
        if verdict.get("scenario_pack_sha256") != observed_pack_hash:
            errors.append(
                "verdict scenario_pack_sha256 mismatch: "
                f"expected {observed_pack_hash}, observed {verdict.get('scenario_pack_sha256')}"
            )
    return errors


def format_errors(errors: list[str]) -> str:
    return "\n".join(f"- {error}" for error in errors)


def write_json(path: str | Path, value: dict[str, Any]) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_text(path: str | Path, value: str) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(value, encoding="utf-8")


def load_manifest(path: str | None) -> dict[str, Any] | None:
    return load_json(path) if path else None


def print_score_summary(scored: dict[str, Any], report_path: str | None, markdown_path: str | None) -> None:
    counts = scored.get("counts") if isinstance(scored.get("counts"), dict) else {}
    runs = scored.get("runs") if isinstance(scored.get("runs"), list) else []
    print(f"Scored runs: {len(runs)}")
    for status in SUMMARY_STATUSES:
        print(f"{status}: {counts.get(status, 0)}")
    coverage = scored.get("scenario_coverage") if isinstance(scored.get("scenario_coverage"), dict) else {}
    print(
        "Scenario coverage: "
        f"{coverage.get('tested_scenarios', 0)}/{coverage.get('total_scenarios', 0)} "
        f"({'complete' if coverage.get('complete') else 'incomplete'})"
    )
    if report_path:
        print(f"Report: {report_path}")
    if markdown_path:
        print(f"Markdown: {markdown_path}")


def cmd_validate(args: argparse.Namespace) -> int:
    errors: list[str] = []
    trace = load_json(args.trace) if args.trace else None
    manifest = load_manifest(args.scenario_pack)
    verdict = load_json(args.verdict) if args.verdict else None
    evidence_manifest = load_json(args.evidence_manifest) if args.evidence_manifest else None
    evidence_events = load_json(args.evidence_events) if args.evidence_events else None

    if (
        trace is None
        and manifest is None
        and verdict is None
        and evidence_manifest is None
        and evidence_events is None
    ):
        errors.append(
            "provide --trace, --scenario-pack, --verdict, --evidence-manifest, or --evidence-events"
        )
    if trace is not None and manifest is None:
        errors.append("trace scoring requires --scenario-pack for an independent authoritative oracle")
    if trace is not None:
        errors.extend(f"JSON Schema: {error}" for error in json_schema_errors(trace, "trace"))
        errors.extend(f"trace: {error}" for error in validate_trace_submission(trace, manifest))
        errors.extend(f"trace integrity: {error}" for error in validate_trace_integrity(trace, manifest))
    if manifest is not None:
        errors.extend(f"JSON Schema: {error}" for error in json_schema_errors(manifest, "scenario-pack"))
        errors.extend(f"scenario-pack: {error}" for error in validate_scenario_pack(manifest))
    if verdict is not None:
        errors.extend(f"JSON Schema: {error}" for error in json_schema_errors(verdict, "verdict"))
        errors.extend(f"verdict: {error}" for error in validate_verdict(verdict))
        errors.extend(
            f"verdict integrity: {error}"
            for error in validate_verdict_integrity(verdict, trace, manifest)
        )
        if trace is None:
            errors.append("verdict semantic validation requires --trace")
        if manifest is None:
            errors.append("verdict semantic validation requires --scenario-pack")
    if evidence_manifest is not None:
        errors.extend(
            f"JSON Schema: {error}"
            for error in json_schema_errors(evidence_manifest, "evidence-manifest")
        )
        evidence_root = Path(args.evidence_root) if args.evidence_root else repo_root()
        errors.extend(
            f"evidence-manifest: {error}"
            for error in validate_evidence_manifest(evidence_manifest, base_dir=evidence_root)
        )
    if evidence_events is not None:
        errors.extend(
            f"JSON Schema: {error}"
            for error in json_schema_errors(evidence_events, "evidence-events")
        )
        readiness = assess_evidence_events(evidence_events)
        errors.extend(
            f"evidence-events: {error}"
            for error in readiness["semantic_conflicts"]
        )

    scored = None
    if not errors and trace is not None:
        scored = score_submission(
            trace,
            manifest,
            trace_sha256=trace_submission_sha256(trace),
            scenario_pack_sha256=compute_scenario_pack_sha256(manifest) if manifest is not None else None,
        )
        errors.extend(f"scored verdict JSON Schema: {error}" for error in json_schema_errors(scored, "verdict"))
        errors.extend(f"scored verdict: {error}" for error in validate_verdict(scored))
        if verdict is not None:
            errors.extend(
                f"verdict semantic: {error}"
                for error in validate_verdict_matches_recomputed(verdict, scored)
            )

    if errors:
        print("Validation failed:", file=sys.stderr)
        print(format_errors(errors), file=sys.stderr)
        return 1

    print("JSON Schema: OK")
    if scored is not None:
        counts = ", ".join(f"{key}={value}" for key, value in sorted(scored.get("counts", {}).items()))
        print(f"ActionBoundary scoreability: OK ({counts or 'no runs'})")
        coverage = scored.get("scenario_coverage") or {}
        print(
            "Scenario coverage: "
            f"{coverage.get('tested_scenarios', 0)}/{coverage.get('total_scenarios', 0)} "
            f"({'complete' if coverage.get('complete') else 'incomplete'})"
        )
    elif manifest is not None and verdict is None:
        print("ActionBoundary scenario-pack checks: OK")
    elif verdict is not None:
        print("ActionBoundary verdict checks: OK")
    elif evidence_manifest is not None:
        print("ActionBoundary evidence-manifest checks: OK")
    elif evidence_events is not None:
        readiness = assess_evidence_events(evidence_events)
        print("ActionBoundary evidence-event checks: OK")
        print(
            "Minimal evidence coverage: "
            + ("READY" if readiness["ready"] else "INCOMPLETE")
        )
        if readiness["missing_events"]:
            print("Missing events: " + ", ".join(readiness["missing_events"]))
    else:
        print("ActionBoundary checks: OK")
    return 0


def cmd_readiness(args: argparse.Namespace) -> int:
    evidence_events = load_json(args.evidence_events)
    errors = json_schema_errors(evidence_events, "evidence-events")
    if errors:
        print("Readiness input failed validation:", file=sys.stderr)
        print(format_errors(errors), file=sys.stderr)
        return 1

    result = assess_evidence_events(evidence_events)
    if args.out:
        write_json(args.out, result)
    else:
        print(json.dumps(result, indent=2, sort_keys=True))
    print("Evidence readiness: " + ("READY" if result["ready"] else "INCOMPLETE"))
    if result["missing_events"]:
        print("Missing events: " + ", ".join(result["missing_events"]))
    if result["semantic_conflicts"]:
        print("Semantic conflicts: " + ", ".join(result["semantic_conflicts"]))
    if args.out:
        print(f"Readiness report: {args.out}")
    return 0


def cmd_score(args: argparse.Namespace) -> int:
    trace_path = args.trace or args.trace_path
    if not trace_path:
        raise ValueError("score requires --trace or TRACE")
    if args.evidence_manifest and not args.out:
        raise ValueError("score --evidence-manifest requires --out so the verdict artifact can be hashed")
    if args.evidence_manifest and not args.scenario_pack:
        raise ValueError("score --evidence-manifest requires --scenario-pack for independent oracle binding")
    if args.execution_profile != REPOSITORY_SYNTHETIC_PROFILE and not args.evidence_manifest:
        raise ValueError("non-synthetic execution profiles require --evidence-manifest")
    if args.customer_execution_attestation and not args.evidence_manifest:
        raise ValueError("--customer-execution-attestation requires --evidence-manifest")
    if args.execution_profile == CUSTOMER_EXECUTED_PROFILE and not args.customer_execution_attestation:
        raise ValueError("customer_executed scoring requires --customer-execution-attestation")
    trace = load_json(trace_path)
    manifest = load_manifest(args.scenario_pack)
    customer_attestation = (
        load_json(args.customer_execution_attestation)
        if args.customer_execution_attestation
        else None
    )
    if manifest is None:
        raise ValueError("score requires --scenario-pack for an independent authoritative oracle")
    errors = [f"JSON Schema: {error}" for error in json_schema_errors(trace, "trace")]
    errors.extend(f"trace: {error}" for error in validate_trace_submission(trace, manifest))
    errors.extend(f"trace integrity: {error}" for error in validate_trace_integrity(trace, manifest))
    if manifest is not None:
        errors.extend(f"JSON Schema: {error}" for error in json_schema_errors(manifest, "scenario-pack"))
        errors.extend(f"scenario-pack: {error}" for error in validate_scenario_pack(manifest))
    if errors:
        print("Validation failed:", file=sys.stderr)
        print(format_errors(errors), file=sys.stderr)
        return 1

    scored = score_submission(
        trace,
        manifest,
        trace_sha256=trace_submission_sha256(trace),
        scenario_pack_sha256=compute_scenario_pack_sha256(manifest) if manifest is not None else None,
    )
    verdict_errors = json_schema_errors(scored, "verdict")
    verdict_errors.extend(validate_verdict(scored))
    if verdict_errors:
        print("Scoring produced an invalid verdict:", file=sys.stderr)
        print(format_errors(verdict_errors), file=sys.stderr)
        return 1

    if args.out:
        write_json(args.out, scored)
    else:
        print(json.dumps(scored, indent=2, sort_keys=True))
    if args.markdown:
        write_text(args.markdown, markdown_summary(scored))
    if args.pdf:
        render_verdict_pdf(scored, args.pdf)
    if args.evidence_manifest:
        evidence_manifest = build_evidence_manifest(
            trace_path=trace_path,
            trace=trace,
            scenario_pack_path=args.scenario_pack,
            scenario_pack=manifest,
            verdict_path=args.out,
            verdict=scored,
            markdown_path=args.markdown,
            pdf_path=args.pdf,
            execution_profile=args.execution_profile,
            customer_execution_attestation_path=args.customer_execution_attestation,
            customer_execution_attestation=customer_attestation,
            root=repo_root(),
        )
        manifest_errors = json_schema_errors(evidence_manifest, "evidence-manifest")
        manifest_errors.extend(validate_evidence_manifest(evidence_manifest, base_dir=repo_root()))
        if manifest_errors:
            print("Evidence manifest generation produced an invalid manifest:", file=sys.stderr)
            print(format_errors(manifest_errors), file=sys.stderr)
            return 1
        write_json(args.evidence_manifest, evidence_manifest)
    if args.out:
        print_score_summary(scored, args.out, args.markdown)
        if args.evidence_manifest:
            print(f"Evidence manifest: {args.evidence_manifest}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="python -m actionboundary")
    subcommands = parser.add_subparsers(dest="command", required=True)

    validate = subcommands.add_parser("validate", help="Validate trace, scenario-pack, or verdict artifacts")
    validate.add_argument("--trace", help="Trace submission JSON")
    validate.add_argument("--scenario-pack", help="Scenario pack manifest JSON")
    validate.add_argument("--verdict", help="Scored verdict JSON")
    validate.add_argument("--evidence-manifest", help="Machine-verifiable evidence manifest JSON")
    validate.add_argument(
        "--evidence-events",
        help="Vendor-neutral minimal evidence-event JSON",
    )
    validate.add_argument(
        "--evidence-root",
        help="Base directory for relative artifact paths recorded in --evidence-manifest",
    )
    validate.set_defaults(func=cmd_validate)

    readiness = subcommands.add_parser(
        "readiness",
        help="Assess minimal event coverage before a customer pilot",
    )
    readiness.add_argument(
        "--evidence-events",
        required=True,
        help="Vendor-neutral minimal evidence-event JSON",
    )
    readiness.add_argument("--out", help="Write the readiness gap report JSON")
    readiness.set_defaults(func=cmd_readiness)

    score = subcommands.add_parser("score", help="Score a trace against an authoritative scenario pack")
    score.add_argument("trace_path", nargs="?", help="Trace submission JSON")
    score.add_argument("--trace", help="Trace submission JSON")
    score.add_argument("--scenario-pack", required=True, help="Authoritative scenario pack manifest JSON")
    score.add_argument("--out", help="Write scored verdict JSON to this path")
    score.add_argument("--markdown", help="Write Markdown summary to this path")
    score.add_argument("--pdf", help="Write a PDF report rendered from the scored verdict")
    score.add_argument("--evidence-manifest", help="Write machine-verifiable evidence manifest JSON")
    score.add_argument(
        "--execution-profile",
        choices=sorted(EXECUTION_PROFILES),
        default=REPOSITORY_SYNTHETIC_PROFILE,
        help="Declare whether evidence came from the repository harness or a customer-owned execution",
    )
    score.add_argument(
        "--customer-execution-attestation",
        help="Customer execution attestation JSON required by the customer_executed profile",
    )
    score.set_defaults(func=cmd_score)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
