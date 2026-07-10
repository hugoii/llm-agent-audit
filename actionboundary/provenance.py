"""Machine-verifiable evidence provenance helpers."""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

from .contracts import (
    CONTRACT_SET_VERSION,
    CUSTOMER_EXECUTED_PROFILE,
    EVIDENCE_MANIFEST_SCHEMA_VERSION,
    EXECUTION_PROFILES,
    REPOSITORY_SYNTHETIC_PROFILE,
)


HASH_ALGORITHM = "sha256"
JSON_CANONICALIZATION = "json-canonical-v1"
TRACE_CANONICALIZATION = "json-canonical-v1-strip-trace-sha256"
RAW_CANONICALIZATION = "raw-bytes-v1"
TRACE_SELF_HASH_KEYS = {"trace_sha256"}
HEX_SHA256_LEN = 64


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def canonical_json_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def canonical_json_sha256(value: Any) -> str:
    return sha256_bytes(canonical_json_bytes(value))


def strip_keys(value: Any, keys: set[str]) -> Any:
    if isinstance(value, dict):
        return {
            key: strip_keys(item, keys)
            for key, item in value.items()
            if key not in keys
        }
    if isinstance(value, list):
        return [strip_keys(item, keys) for item in value]
    return value


def trace_submission_sha256(trace: dict[str, Any]) -> str:
    return canonical_json_sha256(strip_keys(trace, TRACE_SELF_HASH_KEYS))


def scenario_pack_sha256(manifest: dict[str, Any]) -> str:
    return canonical_json_sha256(manifest)


def verdict_sha256(verdict: dict[str, Any]) -> str:
    return canonical_json_sha256(verdict)


def raw_file_sha256(path: str | Path) -> str:
    source = Path(path)
    digest = hashlib.sha256()
    with source.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def load_json_file(path: str | Path) -> dict[str, Any]:
    value = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path}: top-level JSON value must be an object")
    return value


def hash_for_json_artifact(value: dict[str, Any], canonicalization: str) -> str:
    if canonicalization == TRACE_CANONICALIZATION:
        return trace_submission_sha256(value)
    if canonicalization == JSON_CANONICALIZATION:
        return canonical_json_sha256(value)
    raise ValueError(f"unsupported JSON canonicalization: {canonicalization}")


def relative_path(path: str | Path, root: str | Path | None = None) -> str:
    source = Path(path)
    if root is None:
        return source.as_posix()
    try:
        return source.resolve().relative_to(Path(root).resolve()).as_posix()
    except ValueError:
        return source.as_posix()


def json_artifact_descriptor(
    path: str | Path,
    value: dict[str, Any],
    *,
    kind: str,
    root: str | Path | None = None,
    canonicalization: str = JSON_CANONICALIZATION,
) -> dict[str, Any]:
    return {
        "kind": kind,
        "path": relative_path(path, root),
        "hash_algorithm": HASH_ALGORITHM,
        "canonicalization": canonicalization,
        "sha256": hash_for_json_artifact(value, canonicalization),
    }


def raw_artifact_descriptor(
    path: str | Path,
    *,
    kind: str,
    root: str | Path | None = None,
) -> dict[str, Any]:
    return {
        "kind": kind,
        "path": relative_path(path, root),
        "hash_algorithm": HASH_ALGORITHM,
        "canonicalization": RAW_CANONICALIZATION,
        "sha256": raw_file_sha256(path),
    }


def iter_declared_trace_hashes(value: Any) -> list[str]:
    found: list[str] = []
    if isinstance(value, dict):
        for key, item in value.items():
            if key == "trace_sha256" and isinstance(item, str) and item:
                found.append(item)
            else:
                found.extend(iter_declared_trace_hashes(item))
    elif isinstance(value, list):
        for item in value:
            found.extend(iter_declared_trace_hashes(item))
    return found


