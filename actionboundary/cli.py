"""Small CLI for validating and scoring ActionBoundary trace artifacts."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any

from pilot.score_authorization_trace import markdown_summary, score_submission


FINAL_STATUSES = {
    "EXPLOITED",
    "BLOCKED",
    "BENIGN_PASS",
    "BENIGN_REGRESSION",
    "INCONCLUSIVE",
    "INFRASTRUCTURE_ERROR",
    "NOT_TESTED",
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


def validate_trace_submission(trace: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    runs = trace.get("runs")
    normalized_actions = trace.get("normalized_actions")
    if not isinstance(runs, list) and not isinstance(normalized_actions, list):
        errors.append("trace must contain either runs[] or normalized_actions[]")
        return errors

    if isinstance(runs, list):
        if not runs:
            errors.append("runs must contain at least one run")
        for index, run in enumerate(runs, start=1):
            if not isinstance(run, dict):
                errors.append(f"runs[{index}] must be an object")
                continue
            if not run.get("scenario_id"):
                errors.append(f"runs[{index}].scenario_id is required")
            if not run.get("expected_authorization"):
                errors.append(f"runs[{index}].expected_authorization is required")
            if "tool_call_trace" not in run:
                errors.append(f"runs[{index}].tool_call_trace is required")
            elif not isinstance(run.get("tool_call_trace"), list):
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
        for field in ("expected_authorization", "required_runtime_evidence", "allowed_terminal_states"):
            if field not in scenario:
                errors.append(f"scenarios[{index}].{field} is required")
    return errors


def validate_verdict(scored: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if scored.get("schema_version") != "pilot-verdict-1.1":
        errors.append("verdict schema_version must be pilot-verdict-1.1")
    if not isinstance(scored.get("counts"), dict):
        errors.append("verdict counts object is required")
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


def cmd_validate(args: argparse.Namespace) -> int:
    errors: list[str] = []
    trace = load_json(args.trace) if args.trace else None
    manifest = load_manifest(args.scenario_pack)
    verdict = load_json(args.verdict) if args.verdict else None

    if trace is None and manifest is None and verdict is None:
        errors.append("provide --trace, --scenario-pack, or --verdict")
    if trace is not None:
        errors.extend(f"trace: {error}" for error in validate_trace_submission(trace))
    if manifest is not None:
        errors.extend(f"scenario-pack: {error}" for error in validate_scenario_pack(manifest))
    if verdict is not None:
        errors.extend(f"verdict: {error}" for error in validate_verdict(verdict))

    scored = None
    if not errors and trace is not None:
        scored = score_submission(trace, manifest)
        errors.extend(f"scored verdict: {error}" for error in validate_verdict(scored))

    if errors:
        print("Validation failed:", file=sys.stderr)
        print(format_errors(errors), file=sys.stderr)
        return 1

    if scored is not None:
        counts = ", ".join(f"{key}={value}" for key, value in sorted(scored.get("counts", {}).items()))
        print(f"OK: trace is scoreable ({counts or 'no runs'})")
    elif manifest is not None and verdict is None:
        print("OK: scenario pack shape is valid")
    elif verdict is not None:
        print("OK: verdict shape is valid")
    else:
        print("OK")
    return 0


def cmd_score(args: argparse.Namespace) -> int:
    trace = load_json(args.trace)
    manifest = load_manifest(args.scenario_pack)
    errors = [f"trace: {error}" for error in validate_trace_submission(trace)]
    if manifest is not None:
        errors.extend(f"scenario-pack: {error}" for error in validate_scenario_pack(manifest))
    if errors:
        print("Validation failed:", file=sys.stderr)
        print(format_errors(errors), file=sys.stderr)
        return 1

    scored = score_submission(trace, manifest)
    verdict_errors = validate_verdict(scored)
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
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="python -m actionboundary")
    subcommands = parser.add_subparsers(dest="command", required=True)

    validate = subcommands.add_parser("validate", help="Validate trace, scenario-pack, or verdict artifacts")
    validate.add_argument("--trace", help="Trace submission JSON")
    validate.add_argument("--scenario-pack", help="Scenario pack manifest JSON")
    validate.add_argument("--verdict", help="Scored verdict JSON")
    validate.set_defaults(func=cmd_validate)

    score = subcommands.add_parser("score", help="Score a trace against an optional scenario pack")
    score.add_argument("--trace", required=True, help="Trace submission JSON")
    score.add_argument("--scenario-pack", help="Scenario pack manifest JSON")
    score.add_argument("--out", help="Write scored verdict JSON to this path")
    score.add_argument("--markdown", help="Write Markdown summary to this path")
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
