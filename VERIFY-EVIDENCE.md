# Verify ActionBoundary Evidence Artifacts

This page describes how to verify the public synthetic evidence bundle produced
by GitHub Actions, and how the same pattern maps to a private client review.

## Public Synthetic Bundle

The `Public evidence bundle` workflow builds a zip file named
`actionboundary-public-evidence-bundle.zip`. The bundle contains:

- the redacted AP/payment trace;
- the scenario pack;
- the scored verdict JSON;
- the Markdown verdict summary;
- `evidence-manifest-1.0`;
- the relevant schemas;
- `public-evidence-bundle-1.0`;
- `SHA256SUMS`;
- `PUBLIC-EVIDENCE-BUNDLE.json`.

`PUBLIC-EVIDENCE-BUNDLE.json` records the commit SHA, GitHub Actions workflow
metadata, generation timestamp, attestation subject path, and the SHA-256 digest
of each evidence payload file. `SHA256SUMS` is the flat checksum file for
portable verification and also covers `PUBLIC-EVIDENCE-BUNDLE.json`.

## What To Verify

1. Download the latest `actionboundary-public-evidence-bundle` artifact from
   the GitHub Actions run for `master`.
2. Verify GitHub's artifact attestation:

   ```bash
   gh attestation verify actionboundary-public-evidence-bundle.zip \
     -R hugoii/llm-agent-audit
   ```

3. Unzip the bundle and verify file checksums:

   ```bash
   unzip actionboundary-public-evidence-bundle.zip -d actionboundary-public-evidence-bundle
   cd actionboundary-public-evidence-bundle
   sha256sum -c SHA256SUMS
   ```

4. Re-run ActionBoundary's semantic evidence check from the unzipped bundle root:

   ```bash
   python -m actionboundary validate \
     --evidence-root . \
     --evidence-manifest tmp/public-evidence/actionboundary-evidence-manifest.json
   ```

## What This Proves

This proves that GitHub Actions built the public bundle from the repository and
that the bundle files match their recorded hashes. GitHub's artifact attestation
adds the workflow provenance for the zip itself. The ActionBoundary evidence
manifest then proves that the scored verdict matches the trace, scenario pack,
policy version, and report artifact recorded in the evidence manifest.

## What This Does Not Prove

The public bundle is synthetic. It does not prove anything about a customer's
private system. For client work, the customer-controlled execution environment
must also preserve a separate execution attestation: who ran the scenario pack,
when it ran, what environment and agent build were used, which log source was
exported, what hash identifies the exported trace, and where the trace artifact
was placed for retention.

For high-trust client reviews, store the trace, report, evidence manifest, and
customer execution attestation in customer-controlled append-only or write-once
storage, then record the storage URI, retention window, and access-control owner
in the customer execution attestation.
