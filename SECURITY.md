# Security Policy

This repository is a defensive project for testing authorization boundaries in
tool-using AI agents. Please do not use public issues, pull requests, or
discussions to share secrets, production traces, customer data, PHI, PII,
credentials, or live exploit details.

## Supported scope

The supported public scope is the current `master` branch and the latest tagged release of this repository.

The public code and documents are intended for:

- staging or sandbox testing;
- synthetic data and harmless canary values;
- trace-backed review of tool calls and authorization evidence;
- defensive research, reproduction, and documentation.

The public repository is not a place to submit client data or private pilot
traces. Client work is handled separately under the agreed engagement terms,
NDA/MSA where applicable, and a staging-safe data path. See
[Trust & Data Handling](TRUST.md) for the buyer-facing trace handling,
retention, deletion, and third-party processing defaults.

## Reporting a vulnerability

If you believe you found a vulnerability in this repository, email:

`jiahao@actionboundary.dev`

Please include:

- the affected file, script, or document;
- a short description of the issue;
- reproduction steps using synthetic data;
- any relevant environment details;
- the impact you believe the issue could have.

Do not include real customer data, production credentials, live secrets, or
third-party confidential information. If the report involves sensitive details,
send a minimal description first and I will coordinate a safer way to exchange
information.

## Response expectations

This is an independent project, not a 24/7 enterprise support desk. I aim to
acknowledge credible security reports within two business days and will
prioritize issues that could cause unsafe execution, misleading evidence,
secret exposure, or broken reproducibility.

Paid client support, retests, and contractual response terms are governed by the written engagement, not by this public repository.

## Out of scope

The following are out of scope for public vulnerability reports unless they demonstrate a concrete risk in this repository:

- attacks against production systems not owned by this project;
- reports that require real customer data or live credentials;
- generic model jailbreaks without a tool-call or evidence impact;
- social engineering, spam, or denial-of-service against maintainers or third
  parties;
- requests to certify the project as compliant with SOC 2, ISO 27001, HIPAA,
  PCI, or similar frameworks.

## Safety rule

Run tests only in staging or sandbox environments with written authorization.
The review method is designed to answer one narrow question: can a tool-using
agent take a high-impact action without trusted, current, scope-matching
authorization evidence?