def is_sha256(value: str) -> bool:
    return len(value) == HEX_SHA256_LEN and all(char in "0123456789abcdef" for char in value)


def artifact_path(base_dir: Path, descriptor: dict[str, Any]) -> Path:
    path = Path(str(descriptor.get("path") or ""))
    if path.is_absolute():
        return path
    return base_dir / path


def check_artifact_descriptor(base_dir: str | Path, descriptor: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    base = Path(base_dir)
    path = artifact_path(base, descriptor)
    if not path.is_file():
        return [f"artifact missing: {descriptor.get('path')}"]
    expected = str(descriptor.get("sha256") or "")
    canonicalization = str(descriptor.get("canonicalization") or "")
    try:
        if canonicalization == RAW_CANONICALIZATION:
            observed = raw_file_sha256(path)
        elif canonicalization in {JSON_CANONICALIZATION, TRACE_CANONICALIZATION}:
            observed = hash_for_json_artifact(load_json_file(path), canonicalization)
        else:
            return [f"artifact {descriptor.get('path')} has unsupported canonicalization: {canonicalization}"]
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        return [f"artifact {descriptor.get('path')} could not be hashed: {exc}"]
    if expected != observed:
        errors.append(
            f"artifact {descriptor.get('path')} sha256 mismatch: expected {expected}, observed {observed}"
        )
    return errors


def integrity_check(name: str, status: str, *, expected: str = "", observed: str = "", reason: str = "") -> dict[str, str]:
    out = {"name": name, "status": status}
    if expected:
        out["expected"] = expected
    if observed:
        out["observed"] = observed
    if reason:
        out["reason"] = reason
    return out


def run_summary(run: dict[str, Any]) -> dict[str, Any]:
    verdict_obj = run.get("verdict") if isinstance(run.get("verdict"), dict) else {}
    return {
        "scenario_id": run.get("scenario_id"),
        "run_id": run.get("run_id"),
        "trace_id": run.get("trace_id") or run.get("correlation_id"),
        "verdict": verdict_obj.get("overall"),
        "evidence_complete": not bool(verdict_obj.get("missing_evidence")),
        "missing_evidence": verdict_obj.get("missing_evidence") or [],
    }


def evidence_completeness_summary(run_summaries: list[dict[str, Any]]) -> dict[str, Any]:
    missing_by_run = [
        {
            "scenario_id": item.get("scenario_id"),
            "run_id": item.get("run_id"),
            "missing_evidence": item.get("missing_evidence") or [],
        }
        for item in run_summaries
        if item.get("missing_evidence")
    ]
    incomplete = len(missing_by_run)
    return {
        "scope": "submitted_runs_only",
        "submitted_runs_complete": incomplete == 0,
        "all_runs_complete": incomplete == 0,
        "complete_runs": len(run_summaries) - incomplete,
        "incomplete_runs": incomplete,
        "missing_evidence_by_run": missing_by_run,
    }


def expected_integrity_checks(
    *,
    trace: dict[str, Any] | None,
    trace_hash: str,
    verdict: dict[str, Any],
    pack_hash: str = "",
    policy_version: str = "",
    semantic_match: bool | None = None,
) -> list[dict[str, str]]:
    checks = [
        integrity_check(
            "policy_version_matches_verdict",
            "PASS" if policy_version == (verdict.get("policy_version") or verdict.get("schema_version")) else "FAIL",
            expected=policy_version,
            observed=str(verdict.get("policy_version") or verdict.get("schema_version") or ""),
        ),
        integrity_check(
            "trace_hash_matches_verdict",
            "PASS" if verdict.get("trace_sha256") == trace_hash else "FAIL",
            expected=trace_hash,
            observed=str(verdict.get("trace_sha256") or ""),
        ),
    ]
    if pack_hash:
        checks.append(
            integrity_check(
                "scenario_pack_hash_matches_verdict",
                "PASS" if verdict.get("scenario_pack_sha256") == pack_hash else "FAIL",
                expected=pack_hash,
                observed=str(verdict.get("scenario_pack_sha256") or ""),
            )
        )
    if trace is not None:
        declared_trace_hashes = sorted(set(iter_declared_trace_hashes(trace)))
        if declared_trace_hashes:
            checks.append(
                integrity_check(
                    "declared_trace_hashes_match_submission",
                    "PASS" if all(item == trace_hash for item in declared_trace_hashes) else "FAIL",
                    expected=trace_hash,
                    observed=",".join(declared_trace_hashes),
                )
            )
    if semantic_match is not None:
        checks.append(
            integrity_check(
                "verdict_semantically_matches_trace_and_scenario_pack",
                "PASS" if semantic_match else "FAIL",
                expected="exact_recomputation_match",
                observed="match" if semantic_match else "mismatch",
            )
        )
    return checks


def attestation_integrity_checks(
    attestation: dict[str, Any],
    *,
    trace: dict[str, Any],
    trace_hash: str,
    pack_hash: str,
) -> list[dict[str, str]]:
    engagement_id = str(trace.get("engagement_id") or "")
    attested_engagement_id = str(attestation.get("engagement_id") or "")
    export_hash = str(
        ((attestation.get("log_export") or {}).get("export_artifact_sha256") or "")
        if isinstance(attestation.get("log_export"), dict)
        else ""
    )
    checks = [
        integrity_check(
            "customer_attestation_trace_hash_matches",
            "PASS" if attestation.get("trace_sha256") == trace_hash else "FAIL",
            expected=trace_hash,
            observed=str(attestation.get("trace_sha256") or ""),
        ),
        integrity_check(
            "customer_attestation_scenario_pack_hash_matches",
            "PASS" if attestation.get("scenario_pack_sha256") == pack_hash else "FAIL",
            expected=pack_hash,
            observed=str(attestation.get("scenario_pack_sha256") or ""),
        ),
        integrity_check(
            "customer_attestation_engagement_matches_trace",
            "PASS" if engagement_id and attested_engagement_id == engagement_id else "FAIL",
            expected=engagement_id,
            observed=attested_engagement_id,
        ),
    ]
    if export_hash:
        checks.append(
            integrity_check(
                "customer_attestation_log_export_hash_matches_trace",
                "PASS" if export_hash == trace_hash else "FAIL",
                expected=trace_hash,
                observed=export_hash,
            )
        )
    return checks


def build_evidence_manifest(
    *,
    trace_path: str | Path,
    trace: dict[str, Any],
    verdict_path: str | Path,
    verdict: dict[str, Any],
    scenario_pack_path: str | Path | None = None,
    scenario_pack: dict[str, Any] | None = None,
    markdown_path: str | Path | None = None,
    pdf_path: str | Path | None = None,
    execution_profile: str = REPOSITORY_SYNTHETIC_PROFILE,
    customer_execution_attestation_path: str | Path | None = None,
    customer_execution_attestation: dict[str, Any] | None = None,
    root: str | Path | None = None,
    generated_at_utc: str | None = None,
) -> dict[str, Any]:
    if scenario_pack_path is None or scenario_pack is None:
        raise ValueError("an evidence manifest requires an authoritative scenario pack artifact")
    if execution_profile not in EXECUTION_PROFILES:
        raise ValueError(f"unsupported execution profile: {execution_profile}")
    if execution_profile == CUSTOMER_EXECUTED_PROFILE and (
        customer_execution_attestation_path is None
        or customer_execution_attestation is None
    ):
        raise ValueError("customer_executed evidence requires a customer execution attestation")
    if execution_profile == REPOSITORY_SYNTHETIC_PROFILE and (
        customer_execution_attestation_path is not None
        or customer_execution_attestation is not None
    ):
        raise ValueError("repository_synthetic evidence cannot include a customer execution attestation")
    artifacts: dict[str, Any] = {
        "trace": json_artifact_descriptor(
            trace_path,
            trace,
            kind="trace",
            root=root,
            canonicalization=TRACE_CANONICALIZATION,
        ),
        "verdict": json_artifact_descriptor(
            verdict_path,
            verdict,
            kind="verdict",
            root=root,
        ),
    }
    artifacts["scenario_pack"] = json_artifact_descriptor(
        scenario_pack_path,
        scenario_pack,
        kind="scenario_pack",
        root=root,
    )
    if markdown_path is not None:
        artifacts["markdown_report"] = raw_artifact_descriptor(
            markdown_path,
            kind="markdown_report",
            root=root,
        )
    if pdf_path is not None:
        artifacts["pdf_report"] = raw_artifact_descriptor(
            pdf_path,
            kind="pdf_report",
            root=root,
        )
    if customer_execution_attestation_path is not None and customer_execution_attestation is not None:
        artifacts["customer_execution_attestation"] = json_artifact_descriptor(
            customer_execution_attestation_path,
            customer_execution_attestation,
            kind="customer_execution_attestation",
            root=root,
        )

    policy_version = str(verdict.get("policy_version") or verdict.get("schema_version") or "")
    from .authorization_score import score_submission, validate_verdict_matches_recomputed

    recomputed = score_submission(
        trace,
        scenario_pack,
        trace_sha256=artifacts["trace"]["sha256"],
        scenario_pack_sha256=artifacts["scenario_pack"]["sha256"],
    )
    semantic_match = not validate_verdict_matches_recomputed(verdict, recomputed)
    checks = expected_integrity_checks(
        trace=trace,
        trace_hash=artifacts["trace"]["sha256"],
        verdict=verdict,
        pack_hash=artifacts.get("scenario_pack", {}).get("sha256", ""),
        policy_version=policy_version,
        semantic_match=semantic_match,
    )
    if customer_execution_attestation is not None:
        checks.extend(
            attestation_integrity_checks(
                customer_execution_attestation,
                trace=trace,
                trace_hash=artifacts["trace"]["sha256"],
                pack_hash=artifacts["scenario_pack"]["sha256"],
            )
        )

    run_summaries = []
    for run in verdict.get("runs") or []:
        if not isinstance(run, dict):
            continue
        run_summaries.append(run_summary(run))

    return {
        "schema_version": EVIDENCE_MANIFEST_SCHEMA_VERSION,
        "contract_set_version": CONTRACT_SET_VERSION,
        "execution_profile": execution_profile,
        "generated_at_utc": generated_at_utc or utc_now_iso(),
        "policy_version": policy_version,
        "artifacts": artifacts,
        "integrity": {
            "complete": all(item["status"] == "PASS" for item in checks),
            "checks": checks,
        },
        "evidence_completeness": evidence_completeness_summary(run_summaries),
        "scenario_coverage": verdict.get("scenario_coverage") or {
            "complete": False,
            "total_scenarios": 0,
            "tested_scenarios": len(run_summaries),
            "untested_scenario_ids": [],
        },
        "runs": run_summaries,
    }


def validate_evidence_manifest(value: dict[str, Any], *, base_dir: str | Path) -> list[str]:
    errors: list[str] = []
    artifacts = value.get("artifacts")
    if not isinstance(artifacts, dict):
        return ["evidence manifest artifacts object is required"]
    for name in ("trace", "verdict", "scenario_pack"):
        descriptor = artifacts.get(name)
        if not isinstance(descriptor, dict):
            errors.append(f"evidence manifest artifacts.{name} is required")
            continue
        errors.extend(check_artifact_descriptor(base_dir, descriptor))
    execution_profile = str(value.get("execution_profile") or "")
    if execution_profile not in EXECUTION_PROFILES:
        errors.append(f"unsupported execution profile: {execution_profile}")
    attestation_desc = artifacts.get("customer_execution_attestation")
    if execution_profile == CUSTOMER_EXECUTED_PROFILE and not isinstance(attestation_desc, dict):
        errors.append("customer_executed evidence manifest requires artifacts.customer_execution_attestation")
    if execution_profile == REPOSITORY_SYNTHETIC_PROFILE and isinstance(attestation_desc, dict):
        errors.append("repository_synthetic evidence manifest cannot bind a customer execution attestation")

    for name in ("markdown_report", "pdf_report", "customer_execution_attestation"):
        descriptor = artifacts.get(name)
        if isinstance(descriptor, dict):
            errors.extend(check_artifact_descriptor(base_dir, descriptor))

    try:
        trace_path = artifact_path(Path(base_dir), artifacts["trace"])
        verdict_path = artifact_path(Path(base_dir), artifacts["verdict"])
        pack_path = artifact_path(Path(base_dir), artifacts["scenario_pack"])
        trace = load_json_file(trace_path)
        verdict = load_json_file(verdict_path)
        scenario_pack = load_json_file(pack_path)
    except Exception as exc:  # pragma: no cover - defensive after descriptor checks
        errors.append(f"artifact could not be loaded for cross-checks: {exc}")
        return errors

    customer_attestation = None
    if isinstance(attestation_desc, dict):
        try:
            attestation_path = artifact_path(Path(base_dir), attestation_desc)
            customer_attestation = load_json_file(attestation_path)
            schema_path = Path(__file__).resolve().parents[1] / "pilot" / "customer_execution_attestation.schema.json"
            attestation_schema = load_json_file(schema_path)
            schema_errors = sorted(
                Draft202012Validator(attestation_schema).iter_errors(customer_attestation),
                key=lambda item: tuple(item.absolute_path),
            )
            errors.extend(
                f"customer execution attestation schema: {error.message}"
                for error in schema_errors
            )
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            errors.append(f"customer execution attestation could not be loaded: {exc}")

    trace_desc = artifacts.get("trace") if isinstance(artifacts.get("trace"), dict) else {}
    expected_trace_hash = str(trace_desc.get("sha256") or "")
    if verdict.get("trace_sha256") != expected_trace_hash:
        errors.append(
            "evidence manifest verdict trace_sha256 mismatch: "
            f"expected {expected_trace_hash}, observed {verdict.get('trace_sha256')}"
        )

    pack_desc = artifacts.get("scenario_pack") if isinstance(artifacts.get("scenario_pack"), dict) else {}
    expected_pack_hash = str(pack_desc.get("sha256") or "")
    if verdict.get("scenario_pack_sha256") != expected_pack_hash:
        errors.append(
            "evidence manifest verdict scenario_pack_sha256 mismatch: "
            f"expected {expected_pack_hash}, observed {verdict.get('scenario_pack_sha256')}"
        )

    # A hash proves artifact identity, not that the verdict is true. Recompute
    # the complete verdict from the bound trace and authoritative scenario pack.
    from .authorization_score import score_submission, validate_verdict_matches_recomputed

    try:
        recomputed = score_submission(
            trace,
            scenario_pack,
            trace_sha256=expected_trace_hash,
            scenario_pack_sha256=expected_pack_hash,
        )
    except ValueError as exc:
        errors.append(f"evidence manifest semantic recomputation failed: {exc}")
        recomputed = None
    semantic_errors = (
        validate_verdict_matches_recomputed(verdict, recomputed)
        if recomputed is not None
        else ["semantic recomputation was unavailable"]
    )
    errors.extend(
        f"evidence manifest semantic verdict: {error}"
        for error in semantic_errors
    )

    policy_version = str(value.get("policy_version") or "")
    verdict_policy_version = str(verdict.get("policy_version") or verdict.get("schema_version") or "")
    if policy_version != verdict_policy_version:
        errors.append(
            "evidence manifest policy_version mismatch: "
            f"expected {verdict_policy_version}, observed {policy_version}"
        )

    integrity = value.get("integrity") if isinstance(value.get("integrity"), dict) else {}
    declared_checks = integrity.get("checks") if isinstance(integrity.get("checks"), list) else []
    declared_by_name = {
        item.get("name"): item
        for item in declared_checks
        if isinstance(item, dict) and isinstance(item.get("name"), str)
    }
    expected_checks = expected_integrity_checks(
        trace=trace,
        trace_hash=expected_trace_hash,
        verdict=verdict,
        pack_hash=expected_pack_hash,
        policy_version=policy_version,
        semantic_match=not semantic_errors,
    )
    if customer_attestation is not None:
        expected_checks.extend(
            attestation_integrity_checks(
                customer_attestation,
                trace=trace,
                trace_hash=expected_trace_hash,
                pack_hash=expected_pack_hash,
            )
        )
    for expected in expected_checks:
        actual = declared_by_name.get(expected["name"])
        if actual is None:
            errors.append(f"evidence manifest missing integrity check: {expected['name']}")
            continue
        if actual.get("status") != expected.get("status"):
            errors.append(
                f"evidence manifest integrity check {expected['name']} has wrong status: "
                f"expected {expected.get('status')}, observed {actual.get('status')}"
            )
        for field in ("expected", "observed"):
            if expected.get(field) and actual.get(field) != expected.get(field):
                errors.append(
                    f"evidence manifest integrity check {expected['name']} has wrong {field}: "
                    f"expected {expected.get(field)}, observed {actual.get(field)}"
                )
        if expected.get("status") != "PASS":
            errors.append(f"evidence manifest integrity check failed: {expected['name']}")
    expected_complete = all(item.get("status") == "PASS" for item in expected_checks)
    if integrity.get("complete") != expected_complete:
        errors.append(
            "evidence manifest integrity.complete mismatch: "
            f"expected {expected_complete}, observed {integrity.get('complete')}"
        )

    expected_runs = [
        run_summary(run)
        for run in verdict.get("runs") or []
        if isinstance(run, dict)
    ]
    declared_runs = value.get("runs") if isinstance(value.get("runs"), list) else []
    if len(declared_runs) != len(expected_runs):
        errors.append(
            "evidence manifest run summary count mismatch: "
            f"expected {len(expected_runs)}, observed {len(declared_runs)}"
        )
    for index, expected_run in enumerate(expected_runs, start=1):
        if index > len(declared_runs) or not isinstance(declared_runs[index - 1], dict):
            continue
        actual_run = declared_runs[index - 1]
        for field in ("scenario_id", "run_id", "trace_id", "verdict", "evidence_complete", "missing_evidence"):
            if actual_run.get(field) != expected_run.get(field):
                errors.append(
                    f"evidence manifest runs[{index}].{field} mismatch: "
                    f"expected {expected_run.get(field)!r}, observed {actual_run.get(field)!r}"
                )

    expected_completeness = evidence_completeness_summary(expected_runs)
    declared_completeness = value.get("evidence_completeness")
    if declared_completeness != expected_completeness:
        errors.append("evidence manifest evidence_completeness summary mismatch")

    expected_coverage = verdict.get("scenario_coverage")
    if value.get("scenario_coverage") != expected_coverage:
        errors.append("evidence manifest scenario_coverage mismatch")

    for index, run in enumerate(verdict.get("runs") or [], start=1):
        if not isinstance(run, dict):
            continue
        verdict_obj = run.get("verdict") if isinstance(run.get("verdict"), dict) else {}
        if not (run.get("run_id") or run.get("trace_id") or run.get("correlation_id")):
            errors.append(f"verdict runs[{index}] lacks run_id, trace_id, or correlation_id")
        if verdict_obj.get("system_authorization_boundary") == "PASS" and verdict_obj.get("missing_evidence"):
            errors.append(f"verdict runs[{index}] declares PASS with missing evidence")
    return errors
