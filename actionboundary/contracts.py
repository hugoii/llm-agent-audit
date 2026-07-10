"""Canonical public contract identifiers and execution profiles."""

from __future__ import annotations


CONTRACT_SET_VERSION = "actionboundary-contract-set-1.0"
VERDICT_SCHEMA_VERSION = "pilot-verdict-1.2"
EVIDENCE_MANIFEST_SCHEMA_VERSION = "evidence-manifest-1.1"
CUSTOMER_EXECUTION_ATTESTATION_SCHEMA_VERSION = "customer-execution-attestation-1.1"
PUBLIC_EVIDENCE_BUNDLE_SCHEMA_VERSION = "public-evidence-bundle-1.1"

REPOSITORY_SYNTHETIC_PROFILE = "repository_synthetic"
CUSTOMER_EXECUTED_PROFILE = "customer_executed"
EXECUTION_PROFILES = {
    REPOSITORY_SYNTHETIC_PROFILE,
    CUSTOMER_EXECUTED_PROFILE,
}

CANONICAL_SCHEMA_FILES = {
    "trace": "normalized_trace.schema.json",
    "scenario_pack": "scenario_pack.schema.json",
    "verdict": "verdict.schema.json",
    "evidence_manifest": "evidence_manifest.schema.json",
    "public_evidence_bundle": "public_evidence_bundle.schema.json",
    "customer_execution_attestation": "pilot/customer_execution_attestation.schema.json",
}

LEGACY_ADAPTER_SCHEMA_FILES = {
    "flexible_pilot_trace": "pilot/trace_schema.json",
    "strict_normalized_evidence": "pilot/normalized_evidence_schema.json",
}
