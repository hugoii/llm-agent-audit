"""Build the public evidence bundle uploaded and attested by CI."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil
import zipfile

from actionboundary.contracts import (
    CONTRACT_SET_VERSION,
    PUBLIC_EVIDENCE_BUNDLE_SCHEMA_VERSION,
)


ROOT = Path(__file__).resolve().parents[1]

REQUIRED_SOURCE_FILES = [
    "examples/ap_payment_trace.redacted.json",
    "examples/ap_payment_scenario_pack.json",
    "normalized_trace.schema.json",
    "scenario_pack.schema.json",
    "verdict.schema.json",
    "evidence_manifest.schema.json",
    "public_evidence_bundle.schema.json",
    "public_snapshot_suites.json",
    "VERIFY-EVIDENCE.md",
]

GENERATED_ARTIFACTS = [
    "actionboundary-scored-example.json",
    "actionboundary-scored-example.md",
    "actionboundary-scored-example.pdf",
    "actionboundary-evidence-manifest.json",
    "public-snapshot-rescore-summary.json",
]


def public_snapshot_source_files() -> list[str]:
    registry = json.loads((ROOT / "public_snapshot_suites.json").read_text(encoding="utf-8"))
    files: list[str] = []
    for suite in registry.get("suites") or []:
        snapshot_dir = ROOT / str(suite["snapshot_dir"])
        scenario_pack = str(suite["scenario_pack"])
        files.append(scenario_pack)
        readme = snapshot_dir / "README.md"
        if readme.is_file():
            files.append(readme.relative_to(ROOT).as_posix())
        files.extend(
            path.relative_to(ROOT).as_posix()
            for path in sorted(snapshot_dir.glob(str(suite["submission_glob"])))
        )
        files.extend(
            path.relative_to(ROOT).as_posix()
            for path in sorted(snapshot_dir.glob(f"{suite['verdict_prefix']}*.md"))
        )
    return sorted(set(files))


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def copy_file(source: Path, target: Path) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, target)


def rel(path: Path, base: Path) -> str:
    return path.relative_to(base).as_posix()


def write_json(path: Path, value: dict[str, object]) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def make_evidence_manifest_portable(path: Path) -> None:
    manifest = json.loads(path.read_text(encoding="utf-8"))
    artifacts = manifest.get("artifacts") or {}
    for kind in ("verdict", "markdown_report", "pdf_report"):
        descriptor = artifacts.get(kind)
        if not isinstance(descriptor, dict) or not descriptor.get("path"):
            continue
        filename = Path(str(descriptor["path"])).name
        descriptor["path"] = f"tmp/public-evidence/{filename}"
    write_json(path, manifest)


def build_bundle(
    generated_dir: Path,
    output_dir: Path,
    zip_path: Path,
    *,
    git_sha: str = "",
    github_repository: str = "",
    github_ref: str = "",
    github_workflow: str = "",
    github_run_id: str = "",
    github_run_attempt: str = "",
) -> None:
    if output_dir.exists():
        shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    zip_path.parent.mkdir(parents=True, exist_ok=True)
    if zip_path.exists():
        zip_path.unlink()

    copied: list[Path] = []
    for item in REQUIRED_SOURCE_FILES + public_snapshot_source_files():
        source = ROOT / item
        if not source.is_file():
            raise FileNotFoundError(source)
        target = output_dir / item
        copy_file(source, target)
        copied.append(target)

    for item in GENERATED_ARTIFACTS:
        source = generated_dir / item
        if not source.is_file():
            raise FileNotFoundError(source)
        target = output_dir / "tmp" / "public-evidence" / item
        copy_file(source, target)
        if item == "actionboundary-evidence-manifest.json":
            make_evidence_manifest_portable(target)
        copied.append(target)

    file_entries = [
        {
            "path": rel(path, output_dir),
            "sha256": sha256_file(path),
            "bytes": path.stat().st_size,
        }
        for path in sorted(copied)
    ]
    bundle_manifest = {
        "schema_version": PUBLIC_EVIDENCE_BUNDLE_SCHEMA_VERSION,
        "contract_set_version": CONTRACT_SET_VERSION,
        "generated_at_utc": (
            datetime.now(timezone.utc)
            .replace(microsecond=0)
            .isoformat()
            .replace("+00:00", "Z")
        ),
        "git_sha": git_sha,
        "evidence_manifest_path": "tmp/public-evidence/actionboundary-evidence-manifest.json",
        "snapshot_rescore_summary_path": "tmp/public-evidence/public-snapshot-rescore-summary.json",
        "ci": {
            "provider": "github-actions",
            "repository": github_repository,
            "ref": github_ref,
            "workflow": github_workflow,
            "run_id": github_run_id,
            "run_attempt": github_run_attempt,
        },
        "attestation": {
            "subject_path": "actionboundary-public-evidence-bundle.zip",
            "verify_command": "gh attestation verify actionboundary-public-evidence-bundle.zip -R hugoii/llm-agent-audit",
        },
        "files": file_entries,
    }
    manifest_path = output_dir / "PUBLIC-EVIDENCE-BUNDLE.json"
    write_json(manifest_path, bundle_manifest)
    file_entries.append(
        {
            "path": rel(manifest_path, output_dir),
            "sha256": sha256_file(manifest_path),
            "bytes": manifest_path.stat().st_size,
        }
    )

    sums_path = output_dir / "SHA256SUMS"
    checksum_lines = [
        f"{entry['sha256']}  {entry['path']}\n"
        for entry in sorted(file_entries, key=lambda item: str(item["path"]))
    ]
    sums_path.write_text(
        "".join(checksum_lines),
        encoding="utf-8",
    )

    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(output_dir.rglob("*")):
            if path.is_file():
                archive.write(path, rel(path, output_dir))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--generated-dir", required=True, help="Directory containing scored example artifacts")
    parser.add_argument("--output-dir", required=True, help="Directory to assemble before zipping")
    parser.add_argument("--zip", required=True, help="Output zip path")
    parser.add_argument("--git-sha", default="", help="Git commit SHA for CI provenance metadata")
    parser.add_argument("--github-repository", default="", help="GitHub repository owner/name")
    parser.add_argument("--github-ref", default="", help="GitHub ref that triggered the build")
    parser.add_argument("--github-workflow", default="", help="GitHub workflow name")
    parser.add_argument("--github-run-id", default="", help="GitHub Actions run id")
    parser.add_argument("--github-run-attempt", default="", help="GitHub Actions run attempt")
    args = parser.parse_args()

    build_bundle(
        generated_dir=Path(args.generated_dir),
        output_dir=Path(args.output_dir),
        zip_path=Path(args.zip),
        git_sha=args.git_sha,
        github_repository=args.github_repository,
        github_ref=args.github_ref,
        github_workflow=args.github_workflow,
        github_run_id=args.github_run_id,
        github_run_attempt=args.github_run_attempt,
    )
    print(f"wrote {args.zip}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
